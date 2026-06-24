import sqlite3
import time
import os
import subprocess

class BatteryLogRepository:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, "data", "battery_logs.sqlite")
        else:
            self.db_path = os.path.abspath(db_path)

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn
    
    def _execute_with_retry(self, query, params=(), retries=5,delay=0.2):
        for _ in range(retries):
            try:
                conn = self._connect()
                cur = conn.cursor()
                cur.execute(query, params)
                conn.commit()
                conn.close()
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e):
                    time.sleep(delay)
                    continue
                raise
        raise RuntimeError("DB locked too long")
    
    def create_table(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battery_logs (
                uuid TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                plugged INTEGER NOT NULL,
                level INTEGER NOT NULL,
                localisation TEXT,
                event_type TEXT,
                event_chargelevel INTEGER,
                sent INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                interval INTEGER DEFAULT 20,
                allowed_networks TEXT DEFAULT '',
                manual_override INTEGER DEFAULT 0
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO settings (id, interval, allowed_networks, manual_override) VALUES (1, 20, '', 0)")

        conn.commit()
        conn.close()

    def insert_log(self, log):
        self._execute_with_retry("""
            INSERT INTO battery_logs (
                uuid, device_id, timestamp, plugged, level,
                localisation, event_type, event_chargelevel
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log["uuid"],
            log["device_id"],
            log["timestamp"],
            log["plugged"],
            log["level"],
            log["localisation"],
            log["event_type"],
            log["event_chargelevel"],
        ))

    def get_unsent_logs(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM battery_logs
            WHERE sent = 0
            ORDER BY timestamp ASC
                       
        """)

        rows = cursor.fetchall()
        conn.close()

        return rows
    
    def mark_sent(self, log_uuid):
        
        self._execute_with_retry("""
            UPDATE battery_logs
            SET sent = 1
            WHERE uuid = ?
        """, (log_uuid,))

    def delete_old(self, before):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM battery_logs
            WHERE timestamp < ?
        """, (before,))

        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        return deleted
    
    def load_settings(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM settings WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        return dict(row)


    def update_settings(self, interval=None, manual_override=None, allowed_networks=None):
        if interval is not None:
            self._execute_with_retry("UPDATE settings SET interval = ? WHERE id = 1", (interval,))
        if manual_override is not None:
            self._execute_with_retry("UPDATE settings SET manual_override = ? WHERE id = 1", (manual_override,))
        if allowed_networks is not None:
            self._execute_with_retry("UPDATE settings SET allowed_networks = ? WHERE id = 1", (allowed_networks,))

    def delete_safely_sent_logs(self, record_uuids: list):

        if not record_uuids:
            return
        
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute('BEGIN TRANSACTION;')

            format_strings = ','.join(['?'] * len(record_uuids))

            cursor.execute(
                f"DELETE FROM battery_logs WHERE uuid IN ({format_strings})",
                record_uuids
            )

            conn.commit()

            cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_active_ssid(self) -> str:
        try:
            ssid = subprocess.check_output(
                ["nmcli", "-t", "-f", "ACTIVE,NAME", "connection", "show", "--active"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8")

            for line in ssid.splitlines():
                if line.startswith("yes:"):
                    return line.split("yes:")[1].strip()
        except Exception:
            pass
        return ""
    
    def is_network_allowed(self) -> bool:
        settings = self.load_settings()

        allowed_str = settings.get("allowed_networks", "")
        if not allowed_str:
            return True
        
        allowed_list = [net.strip() for net in allowed_str.split(",") if net.strip()]
        current_ssid = self.get_active_ssid()

        print(f"[DEBUG] Current SSID: '{current_ssid}' | Allowed: {allowed_list}")
        return current_ssid in allowed_list