import requests
from tracker.core.battery_log_repository import BatteryLogRepository

DB_PATH = "data/battery_logs.sqlite"

class Sender:
    def __init__(self, repo, endpoint, timeout=5):
        self.timeout = timeout
        self.repo = repo
        self.endpoint = endpoint

    def _is_hub_reachable(self) -> bool:
        try:
            response = requests.head(self.endpoint, timeout=2)
            return response.status_code < 500
        except requests.RequestException:
            return False

    def send_unsent(self):
        if not self._is_hub_reachable():
            print("Network Filter: Hub is unreachable. Keeping local logs.")
            return 0

        unsent = self.repo.get_unsent_logs()
        send_count = 0
        successfully_sent_uuids = []

        for row in unsent:

            payload = dict(row)

            if "uuid" in payload:
                payload["log_uuid"] = payload["uuid"]

            if "plugged" in payload:
                payload["plugged"] = bool(payload["plugged"])

            try:
                response = requests.post(self.endpoint, json=payload, timeout=self.timeout)

                if response.status_code in [200, 201]:
                    successfully_sent_uuids.append(row["uuid"])
                    send_count += 1
                else:
                    continue

            except requests.RequestException:
                break

        if successfully_sent_uuids:
            try:
                for u in successfully_sent_uuids:
                    self.repo.mark_sent(u)
                
                self.repo.delete_safely_sent_logs(successfully_sent_uuids)
                print(f"Successfully flushed {len(successfully_sent_uuids)} rows from SQLite Temp storage")
            except Exception as e:
                print(f"Failed to execute storage flush: {e}")

        return send_count