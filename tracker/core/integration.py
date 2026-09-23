"""
Core Integration Module
-----------------------
Handles the end-to-end telemetry collection cycle: reading hardware states, 
evaluating network whitelist filters, detecting device events, persisting 
logs locally, and syncing unsent logs to the remote endpoint.
"""

from tracker.core.battery_hardware import BatteryHardware
from tracker.core.event_detector import EventDetector
from tracker.core.battery_log_repository import BatteryLogRepository
from tracker.core.sender import Sender
from typing import Any, Dict
import uuid
import logging

logger = logging.getLogger(__name__)

def read_hardware(hw: BatteryHardware) -> Dict[str, Any]:

    return {
        "device_id": hw.get_device_id(),
        "timestamp": hw.get_timestamp(),
        "plugged": 1 if hw.is_plugged() else 0,
        "level": hw.get_battery_level(),
        "localisation": hw.get_localisation(),
    }

#original network check. To be removed if update is effective
"""def is_on_office_network(hw):
    current = hw.get_localisation()
    print(f"[DEBUG] Current network reported by hw: {current!r}")

    office_networks = [
        "Wired connection 1",
        "estia.local"
    ]
    return current in office_networks"""

def run_once(
        repo: BatteryLogRepository, 
        detector: EventDetector, 
        endpoint: str = "http://100.88.115.20:8000/ingest"
    ) -> None:
    logger.debug("Executing run_once collection cycle")

    hw = BatteryHardware()

    if not repo.is_network_allowed():
        logger.info("Network Filter: Not an office whitelist network. Aborting log collection")
        return
    
    state = read_hardware(hw)
    event = detector.detect(state)

    log_entry = {
        "uuid": str(uuid.uuid4()),
        **state,
        "event_type": event["event_type"] if event else None,
        "event_chargelevel": event["event_chargelevel"] if event else None,
    }

    repo.insert_log(log_entry)

    sender = Sender(repo, endpoint=endpoint)
    sender.send_unsent()