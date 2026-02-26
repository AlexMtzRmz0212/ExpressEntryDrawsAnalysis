import logging
import requests
from typing import Any, Dict

from config import Config

logger = logging.getLogger(__name__)

class Fetcher:
    def __init__(self, config = Config):
        self.config = config

    def fetch_json(self) -> Dict[str, Any]:
        try: 
            response = requests.get(
                self.config.URL, 
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data: {e}")
            raise