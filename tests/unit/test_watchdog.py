"""Unit tests for WatchdogThread."""

import time
from unittest.mock import MagicMock

import pytest

from iceguard.watchdog import WatchdogThread


class TestWatchdogThread:
    def test_callback_once_when_below_threshold(self):
        hits = []

        def cb():
            hits.append(1)

        ctx = MagicMock()
        ctx.get_remaining_time_in_millis.return_value = 1000
        w = WatchdogThread(ctx, threshold_ms=5000, callback=cb, poll_interval_ms=100)
        w.start()
        time.sleep(0.35)
        w.disarm()
        assert len(hits) == 1

    def test_disarm_stops_within_reasonable_time(self):
        ctx = MagicMock()
        ctx.get_remaining_time_in_millis.return_value = 600_000
        w = WatchdogThread(ctx, threshold_ms=5000, callback=lambda: None, poll_interval_ms=100)
        w.start()
        time.sleep(0.05)
        w.disarm()
        assert not w.is_armed()

    def test_daemon_thread(self):
        ctx = MagicMock()
        ctx.get_remaining_time_in_millis.return_value = 10_000
        w = WatchdogThread(ctx, threshold_ms=5000, callback=lambda: None, poll_interval_ms=200)
        w.start()
        assert w._thread is not None
        assert w._thread.daemon is True
        w.disarm()
