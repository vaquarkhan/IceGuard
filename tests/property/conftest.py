"""Fixtures for property-based tests (fast, no AWS, no real watchdog threads)."""

import pytest


class _NoOpWatchdog:
    """Stub watchdog for Hypothesis runs: no threads, no sleeps."""

    def __init__(self, _ctx, _threshold, callback, poll_interval_ms=500):
        self._callback = callback

    def start(self) -> None:
        return None

    def started_ok(self) -> bool:
        return True

    def disarm(self) -> None:
        return None

    def is_armed(self) -> bool:
        return False


@pytest.fixture(autouse=True)
def _fast_safe_writer(monkeypatch):
    """Property tests must not open CloudWatch or spawn timing-sensitive threads."""
    monkeypatch.setattr("iceguard.safe_writer.WatchdogThread", _NoOpWatchdog)
    monkeypatch.setattr("iceguard.safe_writer.time.sleep", lambda _secs: None)
