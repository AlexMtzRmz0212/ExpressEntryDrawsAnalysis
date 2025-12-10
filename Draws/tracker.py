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
                if self.config.JSON_PATH.exists():
                    with open(self.config.JSON_PATH, "r") as f:
                        data = json.load(f)
                    df = pd.DataFrame(data["rounds"])
                    columns = [
                        col for col in self.config.SELECTED_COLUMNS
                        if col in df.columns
                    ]
                    logger.info(f"Loaded {len(df)} existing draws.")
                    return df[columns]
                return None
            except Exception as e:
                logger.error(f"Error reading existing data: {e}")
                return None