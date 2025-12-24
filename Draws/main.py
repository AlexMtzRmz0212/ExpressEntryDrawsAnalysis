from manager import Manager

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

def updateData():
    
    manager.clear_screen()
    print("=== EXPRESS ENTRY DATA MANAGER ===")
    logger.info("Starting data update process...")
    updated, existing_count, new_count = manager.update_data()
    if updated:
        logger.info(f"Data updated successfully: {existing_count} → {new_count} draws")
    else:
        logger.info("Data was not updated.")

def main():

    print("\n=== EXPRESS ENTRY DATA ANALYSIS ===")
    # ANALYZER
    # TO DO:Use analyzer inside manager 

    # analysis = manager.analyzer.analyze(data)
    


if __name__ == "__main__":
    manager = Manager()
    updateData()
    main()