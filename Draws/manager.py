import os
import json
import pickle
import logging
import pandas as pd

logger = logging.getLogger(__name__)

from pathlib    import Path
from typing     import Tuple, Union, Any
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

        self.raw_dict = None
        self.processed_df = None

    def clear_screen(self):
        """Clear terminal output."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def save_file(self, 
                  data: Union[dict, pd.DataFrame, list, Any], 
                  filepath: Union[str, Path],
                  format: str = 'auto') -> None:
        """
        Save data to file, automatically detecting format or using specified format.
        
        Args:
            data: Data to save (dict, DataFrame, list, or other serializable object)
            filepath: Path where to save the file
            format: 'auto' (detect from extension), 'json', 'csv', 'pickle', or 'parquet'
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine format
        if format == 'auto':
            if filepath.suffix.lower() == '.json':
                format = 'json'
            elif filepath.suffix.lower() == '.csv':
                format = 'csv'
            elif filepath.suffix.lower() == '.pkl' or filepath.suffix.lower() == '.pickle':
                format = 'pickle'
            elif filepath.suffix.lower() == '.parquet':
                format = 'parquet'
            else:
                # Default to JSON for dict/list, pickle for others
                format = 'json' if isinstance(data, (dict, list)) else 'pickle'
        
        # Save based on format
        try:
            if format == 'json':
                if isinstance(data, (pd.DataFrame, pd.Series)):
                    # Convert DataFrame/Series to dict first
                    data = data.to_dict(orient='records' if isinstance(data, pd.DataFrame) else 'list')
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                    
            elif format == 'csv':
                if isinstance(data, pd.DataFrame):
                    data.to_csv(filepath, index=False)
                elif isinstance(data, (dict, list)):
                    # Convert dict/list to DataFrame first
                    pd.DataFrame(data).to_csv(filepath, index=False)
                else:
                    raise ValueError(f"Cannot save {type(data)} to CSV")
                    
            elif format == 'pickle':
                with open(filepath, 'wb') as f:
                    pickle.dump(data, f)
                    
            elif format == 'parquet':
                if isinstance(data, pd.DataFrame):
                    data.to_parquet(filepath, index=False)
                elif isinstance(data, (dict, list)):
                    pd.DataFrame(data).to_parquet(filepath, index=False)
                else:
                    raise ValueError(f"Cannot save {type(data)} to Parquet")
                    
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            logger.info(f"Saved data to {filepath} ({format} format)")
            
        except Exception as e:
            logger.error(f"Failed to save {filepath}: {e}")
            raise

    def update_data(self) -> Tuple[bool, int, int]:
        """Update data. Returns (success, existing_count, new_count)."""
        try:
            # FETCHER
            data = self.fetcher.fetch_json()
            self.raw_dict = data
            
            # PROCESSOR
            new_df = self.processor.process_data(data["rounds"])
            self.processed_df = new_df
            new_count = len(new_df)
                
            # TRACKER
            existing_df = self.tracker.get_existing_data()
            existing_count = len(existing_df) if existing_df is not None else 0

            # Add metadata
            timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            new_df["metadata"] = {"updated_at": timestamp}
            data["metadata"] = {"updated_at": timestamp}

            # Save new data
            if existing_df is None:
                logger.info("Writing new data to files.")
                self.save_file(data, self.config.DRAWS_JSON, format='json')
                self.save_file(new_df, self.config.PROCESSED, format='csv')
                return True, existing_count, new_count
            
            elif existing_count < new_count:

                logger.info(f"New draws found. Updating data ({existing_count} -> {new_count}).")
                self.save_file(data, self.config.DRAWS_JSON, format='json')
                self.save_file(new_df, self.config.PROCESSED, format='csv')
                return True, existing_count, new_count
            
            else:
                logger.info("No new draws. Data is up to date.")
                return False, existing_count, new_count
        
        except Exception as e:
            logger.error(f"Data update failed: {e}")
            return False, 0, 0
        
    def analyze(self):
        draw_times = self.analyzer.get_draw_times()

    def JUST_UPDATE(self):
        logger.info("Starting data update process...")
        updated, existing_count, new_count = self.update_data()
        if updated:
            logger.info(f"Data updated successfully: {existing_count} → {new_count} draws")
        else:
            logger.info("Data was not updated.")

    def UPDATE_AND_ANALYZE(self):
        self.JUST_UPDATE()
        self.analyze()

        