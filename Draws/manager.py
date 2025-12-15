import os
import json
import logging

logger = logging.getLogger(__name__)

from pathlib    import Path
from typing     import Tuple
from datetime   import datetime

# module      /     Class
from config     import Config
from fetcher    import Fetcher
from processor  import Processor
from tracker    import Tracker
from analyzer   import Analyzer
from mailer     import EmailService

class Manager:
    def __init__(self, data_dir: str = "."):
        self.config             = Config()
        self.config.DATA_PATH   = Path(data_dir)
        self.config.DATA_PATH.mkdir(exist_ok=True)

        # Initialize components
        self.fetcher    = Fetcher(self.config)
        self.processor  = Processor(self.config)
        self.tracker    = Tracker(self.config)
        self.analyzer   = Analyzer(self.config, self.processor)
        self.mailer     = EmailService(self.config)

    def clear_screen(self):
        """Clear terminal output."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def write_json(self, data: dict, filepath: str) -> None:
        """Write data to JSON file."""
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def update_data(self) -> Tuple[bool, int, int]:
        """Update data. Returns (success, existing_count, new_count)."""
        try:
            # FETCHER
            data = self.fetcher.fetch_json()
            
            # PROCESSOR
            new_df = self.processor.process_data(data["rounds"])
            new_count = len(new_df)
                
            # TRACKER
            existing_df = self.tracker.get_existing_data()
            existing_count = len(existing_df) if existing_df is not None else 0

            # Add metadata
            data["metadata"] = {
                "updated_at": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            }

            # Save new data
            if existing_df is None:
                logger.info("No existing data found. Writing new data to file.")
                self.write_json(data, self.config.JSON_PATH)
                return True, existing_count, new_count
            elif existing_count < new_count:
                logger.info(f"New draws found. Updating data ({existing_count} -> {new_count}).")
                self.write_json(data, self.config.JSON_PATH)
                return True, existing_count, new_count
            else:
                logger.info("No new draws. Data is up to date.")
                return False, existing_count, new_count
        
        except Exception as e:
            logger.error(f"Data update failed: {e}")
            return False, 0, 0
        
    # TO DO
    def UPDATE_AND_ANALYZE():
        return None
    
    # TO DO > make able to select which analysis to run
    # by selecting through analyzer methods
    def analyze():
        return None