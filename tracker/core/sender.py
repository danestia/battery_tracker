"""
Sender Module
-------------
Manages HTTP synchronization of local battery log entries to a remote 
ingestion endpoint, handling connectivity checks, payload transformation, 
and local queue flushing upon successful transmission.
"""

import logging
from typing import Any, Dict, List
import requests
from tracker.core.battery_log_repository import BatteryLogRepository

logger = logging.getLogger(__name__)


class Sender:
    def __init__(self, repo: BatteryLogRepository, endpoint: str, timeout: int = 5):
        self.timeout: int = timeout
        self.repo: BatteryLogRepository = repo
        self.endpoint: str = endpoint

    def _is_hub_reachable(self) -> bool:
        try:
            response = requests.options(self.endpoint, timeout=2)
            return response.status_code < 500
        except requests.RequestException:
            return False

    def send_unsent(self) -> int:
        if not self._is_hub_reachable():
            logger.info("Network Filter: Hub is unreachable. Keeping local logs.")
            return 0

        unsent = self.repo.get_unsent_logs()
        send_count = 0
        successfully_sent_uuids: List[str] = []

        for row in unsent:

            payload: Dict[str, Any] = dict(row)

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
                    logger.warning(
                        "Failed to sync log UUID %s. Status code: %s",
                        payload["uuid"],
                        response.status_code
                    )
                    continue

            except requests.RequestException as e:
                logger.warning("Request exception encountered during sync: %s", e)
                break

        if successfully_sent_uuids:
            try:
                for u in successfully_sent_uuids:
                    self.repo.mark_sent(u)
                
                self.repo.delete_safely_sent_logs(successfully_sent_uuids)
                logger.info(f"Successfully flushed {len(successfully_sent_uuids)} rows from SQLite Temp storage.")
            except Exception as e:
                logger.error(f"Failed to execute storage flush: {e}")

        return send_count