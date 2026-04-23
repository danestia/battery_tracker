import psutil
import uuid
import hashlib
import platform
import subprocess

from datetime import datetime

try:
    import ctypes
except ImportError:
    ctypes = None

class BatteryHardware:

    def __init__(self):
        self.os = platform.system()

    def get_device_id(self):
        mac_int = uuid.getnode()
        mac_str = ':'.join(f"{(mac_int >> ele) & 0xff:02x}" for ele in range(40, -1, -8))
        return hashlib.sha256(mac_str.encode()).hexdigest()
    
    #timestamp + localisation - cross platform
    def get_timestamp(self):
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")
    
    def get_battery_level(self):
        if self.os == "Windows":
            return self._win_battery_percent()
        elif self.os == "Linux":
            return self._linux_battery_percent()
        elif self.os == "Darwin":
            return self._mac_battery_percent()
        return None
    
    def is_plugged(self):
        if self.os == "Windows":
            return self._win_is_plugged()
        elif self.os == "Linux":
            return self._linux_is_plugged()
        elif self.os == "Darwin":
            return self._mac_is_plugged()
        return None

    def get_localisation(self):
        if self.os == "Windows":
            return self._win_localisation()
        elif self.os == "Linux":
            return self._linux_localisation()
        elif self.os == "Darwin":
            return self._mac_localisation()
        return "offline"
    
    #WINDOWS
    if ctypes:
        class _SYSTEM_POWER_STATUS(ctypes.Structure):
            _fields_ = [
                ("ACLineStatus", ctypes.c_byte),
                ("BatteryFlag", ctypes.c_byte),
                ("BatteryLifePercent", ctypes.c_byte),
                ("Reserved1", ctypes.c_byte),
                ("BatteryLifeTime", ctypes.c_ulong),
                ("BatteryFullLifeTime", ctypes.c_ulong),
            ]

    def _win_get_status(self):
        if not ctypes or not hasattr(self, "_SYSTEM_POWER_STATUS"):
            return None
        status = self._SYSTEM_POWER_STATUS()
        result = ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
        return status if result else None
    
    def _win_battery_percent(self):
        status = self._win_get_status()
        if status:
            return status.BatteryLifePercent
        return None
    
    def _win_is_plugged(self):
        status = self._win_get_status()
        if status:
            return status.ACLineStatus == 1
        return None
    
    def _win_localisation(self):
        try:
            wifi = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout

            for line in wifi.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    ssid = line.split(":", 1)[1].strip()
                    if ssid:
                        return ssid
        except:
            pass

        try:
            eth = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout

            for line in eth.splitlines():
                if "Connected" in line:
                    parts = line.split()
                    return parts[-1]
        except:
            pass

        return "offline"
    
    #LINUX
    def _linux_battery_percent(self):
        battery = psutil.sensors_battery()
        return battery.percent if battery else None
    
    def _linux_is_plugged(self):
        battery = psutil.sensors_battery()
        return bool(battery.power_plugged) if battery else None
    
    def _linux_localisation(self):
        try:
            wifi = subprocess.run(
                ["iwgetid", "-r"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout.strip()
            if wifi:
                return wifi
        except:
            pass

        try:
            nm = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show", "--active"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout.strip()
            if nm:
                return nm.split(":")[0]
        except:
            pass

        return "offline"
    
    #MAC OS
    def _mac_battery_percent(self):
        try:
            out = subprocess.run(
                ["pmset", "-g", "batt"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout
            percent = out.split("%")[0].split()[-1]
            return int(percent)
        except:
            return None
        
    def _mac_is_plugged(self):
        try:
            out = subprocess.run(
                ["pmset", "-g", "batt"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout.lower()
            return "charging" in out or "charged" in out
        except:
            return None
        
    def _mac_localisation(self):
        try:
            wifi = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout
            for line in wifi.splitlines():
                if " SSID" in line:
                    return line.split(":")[1].strip()
        except:
            pass

        try:
            out = subprocess.run(
                ["networksetup", "-listallhardwareports"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout
            for block in out.split("\n\n"):
                if "Device" in block and "Ethernet" in block:
                    for line in block.splitlines():
                        if line.startswith("Device"):
                            return line.split(":")[1].strip()
        except:
            pass

        return "offline"
    
