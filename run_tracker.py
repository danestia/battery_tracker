import os
import time
import signal
import sys
import argparse
from pathlib import Path

from tracker.core.battery_log_repository import BatteryLogRepository
from tracker.core.event_detector import EventDetector
from tracker.core.sender import Sender
from tracker.core.integration import run_once

_SHUTDOWN_REQUESTED = False

def get_default_db_path() -> Path:
    base = Path(__file__).resolve().parent / "data"
   
    base.mkdir(parents=True, exist_ok=True)
    return base / "battery_logs.sqlite"

def handle_shutdown(signum, frame):
    global _SHUTDOWN_REQUESTED
    print("[SHUTDOWN] Signal received, finishing current cycle...")
    _SHUTDOWN_REQUESTED = True

def register_signals():
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, handle_shutdown)

def parse_args():
    parser = argparse.ArgumentParser(description="Battery Tracker Client Daemon")
    parser.add_argument(
        "--endpoint",
        type=str,
        default=os.environ.get("BATTERY_TRACKER_ENDPOINT", "http://100.88.115.20:8000/ingest"),
        help="Ingest server URL endpoint",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=get_default_db_path(),
        help="Path to SQLite database file",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    register_signals()

    endpoint_url = args.endpoint
    db_path = args.db_path

    print(f"[INIT] Database path: {db_path}")
    print(f"[INIT] Ingest Endpoint: {endpoint_url}")

    repo = BatteryLogRepository(db_path)
    repo.create_table()

    detector = EventDetector()
    sender = Sender(repo, endpoint=endpoint_url)

    print("[STATUS] Battery tracker daemon started")

    while not _SHUTDOWN_REQUESTED:
        raw_settings = repo.load_settings() or {}
        settings = {
            "manual_override": raw_settings.get("manual_override", 0),
            "interval": raw_settings.get("interval", 60),
        }

        if settings["manual_override"] == 1:
            print("[STATUS] Manual override active. Pausing logging...")
            time.sleep(5)
            continue

        try:
            run_once(repo, detector, endpoint=endpoint_url)
        except Exception as e:
            print(f"[ERROR] Cycle execution failed: {e}")

        elapsed = 0
        interval = settings["interval"]
        while not _SHUTDOWN_REQUESTED and elapsed < interval:
            time.sleep(1)
            elapsed += 1

    print("[SHUTDOWN] Flushing unsent log(s)...")
    try:
        sent = sender.send_unsent()
        print(f"[SHUTDOWN] Successfully flushed {sent} log(s)")
    except Exception as e:
        print(f"[SHUTDOWN] Flush failed: {e}")

    print("[SHUTDOWN] Exiting cleanly")
    sys.exit(0)

if __name__ == "__main__":
    main()