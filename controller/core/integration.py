from controller.core.battery_hardware import BatteryHardware
from controller.core.event_detector import EventDetector
from controller.core.battery_log_repository import BatteryLogRepository
from controller.core.sender import Sender

def read_hardware(hw):

    return {
        "device_id": hw.get_device_id(),
        "timestamp": hw.get_timestamp(),
        "plugged": 1 if hw.is_plugged() else 0,
        "level": hw.get_battery_level(),
        "localisation": hw.get_localisation(),
        "voltage": hw.get_design_voltage(),
        "capacity": hw.get_design_capacity(),
        "model": hw.get_model(),
    }

def is_on_office_network(hw):
    current = hw.get_localisation()
    print(f"[DEBUG] Current network reported by hw: {current!r}")

    office_networks = [
        "Wired connection 1"
    ]
    current = hw.get_localisation()
    return current in office_networks

def run_once(repo: BatteryLogRepository, detector: EventDetector, sender: Sender):
    hw = BatteryHardware()

    # Network check - Comment out to disable
    if not is_on_office_network(hw):
        print("Not on office network - logging disabled")
        return

    state = read_hardware(hw)

    event = detector.detect(state)

    log_entry = {
        **state,
        "event_type": event["event_type"] if event else None,
        "event_chargelevel": event["event_chargelevel"] if event else None,
    }

    repo.insert_log(log_entry)

    sender.send_unsent()