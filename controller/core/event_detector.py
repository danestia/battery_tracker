import psutil

def detect_event(battery, state):
    plugged = battery["plugged"]
    percent = battery["percent"]

    #First call: no previous state
    if state.last_plugged is None:
        state.last_plugged = plugged
        state.last_percent = percent
        return None
    
    #detect plug event
    if not state.last_plugged and plugged:
        event = {
            "type": "PLUGGED",
            "chargelevel": percent
        }
        state.last_plugged = plugged
        state.last_percent = percent
        return event
    
    #detect unplug event
    if state.last_plugged and not plugged:
        event = {
            "type": "UNPLUGGED",
            "chargelevel": percent
        }
        state.last_plugged = plugged
        state.last_percent = percent
        return event
    
    #no change/event
    state.last_plugged = plugged
    state.last_percent = percent
    return None
