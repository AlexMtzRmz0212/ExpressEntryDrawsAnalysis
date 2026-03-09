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

    def save_to_all(self, data: dict, df: pd.DataFrame):
        """Save data to all formats."""
        self.save_file(data, self.config.DRAWS.with_suffix('.json'), format='json')
        self.save_file(df, self.config.DRAWS.with_suffix('.csv'), format='csv')
        # self.save_file(df, self.config.DRAWS.with_suffix('.parquet'), format='parquet')
        # self.save_file(df, self.config.DRAWS.with_suffix('.pkl'), format='pickle')

    def update_data(self) -> Tuple[bool, int, int]:
        """Update data. Returns (success, existing_count, new_count)."""
        try:
            # FETCHER
            data = self.fetcher.fetch_json()
            self.raw_dict = data
            
            # PROCESSOR
            new_df = self.processor.process_data(data["rounds"])
            new_count = len(new_df)
                
            # TRACKER
            existing_df = self.tracker.get_existing_data()
            existing_count = len(existing_df) if existing_df is not None else 0

            # Add metadata
            timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            data["metadata"] = {"updated_at": timestamp}
            
            # Save new data

            self.processed_df = new_df
            
            if existing_df is None:
                logger.info("No old data found. Writing new data to files.")
                self.save_to_all(data, new_df)
                return True, existing_count, new_count
            
            elif existing_count < new_count:

                logger.info(f"New draws found. Updating data ({existing_count} -> {new_count}).")
                self.save_to_all(data, new_df)  
                return True, existing_count, new_count
            
            else:
                logger.info("No new draws. Data is up to date.")
                return False, existing_count, new_count
        
        except Exception as e:
            logger.error(f"Data update failed: {e}")
            return False, 0, 0
        
    def analyze(self):
        """Run analysis on current data."""
        if self.processed_df is None:
            logger.error("No data to analyze. Run update_data first.")
            return
        
        try:
            # Get raw data for metadata
            with open(self.config.DRAWS.with_suffix('.json'), 'r') as f:
                raw_data = json.load(f)
                logger.info(f"Loaded raw data for analysis: {len(raw_data.get('rounds', []))} rounds")
            
            # Run analyses
            draw_times = self.analyzer.get_draw_times(self.processed_df)
            time_analysis = self.analyzer.analyze_draw_times(self.processed_df)
            summary_analysis = self.analyzer.analyze_draws(self.processed_df, raw_data)
            
            logger.info(f"Analysis complete: {len(draw_times)} draws processed")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")

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

        