# Battery Tracker (Spoke Node Telemetry Engine)

This repository contains the client-side telemetry engine deployed on participating office workstations ("spokes") for the Human-Computer Interaction (HCI) behavior modification study. 

The tracker monitors hardware power states, detects behavioral events (such as manual plug/unplug actions), applies a strict network whitelist to ensure data collection only happens in-office, and utilizes an offline-resilient transactional loop to securely stream payloads to a central server via Tailscale.

---

## 🏗️ System Architecture & Data Flow

The tracker operates as an independent edge node in a hub-and-spoke telemetry architecture:

1. **Hardware Polling:** System background schedulers execute the core tracking routines at set intervals.
2. **Network Gate:** The repository queries system network interface profiles. If the node is not connected to a whitelisted office network, data collection safely aborts to prevent remote-work tracking or dataset pollution.
3. **Local Cache (WAL Mode):** Valid telemetry is processed through an event-priority state machine and safely cached in a local SQLite file using Write-Ahead Logging (WAL) to handle concurrent operations cleanly.
4. **Resilient Transmission:** A delivery worker queries the local cache, batches unsent data, streams JSON payloads to the central server via an active Tailscale network tunnel, and purges local records only upon explicit server acknowledgement (`200 OK`).

---

## 💾 Local Storage Schema (SQLite)

The local engine utilizes a flat-file SQLite database located at `data/battery_logs.sqlite` containing two operational tables:

### 1. `battery_logs`
Stores the actual captured hardware telemetry metrics awaiting upstream delivery.
* `uuid` (TEXT, PRIMARY KEY): Globally unique identifier for the specific log transaction.
* `device_id` (TEXT): Unique hardware hash identifying the specific machine.
* `timestamp` (TEXT): ISO-8601 string of the exact sample moment.
* `plugged` (INTEGER): Binary indicator (`1` = Charging/AC, `0` = Discharging/Battery).
* `level` (INTEGER): Current battery capacity percentage (0 to 100).
* `localisation` (TEXT): The active network connection profile name at sample time.
* `event_type` (TEXT, Nullable): Categorized behavioral event isolated by the state engine (e.g., `PLUGGED_IN`, `UNPLUGGED`, `LOW_BATTERY`).
* `event_chargelevel` (INTEGER, Nullable): Battery percentage at the precise moment the event occurred.
* `sent` (INTEGER): Status flag (`0` = Cached locally, `1` = Successfully ingested by server).

### 2. `settings`
Maintains operational parameters that govern edge node behavior.
* `id` (INTEGER, PRIMARY KEY): Singleton row key (always `1`).
* `interval` (INTEGER): Default polling step frequency in minutes.
* `allowed_networks` (TEXT): Comma-separated whitelist of office SSIDs or Ethernet profiles.
* `manual_override` (INTEGER): Flag to bypass selective runtime constraints.

---

## ⚙️ Network Configuration & Whitelisting

To protect participant privacy and maintain dataset integrity, telemetry is **only** gathered when a participant is physically connected to an approved office network environment.

### Active Network Detection
The tracking engine inspects active system network connection profiles (such as Wi-Fi SSIDs or Ethernet interface adapters) at runtime.

Before executing telemetry collection:
1. The script queries active system network adapters.
2. It compares the active connection name/IP subnet against the `allowed_networks` whitelist in the local settings store.
3. If no whitelisted connection is detected (e.g., user is working remotely or on public Wi-Fi), the execution loop aborts cleanly without reading system state or writing log entries.

> **Note:** Update the `allowed_networks` parameter in your local `settings` database table to reflect your target office network profile names or SSIDs.

## 🔒 Tailscale Tunnel Security

All data transactions bypass the public internet for data privacy and security. The application references a fixed private IP assigned within your personal **Tailscale Tailnet** (`100.x.x.x`). 
* The spoke machine must have the Tailscale daemon running (`tailscale up`).
* If the Tailscale network tunnel is unreachable, the client-side `Sender` component catches the connection exception gracefully, retains the log file inside the local SQLite database, and safely defers delivery to the next scheduled interval cycle.

---

## 🐧 Linux Installation Guide (Systemd)

