"""IceGuard data models: checkpoints, transactions, and metrics."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from iceguard.enums import TransactionStatus


@dataclass
class FileEntry:
    """A single file in the checkpoint manifest."""

    path: str
    size_bytes: int
    record_count: int
    checksum: str


@dataclass
class CheckpointData:
    """Checkpoint metadata persisted to S3."""

    idempotency_key: str
    table_path: str
    table_format: str
    record_offset: int
    partition_info: Dict[str, Any]
    file_manifest: List[FileEntry]
    created_at: str
    lambda_function_name: str
    lambda_request_id: str
    schema_version: int = 1

    def to_json(self) -> str:
        """Serialize checkpoint to JSON string."""
        payload = asdict(self)
        payload["file_manifest"] = [asdict(fe) for fe in self.file_manifest]
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, raw: str, *, file_path: str = "<memory>") -> CheckpointData:
        """Deserialize checkpoint from JSON; raises CheckpointCorruptionError on invalid data."""
        from iceguard.exceptions import CheckpointCorruptionError

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise CheckpointCorruptionError(file_path, f"invalid JSON: {e}") from e
        try:
            manifest_raw = data["file_manifest"]
            files = [
                FileEntry(
                    path=str(f["path"]),
                    size_bytes=int(f["size_bytes"]),
                    record_count=int(f["record_count"]),
                    checksum=str(f["checksum"]),
                )
                for f in manifest_raw
            ]
            return cls(
                idempotency_key=str(data["idempotency_key"]),
                table_path=str(data["table_path"]),
                table_format=str(data["table_format"]),
                record_offset=int(data["record_offset"]),
                partition_info=dict(data["partition_info"]),
                file_manifest=files,
                created_at=str(data["created_at"]),
                lambda_function_name=str(data["lambda_function_name"]),
                lambda_request_id=str(data["lambda_request_id"]),
                schema_version=int(data.get("schema_version", 1)),
            )
        except (KeyError, TypeError, ValueError) as e:
            raise CheckpointCorruptionError(
                file_path, f"checkpoint schema mismatch: {e}"
            ) from e


@dataclass
class ParticipantState:
    """State of a single participant in a coordinated transaction."""

    participant_id: str
    lambda_function_name: str
    vote: Optional[str]
    phase1_complete: bool
    phase2_complete: bool
    last_heartbeat: str


@dataclass
class TransactionState:
    """Persisted state for two-phase commit coordination."""

    transaction_id: str
    status: TransactionStatus
    participants: List[ParticipantState]
    created_at: str
    updated_at: str
    coordinator_lambda: str
    timeout_ms: int

    def to_json(self) -> str:
        """Serialize transaction state to JSON."""
        payload: Dict[str, Any] = {
            "transaction_id": self.transaction_id,
            "status": self.status.value,
            "participants": [
                {
                    "participant_id": p.participant_id,
                    "lambda_function_name": p.lambda_function_name,
                    "vote": p.vote,
                    "phase1_complete": p.phase1_complete,
                    "phase2_complete": p.phase2_complete,
                    "last_heartbeat": p.last_heartbeat,
                }
                for p in self.participants
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "coordinator_lambda": self.coordinator_lambda,
            "timeout_ms": self.timeout_ms,
        }
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, raw: str, *, file_path: str = "<memory>") -> TransactionState:
        """Deserialize transaction state from JSON."""
        from iceguard.exceptions import CheckpointCorruptionError

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise CheckpointCorruptionError(file_path, f"invalid JSON: {e}") from e
        try:
            parts = [
                ParticipantState(
                    participant_id=str(p["participant_id"]),
                    lambda_function_name=str(p["lambda_function_name"]),
                    vote=p.get("vote"),
                    phase1_complete=bool(p["phase1_complete"]),
                    phase2_complete=bool(p["phase2_complete"]),
                    last_heartbeat=str(p["last_heartbeat"]),
                )
                for p in data["participants"]
            ]
            return cls(
                transaction_id=str(data["transaction_id"]),
                status=TransactionStatus(str(data["status"])),
                participants=parts,
                created_at=str(data["created_at"]),
                updated_at=str(data["updated_at"]),
                coordinator_lambda=str(data["coordinator_lambda"]),
                timeout_ms=int(data["timeout_ms"]),
            )
        except (KeyError, TypeError, ValueError) as e:
            raise CheckpointCorruptionError(
                file_path, f"transaction state schema mismatch: {e}"
            ) from e


@dataclass
class WriteMetric:
    """Metric emitted on write completion."""

    table_name: str
    table_format: str
    outcome: str
    function_name: str
    duration_ms: int
    records_written: int


@dataclass
class NearMissMetric:
    """Metric emitted when rollback prevents data loss."""

    remaining_time_ms: int
    threshold_ms: int
    table_name: str
    function_name: str


@dataclass
class OrphanScanMetric:
    """Metric emitted after orphan scan completion."""

    files_found: int
    files_deleted: int
    total_bytes: int
    scan_duration_ms: int
    table_name: str


@dataclass
class ScanResult:
    """Result of an orphan scan."""

    orphan_files: List[str] = field(default_factory=list)
    files_scanned: int = 0
    total_orphan_bytes: int = 0


@dataclass
class DeleteResult:
    """Result of orphan deletion."""

    deleted: int = 0
    failed: int = 0
