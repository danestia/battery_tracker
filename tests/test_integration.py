import unittest
import uuid
from unittest.mock import MagicMock, patch

from tracker.core.integration import run_once
from tracker.core.battery_log_repository import BatteryLogRepository
from tracker.core.event_detector import EventDetector

TEST_DB = "test_integration.sqlite"

class TestIntegration(unittest.TestCase):

    def setUp(self):
        import os
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        self.repo = BatteryLogRepository(TEST_DB)
        self.repo.create_table()

        self.detector = EventDetector()

    def tearDown(self):
        import os
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    # Fake hardware state
    def fake_state(self, level=50, plugged=1):
        return {
            "uuid": str(uuid.uuid4()),
            "device_id": "abc",
            "timestamp": "2024-01-01 10:00:00",
            "plugged": plugged,
            "level": level,
            "localisation": "office",
            "event_type": None,
            "event_chargelevel": None,
        }
    
    @patch("tracker.core.integration.BatteryHardware")
    @patch("tracker.core.integration.Sender")
    def test_run_once_no_event(self, mock_sender, mock_hw):


        hw = mock_hw.return_value
        hw.get_battery_level.return_value = 50
        hw.is_plugged.return_value = 1
        hw.get_device_id.return_value = "abc"
        hw.get_timestamp.return_value = "2024-01-01 10:00:00"
        hw.get_localisation.return_value = "office"

        sender = mock_sender.return_value

        run_once(self.repo, self.detector)

        logs = self.repo.get_unsent_logs()
        self.assertEqual(len(logs), 1)

        row = logs[0]
        self.assertIsNone(row["event_type"])
        self.assertIsNone(row["event_chargelevel"])

        sender.send_unsent.assert_called_once()

    @patch("tracker.core.integration.BatteryHardware")
    @patch("tracker.core.integration.Sender")
    def test_run_once_with_event(self, mock_sender, mock_hw):


        self.repo.insert_log({
            "uuid": str(uuid.uuid4()),
            "device_id": "abc",
            "timestamp": "2024-01-01 09:59:00",
            "plugged": 0,
            "level": 49,
            "localisation": "office",
            "event_type": None,
            "event_chargelevel": None,
        })

        self.detector.last_plugged = 0
        self.detector.last_percent = 49

        hw = mock_hw.return_value
        hw.get_battery_level.return_value = 49
        hw.is_plugged.return_value = 1
        hw.get_device_id.return_value = "abc"
        hw.get_timestamp.return_value = "2024-01-01 10:00:00"
        hw.get_localisation.return_value = "office"

        sender = mock_sender.return_value

        run_once(self.repo, self.detector)

        logs = self.repo.get_unsent_logs()
        self.assertEqual(len(logs), 2)

        event_log = logs[-1]
        self.assertEqual(event_log["event_type"], "PLUGGED_IN")
        self.assertEqual(event_log["event_chargelevel"], 49)

        sender.send_unsent.assert_called_once()
