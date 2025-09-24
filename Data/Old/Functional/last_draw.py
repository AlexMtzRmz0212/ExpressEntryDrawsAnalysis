import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Tuple
from utils import clear_terminal, fetch_json_data, logger
from update_draws import DrawUpdater

def get_latest_draw_from_csv(csv_path: str = "./Data/ExpressEntry.csv") -> Optional[Dict]:
    """
    Get the latest draw information from CSV file.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Dictionary containing latest draw information or None if file doesn't exist
    """
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            return None
        
        # Get the most recent draw (assuming draws are ordered by drawNumber)
        latest_draw = df.iloc[0].to_dict()
        return latest_draw
        
    except FileNotFoundError:
        return None

def get_previous_draw_from_csv(csv_path: str = "./Data/ExpressEntry.csv") -> Optional[Dict]:
    """
    Get the previous draw information from CSV file.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Dictionary containing previous draw information or None if not available
    """
    try:
        df = pd.read_csv(csv_path)
        if len(df) < 2:
            return None
        
        # Get the previous draw
        previous_draw = df.iloc[1].to_dict()
        return previous_draw
        
    except FileNotFoundError:
        return None

def check_data_freshness() -> Tuple[bool, int, int]:
    """
    Check if data needs updating.
    
    Returns:
        Tuple of (needs_update, existing_count, api_draw_count)
    """
    updater = DrawUpdater()
    
    # Check if CSV file exists and has data
    csv_path = Path("./Data/ExpressEntry.csv")
    existing_count = 0
    if csv_path.exists():
        try:
            existing_count = updater.get_existing_record_count()
        except Exception as e:
            logger.error(f"Error reading existing CSV file: {e}")
            existing_count = 0
    
    # Always check API for available draws, even if CSV doesn't exist
    try:
        data = fetch_json_data(updater.api_url)
        api_draw_count = len(data["rounds"])
        
        if existing_count < api_draw_count:
            return True, existing_count, api_draw_count
        else:
            return False, existing_count, api_draw_count
            
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        # If we can't reach API, assume no update needed but show existing data
        return False, existing_count, 0

def ask_user_for_update(existing_count: int, api_draw_count: int) -> bool:
    """
    Ask user if they want to update the data.
    
    Args:
        existing_count: Number of existing records
        api_draw_count: Number of records available from API
        
    Returns:
        True if user wants to update, False otherwise
    """
    print(f"Your current data has {existing_count} draws.")
    print(f"There are {api_draw_count} draws available from the API.")
    
    if existing_count == 0:
        print("No data file found. Would you like to download the latest data?")
    else:
        print(f"{api_draw_count - existing_count} new draws available. Would you like to update?")
    
    while True:
        response = input("Update data? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'.")

def format_draw_info(draw_data: Dict, previous_draw_data: Optional[Dict] = None):
    """
    Format and display the last draw information.
    
    Args:
        draw_data: Dictionary containing draw information
        previous_draw_data: Dictionary containing previous draw information
    """
    # Extract data with defaults
    draw_date = draw_data.get("drawDate", "Unknown")
    draw_date_full = draw_data.get("drawDateFull", draw_data.get("drawDate", "Unknown"))
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
    
    if draw_date != "Unknown":
        try:
            draw_datetime = datetime.strptime(draw_date, "%Y-%m-%d")
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
                
                if previous_draw_date and previous_draw_date != "Unknown":
                    try:
                        previous_draw_datetime = datetime.strptime(previous_draw_date, "%Y-%m-%d")
                        days_between = (draw_datetime - previous_draw_datetime).days
                        print(f"Days between last two draws: {days_between}")
                        
                        # Show previous draw details
                        prev_draw_number = previous_draw_data.get("drawNumber", "Unknown")
                        prev_draw_date_full = previous_draw_data.get("drawDateFull", previous_draw_date)
                        prev_min_crs = previous_draw_data.get("drawCRS", "Unknown")
                        print(f"Previous draw #{prev_draw_number} on {prev_draw_date_full} (CRS: {prev_min_crs})")
                    except ValueError:
                        print("Could not parse previous draw date.")
                else:
                    print("Could not parse previous draw date.")
            else:
                print("No previous draw data available.")
        except ValueError:
            print("Could not parse draw date for time calculations.")
    else:
        print("Draw date not available.")

def main():
    """Main execution function."""
    clear_terminal()
    
    print("Checking for the latest Express Entry draw...\n")
    
    # Check if data needs updating
    needs_update, existing_count, api_draw_count = check_data_freshness()
    
    # Ask user if they want to update
    if needs_update:
        should_update = ask_user_for_update(existing_count, api_draw_count)
        if should_update:
            updater = DrawUpdater()
            data_updated = updater.update_data()
            if data_updated:
                print("Data was successfully updated.\n")
        else:
            print("Using existing data.\n")
    
    # Get the latest and previous draws from CSV
    latest_draw = get_latest_draw_from_csv()
    previous_draw = get_previous_draw_from_csv()
    
    if latest_draw:
        format_draw_info(latest_draw, previous_draw)
    else:
        print("No draw data available. Please check your data files.")

if __name__ == "__main__":
    main()