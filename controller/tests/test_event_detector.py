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

