"""Checkpoint schema version migration."""

from __future__ import annotations

from typing import Any, Dict

from iceguard.models import CheckpointData, FileEntry

CURRENT_SCHEMA_VERSION = 1


def migrate_checkpoint_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Upgrade raw checkpoint dict to the latest schema version."""
    version = int(data.get("schema_version", 1))
    if version < 1:
        data["schema_version"] = 1
        version = 1
    if version == 1:
        data.setdefault("partition_info", {})
        manifest = data.get("file_manifest") or []
        normalized = []
        for entry in manifest:
            if isinstance(entry, dict):
                normalized.append(
                    {
                        "path": str(entry.get("path", "")),
                        "size_bytes": int(entry.get("size_bytes", 0)),
                        "record_count": int(entry.get("record_count", 0)),
                        "checksum": str(entry.get("checksum", "")),
                    }
                )
        data["file_manifest"] = normalized
    if int(data.get("schema_version", 1)) > CURRENT_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported checkpoint schema_version {data.get('schema_version')}"
        )
    data["schema_version"] = CURRENT_SCHEMA_VERSION
    return data


def load_checkpoint_migrated(raw: str, *, file_path: str = "<memory>") -> CheckpointData:
    """Parse JSON and apply migrations before building CheckpointData."""
    import json

    from iceguard.exceptions import CheckpointCorruptionError

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise CheckpointCorruptionError(file_path, f"invalid JSON: {e}") from e
    if not isinstance(data, dict):
        raise CheckpointCorruptionError(file_path, "checkpoint root must be object")
    required = (
        "idempotency_key",
        "table_path",
        "table_format",
        "record_offset",
        "file_manifest",
        "created_at",
        "lambda_function_name",
        "lambda_request_id",
    )
    for field in required:
        if field not in data:
            raise CheckpointCorruptionError(
                file_path, f"checkpoint schema mismatch: missing {field!r}"
            )
    try:
        migrated = migrate_checkpoint_dict(data)
    except (KeyError, TypeError, ValueError) as e:
        raise CheckpointCorruptionError(file_path, f"checkpoint schema mismatch: {e}") from e
    files = [
        FileEntry(
            path=str(f["path"]),
            size_bytes=int(f["size_bytes"]),
            record_count=int(f["record_count"]),
            checksum=str(f["checksum"]),
        )
        for f in migrated["file_manifest"]
    ]
    return CheckpointData(
        idempotency_key=str(migrated["idempotency_key"]),
        table_path=str(migrated["table_path"]),
        table_format=str(migrated["table_format"]),
        record_offset=int(migrated["record_offset"]),
        partition_info=dict(migrated["partition_info"]),
        file_manifest=files,
        created_at=str(migrated["created_at"]),
        lambda_function_name=str(migrated["lambda_function_name"]),
        lambda_request_id=str(migrated["lambda_request_id"]),
        schema_version=int(migrated["schema_version"]),
    )
