from tracker.core.battery_log_repository import BatteryLogRepository
from tracker.core.sender import Sender
from pathlib import Path

def main() -> None:
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "data" / "battery_logs.sqlite"

    repo = BatteryLogRepository(db_path)

    #OCTOPUS - hardcoded server IP
    sender = Sender(repo, endpoint="http://100.88.115.20:8000/ingest")
    sent = sender.send_unsent()
    print(f"[DELIVERY] Sent {sent} log(s) to hub")

if __name__ == "__main__":
    main()