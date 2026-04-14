# plantform
This is a first entry for github (README to be written later)

This project so far is started by running run_tracker.py
This will start the logging of battery events (plugged_in, unplugged, etc) at intervals. This functionality is tested and workign correctly.

The following are scripts to implement on linux machines to ensure the tracker auto-starts Mon - Fri at 9:00 and auto-stops at 17:00.

Scripts for Linux systems:
1. Type in terminal: sudo nano /etc/systemd/system/battery-tracker.service
2. Paste the following-
[Unit]
Description=Battery Tracker

[Service]
Type=simple
WorkingDirectory=/home/dan/Documents/code/github_project/plantform
ExecStart=/usr/bin/python3 run_tracker.py
Restart=on-failure

[Install]
WantedBy=multi-user.target

Pausing README writing because directories will change after containerisation
