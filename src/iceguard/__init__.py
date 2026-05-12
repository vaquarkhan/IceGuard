"""IceGuard: Reliability library for Spark-on-AWS-Lambda writes."""

from __future__ import annotations

from typing import Any, Optional, Union

from iceguard.adapters import DeltaLakeAdapter, IcebergAdapter
from iceguard.checkpoint_store import CheckpointStore
from iceguard.config import IceGuardConfig
from iceguard.enums import TableFormat
from iceguard.exceptions import (
    CheckpointCorruptionError,
    CoordinatorTimeoutError,
    IceGuardConfigError,
    IceGuardContextError,
    IceGuardError,
    IceGuardInitializationError,
    IceGuardRollbackError,
)
from iceguard.safe_writer import SafeWriter


__version__ = "0.1.0"


def protect(
    lambda_context: Any,
    table_format: Union[str, TableFormat] = "iceberg",
    rollback_threshold_ms: int = 30000,
    checkpoint_interval: int = 5000,
    idempotency_key: Optional[str] = None,
    s3_bucket: Optional[str] = None,
    coordinator_id: Optional[str] = None,
) -> SafeWriter:
    """Return a configured :class:`SafeWriter` for ``with iceguard.protect(ctx):`` usage.

    ``coordinator_id`` is reserved for future coordinated-write wiring.
    """
    del coordinator_id  # reserved for multi-Lambda coordination wiring

    if isinstance(table_format, TableFormat):
        tf_enum = table_format
    else:
        try:
            tf_enum = TableFormat(str(table_format).lower())
        except ValueError as e:
            supported = [f.value for f in TableFormat]
            raise IceGuardConfigError(
                f"table_format must be one of {supported}, got {table_format!r}",
                field="table_format",
                value=table_format,
                valid_range=supported,
            ) from e

    config = IceGuardConfig(
        rollback_threshold_ms=rollback_threshold_ms,
        checkpoint_interval=checkpoint_interval,
        table_format=tf_enum,
        s3_bucket=s3_bucket,
    )
    store: Optional[CheckpointStore] = None
    if s3_bucket:
        store = CheckpointStore(s3_bucket, config.s3_prefix)

    adapter = DeltaLakeAdapter() if tf_enum == TableFormat.DELTA else IcebergAdapter()

    return SafeWriter(
        lambda_context,
        config,
        adapter,
        idempotency_key=idempotency_key,
        checkpoint_store=store,
    )


__all__ = [
    "protect",
    "SafeWriter",
    "IceGuardConfig",
    "TableFormat",
    "IceGuardError",
    "IceGuardInitializationError",
    "IceGuardContextError",
    "IceGuardConfigError",
    "IceGuardRollbackError",
    "CheckpointCorruptionError",
    "CoordinatorTimeoutError",
    "__version__",
]
