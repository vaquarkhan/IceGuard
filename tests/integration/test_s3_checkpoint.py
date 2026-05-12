"""Integration: checkpoint store with mocked S3."""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from iceguard.checkpoint_store import CheckpointStore
from iceguard.models import CheckpointData


def test_checkpoint_cycle_and_health():
    bucket: dict[str, bytes] = {}

    def put(**kw):
        bucket[kw["Key"]] = kw["Body"]

    def get(**kw):
        k = kw["Key"]
        if k not in bucket:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "n"}}, "GetObject"
            )
        b = bucket[k]

        class B:
            def read(self_inner):
                return b if isinstance(b, bytes) else b.encode()

        return {"Body": B()}

    def delete(**kw):
        bucket.pop(kw["Key"], None)

    client = MagicMock()
    client.put_object.side_effect = put
    client.get_object.side_effect = get
    client.delete_object.side_effect = delete
    client.head_bucket.return_value = {}

    cs = CheckpointStore("buck", "pre/", s3_client=client)
    cp = CheckpointData(
        idempotency_key="k",
        table_path="s3://t",
        table_format="iceberg",
        record_offset=1,
        partition_info={},
        file_manifest=[],
        created_at="2024-01-01T00:00:00+00:00",
        lambda_function_name="f",
        lambda_request_id="r",
    )
    cs.save("key1", cp)
    loaded = cs.load("key1")
    assert loaded is not None and loaded.record_offset == 1
    cs.delete("key1")
    assert cs.load("key1") is None

    with patch("boto3.client", return_value=client):
        assert cs.health_check(timeout_ms=100) is True
