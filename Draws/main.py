from manager import Manager

import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

def main():
    # MANAGER
    manager = Manager()
    manager.clear_screen()
    success, existing_count, new_count = manager.update_data()
    if success:
        print(f"Data updated successfully: {existing_count} → {new_count} draws")
    else:
        print("Data was not updated.")

    # ANALYZER
    with open(manager.config.JSON_PATH, "r") as f:
        data = json.load(f)
    analysis = manager.analyzer.analyze(data)

    if analysis:
        print("✅ Analysis completed and files saved")
    else:
        print("   ❌ Analysis failed")
    


if __name__ == "__main__":
    main()