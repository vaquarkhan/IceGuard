"""Unit tests for CheckpointStore."""

import io
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from iceguard.checkpoint_store import CheckpointStore
from iceguard.exceptions import CheckpointCorruptionError
from iceguard.models import CheckpointData, FileEntry


def _sample_checkpoint() -> CheckpointData:
    return CheckpointData(
        idempotency_key="k1",
        table_path="s3://b/t",
        table_format="iceberg",
        record_offset=10,
        partition_info={},
        file_manifest=[
            FileEntry("s3://b/f1", 1, 1, "x"),
        ],
        created_at="2024-01-01T00:00:00+00:00",
        lambda_function_name="fn",
        lambda_request_id="rid",
    )


def test_save_load_delete_roundtrip():
    store: dict[str, bytes] = {}

    def put_object(**kwargs):
        store[kwargs["Key"]] = kwargs["Body"]

    def get_object(**kwargs):
        key = kwargs["Key"]
        if key not in store:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "not found"}},
                "GetObject",
            )

        class Body:
            def read(self_inner):
                b = store[key]
                return b if isinstance(b, bytes) else b.encode("utf-8")

        return {"Body": Body()}

    def delete_object(**kwargs):
        store.pop(kwargs["Key"], None)

    client = MagicMock()
    client.put_object.side_effect = put_object
    client.get_object.side_effect = get_object
    client.delete_object.side_effect = delete_object

    cs = CheckpointStore("bucket", "pfx/", s3_client=client)
    cp = _sample_checkpoint()
    cs.save("abc", cp)
    loaded = cs.load("abc")
    assert loaded is not None
    assert loaded.record_offset == 10
    cs.delete("abc")
    assert cs.load("abc") is None


def test_load_missing_returns_none():
    client = MagicMock()
    client.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "nope"}},
        "GetObject",
    )
    cs = CheckpointStore("b", s3_client=client)
    assert cs.load("missing") is None


def test_load_corrupt_json_raises():
    client = MagicMock()
    client.get_object.return_value = {"Body": io.BytesIO(b"not json {")}

    cs = CheckpointStore("b", s3_client=client)
    with pytest.raises(CheckpointCorruptionError):
        cs.load("x")


def test_save_fail_open_no_exception():
    client = MagicMock()
    client.put_object.side_effect = RuntimeError("network")
    cs = CheckpointStore("b", s3_client=client)
    cs.save("k", _sample_checkpoint())


def test_health_check_timeout_returns_false():
    with patch("boto3.client") as bc:
        cw = MagicMock()
        cw.head_bucket.side_effect = Exception("down")
        cw.list_objects_v2.side_effect = Exception("down")
        bc.return_value = cw
        cs = CheckpointStore("bucket")
        assert cs.health_check(timeout_ms=100) is False


def test_health_check_success():
    with patch("boto3.client") as bc:
        cw = MagicMock()
        cw.head_bucket.return_value = {}
        bc.return_value = cw
        cs = CheckpointStore("bucket")
        assert cs.health_check(timeout_ms=5000) is True
