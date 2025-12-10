import requests
from datetime import datetime
import os

def clear_terminal():
    """Clear terminal output for better visibility."""
    os.system('cls' if os.name == 'nt' else 'clear')

def fetch_draw_info(url):
    """
    Fetch Express Entry draw information.
    
    Args:
        url (str): The API endpoint URL
        
    Returns:
        tuple: (latest_draw, previous_draw) - Information about the most recent and previous draws
        
    Raises:
        SystemExit: If API request fails or data format is invalid
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if "rounds" not in data or not data["rounds"]:
            print("Error: No draw data found.")
            exit(1)
            
        rounds = data["rounds"]
        
        # Get the most recent draw (first item in the list)
        latest_draw = rounds[0]
        
        # Get the previous draw if it exists
        previous_draw = rounds[1] if len(rounds) > 1 else None
        
        return latest_draw, previous_draw
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        exit(1)

def format_draw_info(draw_data, previous_draw_data=None):
    """
    Format and display the last draw information.
    
    Args:
        draw_data (dict): Dictionary containing draw information
        previous_draw_data (dict, optional): Dictionary containing previous draw information
    """
    draw_date = draw_data.get("drawDate", "Unknown")
    draw_date_full = draw_data.get("drawDateFull", "Unknown")
    draw_number = draw_data.get("drawNumber", "Unknown")
    draw_name = draw_data.get("drawName", "Unknown")
    draw_size = draw_data.get("drawSize", "Unknown")
    min_crs = draw_data.get("drawCRS", "Unknown")
    
    
    print("=" * 50)
    print("LATEST EXPRESS ENTRY DRAW INFORMATION")
    print("=" * 50)
    print(f"Draw Number: {draw_number}")
    print(f"Draw Date: {draw_date_full}")
    print(f"Draw Type: {draw_name}")
    print(f"Invitations Issued: {draw_size}")
    print(f"Minimum CRS Score: {min_crs}")
    print("=" * 50)
    
    # Calculate days since last draw
    try:
        draw_datetime = datetime.strptime(draw_date, "%Y-%m-%d")
        current_date = datetime.now()
        days_since = (current_date - draw_datetime).days
        
        if days_since == 0:
            print("This draw happened TODAY!")
        elif days_since == 1:
            print("This draw happened YESTERDAY.")
        else:
            print(f"Days since last draw: {days_since}")
    
        # Calculate days from the last draw to the previous one
        if previous_draw_data:
            previous_draw_date = previous_draw_data.get("drawDate", "Unknown")
            if previous_draw_date != "Unknown":
                previous_draw_datetime = datetime.strptime(previous_draw_date, "%Y-%m-%d")
                days_between = (draw_datetime - previous_draw_datetime).days
                print(f"Days between last two draws: {days_between}")
                
                # Show previous draw details for reference
                prev_draw_number = previous_draw_data.get("drawNumber", "Unknown")
                prev_draw_date_full = previous_draw_data.get("drawDateFull", "Unknown")
                prev_min_crs = previous_draw_data.get("drawCRS", "Unknown")
                print(f"Previous draw #{prev_draw_number} on {prev_draw_date_full} (CRS: {prev_min_crs})")
            else:
                print("Could not parse previous draw date.")
        else:
            print("No previous draw data available.")
            
    except ValueError as e:
        print(f"Could not calculate days since last draw: {e}")

def main():
    """Main execution function."""
    # Clear terminal for clean output
    clear_terminal()
    
    # API endpoint for Express Entry draw data
    api_url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
    
    print("Checking for the latest Express Entry draw...")
    print()
    
    # Fetch and display the latest draw information
    latest_draw, previous_draw = fetch_draw_info(api_url)
    format_draw_info(latest_draw, previous_draw)

if __name__ == "__main__":
    main()