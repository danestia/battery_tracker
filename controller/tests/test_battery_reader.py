import unittest
from unittest.mock import patch
from controller.core.battery_reader import read_battery

class TestBatteryReader(unittest.TestCase):

    @patch("psutil.sensors_battery")
    def test_read_battery_returns_expected_fields(self, mock_batt):
        mock_batt.return_value.percent = 87
        mock_batt.return_value.power_plugged = True

        result = read_battery()

        self.assertEqual(result["percent"], 87)
        self.assertTrue(result["plugged"])