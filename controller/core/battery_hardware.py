import psutil
import uuid
import hashlib
import subprocess

from datetime import datetime

try:
    import wmi
except ImportError:
    class _WMIUnavailable:
        def WMI(self):
            raise RuntimeError("WMI is only available for Windows systems")
    wmi = _WMIUnavailable()

class BatteryHardware:

    def __init__(self):
        
        try:
            self._wmi = wmi.WMI()
            batteries = self._wmi.CIM_Battery()
            self._battery = batteries[0] if batteries else None
        except Exception:
            self._battery = None

    #psutil readings + device id(cross platform)
    def get_battery_level(self):
        battery = psutil.sensors_battery()
        return battery.percent if battery else None
    
    def is_plugged(self):
        battery = psutil.sensors_battery()
        return bool(battery.power_plugged) if battery else None
    
    def get_device_id(self):
        mac_int = uuid.getnode()
        mac_str = ':'.join(f"{(mac_int >> ele) & 0xff:02x}" for ele in range(40, -1, -8))
        return hashlib.sha256(mac_str.encode()).hexdigest()
    
    #WMI readings - Windows only
    def get_model(self):
        if self._battery:
            return getattr(self._battery, "Name", None)
        return None

    def get_design_voltage(self):
        if self._battery:
            return getattr(self._battery, "DesignVoltage", None)
        return None

    def get_design_capacity(self):
        if self._battery:
            voltage = getattr(self._battery, "DesignVoltage", None)
            capacity = getattr(self._battery, "DesignCapacity", None)
            if voltage and capacity:
                return capacity / voltage
        return None

    #timestamp + localisation - cross platform
    def get_timestamp(self):
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")

    import subprocess

    def get_localisation(self):
        """
        Returns the current network identifier:
        - Wi-Fi SSID if on Wi-Fi
        - Connection name if on Ethernet
        - 'offline' if not connected
        """
        try:
            # First try Wi-Fi SSID
            wifi = subprocess.run(
                ["iwgetid", "-r"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout.strip()

            if wifi:
                return wifi

            # Fallback: NetworkManager active connection name (works for Ethernet)
            nm = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show", "--active"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout.strip()

            if nm:
                # Example output: "OfficeLAN:enp0s31f6"
                name = nm.split(":")[0]
                return name

            return "offline"

        except Exception:
            return "offline"