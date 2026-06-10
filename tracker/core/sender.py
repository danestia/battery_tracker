import requests

class Sender:
    def __init__(self, repo, endpoint, timeout=5):
        self.timeout = timeout
        self.repo = repo
        self.endpoint = endpoint

    def send_unsent(self):
        unsent = self.repo.get_unsent_logs()
        send_count = 0

        for row in unsent:

            payload = dict(row)

            if "uuid" in payload:
                payload["log_uuid"] = payload.pop("uuid")

            try:
                response = requests.post(self.endpoint, json=payload, timeout=self.timeout)

                if response.status_code == 200:
                    self.repo.mark_sent(row["uuid"])
                    send_count += 1
                else:
                    continue

            except Exception:
                continue

        return send_count