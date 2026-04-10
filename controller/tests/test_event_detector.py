import unittest
from controller.core.state import State
from controller.core.event_detector import detect_event

class TestEventDetector(unittest.TestCase):

    def test_first_call_produces_no_event(self):
        state = State()
        battery = {"percent": 50, "plugged": True}

        event = detect_event(battery, state)

        self.assertIsNone(event)

    def test_detects_plug_event(self):
        state = State()
        state.last_plugged = False #previously unplugged
        state.last_percent = 40

        battery = {"percent": 60, "plugged": True}

        event = detect_event(battery, state)

        self.assertIsNotNone(event)
        self.assertEqual(event["type"], "PLUGGED")
        self.assertEqual(event["chargelevel"], 60)

    def test_detects_unplug_event(self):
        state = State()
        state.last_plugged = True #previously plugged
        state.last_percent = 90

        battery = {"percent": 85, "plugged": False}

        event = detect_event(battery, state)

        self.assertIsNotNone(event)
        self.assertEqual(event["type"], "UNPLUGGED")
        self.assertEqual(event["chargelevel"], 85)

    def test_charge_up_event(self):
        state = State()
        state.last_plugged = True
        state.last_percent = 40

        battery = {"percent": 50, "plugged": True}

        event = detect_event(battery, state)

        self.assertIsNotNone(event)
        self.assertEqual(event["type"], "CHARGE_UP")
        self.assertEqual(event["chargelevel"], 50)

    def test_charge_down_event(self):
        state = State()
        state.last_plugged = False
        state.last_percent = 80

        battery = {"percent": 70, "plugged": False}

        event = detect_event(battery, state)

        self.assertIsNotNone(event)
        self.assertEqual(event["type"], "CHARGE_DOWN")
        self.assertEqual(event["chargelevel"], 70)

    def test_low_battery_event(self):
        state = State()
        state.last_plugged = False
        state.last_percent = 25

        battery = {"percent": 19, "plugged": False}

        event = detect_event(battery, state)

        self.assertIsNotNone(event)
        self.assertEqual(event["type"], "LOW_BATTERY")
        self.assertEqual(event["chargelevel"], 19)

    def test_fully_charged_event(self):
        state = State()
        state.last_plugged = True
        state.last_percent = 95

        battery ={"percent": 100, "plugged": True}

        event = detect_event(battery, state)

        self.assertIsNotNone(event)
        self.assertEqual(event["type"], "FULLY_CHARGED")
        self.assertEqual(event["chargelevel"], 100)

    def test_no_event(self):
        state = State()
        state.last_plugged = True
        state.last_percent = 60

        battery = {"percent": 60, "plugged": True}

        event = detect_event(battery, state)

        self.assertIsNone(event)
        self.assertEqual(state.last_plugged, True)
        self.assertEqual(state.last_percent, 60)

