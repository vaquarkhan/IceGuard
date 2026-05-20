"""Chaos-style tests: rollback at distinct points in the write lifecycle."""

from unittest.mock import MagicMock, patch

import pytest

from iceguard.adapters import IcebergAdapter
from iceguard.config import IceGuardConfig
from iceguard.exceptions import IceGuardRollbackError
from iceguard.metrics import NullMetricsEmitter
from iceguard.safe_writer import SafeWriter


def _ctx(remaining_ms: int = 600_000):
    c = MagicMock()
    c.get_remaining_time_in_millis.return_value = remaining_ms
    c.aws_request_id = "chaos-req"
    c.function_name = "chaos-fn"
    return c


def test_rollback_on_enter_when_time_exhausted():
    sw = SafeWriter(
        _ctx(1000),
        IceGuardConfig(rollback_threshold_ms=5000),
        IcebergAdapter(),
        metrics_emitter=NullMetricsEmitter(),
    )
    with pytest.raises(IceGuardRollbackError):
        sw.__enter__()


def test_rollback_before_first_chunk():
    sw = SafeWriter(_ctx(), IceGuardConfig(checkpoint_interval=10), IcebergAdapter(), metrics_emitter=NullMetricsEmitter())
    with pytest.raises(IceGuardRollbackError):
        with sw:
            sw._rollback.set()
            sw.write(
                path="s3://b/t",
                total_records=100,
                batch_writer=lambda s, e: None,
            )


def test_rollback_mid_chunks_deletes_paths():
    deleted: list[str] = []
    with patch("iceguard.adapters.delete_s3_uri", side_effect=lambda u, **k: deleted.append(u)):
        sw = SafeWriter(_ctx(), IceGuardConfig(checkpoint_interval=10), IcebergAdapter(), metrics_emitter=NullMetricsEmitter())
        with pytest.raises(IceGuardRollbackError):
            with sw:

                def bw(s, e):
                    if e >= 20:
                        sw._rollback.set()

                sw.write(
                    path="s3://b/t",
                    total_records=50,
                    batch_writer=bw,
                    track_paths=lambda s, e: [f"s3://b/t/p-{s}-{e}.parquet"],
                )
    assert deleted


def test_dlq_called_on_rollback():
    sw = SafeWriter(
        _ctx(),
        IceGuardConfig(),
        IcebergAdapter(),
        metrics_emitter=NullMetricsEmitter(),
        dlq_queue_url="https://sqs.us-east-1.amazonaws.com/123/q",
    )
    with patch("iceguard.dlq.publish_rollback_event") as pub:
        with pytest.raises(IceGuardRollbackError):
            with sw:
                sw._rollback.set()
                sw.write(path="s3://b/t", total_records=10, batch_writer=lambda s, e: None)
        pub.assert_called_once()
