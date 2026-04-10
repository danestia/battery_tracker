import requests

class Sender:
    def __init__(self, repo, endpoint):
        """
        repo: BatteryLogRepository instance
        endpoint: URL to POST logs to
        """
        self.repo = repo
        self.endpoint = endpoint

    def send_unsent(self):
        unsent = self.repo.get_unsent_logs()
        send_count = 0

        for row in unsent:
            rowid = row["rowid"]

            payload = {key:row[key] for key in row.keys() if key != "rowid"}

            try:
                response = requests.post(self.endpoint, json=payload)

                if response.status_code == 200:
                    self.repo.mark_sent(rowid)
                    send_count += 1
                else:
                    continue

            except Exception:
                continue

        return send_count