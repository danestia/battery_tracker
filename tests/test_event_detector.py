import unittest
from tracker.core.event_detector import EventDetector


class TestEventDetector(unittest.TestCase):

    def setUp(self):
        self.detector = EventDetector()

    def test_first_call_produces_no_event(self):
        battery = {"plugged": 1, "level": 50}
        event = self.detector.detect(battery)
        self.assertIsNone(event)

    def test_detects_plug_event(self):
        self.detector.last_plugged = 0
        self.detector.last_percent = 50

        battery = {"plugged": 1, "level": 50}
        event = self.detector.detect(battery)

        self.assertEqual(event["event_type"], "PLUGGED_IN")
        self.assertEqual(event["event_chargelevel"], 50)

    def test_detects_unplug_event(self):
        self.detector.last_plugged = 1
        self.detector.last_percent = 50

        battery = {"plugged": 0, "level": 50}
        event = self.detector.detect(battery)

        self.assertEqual(event["event_type"], "UNPLUGGED")
        self.assertEqual(event["event_chargelevel"], 50)

    def test_charge_up_event(self):
        self.detector.last_plugged = 1
        self.detector.last_percent = 40

        battery = {"plugged": 1, "level": 45}
        event = self.detector.detect(battery)

        self.assertEqual(event["event_type"], "CHARGE_UP")
        self.assertEqual(event["event_chargelevel"], 45)

    def test_charge_down_event(self):
        self.detector.last_plugged = 0
        self.detector.last_percent = 60

        battery = {"plugged": 0, "level": 55}
        event = self.detector.detect(battery)

        self.assertEqual(event["event_type"], "CHARGE_DOWN")
        self.assertEqual(event["event_chargelevel"], 55)

    def test_low_battery_event(self):
        self.detector.last_plugged = 0
        self.detector.last_percent = 25

        battery = {"plugged": 0, "level": 19}
        event = self.detector.detect(battery)

        self.assertEqual(event["event_type"], "LOW_BATTERY")
        self.assertEqual(event["event_chargelevel"], 19)

    def test_fully_charged_event(self):
        self.detector.last_plugged = 1
        self.detector.last_percent = 99

        battery = {"plugged": 1, "level": 100}
        event = self.detector.detect(battery)

        self.assertEqual(event["event_type"], "FULLY_CHARGED")
        self.assertEqual(event["event_chargelevel"], 100)

    def test_no_event(self):
        self.detector.last_plugged = 1
        self.detector.last_percent = 50

        battery = {"plugged": 1, "level": 50}
        event = self.detector.detect(battery)

        self.assertIsNone(event)
