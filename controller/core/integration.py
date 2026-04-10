from controller.core.battery_reader import read_battery
from controller.core.event_detector import detect_event
from controller.core.sender import send_event

def run_once(state):
    battery = read_battery()
    event = detect_event(battery, state)

    if event is None:
        return False
    
    return send_event(event)

