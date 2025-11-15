import pandas as pd
import json
import requests
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Tuple, Any
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExpressEntryManager:
    """Unified class to manage Express Entry draw data."""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.json_path = self.data_dir / "Data/EE.json"
        self.api_url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
        
        # Define columns to keep (reduced for efficiency)
        self.selected_columns = [
            "drawNumber", 
            "drawDate", 
            # "drawDateFull",
            "drawDateTime", 
            "drawName", 
            "drawSize", 
            "drawCRS", 
            "drawText2", 
            "drawCutOff",
            "drawDistributionAsOn",
            "dd1",
            "dd2",
            "dd3",
            "dd4",
            "dd5",
            "dd6",
            "dd7",
            "dd8",
            "dd9",
            "dd10",
            "dd11",
            "dd12",
            "dd13",
            "dd14",
            "dd15",
            "dd16",
            "dd17",
            "dd18"
        ]
    
    def clear_terminal(self):
        """Clear terminal output."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def fetch_json_data(self, timeout: int = 10) -> Dict[str, Any]:
        """Fetch JSON data from API endpoint."""
        try:
            response = requests.get(self.api_url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data: {e}")
            raise
    
    def get_existing_data(self) -> Optional[pd.DataFrame]:
        """Get existing data from JSON if available."""
        try:
            if self.json_path.exists():
                with open(self.json_path, "r") as f:
                    data = json.load(f)
                df = pd.DataFrame(data["rounds"])
                # Select only needed columns that exist in the data
                available_columns = [col for col in self.selected_columns if col in df.columns]
                logger.info(f"Loaded {len(df)} existing draws from JSON")
                return df[available_columns]
            return None
        except Exception as e:
            logger.error(f"Error reading JSON: {e}")
            return None
    
    def process_draw_data(self, rounds_data: list) -> pd.DataFrame:
        """Process raw rounds data into structured DataFrame."""
        df = pd.DataFrame(rounds_data)
        
        # Select only needed columns that exist in the data
        available_columns = [col for col in self.selected_columns if col in df.columns]
        return df[available_columns].sort_values('drawDate',ascending=False).reset_index(drop=True)
    
    def parse_draw_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse various datetime formats found in the data."""
        if not datetime_str or not isinstance(datetime_str, str):
            return None
        
        # Clean the string
        datetime_str = datetime_str.strip()
        
        # Handle specific problematic patterns first
        
        # Pattern 1: "January 23, 2025 2025-01-23 15:30:04 UTC" (duplicate dates)
        if "202" in datetime_str and datetime_str.count("202") > 1:
            try:
                # Extract the ISO datetime part (YYYY-MM-DD HH:MM:SS)
                for part in datetime_str.split():
                    if part.startswith("202") and "-" in part and ":" in " ".join(datetime_str.split()[datetime_str.split().index(part):]):
                        # Find the time part
                        parts = datetime_str.split()
                        iso_index = parts.index(part)
                        if iso_index + 1 < len(parts) and ":" in parts[iso_index + 1]:
                            iso_str = f"{parts[iso_index]} {parts[iso_index + 1]} UTC"
                            return datetime.strptime(iso_str, "%Y-%m-%d %H:%M:%S UTC")
            except (ValueError, IndexError):
                pass
        
        # Pattern 2: "May 31, 2024 at12:48:30 UTC" (missing space after 'at')
        if "at" in datetime_str and "at " not in datetime_str:
            datetime_str = datetime_str.replace("at", "at ")
        
        # Pattern 3: Handle various comma and spacing issues
        datetime_str = datetime_str.replace("  ", " ")  # Remove double spaces
        
        # Pattern 4: Handle "AM/PM" inconsistencies (like "15:48:39 AM")
        # Remove AM/PM when time is clearly in 24-hour format
        time_match = re.search(r'(\d{1,2}:\d{2}:\d{2})\s*(AM|PM)', datetime_str, re.IGNORECASE)
        if time_match:
            time_part, am_pm = time_match.groups()
            hour = int(time_part.split(':')[0])
            if hour >= 13:  # If hour is 13 or more, it's already 24-hour format
                datetime_str = datetime_str.replace(f" {am_pm}", "").replace(am_pm, "")
        
        # Pattern 5: Handle "March 01, 2023, at 17:24:39 UTC" (comma before 'at')
        datetime_str = re.sub(r',\s*at\s+', ' at ', datetime_str)
        
        # Pattern 6: Handle "February 02 2022 at 14:16:27 UTC" (missing comma in date)
        # Add comma after day if missing: "February 02 2022" -> "February 02, 2022"
        date_part_match = re.search(r'([A-Za-z]+)\s+(\d{1,2})\s+(\d{4})', datetime_str)
        if date_part_match and ',' not in datetime_str:
            month, day, year = date_part_match.groups()
            datetime_str = datetime_str.replace(f"{month} {day} {year}", f"{month} {day}, {year}")
        
        # Try multiple standard formats
        formats_to_try = [
            "%B %d, %Y at %H:%M:%S UTC",        # "January 31, 2015 at 11:59:48 UTC"
            "%B %d, %Y %H:%M:%S UTC",           # "March 20, 2023 14:30:00 UTC" 
            "%B %d, %Y %H:%M:%S %p UTC",        # "October 25, 2023 03:48:39 PM UTC"
            "%B %d,%Y %H:%M:%S UTC",            # "January 31,2015 at 11:59:48 UTC"
            "%B %d, %Y, %H:%M:%S UTC",          # "November 1, 2017, at 12:55:44 UTC"
            "%B %d, %Y, at %H:%M:%S UTC",       # "March 01, 2023, at 17:24:39 UTC"
            "%B %d %Y %H:%M:%S UTC",            # "February 02 2022 at 14:16:27 UTC" (after fix)
            "%Y-%m-%d %H:%M:%S UTC",            # "2025-01-23 15:30:04 UTC"
            "%B %d, %Y %H:%M:%S",               # No timezone
            "%B %d, %Y at %H:%M:%S",            # No timezone with 'at'
        ]
        
        for fmt in formats_to_try:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        # Final attempt: More flexible parsing for really problematic cases
        try:
            # Extract just the date part using regex
            date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', datetime_str)
            if date_match:
                month, day, year = date_match.groups()
                # Extract time part
                time_match = re.search(r'(\d{1,2}:\d{2}:\d{2})', datetime_str)
                if time_match:
                    time_str = time_match.group(1)
                    # Create a basic datetime
                    base_datetime = datetime.strptime(f"{month} {day} {year} {time_str}", "%B %d %Y %H:%M:%S")
                    return base_datetime
        except ValueError:
            pass
        
        logger.warning(f"Could not parse datetime: {datetime_str}")
        return None
        
    def update_data(self) -> Tuple[bool, int, int]:
        """Update draw data from API. Returns (success, existing_count, new_count)."""
        try:
            # Fetch new data
            data = self.fetch_json_data()
            new_df = self.process_draw_data(data["rounds"])
            new_count = len(new_df)

            # Add today's datetime as metadata
            # Use local time zone for updated_at
            local_time = datetime.now().astimezone()
            data["metadata"] = {
                "updated_at": local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            }

            # Check existing data
            existing_df = self.get_existing_data()
            existing_count = len(existing_df) if existing_df is not None else 0
            
            # Only update if there are changes
            if existing_count == new_count and existing_df is not None:
                logger.info("Number of draws unchanged")
                # Still save to update metadata
                with open(self.json_path, "w") as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Updated metadata: {existing_count} draws")
                return False, existing_count, new_count
            
            # Save new data to JSON
            with open(self.json_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Updated data: {existing_count} → {new_count} draws")
            return True, existing_count, new_count
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False, 0, 0
    
    def get_latest_draws(self, count: int = 2) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Get latest and previous draw data efficiently."""
        df = self.get_existing_data()
        if df is None or df.empty:
            return None, None
        
        latest = df.iloc[0].to_dict() if len(df) > 0 else None
        previous = df.iloc[1].to_dict() if len(df) > 1 else None
        
        return latest, previous
    
    def check_data_freshness(self) -> Tuple[bool, int, int]:
        """Check if data needs updating without full download."""
        existing_df = self.get_existing_data()
        existing_count = len(existing_df) if existing_df is not None else 0
        
        try:
            data = self.fetch_json_data()
            api_count = len(data["rounds"])
            return existing_count < api_count, existing_count, api_count
        except:
            return False, existing_count, 0
    
    def format_draw_info(self, draw_data: Dict, previous_draw_data: Optional[Dict] = None):
        """Format and display draw information."""
        if not draw_data:
            print("No draw data available")
            return
        
        # Extract data with safe defaults
        draw_number = draw_data.get("drawNumber", "Unknown")
        draw_date = draw_data.get("drawDate", "Unknown")
        draw_date_full = draw_data.get("drawDateFull", draw_date)
        draw_datetime_str = draw_data.get("drawDateTime", "")
        draw_name = draw_data.get("drawName", "Unknown")
        draw_size = draw_data.get("drawSize", "Unknown")
        min_crs = draw_data.get("drawCRS", "Unknown")

        # Display
        separator = "=" * 50
        print(f"\n{separator}\nLATEST EXPRESS ENTRY DRAW #{draw_number}\n{separator}")
        print(f"Date: {draw_datetime_str}")
        print(f"Type: {draw_name}")
        print(f"Invitations: {draw_size}")
        print(f"Minimum CRS: {min_crs}")
        
        # Time calculations
        if draw_date != "Unknown":
            try:
                current_date = datetime.now(timezone.utc).replace(tzinfo=None)
                draw_datetime = datetime.strptime(draw_date, "%Y-%m-%d")
                days_since = (current_date - draw_datetime).days
                
                time_msg = "TODAY!" if days_since == 0 else f"{days_since} day ago" if days_since == 1 else f"{days_since} days ago"
                print(f"\nThis draw happened {time_msg}")
                
                # Compare with previous draw
                if previous_draw_data:
                    prev_date = previous_draw_data.get("drawDate")
                    if prev_date and prev_date != "Unknown":
                        prev_datetime = datetime.strptime(prev_date, "%Y-%m-%d")
                        days_between = (draw_datetime - prev_datetime).days
                        # prev_crs = previous_draw_data.get("drawCRS", "Unknown")
                        print(f"Days since previous draw: {days_between}")
                        # print(f"Previous draw CRS: {prev_crs}")
                        
            except ValueError:
                print("\nCould not parse date information")
        
        print(separator)
        return draw_number, draw_datetime, draw_name, draw_size, min_crs, days_since, days_between

    def analyze_draws(self):
        """Analyze draw data from the JSON file and display summary statistics."""
        if not self.json_path.exists():
            print("\n❌ Analysis failed: JSON file not found. Please update data first.")
            return

        try:
            with open(self.json_path, "r") as f:
                data = json.load(f)

            # Convert to DataFrame
            df = pd.DataFrame(data["rounds"])

            # --- Data Cleaning & Preparation ---
            # Convert key columns to numeric types for calculation.
            # 'coerce' will turn any non-numeric values (like 'N/A') into NaN (Not a Number)
            df['drawDate'] = pd.to_datetime(df['drawDate'], errors='coerce')
            df['drawSize'] = pd.to_numeric(df['drawSize'], errors='coerce')
            df['drawCRS'] = pd.to_numeric(df['drawCRS'], errors='coerce')

            # --- Analysis ---
            try:
                earliest_date = df['drawDate'].min().date() if not df['drawDate'].isnull().all() else "N/A"
                earliest_date = earliest_date if isinstance(earliest_date, str) else earliest_date.isoformat()
                print("earliest_date:", earliest_date)
                
                latest_date = df['drawDate'].max().date() if not df['drawDate'].isnull().all() else "N/A"
                latest_date = latest_date if isinstance(latest_date, str) else latest_date.isoformat()  
                print("latest_date:", latest_date)

                total_draws = len(df)
                print("total_draws:", total_draws)

                highest_draw_size = int(df['drawSize'].max()) if not df['drawSize'].isnull().all() else "N/A"
                print("highest_draw_size:", highest_draw_size)

                average_draw_size = round(df['drawSize'].mean(), 2) if not df['drawSize'].isnull().all() else "N/A"
                print("average_draw_size:", average_draw_size)

                lowest_draw_size = int(df['drawSize'].min()) if not df['drawSize'].isnull().all() else "N/A"
                print("lowest_draw_size:", lowest_draw_size)

                cv_draw_size = round(df['drawSize'].std() / df['drawSize'].mean()*100, 2) if not df['drawSize'].isnull().all() and df['drawSize'].mean() != 0 else "N/A"
                print("cv_draw_size:", cv_draw_size)

                highest_crs = int(df['drawCRS'].max()) if not df['drawCRS'].isnull().all() else "N/A"
                print("highest_crs:", highest_crs)

                print(df['drawCRS'].dtype)  # Debugging line to check dtype
                average_crs = round(df['drawCRS'].mean(), 2) if not df['drawCRS'].isnull().all() else "N/A"
                print("average_crs:", average_crs)

                lowest_crs = int(df['drawCRS'].min()) if not df['drawCRS'].isnull().all() else "N/A"
                print("lowest_crs:", lowest_crs)

                cv_crs = round(df['drawCRS'].std() / df['drawCRS'].mean()*100, 2) if not df['drawCRS'].isnull().all() and df['drawCRS'].mean() != 0 else "N/A"
                print("cv_crs:", cv_crs)

            except Exception as e:
                logger.error(f"Error during analysis calculation: {e}")
                print("\n❌ Error during analysis calculation.")
                return None
            
            try:
                analysis = {
                    "updated":{
                        "last": data.get("metadata", {}).get("updated_at", "N/A")
                    },
                    "draws": {
                        "total": total_draws
                    },
                    "draw date": {
                        "earliest": earliest_date,
                        "latest": latest_date
                    },
                    "size": {
                        "highest": highest_draw_size,
                        "average": average_draw_size,
                        "lowest": lowest_draw_size,
                        "coefficient_of_variation": cv_draw_size
                    },
                    "score": {
                        "highest": highest_crs,
                        "average": average_crs,
                        "lowest": lowest_crs,
                        "coefficient_of_variation": cv_crs
                    }
                }
                with open(self.data_dir / "Data/analysis.json", "w") as f:
                    json.dump(analysis, f, indent=2)
            except Exception as e:
                logger.error(f"Error during analysis saving: {e}")
                print("\n❌ Error during analysis saving.")
                return None

            # Run time analysis
            time_analysis = self.analyze_draw_times()
            
            # Save full draws data for web visualization
            with open(self.data_dir / "Data/EE.json", "w") as f:
                json.dump(data, f, indent=2)
                
            print(f"✅ Time analysis: {time_analysis.get('total_draws_with_times', 0)} draws with times")
            return analysis

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to analyze JSON file: {e}")
            print("\n❌ Analysis failed due to a problem with the JSON file.")
        except Exception as e:
            logger.error(f"An unexpected error occurred during analysis: {e}")
            print("\n❌ An unexpected error occurred during analysis.")
    
    def send_email(self, subject: str, body: str, to_email: str, from_email: str, smtp_server: str, smtp_port: int, smtp_user: str, smtp_password: str):
        """Send an email with the given subject and body."""
        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info("Email sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def get_draw_times_for_analysis(self) -> list:
        """Extract draw times for web visualization."""
        try:
            with open(self.json_path, "r") as f:
                data = json.load(f)
            
            draws_data = []
            for draw in data["rounds"]:
                draw_info = {
                    "drawNumber": draw.get("drawNumber"),
                    "drawDateTime": draw.get("drawDateTime"),
                    "drawName": draw.get("drawName"),
                    "drawSize": draw.get("drawSize"),
                    "drawCRS": draw.get("drawCRS")
                }
                draws_data.append(draw_info)
            
            return draws_data
        except Exception as e:
            logger.error(f"Error extracting draw times: {e}")
            return []
    
    def analyze_draw_times(self) -> dict:
        """Analyze draw times and return statistics for web visualization."""
        try:
            with open(self.json_path, "r") as f:
                data = json.load(f)
            
            draws = data["rounds"]
            hour_counts = [0] * 24
            valid_times = []
            draw_timeline = []  # For the line chart
            
            for draw in draws:
                draw_time = draw.get("drawDateTime")
                
                if draw_time:
                    parsed_time = self.parse_draw_datetime(draw_time)
                    if parsed_time:
                        hour = parsed_time.hour
                        hour_counts[hour] += 1
                        
                        # Add to valid times for detailed analysis
                        valid_times.append({
                            "drawNumber": draw.get("drawNumber"),
                            "hour": hour,
                            "time": parsed_time.strftime("%H:%M"),
                            "date": parsed_time.strftime("%Y-%m-%d"),
                            "datetime_iso": parsed_time.isoformat(),
                            "drawName": draw.get("drawName"),
                            "original_string": draw_time
                        })
                        
                        # Add to timeline for line chart (chronological order)
                        draw_timeline.append({
                            "date": parsed_time.strftime("%Y-%m-%d"),
                            "datetime": parsed_time.isoformat(),
                            "time": parsed_time.hour + parsed_time.minute/60,  # Decimal hour for plotting
                            "hour": hour,
                            "minute": parsed_time.minute,
                            "drawNumber": draw.get("drawNumber"),
                            "drawName": draw.get("drawName"),
                            "drawSize": draw.get("drawSize"),
                            "drawCRS": draw.get("drawCRS")
                        })
            
            # Sort timeline by date for proper line chart ordering
            draw_timeline.sort(key=lambda x: x["datetime"])
            
            # Calculate statistics
            total_draws = len(valid_times)
            #most_common_hour = hour_counts.index(max(hour_counts)) if total_draws > 0 else None
            if total_draws > 0:
                max_count = max(hour_counts)
                max_indices = [i for i, c in enumerate(hour_counts) if c == max_count]
                if max_indices:
                    # group consecutive hours into ranges
                    ranges = []
                    start = end = max_indices[0]
                    for idx in max_indices[1:]:
                        if idx == end + 1:
                            end = idx
                        else:
                            ranges.append((start, end))
                            start = end = idx
                    ranges.append((start, end))
                    # pick the longest consecutive range (tie -> earliest)
                    best_start, best_end = max(ranges, key=lambda r: (r[1] - r[0] + 1, -r[0]))
                    def _fmt_hour(h: int) -> str:
                        h_mod = h % 24
                        suffix = "AM" if h_mod < 12 else "PM"
                        hour12 = h_mod % 12
                        if hour12 == 0:
                            hour12 = 12
                        return f"{hour12} {suffix}"
                    # format as "best_start AM/PM - best_end+1 AM/PM"
                    most_common_hour = f"{_fmt_hour(best_start)} - {_fmt_hour(best_end + 1)}"
                else:
                    most_common_hour = None
            else:
                most_common_hour = None
            avg_hour = sum(hour * count for hour, count in enumerate(hour_counts)) / total_draws if total_draws > 0 else None
            
            time_analysis = {
                "total_draws_with_times": total_draws,
                "hour_distribution": hour_counts,
                "most_common_hour": most_common_hour,
                "average_hour": round(avg_hour, 2) if avg_hour else None,
                "draw_times": valid_times,
                "draw_timeline": draw_timeline,  # This is for the line chart
                "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Save time analysis separately
            with open(self.data_dir / "Data/time_analysis.json", "w") as f:
                json.dump(time_analysis, f, indent=2)
            
            logger.info(f"Time analysis completed: {total_draws} draws with valid times")
            return time_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing draw times: {e}")
            return {}


def main():
    """Quick test for the new time analysis features."""
    manager = ExpressEntryManager()
    
    manager.clear_terminal()
    
    print("🧪 Testing new time analysis features...")
    
    # Test 1: Update data
    print("\n1. Updating data...")
    success, old_count, new_count = manager.update_data()
    print(f"   Update result: {success}, {old_count} -> {new_count} draws")
    
    # Test 2: Get draw times for analysis
    print("\n2. Extracting draw times...")
    draw_times = manager.get_draw_times_for_analysis()
    print(f"   Found {len(draw_times)} draws with time data")
    
    # Test 3: Run analysis (this should now save EE.json for web)
    print("\n3. Running analysis...")
    analysis = manager.analyze_draws()
    if analysis:
        print("   ✅ Analysis completed and files saved")
    else:
        print("   ❌ Analysis failed")


if __name__ == "__main__":
    main()