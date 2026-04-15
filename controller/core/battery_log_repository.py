import sqlite3

class BatteryLogRepository:
    def __init__(self, db_path="battery_logs.splite"):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_table(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battery_logs (
                device_id TEXT,
                timestamp TEXT,
                plugged INTEGER,
                level INTEGER,
                localisation TEXT,
                voltage INTEGER,
                capacity REAL,
                model TEXT,
                event_type TEXT,
                event_chargelevel INTEGER,
                sent INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def insert_log(self, log):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO battery_logs (
                device_id, timestamp, plugged, level,
                localisation, voltage, capacity, model,
                event_type, event_chargelevel, sent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            log["device_id"],
            log["timestamp"],
            log["plugged"],
            log["level"],
            log["localisation"],
            log["voltage"],
            log["capacity"],
            log["model"],
            log["event_type"],
            log["event_chargelevel"],
        ))

        conn.commit()
        conn.close()

    def get_unsent_logs(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT rowid, * FROM battery_logs
            WHERE sent = 0
            ORDER BY timestamp ASC
                       
        """)

        rows = cursor.fetchall()
        conn.close()

        return rows
    
    def mark_sent(self, rowid):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE battery_logs
            SET sent = 1
            WHERE rowid = ?
        """, (rowid,))

        conn.commit()
        conn.close()

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
        conn = self._connect()
        cursor = conn.cursor()

        if interval is not None:
            cursor.execute("UPDATE settings SET interval = ? WHERE id = 1", (interval,))
        if manual_override is not None:
            cursor.execute("UPDATE settings SET manual_override = ? WHERE id = 1", (manual_override,))
        if allowed_networks is not None:
            cursor.execute("UPDATE settings SET allowed_networks = ? WHERE id = 1", (allowed_networks,))

        conn.commit()
        conn.close()
