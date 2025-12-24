import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)

from typing import Optional

class Tracker:
    """Tracks existing draw data."""
    def __init__(self, config):
        self.config = config
    def get_existing_data(self) -> Optional[pd.DataFrame]:
            """Get existing data if available."""
            try:
                logger.info("Checking for existing data...")
                if self.config.DRAWS_JSON.exists() and self.config.PROCESSED.exists():
                    
                    with open(self.config.DRAWS_JSON, "r") as f:
                        data = json.load(f)
                    logger.info(f"Found {len(data.get('rounds', []))} draws from {self.config.DRAWS_JSON}")

                    processed_data = pd.read_csv(self.config.PROCESSED)
                    logger.info(f"Found {len(processed_data)} draws from {self.config.PROCESSED}")

                    return processed_data
                logger.info("No existing data or incomplete.")  
                return None
            except Exception as e:
                logger.error(f"Error reading existing data: {e}")
                return None