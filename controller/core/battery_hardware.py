import psutil
import uuid
import hashlib
import platform
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

    def get_localisation(self):
        """
        Returns the current network identifier:
        - Wi-Fi SSID if on Wi-Fi
        - Connection name if on Ethernet
        - 'offline' if not connected
        """

        os_name = platform.system()

        #Windows
        if os_name == "Windows":
            try:
                output = subprocess.check_output(
                    ["netsh", "wlan", "show", "interfaces"],
                    encoding="utf-8",
                    errors="ignore"
                )
                for line in output.splitlines():
                    if "SSID" in line and "BSSID" not in line:
                        ssid = line.split(":", 1)[1].strip()
                        if ssid:
                            return ssid
            except:
                pass

            try:
                output = subprocess.check_output(
                    ["netsh", "interface", "show", "interface"],
                    encoding="utf-8",
                    errors="ignore"
                )
                for line in output.splitlines():
                    if "Connected" in line:
                        return line.split()[-1]
            except:
                pass

            return "offline"

        #Linux
        if os_name == "Linux":
            try:
                wifi = subprocess.check_output(
                    ["iwgetid", "-r"],
                    encoding="utf-8",
                    errors="ignore"
                ).strip()

                if wifi:
                    return wifi
            except:
                pass

            try:
                nm = subprocess.check_output(
                    ["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show", "--active"],
                    encoding="utf-8",
                    errors="ignore"
                ).strip()

                if nm:
                    return nm.split(":")[0]
            except:
                pass

            return "offline"
        
        #MacOS
        if os_name == "Darwin":
            try:
                output = subprocess.check_output(
                    ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                    encoding="utf-8",
                    errors="ignore"
                )
                for line in output.splitlines():
                    if "SSID" in line:
                        return line.split(":")[1].strip()
            except:
                pass

            return "offline"

        #Unknown    
        return "offline"