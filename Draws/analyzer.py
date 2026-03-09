import logging
import json
import re

import pandas as pd
import numpy as np

from datetime import datetime
from typing import Optional, Dict, List, Any


logger = logging.getLogger(__name__)

class Analyzer:
    def __init__(self, config, processor):
        self.config = config
        self.processor = processor
        self.analysis_path = config.ANALYSIS_JSON
        self.time_analysis_path = config.TIME_ANALYSIS_JSON
    
    def get_draw_times(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract draw times for analysis."""
        if df is None or df.empty:
            logger.warning("DataFrame is empty. No draw times to extract.")
            return []
        
        draws_data = []
        for _, row in df.iterrows():
            draw_info = {
                "drawNumber": row.get("drawNumber"),
                "drawDateTime": row.get("drawDateTime"),
                "drawName": row.get("drawName"),
                "drawSize": row.get("drawSize"),
                "drawCRS": row.get("drawCRS")
            }
            draws_data.append(draw_info)
        
        return draws_data
    
    def parse_draw_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse various datetime formats found in the data."""
        if not datetime_str or not isinstance(datetime_str, str):
            return None
        
        # Clean the string
        datetime_str = datetime_str.strip()
        
        # Pattern 1: "January 23, 2025 2025-01-23 15:30:04 UTC" (duplicate dates)
        if "202" in datetime_str and datetime_str.count("202") > 1:
            try:
                for part in datetime_str.split():
                    if part.startswith("202") and "-" in part:
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
        
        datetime_str = datetime_str.replace("  ", " ")
        
        # Pattern 3: "15:48:39 AM" - remove AM/PM if 24-hour format
        time_match = re.search(r'(\d{1,2}:\d{2}:\d{2})\s*(AM|PM)', datetime_str, re.IGNORECASE)
        if time_match:
            time_part, am_pm = time_match.groups()
            hour = int(time_part.split(':')[0])
            if hour >= 13:
                datetime_str = datetime_str.replace(f" {am_pm}", "").replace(am_pm, "")
        
        # Pattern 4: "March 01, 2023, at 17:24:39 UTC" (comma before 'at')
        datetime_str = re.sub(r',\s*at\s+', ' at ', datetime_str)
        
        # Pattern 5: "February 02 2022 at 14:16:27 UTC" (missing comma)
        date_part_match = re.search(r'([A-Za-z]+)\s+(\d{1,2})\s+(\d{4})', datetime_str)
        if date_part_match and ',' not in datetime_str:
            month, day, year = date_part_match.groups()
            datetime_str = datetime_str.replace(f"{month} {day} {year}", f"{month} {day}, {year}")
        
        # Try formats
        formats_to_try = [
            "%B %d, %Y at %H:%M:%S UTC",
            "%B %d, %Y %H:%M:%S UTC",
            "%B %d, %Y %H:%M:%S %p UTC",
            "%B %d,%Y %H:%M:%S UTC",
            "%B %d, %Y, %H:%M:%S UTC",
            "%B %d, %Y, at %H:%M:%S UTC",
            "%B %d %Y %H:%M:%S UTC",
            "%Y-%m-%d %H:%M:%S UTC",
            "%B %d, %Y %H:%M:%S",
            "%B %d, %Y at %H:%M:%S",
        ]
        
        for fmt in formats_to_try:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        # Final attempt: extract date and time parts separately
        try:
            date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', datetime_str)
            if date_match:
                month, day, year = date_match.groups()
                time_match = re.search(r'(\d{1,2}:\d{2}:\d{2})', datetime_str)
                if time_match:
                    time_str = time_match.group(1)
                    return datetime.strptime(f"{month} {day} {year} {time_str}", "%B %d %Y %H:%M:%S")
        except ValueError:
            pass
        
        logger.warning(f"Could not parse datetime: {datetime_str}")
        return None

    def analyze_draw_times(self, df: pd.DataFrame) -> dict:
        """Analyze draw times and return statistics."""
        if df is None or df.empty:
            return {}
        
        draws = df.to_dict('records')
        hour_counts = [0] * 24
        valid_times = []
        draw_timeline = []
        
        for draw in draws:
            draw_time = draw.get("drawDateTime")
            if draw_time:
                parsed_time = self.parse_draw_datetime(draw_time)
                if parsed_time:
                    hour = parsed_time.hour
                    hour_counts[hour] += 1
                    
                    valid_times.append({
                        "drawNumber": draw.get("drawNumber"),
                        "hour": hour,
                        "time": parsed_time.strftime("%H:%M"),
                        "date": parsed_time.strftime("%Y-%m-%d"),
                        "datetime_iso": parsed_time.isoformat(),
                        "drawName": draw.get("drawName"),
                        "original_string": draw_time
                    })
                    
                    draw_timeline.append({
                        "date": parsed_time.strftime("%Y-%m-%d"),
                        "datetime": parsed_time.isoformat(),
                        "time": parsed_time.hour + parsed_time.minute/60,
                        "hour": hour,
                        "minute": parsed_time.minute,
                        "drawNumber": draw.get("drawNumber"),
                        "drawName": draw.get("drawName"),
                        "drawSize": draw.get("drawSize"),
                        "drawCRS": draw.get("drawCRS")
                    })
        
        draw_timeline.sort(key=lambda x: x["datetime"])
        total_draws = len(valid_times)
        
        # Find most common hour range
        most_common_hour = None
        if total_draws > 0:
            max_count = max(hour_counts)
            max_indices = [i for i, c in enumerate(hour_counts) if c == max_count]
            if max_indices:
                ranges = []
                start = end = max_indices[0]
                for idx in max_indices[1:]:
                    if idx == end + 1:
                        end = idx
                    else:
                        ranges.append((start, end))
                        start = end = idx
                ranges.append((start, end))
                best_start, best_end = max(ranges, key=lambda r: (r[1] - r[0] + 1, -r[0]))
                
                def _fmt_hour(h: int) -> str:
                    h_mod = h % 24
                    suffix = "AM" if h_mod < 12 else "PM"
                    hour12 = h_mod % 12
                    if hour12 == 0:
                        hour12 = 12
                    return f"{hour12} {suffix}"
                
                most_common_hour = f"{_fmt_hour(best_start)} - {_fmt_hour(best_end + 1)}"
        
        avg_hour = sum(hour * count for hour, count in enumerate(hour_counts)) / total_draws if total_draws > 0 else None
        
        time_analysis = {
            "total_draws_with_times": total_draws,
            "hour_distribution": hour_counts,
            "most_common_hour": most_common_hour,
            "average_hour": round(avg_hour, 2) if avg_hour else None,
            "draw_times": valid_times,
            "draw_timeline": draw_timeline,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save to file
        with open(self.time_analysis_path, "w") as f:
            json.dump(time_analysis, f, indent=2)
        
        logger.info(f"Time analysis completed: {total_draws} draws with valid times")
        return time_analysis
    
    def json_serializer(self, obj):
        """Handle non-serializable objects for JSON."""
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Type {type(obj)} not serializable")

    def analyze_draws(self, df: pd.DataFrame, raw_data: dict) -> Optional[dict]:
        """Analyze draw data and save summary statistics."""
        if df is None or df.empty:
            logger.error("No data to analyze")
            return None
        
        try:
            # Prepare data
            df_analysis = df.copy()
            df_analysis['drawDate'] = pd.to_datetime(df_analysis['drawDate'], errors='coerce')
            df_analysis['drawSize'] = pd.to_numeric(df_analysis['drawSize'], errors='coerce')
            df_analysis['drawCRS'] = pd.to_numeric(df_analysis['drawCRS'], errors='coerce')
            
            # Get latest draw
            latest_draw = df_analysis.iloc[0].to_dict() if not df_analysis.empty else {}
            
            # Calculate statistics
            earliest_date = df_analysis['drawDate'].min().date() if not df_analysis['drawDate'].isnull().all() else "N/A"
            earliest_date = earliest_date if isinstance(earliest_date, str) else earliest_date.isoformat()
            
            latest_date = df_analysis['drawDate'].max().date() if not df_analysis['drawDate'].isnull().all() else "N/A"
            latest_date = latest_date if isinstance(latest_date, str) else latest_date.isoformat()
            
            total_draws = len(df_analysis)
            highest_draw_size = int(df_analysis['drawSize'].max()) if not df_analysis['drawSize'].isnull().all() else "N/A"
            average_draw_size = round(df_analysis['drawSize'].mean(), 2) if not df_analysis['drawSize'].isnull().all() else "N/A"
            lowest_draw_size = int(df_analysis['drawSize'].min()) if not df_analysis['drawSize'].isnull().all() else "N/A"
            
            cv_draw_size = round(df_analysis['drawSize'].std() / df_analysis['drawSize'].mean() * 100, 2) \
                if not df_analysis['drawSize'].isnull().all() and df_analysis['drawSize'].mean() != 0 else "N/A"
            
            highest_crs = int(df_analysis['drawCRS'].max()) if not df_analysis['drawCRS'].isnull().all() else "N/A"
            average_crs = round(df_analysis['drawCRS'].mean(), 2) if not df_analysis['drawCRS'].isnull().all() else "N/A"
            lowest_crs = int(df_analysis['drawCRS'].min()) if not df_analysis['drawCRS'].isnull().all() else "N/A"
            
            cv_crs = round(df_analysis['drawCRS'].std() / df_analysis['drawCRS'].mean() * 100, 2) \
                if not df_analysis['drawCRS'].isnull().all() and df_analysis['drawCRS'].mean() != 0 else "N/A"
            
            # Compile analysis with latest_draw field
            analysis = {
                "latest_draw": {
                    "crs": latest_draw.get("drawCRS", "N/A"),
                    "number": latest_draw.get("drawNumber", "N/A"),
                    "date": latest_draw.get("drawDate", "N/A"),
                    "size": latest_draw.get("drawSize", "N/A"),
                    "name": latest_draw.get("drawName", "N/A")
                },
                "total_draws": total_draws,
                "updated": {
                    "last": raw_data.get("metadata", {}).get("updated_at", "N/A")
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
            
            # Save analysis
            with open(self.analysis_path, "w") as f:
                # json.dump(analysis, f, indent=2)
                json.dump(analysis, f, indent=2, default=self.json_serializer)
            
            logger.info("Analysis completed and saved")
            return analysis
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            return None