import unittest
from unittest.mock import patch, MagicMock
from controller.core.battery_hardware import BatteryHardware

class TestBatteryHardware(unittest.TestCase):

    @patch("controller.core.battery_hardware.psutil.sensors_battery")
    def test_get_battery_level(self, mock_sensors):
        mock_sensors.return_value.percent = 55
        hw = BatteryHardware()
        self.assertEqual(hw.get_battery_level(), 55)

    @patch("controller.core.battery_hardware.psutil.sensors_battery")
    def test_is_plugged(self, mock_sensors):
        mock_sensors.return_value.is_plugged = True
        hw = BatteryHardware()
        self.assertEqual(hw.is_plugged())

    @patch("controller.core.battery_hardware.wmi.WMI")
    def test_get_model(self, mock_wmi):
        mock_battery = MagicMock()
        mock_battery.Name = "TestBatteryModel"
        mock_wmi.return_value.CIM_Battery.return_value = [mock_battery]

        hw = BatteryHardware()
        self.assertEqual(hw.getModel(), "TestBatteryName")

    @patch("controller.core.battery_hardware.wmi.WMI")
    def test_get_design_voltage(self, mock_wmi):
        mock_battery = MagicMock()
        mock_battery.DesignVoltage = 12000
        mock_battery.DesignCapacity = 60000
        mock_wmi.return_value.CIM_Battery.return_value = [mock_battery]

        hw = BatteryHardware()
        self.assertEqual(hw.get_design_capacity(), 60000 / 12000)

    def test_get_timestamp(self):
        hw = BatteryHardware()
        ts = hw.get_timestamp()

        self.assertIsInstance(ts, str)
        self.assertRegex(ts, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

    def test_get_localisation(self):
        hw = BatteryHardware()

        self.assertEqual(hw.get_localisation(), "office")