"""Live AWS E2E tests (optional). Run: pytest tests/e2e -m aws"""

import os

import pytest

pytestmark = pytest.mark.aws

AWS_RUN = os.environ.get("ICEGUARD_AWS_E2E", "").lower() in ("1", "true", "yes")
BUCKET = os.environ.get("ICEGUARD_E2E_BUCKET")
TABLE_PREFIX = os.environ.get("ICEGUARD_E2E_TABLE_PREFIX", "iceguard-e2e/table")


@pytest.fixture
def _skip_without_aws():
    if not AWS_RUN or not BUCKET:
        pytest.skip("Set ICEGUARD_AWS_E2E=1 and ICEGUARD_E2E_BUCKET for live tests")


@pytest.mark.usefixtures("_skip_without_aws")
def test_checkpoint_roundtrip_on_s3():
    import boto3

    from iceguard.checkpoint_store import CheckpointStore
    from iceguard.models import CheckpointData

    store = CheckpointStore(BUCKET, prefix="iceguard/e2e/")
    cp = CheckpointData(
        idempotency_key="e2e-key",
        table_path=f"s3://{BUCKET}/{TABLE_PREFIX}",
        table_format="iceberg",
        record_offset=42,
        partition_info={},
        file_manifest=[],
        created_at="2026-01-01T00:00:00+00:00",
        lambda_function_name="e2e",
        lambda_request_id="e2e-req",
    )
    store.save("e2e-key", cp)
    loaded = store.load("e2e-key")
    assert loaded is not None
    assert loaded.record_offset == 42
    store.delete("e2e-key")
    assert store.load("e2e-key") is None


@pytest.mark.usefixtures("_skip_without_aws")
def test_express_bucket_name_heuristic():
    from iceguard.s3_ops import validate_express_one_zone_bucket

    assert validate_express_one_zone_bucket("mybucket--use1-az1--x-s3") is True
    assert validate_express_one_zone_bucket(BUCKET) in (True, False)
