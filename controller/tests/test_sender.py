import unittest
from unittest.mock import patch, MagicMock
from controller.core.battery_log_repository import BatteryLogRepository
from controller.core.sender import Sender

TEST_DB = "test_sender.sqlite"

class TestSender(unittest.TestCase):

    def setUp(self):
        import os
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        self.repo = BatteryLogRepository(TEST_DB)
        self.repo.create_table()

        self.sender = Sender(
            repo=self.repo,
            endpoint="https://tempsite.com/post"
        )

    def tearDown(self):
        import os
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def insert_log(self, device_id="id1", ts="2024-01-01 10:00:00"):
        log = {
            "device_id": device_id,
            "timestamp": ts,
            "plugged": 1,
            "level": 50,
            "localisation": "office",
            "event_type": None,
            "event_chargelevel": None,
        }
        self.repo.insert_log(log)

    @patch("controller.core.sender.requests.post")
    def test_send_success(self, mock_post):
        self.insert_log()

        mock_post.return_value.status_code = 200

        sent_count = self.sender.send_unsent()

        self.assertEqual(sent_count, 1)

        unsent = self.repo.get_unsent_logs()

        self.assertEqual(len(unsent), 0)

    @patch("controller.core.sender.requests.post")
    def test_send_failure_status(self, mock_post):
        self.insert_log()

        mock_post.return_value.status_code = 500

        sent_count = self.sender.send_unsent()

        self.assertEqual(sent_count, 0)

        unsent = self.repo.get_unsent_logs()
        self.assertEqual(len(unsent), 1)

    @patch("controller.core.sender.requests.post")
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

