import psutil
import uuid
import hashlib
from datetime import datetime

try:
    import wmi
except ImportError:
    wmi = None

class BatteryHardware:

    def __init__(self):
        if wmi:
            try:
                self._wmi = wmi.WMI()
                batteries = self.wmi.CIM_Battery()
                self._battery = batteries[0] if batteries else None
            except Exception:
                self._battery = None
        else:
            self._battery = None
