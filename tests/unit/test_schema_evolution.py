"""Schema evolution for checkpoints."""

from iceguard.models import CheckpointData, FileEntry
from iceguard.schema_evolution import CURRENT_SCHEMA_VERSION, migrate_checkpoint_dict


def test_migrate_sets_schema_version():
    data = {
        "idempotency_key": "k",
        "table_path": "s3://t",
        "table_format": "iceberg",
        "record_offset": 0,
        "partition_info": {},
        "file_manifest": [],
        "created_at": "2026-01-01T00:00:00+00:00",
        "lambda_function_name": "fn",
        "lambda_request_id": "r",
    }
    out = migrate_checkpoint_dict(data)
    assert out["schema_version"] == CURRENT_SCHEMA_VERSION


def test_from_json_uses_migration():
    cp = CheckpointData(
        idempotency_key="k",
        table_path="s3://t",
        table_format="iceberg",
        record_offset=5,
        partition_info={},
        file_manifest=[FileEntry("p", 1, 1, "c")],
        created_at="2026-01-01T00:00:00+00:00",
        lambda_function_name="fn",
        lambda_request_id="r",
        schema_version=1,
    )
    loaded = CheckpointData.from_json(cp.to_json())
    assert loaded.record_offset == 5
