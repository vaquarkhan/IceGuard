"""IceGuard: Reliability library for Spark-on-AWS-Lambda writes."""

from __future__ import annotations

from typing import Any, Optional, Union

from iceguard.adapters import (
    DeltaLakeAdapter,
    HudiAdapter,
    IcebergAdapter,
    TableFormatAdapter,
    delta_adapter,
    hudi_adapter,
    iceberg_adapter,
)
from iceguard.checkpoint_store import CheckpointStore
from iceguard.config import IceGuardConfig
from iceguard.durable import DurableCheckpointBridge
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
from iceguard.models import DeleteResult, ScanResult
from iceguard.orphan_scanner import OrphanScanner
from iceguard.safe_writer import SafeWriter
from iceguard.spark_write import write_dataframe

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("iceguard")
except Exception:
    __version__ = "0.2.0"


def protect(
    lambda_context: Any,
    table_format: Union[str, TableFormat] = "iceberg",
    rollback_threshold_ms: int = 30000,
    checkpoint_interval: int = 5000,
    idempotency_key: Optional[str] = None,
    s3_bucket: Optional[str] = None,
    coordinator_id: Optional[str] = None,
    orphan_retention_hours: int = 72,
    orphan_batch_size: int = 1000,
    enable_cloudwatch_metrics: bool = False,
    enable_opentelemetry_metrics: bool = False,
    *,
    catalog: Any = None,
    delta_log: Any = None,
    hudi_commit_client: Any = None,
    table_identifier: Optional[str] = None,
    adapter: Optional[TableFormatAdapter] = None,
    durable_context: Optional[Any] = None,
) -> SafeWriter:
    """Return a configured :class:`SafeWriter` for chunked writes under Lambda protection.

    Use ``writer.write(...)`` or :func:`write_dataframe` for Spark. A bare
    ``df.write.save()`` inside this context is **not** protected.
    """
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
        orphan_retention_hours=orphan_retention_hours,
        orphan_batch_size=orphan_batch_size,
    )
    store: Optional[CheckpointStore] = None
    if s3_bucket:
        store = CheckpointStore(s3_bucket, config.s3_prefix)

    resolved_key = idempotency_key
    if coordinator_id:
        base = resolved_key or str(getattr(lambda_context, "aws_request_id", "run"))
        resolved_key = f"{coordinator_id}:{base}"

    if adapter is None:
        if tf_enum == TableFormat.DELTA:
            adapter = DeltaLakeAdapter(log=delta_log)
        elif tf_enum == TableFormat.HUDI:
            adapter = HudiAdapter(commit_client=hudi_commit_client)
        else:
            adapter = IcebergAdapter(catalog=catalog, table_identifier=table_identifier)

    bridge = None
    if durable_context is not None and store is not None:
        bridge = DurableCheckpointBridge(store, durable_context)

    return SafeWriter(
        lambda_context,
        config,
        adapter,
        idempotency_key=resolved_key,
        checkpoint_store=store,
        durable_bridge=bridge,
        enable_cloudwatch_metrics=enable_cloudwatch_metrics,
        enable_opentelemetry_metrics=enable_opentelemetry_metrics,
    )


def scan_orphans(
    table_path: str,
    adapter: TableFormatAdapter,
    *,
    retention_hours: int = 72,
    batch_size: int = 1000,
    delete: bool = False,
    metrics_emitter: Optional[Any] = None,
    s3_client: Optional[Any] = None,
) -> Union[ScanResult, tuple[ScanResult, DeleteResult]]:
    """Scan (and optionally delete) orphan Parquet files under ``table_path``."""
    scanner = OrphanScanner(
        adapter,
        retention_hours=retention_hours,
        batch_size=batch_size,
        metrics_emitter=metrics_emitter,
        s3_client=s3_client,
    )
    scan = scanner.scan(table_path)
    if not delete:
        return scan
    dr = scanner.delete_orphans(scan.orphan_files)
    return scan, dr


__all__ = [
    "protect",
    "write_dataframe",
    "scan_orphans",
    "SafeWriter",
    "IceGuardConfig",
    "TableFormat",
    "IcebergAdapter",
    "DeltaLakeAdapter",
    "HudiAdapter",
    "iceberg_adapter",
    "delta_adapter",
    "hudi_adapter",
    "DurableCheckpointBridge",
    "OrphanScanner",
    "ScanResult",
    "DeleteResult",
    "IceGuardError",
    "IceGuardInitializationError",
    "IceGuardContextError",
    "IceGuardConfigError",
    "IceGuardRollbackError",
    "CheckpointCorruptionError",
    "CoordinatorTimeoutError",
    "__version__",
]
