import psutil


def read_battery():
    b = psutil.sensors_battery()
    return {
        "percent": b.percent,
        "plugged": b.power_plugged
    }