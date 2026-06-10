import os
import sqlite3
import unittest
from tracker.core.battery_log_repository import BatteryLogRepository

TEST_DB = "test_battery_log.sqlite"

class TestBatteryLogRepository(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        self.repo = BatteryLogRepository(TEST_DB)
        self.repo.create_table()

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_table_created(self):
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT name FROM sqlite_master
                       WHERE type='table' AND name='battery_logs'
                    """)
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertIsNotNone(result)

    def test_insert_log(self):
        log = {
            "id": "test-uuid-1",
            "device_id": "abc123",
            "timestamp": "2024-01-01 12:00:00",
            "plugged": 1,
            "level": 80,
            "localisation": "bureau",
            "event_type": "CHARGE_UP",
            "event_chargelevel": 80,
        }

        self.repo.insert_log(log)

        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM battery_logs")
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 1)

    def test_get_unsent_logs(self):
        log1 = {
            "id": "test-uuid-2",
            "device_id": "id1",
            "timestamp": "2024-01-01 10:00:00",
            "plugged": 1,
            "level": 50,
            "localisation": "bureau",
            "event_type": None,
            "event_chargelevel": None,
        }

        log2 = {
            "id": "test-uuid-3",
            "device_id": "id2",
            "timestamp": "2024-01-01 11:00:00",
            "plugged": 0,
            "level": 40,
            "localisation": "bureau",
            "event_type": "UNPLUGGED",
            "event_chargelevel": 40,
        }

        self.repo.insert_log(log1)
        self.repo.insert_log(log2)

        unsent = self.repo.get_unsent_logs()

        self.assertEqual(len(unsent), 2)

    def test_mark_sent(self):
        log = {
            "id": "test-uuid-4",
            "device_id": "id1",
            "timestamp": "2024-01-01 10:00:00",
            "plugged": 1,
            "level": 50,
            "localisation": "bureau",
            "event_type": None,
            "event_chargelevel": None,
        }

        self.repo.insert_log(log)

        unsent = self.repo.get_unsent_logs()
        row_id = unsent[0]["id"]

        self.repo.mark_sent(row_id)

        unsent_after = self.repo.get_unsent_logs()

        self.assertEqual(len(unsent_after), 0)

    def test_delete_old(self):
        log = {
            "id": "test-uuid-5",
            "device_id": "id1",
            "timestamp": "2024-01-01 10:00:00",
            "plugged": 1,
            "level": 50,
            "localisation": "bureau",
            "event_type": None,
            "event_chargelevel": None,
        }

        self.repo.insert_log(log)

        deleted = self.repo.delete_old(before="2024-01-02 00:00:00")

        self.assertEqual(deleted, 1)
