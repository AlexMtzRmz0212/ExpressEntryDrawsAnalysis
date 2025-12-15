from config import Config

from typing import List, Dict, Optional
from datetime import datetime

import pandas as pd
import logging
import re

logger = logging.getLogger(__name__)


class Processor:
    def __init__(self, config: Config):
        self.config = config

    def process_data(self, rounds: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(rounds)

        selected_columns = [
            col for col in self.config.SELECTED_COLUMNS
            if col in df.columns
        ]

        return df[selected_columns].sort_values('drawDate', ascending=False).reset_index(drop=True)
    
    def parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        if not datetime_str or not isinstance(datetime_str, str):
            return None
        
        datetime_str = self._clean_dt_string(datetime_str)
        parsed_dt = self._try_dt_formats(datetime_str)

        if not parsed_dt:
            parsed_dt = self._fallback_parse(datetime_str)

        if not parsed_dt:
            logger.warning(f"Failed to parse datetime string: {datetime_str}")

        return parsed_dt
    
    def _clean_dt_string(self, dt_str: str) -> str:
        """Clean and normalize datetime string."""

        # Remove double spaces
        dt_str = dt_str.replace("  ", " ")

        # Fix common patterns
        patterns = [
            (r"at(\d)", r"at \1"),  # Add space after 'at'
            (r",\s*at\s+", " at "),  # Fix comma before 'at'
        ]

        for pattern, replacement in patterns:
            dt_str = re.sub(pattern, replacement, dt_str)

        return self._fix_date_format(dt_str)
    
    def _fix_date_format(self, dt_str: str) -> str:
        """Fix common date format issues."""

        # Add comma after day if missing
        match = re.match(r'([A-Za-z]+)\s+(\d{1,2})\s+(\d{4})', dt_str)

        if match and ',' not in dt_str:
            month, day, year = match.groups()
            dt_str = dt_str.replace(
                f"{month} {day} {year}", 
                f"{month} {day}, {year}"
            )

        return dt_str
    
    def _try_dt_formats(self, dt_str: str) -> Optional[datetime]:
        """Try multiple datetime formats."""
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
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        return None
    
    def _fallback_parse(self, dt_str: str) -> Optional[datetime]:
        """Fallback method for problematic datetime strings."""
        try:
            date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', dt_str)
            time_match = re.search(r'(\d{1,2}:\d{2}:\d{2})', dt_str)
            
            if date_match and time_match:
                month, day, year = date_match.groups()
                time_str = time_match.group(1)
                return datetime.strptime(
                    f"{month} {day} {year} {time_str}", 
                    "%B %d %Y %H:%M:%S"
                )
        except ValueError:
            pass
        return None