Follow these steps to deploy and schedule the tracking daemon on a Linux (Ubuntu/XFCE) spoke machine using systemd.

### 1. Project Deployment
Clone the repository and set up your python environment:

# Ensure dependencies like psutil and requests are installed
pip3 install -r battery_tracker/requirements.txt
```

### 2. Create the Systemd Service File
Create a service configuration file to tell systemd how to run your tracker script:
```bash
sudo nano /etc/systemd/system/battery-tracker.service
```
Paste the following contents into the file (adjusting paths for your local user username):
```ini
[Unit]
Description=Battery Tracker Telemetry Logger Spoke Service
After=network.target tailscaled.service

[Service]
Type=oneshot
User=<USER>
WorkingDirectory=<YOUR DIRECTORY>
ExecStart=/usr/bin/python3 -c "from tracker.core.battery_log_repository import BatteryLogRepository; from tracker.core.event_detector import EventDetector; from tracker.core.integration import run_once; repo=BatteryLogRepository(); repo.create_table(); detector=EventDetector(); run_once(repo, detector)"

[Install]
WantedBy=multi-user.target
```

### 3. Create the Systemd Timer File
Create a timer file to trigger the service file automatically every 20 minutes:
```bash
sudo nano /etc/systemd/system/battery-tracker.timer
```
Paste the following configuration:
```ini
[Unit]
Description=Run Battery Tracker every minute

[Timer]
OnBootSec=5min
OnUnitActiveSec=1min

[Install]
WantedBy=timers.target
```

### 4. Enable and Start the Schedulers
Reload systemd to read your new scripts, enable the timer so it survives system reboots, and start the tracker sequence immediately:
```bash
sudo systemctl daemon-reload
sudo systemctl enable battery-tracker.timer
sudo systemctl start battery-tracker.timer
```

### 5. Monitor and Verify Logs
To verify that the systemd timer is functioning and see script debugging text:
```bash
sudo systemctl status battery-tracker.timer
journalctl -u battery-tracker.service -n 50
```

---

## 🪟 Windows Installation Guide

Follow these steps to deploy and schedule the tracking daemon on a Windows-based workspace machine.

### 1. Prerequisites & Environment Setup
1. Download and install **Python 3.x** for Windows (ensure you check the box to **"Add Python to PATH"** during installation).
2. Download and authenticate the **Tailscale for Windows** client application.
3. Open a PowerShell terminal and clone or copy the project code to your local machine:
   ```powershell
   cd C:\Users\YourUsername\ProjectRepo
   pip install psutil requests
   ```

### 2. Automated Run Script
Create a simple batch script launcher inside your project directory called `launch_tracker.bat` to handle execution context:
```batch
@echo off
cd C:\Users\YourUsername\ProjectRepo\battery_tracker
python -c "from tracker.core.battery_log_repository import BatteryLogRepository; from tracker.core.event_detector import EventDetector; from tracker.core.integration import run_once; repo=BatteryLogRepository(); repo.create_table(); detector=EventDetector(); run_once(repo, detector)"
```

### 3. Schedule Task via Windows Task Scheduler
Windows uses the **Task Scheduler** engine to handle scheduling instead of systemd:

1. Open the Start Menu, type **Task Scheduler**, and hit Enter.
2. Click **Create Basic Task** in the Actions pane on the right.
3. **Name:** `Battery Tracker Spoke Telemetry`
4. **Trigger:** Select **Daily**. Set the start time.
5. **Action:** Select **Start a program**.
6. **Program/script:** Browse and select your `launch_tracker.bat` file.
7. Click **Finish** to build the base task.

### 4. Adjust Intervals for Continuous Office Tracking
To ensure the script triggers every 20 minutes continuously:
1. Double-click your new task inside the **Task Scheduler Library** list to open its properties.
2. Navigate to the **Triggers** tab, select the daily trigger, and click **Edit**.
3. Under **Advanced settings**, check the box for **Repeat task every:** and select or type **20 minutes**.
4. Set **for a duration of:** to **Indefinitely**.
5. Navigate to the **Conditions** tab and uncheck **Start the task only if the computer is on AC power** (otherwise it will refuse to log behavior when the user is operating on battery power).
6. Click **OK** to save.