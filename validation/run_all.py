#!/usr/bin/env python3
"""Run core IceGuard validation checks (no AWS required except optional S3 tests)."""

from __future__ import annotations

import sys
import time
from unittest.mock import MagicMock

# Ensure src layout is importable when run as ``python validation/run_all.py``.
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from iceguard.adapters import IcebergAdapter
from iceguard.config import IceGuardConfig
from iceguard.enums import TableFormat
from iceguard.exceptions import IceGuardInitializationError, IceGuardRollbackError
from iceguard.metrics import BackgroundMetricsEmitter, MetricsEmitter, NullMetricsEmitter
from iceguard.safe_writer import SafeWriter
from iceguard.watchdog import WatchdogThread


def _ok(name: str) -> None:
    print(f"PASS  {name}")


def _fail(name: str, detail: str) -> None:
    print(f"FAIL  {name}: {detail}")
    raise SystemExit(1)


def t_watchdog_started_vs_alive() -> None:
    ctx = MagicMock()
    ctx.get_remaining_time_in_millis.return_value = 1000
    fired = []

    w = WatchdogThread(ctx, 5000, lambda: fired.append(1), poll_interval_ms=100)
    w.start()
    time.sleep(0.3)
    assert w.started_ok(), "watchdog must report started even after firing"
    assert len(fired) == 1
    w.disarm()
    _ok("watchdog_started_ok_after_fire")


def t_enter_rollback_not_init() -> None:
    ctx = MagicMock()
    ctx.get_remaining_time_in_millis.return_value = 1000
    ctx.function_name = "fn"
    ctx.aws_request_id = "r"
    sw = SafeWriter(
        ctx,
        IceGuardConfig(rollback_threshold_ms=5000),
        IcebergAdapter(),
        metrics_emitter=NullMetricsEmitter(),
    )
    try:
        sw.__enter__()
        _fail("enter_rollback", "expected IceGuardRollbackError")
    except IceGuardRollbackError:
        _ok("enter_raises_rollback_when_below_threshold")


def t_background_metrics_non_blocking() -> None:
    inner = MagicMock(spec=MetricsEmitter)
    bg = BackgroundMetricsEmitter(inner)

    def slow_emit(*a, **k):
        time.sleep(0.5)

    inner.emit_checkpoint_resume.side_effect = slow_emit
    t0 = time.perf_counter()
    bg.emit_checkpoint_resume(1)
    elapsed = time.perf_counter() - t0
    bg.close()
    if elapsed > 0.2:
        _fail("background_metrics", f"emit blocked for {elapsed:.2f}s")
    _ok("background_metrics_non_blocking")


def t_adapter_s3_delete_called() -> None:
    s3 = MagicMock()
    adapter = IcebergAdapter(committed_files=set(), s3_client=s3)
    adapter.delete_uncommitted_files(["s3://bkt/data/f1.parquet"])
    s3.delete_object.assert_called()
    _ok("adapter_deletes_s3_paths")


def t_config_string_format() -> None:
    c = IceGuardConfig(table_format="iceberg")
    assert c.table_format == TableFormat.ICEBERG
    _ok("config_accepts_string_table_format")


def main() -> None:
    print("IceGuard validation\n")
    t_watchdog_started_vs_alive()
    t_enter_rollback_not_init()
    t_background_metrics_non_blocking()
    t_adapter_s3_delete_called()
    t_config_string_format()
    print("\nAll validation checks passed.")


if __name__ == "__main__":
    main()
