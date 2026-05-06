import time
import signal
import sys

from pathlib import Path

from controller.core.battery_log_repository import BatteryLogRepository
from controller.core.event_detector import EventDetector
from controller.core.sender import Sender
from controller.core.integration import run_once

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "battery_logs.sqlite"

shutdown_requested = False

def handle_shutdown(signum, frame):
    global shutdown_requested
    print("[SHUTDOWN] Signal received, finishing current cycle...")
    shutdown_requested = True

def register_signals():
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, handle_shutdown)

def main():
    register_signals()

    print("[DEBUG] main() entered")
    repo = BatteryLogRepository(DB_PATH)
    repo.create_table()
    print("[DEBUG] repo ready")

    detector = EventDetector()
    #placeholder (octopus)
    sender = Sender(repo, endpoint="http://localhost:9999/see-ya-later")

    print("Battery tracker started. Logging at intervals.")

    while not shutdown_requested:
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

        elapsed = 0
        interval = settings["interval"]
        while not shutdown_requested and elapsed < interval:
            time.sleep(1)
            elapsed += 1

    print("[SHUTDOWN] Loop exited. Flushing unsent log(s)...")
    try:
        sent = sender.send_unsent()
        print(f"[SHUTDOWN] flushed {sent} log(s)")
    except Exception as e:
        print(f"[SHUTDOWN] Flush failed: {e}")


    print("[SHUTDOWN] Exiting cleanly")
    sys.exit(0)


if __name__ == "__main__":
    main()