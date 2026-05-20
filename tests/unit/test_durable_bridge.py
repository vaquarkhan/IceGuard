"""Durable checkpoint bridge tests."""

import json
from unittest.mock import MagicMock

from iceguard.checkpoint_store import CheckpointStore
from iceguard.durable import DurableCheckpointBridge
from iceguard.models import CheckpointData, FileEntry


def test_durable_bridge_mirrors_checkpoint():
    store = MagicMock(spec=CheckpointStore)
    durable = MagicMock()
    bridge = DurableCheckpointBridge(store, durable)
    cp = CheckpointData(
        idempotency_key="k",
        table_path="s3://t",
        table_format="iceberg",
        record_offset=10,
        partition_info={},
        file_manifest=[],
        created_at="2026-01-01T00:00:00+00:00",
        lambda_function_name="fn",
        lambda_request_id="r",
    )
    bridge.save("k", cp)
    store.save.assert_called_once_with("k", cp)
    durable.checkpoint.assert_called_once()
    payload = durable.checkpoint.call_args[0][0]
    assert json.loads(payload.decode())["record_offset"] == 10
