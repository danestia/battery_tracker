import psutil

def detect_event(battery, state):
    plugged = battery["plugged"]
    percent = battery["percent"]

    #First call: no previous state
    if state.last_plugged is None:
        state.last_plugged = plugged
        state.last_percent = percent
        return None
    
    events = []

    if not state.last_plugged and plugged:
        events.append(("PLUGGED", percent))

    if  state.last_plugged and not plugged:
        events.append(("UNPLUGGED", percent))

    if percent < 20 and state.last_percent >= 20:
        events.append(("LOW_BATTERY", percent))

    if percent == 100 and state.last_percent < 100:
        events.append(("FULLY_CHARGED", percent))

    if plugged and percent > state.last_percent:
        events.append(("CHARGE_UP", percent))

    if not plugged and percent < state.last_percent:
        events.append(("CHARGE_DOWN", percent))



    
    #detect plug event
    """ if not state.last_plugged and plugged:
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

    #charge up when plugged
    if plugged and percent > state.last_percent:
        event = {
            "type": "CHARGE_UP",
            "chargelevel": percent
        }
        state.last_plugged = plugged
        state.last_percent = percent
        return event
    
    #charge down when unplugged
    if not plugged and percent < state.last_percent:
        event = {
            "type": "CHARGE_DOWN",
            "chargelevel": percent
        }
        state.last_plugged = plugged
        state.last_percent = percent
        return event
    
    #low battery (<20%)
    if percent < 20 and state.last_percent >= 20:
        event = {
            "type": "LOW_BATTERY",
            "chargelevel": percent
        }
        state.last_plugged = plugged
        state.last_percent = percent
        return event
    
    #fully charged (100%)
    if percent == 100 and state.last_percent < 100:
        event = {
            "type": "FULLY_CHARGED",
            "chargelevel": percent
        }
        state.last_plugged = plugged """
    
    #no change/event
    if not events:
        state.last_plugged = plugged
        state.last_percent = percent
        return None

    PRIORITY = [
        "PLUGGED",
        "UNPLUGGED",
        "LOW_BATTERY",
        "FULLY_CHARGED",
        "CHARGE_UP",
        "CHARGE_DOWN",
    ]
    events.sort(key=lambda e: PRIORITY.index(e[0]))
    chosen_type, chosen_level = events[0]

    state.last_plugged = plugged
    state.last_percent = percent

    return {"type": chosen_type, "chargelevel": chosen_level}


