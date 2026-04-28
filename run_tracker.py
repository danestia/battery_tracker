import time

from controller.core.battery_log_repository import BatteryLogRepository
from controller.core.event_detector import EventDetector
from controller.core.sender import Sender
from controller.core.integration import run_once

DB_PATH = "battery_logs.sqlite"

def main():
    print("[DEBUG] main() entered")
    repo = BatteryLogRepository(DB_PATH)
    repo.create_table()
    print("[DEBUG] repo ready")

    detector = EventDetector()

    #placeholder (octopus)
    sender = Sender(repo, endpoint="http://localhost:9999/see-ya-later")

    print("Battery tracker started. Logging at intervals.")

    while True:
        print("[DEBUG] loop tick")

        settings = repo.load_settings()
        print("[DEBUG] settings", settings)

        if settings["manual_override"] == 1:
            print("[DEBUG] manual_override active, sleeping")
            time.sleep(1)
            continue

        try: 
            print("[DEBUG] calling run_once")   
            run_once(repo, detector, sender)
            print("[DEBUG] run_once completed")
        except Exception as e:
            print("Error:", e)
            raise

        print("[DEBUG] sleeping for", settings["interval"])
        time.sleep(settings["interval"])

if __name__ == "__main__":
    main()