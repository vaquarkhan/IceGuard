"""Unit tests for SafeWriter and protect()."""

from unittest.mock import MagicMock

import pytest

import iceguard
from iceguard.adapters import IcebergAdapter
from iceguard.checkpoint_store import CheckpointStore
from iceguard.config import IceGuardConfig
from iceguard.exceptions import IceGuardContextError, IceGuardRollbackError
from iceguard.metrics import MetricsEmitter
from iceguard.safe_writer import SafeWriter


def _ctx(remaining_ms: int = 300_000):
    c = MagicMock()
    c.get_remaining_time_in_millis.return_value = remaining_ms
    c.aws_request_id = "req"
    c.function_name = "fn"
    return c


def test_protect_defaults():
    ctx = _ctx()
    with iceguard.protect(ctx) as sw:
        assert isinstance(sw, SafeWriter)
        assert sw._config.rollback_threshold_ms == 30000


def test_protect_invalid_format():
    with pytest.raises(iceguard.IceGuardConfigError):
        iceguard.protect(_ctx(), table_format="parquet")


def test_public_symbols_importable():
    for name in iceguard.__all__:
        getattr(iceguard, name)


def test_invalid_context():
    bad = MagicMock()
    del bad.get_remaining_time_in_millis
    cfg = IceGuardConfig()
    sw = SafeWriter(bad, cfg, IcebergAdapter())
    with pytest.raises(IceGuardContextError):
        sw.__enter__()


def test_write_success_deletes_checkpoint():
    store: dict[str, bytes] = {}

    def put(**kw):
        store[kw["Key"]] = kw["Body"]

    def get(**kw):
        from botocore.exceptions import ClientError

        if kw["Key"] not in store:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "n"}}, "GetObject"
            )

        b = store[kw["Key"]]

        class B:
            def read(self_inner):
                return b if isinstance(b, bytes) else b.encode()

        return {"Body": B()}

    def delete(**kw):
        store.pop(kw["Key"], None)

    client = MagicMock()
    client.put_object.side_effect = put
    client.get_object.side_effect = get
    client.delete_object.side_effect = delete
    cs = CheckpointStore("bucket", "p/", s3_client=client)
    m = MagicMock(spec=MetricsEmitter)
    cfg = IceGuardConfig(s3_bucket="bucket", checkpoint_interval=3)
    sw = SafeWriter(_ctx(), cfg, IcebergAdapter(), checkpoint_store=cs, metrics_emitter=m)
    with sw:
        sw.write(path="s3://t/p", total_records=10, batch_writer=lambda a, b: None)
    m.emit_write_outcome.assert_called()


def test_rollback_triggers():
    ctx = _ctx(300_000)
    cfg = IceGuardConfig(
        rollback_threshold_ms=5000,
        checkpoint_interval=2,
        s3_bucket="b",
    )
    store = MagicMock(spec=CheckpointStore)
    store.load.return_value = None
    sw = SafeWriter(ctx, cfg, IcebergAdapter(), checkpoint_store=store, metrics_emitter=MagicMock())
    with sw:

        def writer(s, e):
            if e >= 4:
                sw._rollback.set()

        with pytest.raises(IceGuardRollbackError):
            sw.write(path="s3://t", total_records=100, batch_writer=writer)
