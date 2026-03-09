import pandas as pd
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class Tracker:
    """Tracks existing draw data."""
    def __init__(self, config):
        self.config = config
        
    def get_existing_data(self) -> Optional[pd.DataFrame]:
        """Get existing data if available."""
        try:
            logger.info("Checking for existing data...")
            
            # Create paths with correct extensions
            json_path = self.config.DRAWS.with_suffix('.json')
            csv_path = self.config.DRAWS.with_suffix('.csv')
            
            # Prefer CSV if it exists (already processed format)
            if csv_path.exists():
                data = pd.read_csv(csv_path)
                logger.info(f"Found {len(data)} draws from {csv_path}")
                if not json_path.exists():
                    logger.warning(f"CSV found but JSON missing. Consider saving JSON for raw data.")
                    # manager.save_file(csv_path, json_path, format='json')
                return data
            
            # Fall back to JSON if CSV doesn't exist
            if json_path.exists():
                logger.info(f"CSV not found. Loading raw data from {json_path}...")
                with open(json_path, "r") as f:
                    raw_data = json.load(f)
                
                # Convert JSON to DataFrame
                rounds = raw_data.get('rounds', [])
                if rounds:
                    data = pd.DataFrame(rounds)
                    logger.info(f"Found {len(data)} draws from {json_path}")
                    return data
                else:
                    logger.info(f"No rounds found in {json_path}")
                    return None
                
            logger.info("No existing data found.")
            return None
            
        except Exception as e:
            logger.error(f"Error reading existing data: {e}")
            return None