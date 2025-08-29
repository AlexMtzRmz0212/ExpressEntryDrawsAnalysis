import requests
from datetime import datetime, timezone
import os
import logging
from typing import Optional, Dict, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_terminal():
    """Clear terminal output for better visibility."""
    os.system('cls' if os.name == 'nt' else 'clear')

def fetch_draw_info(url: str, timeout: int = 10) -> Tuple[Dict, Optional[Dict]]:
    """
    Fetch Express Entry draw information.
    
    Args:
        url: The API endpoint URL
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (latest_draw, previous_draw) information
        
    Raises:
        SystemExit: If API request fails or data format is invalid
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("rounds"):
            logger.error("No draw data found in response")
            exit(1)
            
        rounds = data["rounds"]
        
        # Return latest and previous draws
        return rounds[0], rounds[1] if len(rounds) > 1 else None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        exit(1)
    except ValueError as e:
        logger.error(f"Error parsing JSON response: {e}")
        exit(1)

def parse_date(date_str: str) -> Optional[datetime]:
    """Safely parse date string."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

def format_draw_info(draw_data: Dict, previous_draw_data: Optional[Dict] = None):
    """
    Format and display the last draw information.
    
    Args:
        draw_data: Dictionary containing draw information
        previous_draw_data: Dictionary containing previous draw information
    """
    # Extract data with defaults
    draw_date = draw_data.get("drawDate", "Unknown")
    draw_date_full = draw_data.get("drawDateFull", "Unknown")
    draw_number = draw_data.get("drawNumber", "Unknown")
    draw_name = draw_data.get("drawName", "Unknown")
    draw_size = draw_data.get("drawSize", "Unknown")
    min_crs = draw_data.get("drawCRS", "Unknown")
    
    # Format output
    separator = "=" * 50
    print(f"{separator}\nLATEST EXPRESS ENTRY DRAW INFORMATION\n{separator}")
    print(f"Draw Number: {draw_number}")
    print(f"Draw Date: {draw_date_full}")
    print(f"Draw Type: {draw_name}")
    print(f"Invitations Issued: {draw_size}")
    print(f"Minimum CRS Score: {min_crs}")
    print(separator)
    
    # Calculate days since last draw
    current_date = datetime.now(timezone.utc).replace(tzinfo=None)
    draw_datetime = parse_date(draw_date)
    
    if draw_datetime:
        days_since = (current_date - draw_datetime).days
        
        if days_since == 0:
            print("This draw happened TODAY!")
        elif days_since == 1:
            print("This draw happened YESTERDAY.")
        else:
            print(f"Days since last draw: {days_since}")
        
        # Calculate days between draws if previous draw exists
        if previous_draw_data:
            previous_draw_date = previous_draw_data.get("drawDate")
            previous_draw_datetime = parse_date(previous_draw_date)
            
            if previous_draw_datetime:
                days_between = (draw_datetime - previous_draw_datetime).days
                print(f"Days between last two draws: {days_between}")
                
                # Show previous draw details
                prev_draw_number = previous_draw_data.get("drawNumber", "Unknown")
                prev_draw_date_full = previous_draw_data.get("drawDateFull", "Unknown")
                prev_min_crs = previous_draw_data.get("drawCRS", "Unknown")
                print(f"Previous draw #{prev_draw_number} on {prev_draw_date_full} (CRS: {prev_min_crs})")
            else:
                print("Could not parse previous draw date.")
        else:
            print("No previous draw data available.")
    else:
        print("Could not parse draw date for time calculations.")

def main():
    """Main execution function."""
    clear_terminal()
    
    # API endpoint for Express Entry draw data
    api_url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
    
    print("Checking for the latest Express Entry draw...\n")
    
    # Fetch and display the latest draw information
    latest_draw, previous_draw = fetch_draw_info(api_url)
    format_draw_info(latest_draw, previous_draw)

if __name__ == "__main__":
    main()