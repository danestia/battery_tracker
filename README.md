# plantform
This is a first entry for github (README to be written later)

This project so far is started by running run_tracker.py
This will start the logging of battery events (plugged_in, unplugged, etc) at intervals. This functionality is tested and workign correctly.

The following are scripts to implement on linux machines to ensure the tracker auto-starts Mon - Fri at 9:00 and auto-stops at 17:00.

Scripts for Linux systems:
1. Type in terminal: sudo nano /etc/systemd/system/battery-tracker.service
2. Paste the following, save and exit -
[Unit]
Description=Battery Tracker

[Service]
Type=simple
WorkingDirectory=/home/dan/Documents/code/github_project/plantform
ExecStart=/usr/bin/python3 run_tracker.py
Restart=on-failure

[Install]
WantedBy=multi-user.target

3. Type: sudo nano /etc/systemd/system/battery-tracker-start.timer

4. Paste the following, save and exit -
[Unit]
Description=Start Battery Tracker at 09:00

[Timer]
OnCalendar=Mon..Fri 09:00
Persistent=true
Unit=battery-tracker.service

[Install]
WantedBy=timers.target

5. Type: sudo nano /etc/systemd/system/battery-tracker-stop.timer

6. Paste the following, save and exit -
[Unit]
Description=Stop Battery Tracker at 17:00

[Timer]
OnCalendar=Mon..Fri 17:00
Persistent=true
Unit=battery-tracker.service

[Install]
WantedBy=timers.target

7. Reload systemd with: sudo systemctl daemon-reload (must be done every edit/update)

8. Enable and start the timers.
Repectively:
sudo systemctl enable --now battery-tracker-start.timer
sudo systemctl enable --now battery-tracker-stop.timer

9. Confirm timer implementation: systemctl list-timers | grep battery

Pausing README writing because directories will change after containerisation
