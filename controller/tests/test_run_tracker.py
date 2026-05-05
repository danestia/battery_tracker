import signal
import sys
import unittest
from unittest.mock import MagicMock, patch, call

import run_tracker

class TestHandleShutdown(unittest.TestCase):

    def setUp(self):
        run_tracker.shutdown_requested = False

    def tearDown(self):
        run_tracker.shutdown_requested = False

    def test_sets_shutdown_flag(self):
        run_tracker.handle_shutdown(signal.SIGTERM, None)
        self.assertTrue(run_tracker.shutdown_requested)

    def test_idempotent(self):
        run_tracker.handle_shutdown(signal.SIGTERM, None)
        run_tracker.handle_shutdown(signal.SIGTERM, None)
        self.assertTrue(run_tracker.shutdown_requested)

class TestRegisterSignals(unittest.TestCase):

    def test_registers_sigterm_and_sigint(self):
        with patch("signal.signal") as mock_signal:
            run_tracker.register_signals()
            calls = mock_signal.call_args_list
            registered = [c[0][0] for c in calls]
            self.assertIn(signal.SIGTERM, registered)
            self.assertIn(signal.SIGINT, registered)

    def test_registers_sigbreak_on_windows(self):
        with patch("run_tracker.sys") as mock_sys, \
             patch("signal.signal") as mock_signal:
            mock_sys.platform = "win32"
            run_tracker.register_signals()
            calls = mock_signal.call_args_list
            registered = [c[0][0] for c in calls]
            self.assertIn(signal.SIGBREAK, registered)

    def test_no_sigbreak_on_linux(self):
        with patch("run_tracker.sys") as mock_sys, \
             patch("signal.signal") as mock_signal:
            mock_sys.platform = "linux"
            run_tracker.register_signals()
            calls = mock_signal.call_args_list
            registered = [c[0][0] for c in calls]
            self.assertNotIn(signal.SIGBREAK, registered)
