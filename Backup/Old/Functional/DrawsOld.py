""" This used to use CSV 
but the current one only uses JSON 
for efficiency and simplicity.
"""
import pandas as pd
import json
import requests
import os
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
        self.csv_path = self.data_dir / "EE.csv"
        self.json_path = self.data_dir / "EE.json"
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
        """Get existing data from CSV if available."""
        try:
            if self.csv_path.exists():
                df = pd.read_csv(self.csv_path)
                logger.info(f"Loaded {len(df)} existing draws")
                return df
            return None
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return None
    
    def process_draw_data(self, rounds_data: list) -> pd.DataFrame:
        """Process raw rounds data into structured DataFrame."""
        df = pd.DataFrame(rounds_data)
        
        # Select only needed columns that exist in the data
        available_columns = [col for col in self.selected_columns if col in df.columns]
        return df[available_columns].sort_values('drawDate',ascending=False).reset_index(drop=True)    #.sort_values('drawNumber', ascending=False).reset_index(drop=True)
    
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

            # Save JSON data
            with open(self.json_path, "w") as f:
                json.dump(data, f, indent=2)
            # Check existing data
            existing_df = self.get_existing_data()
            existing_count = len(existing_df) if existing_df is not None else 0
            
            # Only update if there are changes
            if existing_count == new_count and existing_df is not None:
                logger.info("Number of draws unchanged")
                new_df.to_csv(self.csv_path, index=False)
                logger.info(f"Updated data: {existing_count} → {new_count} draws")
                return False, existing_count, new_count
            
            # Save new data
            new_df.to_csv(self.csv_path, index=False)
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
        draw_datetime = draw_data.get("drawDateTime", "")
        draw_name = draw_data.get("drawName", "Unknown")
        draw_size = draw_data.get("drawSize", "Unknown")
        min_crs = draw_data.get("drawCRS", "Unknown")

        # Display
        separator = "=" * 50
        print(f"\n{separator}\nLATEST EXPRESS ENTRY DRAW #{draw_number}\n{separator}")
        print(f"Date: {draw_datetime}")
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
        return draw_number,draw_datetime, draw_name, draw_size, min_crs, days_since, days_between

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
                with open(self.data_dir / "analysis.json", "w") as f:
                    json.dump(analysis, f, indent=2)
            except Exception as e:
                logger.error(f"Error during analysis calculation or saving: {e}")
                print("\n❌ Error during analysis calculation or saving.")
                return None
            return analysis

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to analyze JSON file: {e}")
            print("\n❌ Analysis failed due to a problem with the JSON file.")
        except Exception as e:
            logger.error(f"An unexpected error occurred during analysis: {e}")
            print("\n❌ An unexpected error occurred during analysis.")

    def ask_user_confirmation(self, prompt: str) -> bool:
        """Get yes/no confirmation from user."""
        while True:
            response = input(f"{prompt} (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            print("Please enter 'y' or 'n'")
    
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

def main():
    """Main execution function."""
    manager = ExpressEntryManager()
    manager.clear_terminal()
    
    print("🚀 Express Entry Draw")
    print("=" * 30)
    
    # Check data status
    needs_update, existing_count, api_count = manager.check_data_freshness()
    
    # Handle updates
    if needs_update or existing_count == 0:
        if existing_count == 0:
            print("📥 No data found. Download latest draws?")
        else:
            print(f"📊 Current draws: {existing_count}")
            print(f"📈 Available online: {api_count}")
            print(f"🆕 New draws available: {api_count - existing_count}")
        
        if manager.ask_user_confirmation("Update data?"):
            success, old_count, new_count = manager.update_data()
            if success:
                print(f"✅ Updated successfully! {old_count} → {new_count} draws")
            else:
                print("❌ Update failed")
        else:
            print("ℹ️ Using existing data")
    else:
        print("✅ Data is already up to date.")
        if manager.ask_user_confirmation("Force update anyway?"):
            success, old_count, new_count = manager.update_data()
            if not success:
                print(f"✅ Forced update successful! {old_count} → {new_count} draws")
            else:
                print("❌ Forced update failed")
        else:
            print("ℹ️ No update performed.")

    # Display latest draw info
    latest, previous = manager.get_latest_draws()
    number, datetime, name, size, crs, since, between = manager.format_draw_info(latest, previous)

    manager.send_email(
        subject=f"New Express Entry Draw #{number} - {name}",
        body=f"Draw Date: {datetime}\nType: {name}\nInvitations: {size}\nMinimum CRS: {crs}\nThis Draw happened: {since}\nDays Between Previous Draw: {between}",
        to_email="jesus.mtz.rmz.jamr@gmail.com",
        from_email="alejandro.martinez.rmz97@gmail.com",
        smtp_server="smtp.example.com",
        smtp_port=587,
        smtp_user="smtp_user",
        smtp_password="smtp_password"
    )

    if manager.ask_user_confirmation("\nWould you like to see the analysis of draws?"):
        analysis = manager.analyze_draws()
        if analysis is not None:
            print("\n📊 Draw Analysis Summary:")
            print(analysis)
        else:
            print("❌ Analysis could not be performed.")

if __name__ == "__main__":
    main()

# Usage:
# # Run the main application
# python Draws.py

# # Just update data (for automation)
# python -c "from Draws import ExpressEntryManager; m = ExpressEntryManager(); m.update_data()"

# # Get latest draw info only
# python -c "from Draws import ExpressEntryManager; m = ExpressEntryManager(); latest, prev = m.get_latest_draws(); m.format_draw_info(latest, prev)"