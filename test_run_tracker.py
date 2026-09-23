import signal
import sys
import unittest
from unittest.mock import MagicMock, patch, call

import run_tracker

class TestHandleShutdown(unittest.TestCase):

    def setUp(self):
        run_tracker._SHUTDOWN_REQUESTED = False

    def tearDown(self):
        run_tracker._SHUTDOWN_REQUESTED = False

    def test_sets_shutdown_flag(self):
        run_tracker.handle_shutdown(signal.SIGTERM, None)
        self.assertTrue(run_tracker._SHUTDOWN_REQUESTED)

    def test_idempotent(self):
        run_tracker.handle_shutdown(signal.SIGTERM, None)
        run_tracker.handle_shutdown(signal.SIGTERM, None)
        self.assertTrue(run_tracker._SHUTDOWN_REQUESTED)

class TestRegisterSignals(unittest.TestCase):

    def test_registers_sigterm_and_sigint(self):
        with patch("signal.signal") as mock_signal:
            run_tracker.register_signals()
            calls = mock_signal.call_args_list
            registered = [c[0][0] for c in calls]
            self.assertIn(signal.SIGTERM, registered)
            self.assertIn(signal.SIGINT, registered)

    def test_registers_sigbreak_on_windows(self):
        if sys.platform != "win32":
            self.skipTest("SIGBREAK is Windows only")
        with patch("run_tracker.sys") as mock_sys, \
             patch("signal.signal") as mock_signal:
            mock_sys.platform = "win32"
            run_tracker.register_signals()
            calls = mock_signal.call_args_list
            registered = [c[0][0] for c in calls]
            self.assertIn(signal.SIGBREAK, registered)

    def test_no_sigbreak_on_linux(self):
        import sys

        windows_sigbreak = getattr(signal, "SIGBREAK", 21)

        with patch("run_tracker.sys") as mock_sys, \
             patch("signal.signal") as mock_signal:
            
            mock_sys.platform = "linux"
            run_tracker.register_signals()

            calls = mock_signal.call_args_list
            registered = [c[0][0] for c in calls]

            self.assertNotIn(windows_sigbreak, registered)

class TestMainLoop(unittest.TestCase):

    def setUp(self):
        run_tracker._SHUTDOWN_REQUESTED = False
        self.argv_patcher = patch("sys.argv", ["run_tracker.py"])
        self.argv_patcher.start()

    def tearDown(self):
        run_tracker._SHUTDOWN_REQUESTED = False
        self.argv_patcher.stop()

    def make_repo(self, interval=1, manual_override=0):
        repo = MagicMock()
        repo.load_settings.return_value = {
            "interval": interval,
            "manual_override": manual_override
        }
        return repo
    
    @patch("run_tracker.register_signals")
    @patch("run_tracker.BatteryLogRepository")
    @patch("run_tracker.EventDetector")
    @patch("run_tracker.Sender")
    @patch("run_tracker.run_once")
    @patch("run_tracker.sys")
    def test_calls_run_once_then_flushes_on_shutdown(
        self, mock_sys, mock_run_once, mock_sender_cls,
        mock_detector_cls, mock_repo_cls, mock_register
    ):
        repo = self.make_repo(interval=1)
        mock_repo_cls.return_value = repo

        sender = MagicMock()
        sender.send_unsent.return_value = 3
        mock_sender_cls.return_value = sender

        def shutdown_after_first(*args, **kwargs):
            run_tracker._SHUTDOWN_REQUESTED = True
        mock_run_once.side_effect = shutdown_after_first

        mock_sys.exit = MagicMock()
        mock_sys.platform = "linux"

        run_tracker.main()

        mock_run_once.assert_called_once()
        sender.send_unsent.assert_called_once()
        mock_sys.exit.assert_called_once_with(0)

    @patch("run_tracker.register_signals")
    @patch("run_tracker.BatteryLogRepository")
    @patch("run_tracker.EventDetector")
    @patch("run_tracker.Sender")
    @patch("run_tracker.run_once")
    @patch("run_tracker.sys")
    def test_flush_even_if_run_once_never_called(
        self, mock_sys, mock_run_once, mock_sender_cls,
        mock_detector_cls, mock_repo_cls, mock_register
    ):
        repo = self.make_repo(interval=1)
        mock_repo_cls.return_value = repo

        sender = MagicMock()
        sender.send_unsent.return_value = 0
        mock_sender_cls.return_value = sender

        run_tracker._SHUTDOWN_REQUESTED = True

        mock_sys.exit = MagicMock()
        mock_sys.platform = "linux"

        run_tracker.main()

        mock_run_once.assert_not_called()
        sender.send_unsent.assert_called_once()
        mock_sys.exit.assert_called_once_with(0)

    @patch("run_tracker.register_signals")
    @patch("run_tracker.BatteryLogRepository")
    @patch("run_tracker.EventDetector")
    @patch("run_tracker.Sender")
    @patch("run_tracker.run_once")
    @patch("run_tracker.sys")
    def test_clean_exit_even_if_send_raises(
        self, mock_sys, mock_run_once, mock_sender_cls,
        mock_detector_cls, mock_repo_cls, mock_register
    ):
        repo = self.make_repo(interval=1)
        mock_repo_cls.return_value = repo

        sender = MagicMock()
        sender.send_unsent.side_effect = Exception("network down")
        mock_sender_cls.return_value = sender

        def shutdown_after_first(*args, **kwargs):
            run_tracker._SHUTDOWN_REQUESTED = True
        mock_run_once.side_effect = shutdown_after_first

        mock_sys.exit = MagicMock()
        mock_sys.platform = "linux"

        run_tracker.main()

        sender.send_unsent.assert_called_once()
        mock_sys.exit.assert_called_once_with(0)

    @patch("run_tracker.register_signals")
    @patch("run_tracker.BatteryLogRepository")
    @patch("run_tracker.EventDetector")
    @patch("run_tracker.Sender")
    @patch("run_tracker.run_once")
    @patch("run_tracker.sys")
    def test_manual_override_skips_run_once(
        self, mock_sys, mock_run_once, mock_sender_cls,
        mock_detector_cls, mock_repo_cls, mock_register
    ):
        call_count = 0

        def settings_then_shutdown():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                run_tracker._SHUTDOWN_REQUESTED = True
            return {"interval": 1, "manual_override": 1}
        
        repo = MagicMock()
        repo.load_settings.side_effect = settings_then_shutdown
        mock_repo_cls.return_value = repo
        
        sender = MagicMock()
        sender.send_unsent.return_value = 0
        mock_sender_cls.return_value = sender

        mock_sys.exit = MagicMock()
        mock_sys.platform = "linux"

        run_tracker.main()

        mock_run_once.assert_not_called()
        mock_sys.exit.assert_called_once_with(0)
    
        
