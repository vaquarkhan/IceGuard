# Feature: iceguard, Property 4–5: SafeWriter checkpoint semantics
from unittest.mock import MagicMock

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from iceguard.adapters import IcebergAdapter
from iceguard.config import IceGuardConfig
from iceguard.metrics import MetricsEmitter
from iceguard.safe_writer import SafeWriter


def _ctx():
    c = MagicMock()
    c.get_remaining_time_in_millis.return_value = 600_000
    c.aws_request_id = "r"
    c.function_name = "fn"
    return c


@settings(max_examples=40, deadline=None)
@given(st.integers(min_value=0, max_value=100), st.integers(min_value=1, max_value=200))
def test_property_4_resume_skips_first_n_records(n: int, total: int) -> None:
    assume(n < total)
    from iceguard.checkpoint_store import CheckpointStore
    from iceguard.models import CheckpointData, FileEntry

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

    client = MagicMock()
    client.put_object.side_effect = put
    client.get_object.side_effect = get
    client.delete_object.side_effect = lambda **k: store.pop(k["Key"], None)
    cs = CheckpointStore("b", "p/", s3_client=client)
    cp = CheckpointData(
        idempotency_key="r",
        table_path="s3://t",
        table_format="iceberg",
        record_offset=n,
        partition_info={},
        file_manifest=[],
        created_at="2024-01-01T00:00:00+00:00",
        lambda_function_name="fn",
        lambda_request_id="r",
    )
    cs.save("r", cp)
    cfg = IceGuardConfig(s3_bucket="b", checkpoint_interval=1000)
    metrics = MagicMock(spec=MetricsEmitter)
    sw = SafeWriter(
        _ctx(),
        cfg,
        IcebergAdapter(),
        checkpoint_store=cs,
        idempotency_key="r",
        metrics_emitter=metrics,
    )
    processed = []

    with sw:

        def bw(a, b):
            processed.append((a, b))

        sw.write(path="s3://t", total_records=total, batch_writer=bw)
    starts = [a for a, _ in processed]
    assert min(starts) >= n


@settings(max_examples=40, deadline=None)
@given(st.integers(min_value=1, max_value=50), st.integers(min_value=1, max_value=20))
def test_property_5_checkpoint_writes_proportional_to_interval(total: int, interval: int) -> None:
    from iceguard.checkpoint_store import CheckpointStore

    store = MagicMock(spec=CheckpointStore)
    store.load.return_value = None
    cfg = IceGuardConfig(s3_bucket="x", checkpoint_interval=interval)
    metrics = MagicMock(spec=MetricsEmitter)
    sw = SafeWriter(_ctx(), cfg, IcebergAdapter(), checkpoint_store=store, metrics_emitter=metrics)
    with sw:
        sw.write(
            path="s3://t",
            total_records=total,
            batch_writer=lambda a, b: None,
        )
    saves = store.save.call_count
    expected = 0
    pos = 0
    while pos < total:
        pos = min(pos + interval, total)
        expected += 1
    assert saves == expected
