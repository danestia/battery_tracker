import unittest
from unittest.mock import patch
from controller.core.state import State
from controller.core.integration import run_once

class TestIntegration(unittest.TestCase):
    @patch("controller.core.integration.send_event")
    @patch("controller.core.integration.read_battery")
    @patch("controller.core.integration.detect_event")
    def test_integration_flow(self, mock_detect, mock_read, mock_send):
        mock_read.return_value = {"percent": 50, "plugged": True}
        mock_detect.return_value = {"type": "PLUGGED", "chargelevel": 50}
        mock_send.return_value = True

        state = State()

        result = run_once(state)

        mock_read.assert_called_once()
        mock_detect.assert_called_once_with({"percent": 50, "plugged": True}, state)
        mock_send.assert_called_once_with({"type": "PLUGGED", "chargelevel": 50})
        self.assertTrue(result)