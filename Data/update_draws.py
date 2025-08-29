import pandas as pd
import json
from pathlib import Path
from utils import fetch_json_data, logger

class DrawUpdater:
    """Class to handle Express Entry draw data updates."""
    
    def __init__(self, data_dir: str = "./Data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.csv_path = self.data_dir / "ExpressEntry.csv"
        self.json_path = self.data_dir / "ExpressEntry.json"
        self.api_url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
    
    def get_existing_record_count(self) -> int:
        """
        Get the number of existing records in the CSV file.
        
        Returns:
            Number of existing records (excluding header)
        """
        try:
            existing_df = pd.read_csv(self.csv_path)
            return len(existing_df)
        except FileNotFoundError:
            return 0
    
    def process_draw_data(self, rounds_data: list) -> pd.DataFrame:
        """
        Process the raw rounds data into a structured DataFrame.
        
        Args:
            rounds_data: List of draw round dictionaries
            
        Returns:
            Processed DataFrame with selected columns
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
    
    def update_data(self) -> bool:
        """
        Update the draw data from the API.
        
        Returns:
            True if data was updated, False if no update was needed
        """
        try:
            # Fetch data from API
            data = fetch_json_data(self.api_url)
            
            # Save JSON data
            with open(self.json_path, "w") as json_file:
                json.dump(data, json_file, indent=4)
            
            api_draw_count = len(data["rounds"])
            
            # Check existing records
            existing_count = self.get_existing_record_count()
            
            if existing_count == 0:
                logger.info(f"No existing file found. Creating new {self.csv_path}")
                logger.info(f"API reports {api_draw_count} total draws available")
            else:
                logger.info(f"Existing records in {self.csv_path}: {existing_count}")
                logger.info(f"API reports {api_draw_count} total draws available")
            
            # Skip processing if no new draws available
            if existing_count == api_draw_count:
                logger.info("No new draws to add.")
                return False
            
            # Process and save the data
            df = self.process_draw_data(data["rounds"])
            actual_records = len(df)
            df.to_csv(self.csv_path, index=False)
            
            logger.info(f"Successfully updated {self.csv_path} with {actual_records} draws.")
            return True
            
        except Exception as e:
            logger.error(f"Error updating draw data: {e}")
            return False

def main():
    """Main execution function."""
    from utils import clear_terminal
    
    clear_terminal()
    updater = DrawUpdater()
    updater.update_data()

if __name__ == "__main__":
    main()