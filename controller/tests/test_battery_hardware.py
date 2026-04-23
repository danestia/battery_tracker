import unittest
from unittest.mock import patch, MagicMock
from controller.core.battery_hardware import BatteryHardware

class TestBatteryHardware(unittest.TestCase):

    #WINDOWS
    @patch("controller.core.battery_hardware.platform.system", return_value="Windows")
    @patch("controller.core.battery_hardware.BatteryHardware._win_get_status")
    def test_windows_battery(self, mock_win_get_status, mock_platform):        
        fake = MagicMock()
        fake.ACLineStatus = 1
        fake.BatteryLifePercent = 87

        mock_win_get_status.return_value = fake

        hw = BatteryHardware()
        self.assertEqual(hw.get_battery_level(), 87)
        self.assertTrue(hw.is_plugged())

    @patch("controller.core.battery_hardware.platform.system", return_value="Windows")
    @patch("controller.core.battery_hardware.subprocess.run")
    def test_windows_localisation(self, mock_run, mock_os):
        mock_run.return_value.stdout = """
            SSID                   : TestNetwork
            BSSID                  : 00:11:22:33:44:55
        """

        hw = BatteryHardware()
        self.assertEqual(hw.get_localisation(), "TestNetwork")

    #LINUX

    @patch("controller.core.battery_hardware.platform.system", return_value="Linux")
    @patch("controller.core.battery_hardware.psutil.sensors_battery")
    def test_linux_battery(self, mock_batt, mock_os):
        mock_batt.return_value.percent = 55
        mock_batt.return_value.power_plugged = False

        hw = BatteryHardware()
        self.assertEqual(hw.get_battery_level(), 55)
        self.assertFalse(hw.is_plugged())

    @patch("controller.core.battery_hardware.platform.system", return_value="Linux")
    @patch("controller.core.battery_hardware.subprocess.run")
    def test_linux_localisation(self, mock_run, mock_os):
        mock_run.return_value.stdout = "OfficeWifi"

        hw = BatteryHardware()
        self.assertEqual(hw.get_localisation(), "OfficeWifi")

    #MAC OS

    @patch("controller.core.battery_hardware.platform.system", return_value="Darwin")
    @patch("controller.core.battery_hardware.subprocess.run")
    def test_mac_battery(self, mock_run, mock_os):
        mock_run.return_value.stdout = " -InternalBattery-0 87%; charging"

        hw = BatteryHardware()
        self.assertEqual(hw.get_battery_level(), 87)
        self.assertTrue(hw.is_plugged())

    @patch("controller.core.battery_hardware.platform.system", return_value="Darwin")
    @patch("controller.core.battery_hardware.subprocess.run")
    def test_mac_localisation(self, mock_run, mock_os):
        mock_run.return_value.stdout = "     SSID: HomeNetwork"

        hw = BatteryHardware()
        self.assertEqual(hw.get_localisation(), "HomeNetwork")

    #CROSS PLATFORM

    def test_get_timestamp(self):
        hw = BatteryHardware()
        ts = hw.get_timestamp()
        self.assertIsInstance(ts, str)
        self.assertRegex(ts, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

    def test_get_device_id(self):
        hw = BatteryHardware()
        device_id = hw.get_device_id()
        self.assertIsInstance(device_id, str)
        self.assertEqual(len(device_id), 64) #length of SHA-256 is 64



