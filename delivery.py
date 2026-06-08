from tracker.core.battery_log_repository import BatteryLogRepository
from tracker.core.sender import Sender
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "battery_logs.sqlite"

repo = BatteryLogRepository(DB_PATH)
sender = Sender(repo, endpoint="http://100.88.115.20:8000/ingest/")
sent = sender.send_unsent()
print(f"[DELIVERY] Sent {sent} log(s) to hub")
