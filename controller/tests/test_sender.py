import unittest
from unittest.mock import patch
from controller.core.sender import send_event

class TestSender(unittest.TestCase):

    @patch("controller.core.sender.requests.post")
    def test_send_event_success(self, mock_post):
        mock_post.return_value.status_code = 200

        event = {"type": "PLUGGED", "chargelevel": 87}
        result = send_event(event)

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("controller.core.sender.requests.post")
    def test_send_event_failure(self, mock_post):
        mock_post.return_value.status_code = 500

        event = {"type": "UNPLUGGED", "chargelevel": 42}
        result = send_event(event)

        self.assertFalse(result)
        mock_post.assert_called_once()