class EventDetector:

    def __init__(self):
        self.last_plugged = None
        self.last_percent = None

    def detect(self, battery):
        plugged = battery["plugged"]
        percent = battery["level"]

        #First call: no previous state
        if self.last_plugged is None:
            self.last_plugged = plugged
            self.last_percent = percent
            return None
        
        events = []

        if not self.last_plugged and plugged:
            events.append(("PLUGGED_IN", percent))

        if  self.last_plugged and not plugged:
            events.append(("UNPLUGGED", percent))

        if percent < 20 and self.last_percent >= 20:
            events.append(("LOW_BATTERY", percent))

        if percent == 100 and self.last_percent < 100:
            events.append(("FULLY_CHARGED", percent))

        if plugged and percent > self.last_percent:
            events.append(("CHARGE_UP", percent))

        if not plugged and percent < self.last_percent:
            events.append(("CHARGE_DOWN", percent))
        
        #no change/event
        if not events:
            self.last_plugged = plugged
            self.last_percent = percent
            return None

        PRIORITY = [
            "PLUGGED_IN",
            "UNPLUGGED",
            "LOW_BATTERY",
            "FULLY_CHARGED",
            "CHARGE_UP",
            "CHARGE_DOWN",
        ]
        events.sort(key=lambda e: PRIORITY.index(e[0]))
        chosen_type, chosen_level = events[0]

        self.last_plugged = plugged
        self.last_percent = percent

        return {
            "event_type": chosen_type,
            "event_chargelevel": chosen_level
        }


