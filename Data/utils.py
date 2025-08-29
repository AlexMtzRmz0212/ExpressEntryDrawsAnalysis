import os
import logging
from typing import Optional, Dict, Any
import requests
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_terminal():
    """Clear terminal output for better visibility."""
    os.system('cls' if os.name == 'nt' else 'clear')

def fetch_json_data(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Fetch JSON data from API endpoint.
    
    Args:
        url: The API endpoint URL
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary containing JSON data
        
    Raises:
        SystemExit: If API request fails or data format is invalid
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        raise