"""SafeWriter __enter__ rollback vs initialization errors."""

import time
from unittest.mock import MagicMock

import pytest

from iceguard.adapters import IcebergAdapter
from iceguard.config import IceGuardConfig
from iceguard.exceptions import IceGuardInitializationError, IceGuardRollbackError
from iceguard.metrics import NullMetricsEmitter
from iceguard.safe_writer import SafeWriter


def test_enter_raises_rollback_not_init_when_already_below_threshold():
    ctx = MagicMock()
    ctx.get_remaining_time_in_millis.return_value = 1000
    ctx.function_name = "fn"
    ctx.aws_request_id = "r"
    cfg = IceGuardConfig(rollback_threshold_ms=5000)
    sw = SafeWriter(ctx, cfg, IcebergAdapter(), metrics_emitter=NullMetricsEmitter())
    with pytest.raises(IceGuardRollbackError):
        sw.__enter__()


def test_enter_raises_init_when_watchdog_never_starts(monkeypatch):
    ctx = MagicMock()
    ctx.get_remaining_time_in_millis.return_value = 600_000
    ctx.function_name = "fn"

    class BrokenWatchdog:
        def __init__(self, *a, **k):
            pass

        def start(self):
            pass

        def started_ok(self):
            return False

        def disarm(self):
            pass

    monkeypatch.setattr("iceguard.safe_writer.WatchdogThread", BrokenWatchdog)
    cfg = IceGuardConfig()
    sw = SafeWriter(ctx, cfg, IcebergAdapter(), metrics_emitter=NullMetricsEmitter())
    with pytest.raises(IceGuardInitializationError):
        sw.__enter__()
