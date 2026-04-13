import time

from controller.core.battery_log_repository import BatteryLogRepository
from controller.core.event_detector import EventDetector
from controller.core.sender import Sender
from controller.core.integration import run_once

DB_PATH = "battery_logs.sqlite"

def main():
    repo = BatteryLogRepository(DB_PATH)
    repo.create_table()

    detector = EventDetector()

    #placeholder (octopus)
    sender = Sender(repo, endpoint="http://localhost:9999/see-ya-later")

    print("Battery tracker started. Logging every 20 seconds.")

    while True:
        run_once(repo, detector, sender)
        time.sleep(20)

if __name__ == "__main__":
    main()