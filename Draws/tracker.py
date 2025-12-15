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
                if self.config.DRAWS_JSON.exists():
                    logger.info(f"Loading existing data from {self.config.DRAWS_JSON}")
                    with open(self.config.DRAWS_JSON, "r") as f:
                        data = json.load(f)
                    df = pd.DataFrame(data["rounds"])
                    columns = [
                        col for col in self.config.SELECTED_COLUMNS
                        if col in df.columns
                    ]
                    logger.info(f"Loaded {len(df)} existing draws.")
                    return df#[columns] # Return only selected columns
                logger.info("No existing data found.")  
                return None
            except Exception as e:
                logger.error(f"Error reading existing data: {e}")
                return None