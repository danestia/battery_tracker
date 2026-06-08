from tracker.core.battery_hardware import BatteryHardware
from tracker.core.event_detector import EventDetector
from tracker.core.battery_log_repository import BatteryLogRepository
from tracker.core.sender import Sender
import uuid

def read_hardware(hw):

    return {
        "device_id": hw.get_device_id(),
        "timestamp": hw.get_timestamp(),
        "plugged": 1 if hw.is_plugged() else 0,
        "level": hw.get_battery_level(),
        "localisation": hw.get_localisation(),
    }

def is_on_office_network(hw):
    current = hw.get_localisation()
    print(f"[DEBUG] Current network reported by hw: {current!r}")

    office_networks = [
        "Wired connection 1",
        "estia.local"
    ]
    return current in office_networks

def run_once(repo: BatteryLogRepository, detector: EventDetector):
    hw = BatteryHardware()
    state = read_hardware(hw)
    event = detector.detect(state)

    log_entry = {
        "id": str(uuid.uuid4()),
        **state,
        "event_type": event["event_type"] if event else None,
        "event_chargelevel": event["event_chargelevel"] if event else None,
    }

    repo.insert_log(log_entry)

    sender = Sender(repo)
    sender.send_unsent()