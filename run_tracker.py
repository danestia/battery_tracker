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

    print("Battery tracker started. Logging at intervals.")

    while True:
        settings = repo.load_settings()
        if settings["manual_override"] == 1:
            time.sleep(1)
            continue

        run_once(repo, detector, sender)

        time.sleep(settings["interval"])

if __name__ == "__main__":
    main()