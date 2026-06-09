import unittest
import os
import uuid
from unittest.mock import patch, MagicMock
from tracker.core.battery_log_repository import BatteryLogRepository
from tracker.core.sender import Sender

# Use a specific test database filename
TEST_DB = "test_sender_temp.sqlite"

class TestSender(unittest.TestCase):

    def setUp(self):
        # Clean up any leftover file from a previous crashed run
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except PermissionError:
                pass

        self.repo = BatteryLogRepository(TEST_DB)
        self.repo.create_table()

        self.sender = Sender(
            repo=self.repo,
            endpoint="https://tempsite.com/post"
        )

    def tearDown(self):
        # 1. Break references and force garbage collection to release SQLite file handles
        self.sender = None
        self.repo = None
        
        # 2. Clean up the physical file from disk safely
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except PermissionError:
                # If Windows is still holding onto it briefly, don't crash the test run
                pass

    def insert_log(self, device_id="id1", ts="2024-01-01 10:00:00"):
        log = {
            "id": str(uuid.uuid4()),  # Generates unique IDs to prevent IntegrityErrors
            "device_id": device_id,
            "timestamp": ts,
            "plugged": 1,
            "level": 50,
            "localisation": "office",
            "event_type": None,
            "event_chargelevel": None,
        }
        self.repo.insert_log(log)

    @patch("tracker.core.sender.requests.post")
    def test_send_success(self, mock_post):
        self.insert_log()

        mock_post.return_value.status_code = 200

        sent_count = self.sender.send_unsent()

        self.assertEqual(sent_count, 1)

        unsent = self.repo.get_unsent_logs()
        self.assertEqual(len(unsent), 0)

    @patch("tracker.core.sender.requests.post")
    def test_send_failure_status(self, mock_post):
        self.insert_log()

        mock_post.return_value.status_code = 500

        sent_count = self.sender.send_unsent()

        self.assertEqual(sent_count, 0)

        unsent = self.repo.get_unsent_logs()
        self.assertEqual(len(unsent), 1)

    @patch("tracker.core.sender.requests.post")
    def test_partial_success(self, mock_post):
        self.insert_log(device_id="id1")
        self.insert_log(device_id="id2")

        mock_post.side_effect = [
            MagicMock(status_code=200),
            MagicMock(status_code=500),
        ]

        sent_count = self.sender.send_unsent()

        self.assertEqual(sent_count, 1)

        unsent = self.repo.get_unsent_logs()
        self.assertEqual(len(unsent), 1)