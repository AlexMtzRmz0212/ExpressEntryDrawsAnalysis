import requests
import pandas as pd
import os

def clear_terminal():
    """Clear terminal output for better visibility."""
    os.system('cls' if os.name == 'nt' else 'clear')

def fetch_express_entry_data(url):
    """
    Fetch Express Entry draw data from the official Canada.ca JSON API.
    
    Args:
        url (str): The API endpoint URL
        
    Returns:
        dict: JSON data containing rounds information
        
    Raises:
        SystemExit: If API request fails or data format is invalid
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises exception for bad status codes
        data = response.json()
        
        if "rounds" not in data:
            print("Error: No 'rounds' key found in the JSON data.")
            exit(1)
            
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        exit(1)

def get_existing_record_count(filename):
    """
    Get the number of existing records in the CSV file.
    
    Args:
        filename (str): Path to the CSV file
        
    Returns:
        int: Number of existing records (excluding header)
    """
    try:
        existing_df = pd.read_csv(filename)
        return len(existing_df)
    except FileNotFoundError:
        return 0

def process_draw_data(rounds_data):
    """
    Process the raw rounds data into a structured DataFrame.
    
    Args:
        rounds_data (list): List of draw round dictionaries
        
    Returns:
        pd.DataFrame: Processed DataFrame with selected columns
    """
    # Define the columns we want to keep
    selected_columns = [
        "drawNumber", "drawDate", "drawName", "drawSize", "drawCRS",
        "drawText2", "drawDateTime", "drawCutOff", "drawDistributionAsOn",
        "dd1", "dd2", "dd3", "dd4", "dd5", "dd6", "dd7", "dd8", "dd9",
        "dd10", "dd11", "dd12", "dd13", "dd14", "dd15", "dd16", "dd17", "dd18"
    ]
    
    # Convert rounds data to DataFrame
    df = pd.DataFrame(rounds_data)
    
    # Select only the columns we need
    return df[selected_columns]

def main():
    """Main execution function."""
    # Clear terminal for clean output
    clear_terminal()
    
    # API endpoint for Express Entry draw data
    api_url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
    csv_filename = "ExpressEntry.csv"
    
    # Fetch data from API
    data = fetch_express_entry_data(api_url)
    api_draw_count = len(data["rounds"])
    
    # Check existing records
    existing_count = get_existing_record_count(csv_filename)
    
    if existing_count == 0:
        print(f"No existing file found. Creating new {csv_filename}")
        print(f"API reports {api_draw_count} total draws available")
    else:
        print(f"Existing records in {csv_filename}: {existing_count}")
        print(f"API reports {api_draw_count} total draws available")
    
    # Skip processing if no new draws available
    if existing_count == api_draw_count:
        print("No new draws to add.")
        return
    
    # Process and save the data
    df = process_draw_data(data["rounds"])
    actual_records = len(df)
    df.to_csv(csv_filename, index=False)
    
    print(f"Successfully updated {csv_filename} with {actual_records} draws.")

if __name__ == "__main__":
    main()