"""Checkpoint KMS encryption."""

from unittest.mock import MagicMock

from iceguard.checkpoint_store import CheckpointStore
from iceguard.models import CheckpointData


def test_put_object_includes_kms_when_configured():
    client = MagicMock()
    store = CheckpointStore("b", kms_key_id="arn:aws:kms:us-east-1:1:key/abc", s3_client=client)
    cp = CheckpointData(
        idempotency_key="k",
        table_path="s3://t",
        table_format="iceberg",
        record_offset=0,
        partition_info={},
        file_manifest=[],
        created_at="2026-01-01T00:00:00+00:00",
        lambda_function_name="fn",
        lambda_request_id="r",
    )
    store.save("k", cp)
    kwargs = client.put_object.call_args.kwargs
    assert kwargs.get("ServerSideEncryption") == "aws:kms"
    assert kwargs.get("SSEKMSKeyId") == "arn:aws:kms:us-east-1:1:key/abc"
