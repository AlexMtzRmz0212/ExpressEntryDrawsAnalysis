from manager import Manager

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    manager = Manager()
    manager.clear_screen()
    manager.JUST_UPDATE()
    
if __name__ == "__main__":
    main()