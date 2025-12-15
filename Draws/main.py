from manager import Manager

import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

def main():

    print("=== LOTTERY DATA MANAGER ===")
    # MANAGER
    manager = Manager()
    manager.clear_screen()
    updated, existing_count, new_count = manager.update_data()
    if updated:
        print(f"Data updated successfully: {existing_count} → {new_count} draws")
    else:
        print("Data was not updated.")

    # ANALYZER
    # TO DO:Use analyzer inside manager 

    # TO DO: See if json can be saved as attribute 
    # instead of reloading from file every time


    with open(manager.config.JSON_PATH, "r") as f:
        data = json.load(f)
    analysis = manager.analyzer.analyze(data)

    if analysis:
        print("✅ Analysis completed and files saved")
    else:
        print("   ❌ Analysis failed")
    


if __name__ == "__main__":
    main()