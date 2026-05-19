"""Orphan Parquet scanner with batched deletes and metrics."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, List, Optional, Tuple

from iceguard.adapters import TableFormatAdapter
from iceguard.exceptions import IceGuardConfigError
from iceguard.metrics import MetricsEmitterProtocol, NullMetricsEmitter
from iceguard.models import DeleteResult, ScanResult
from iceguard.s3_ops import S3_DELETE_BATCH_LIMIT, delete_s3_uri, list_parquet_candidates

logger = logging.getLogger(__name__)

FileEntryMeta = Tuple[str, float, int]  # uri, age_hours, size_bytes


class OrphanScanner:
    """Detect and remove uncommitted Parquet files past retention."""

    def __init__(
        self,
        adapter: TableFormatAdapter,
        retention_hours: int = 72,
        batch_size: int = 1000,
        metrics_emitter: Optional[MetricsEmitterProtocol] = None,
        *,
        list_candidates: Optional[Callable[[str], List[FileEntryMeta]]] = None,
        delete_uri: Optional[Callable[[str], None]] = None,
        s3_client: Optional[Any] = None,
    ) -> None:
        self._adapter = adapter
        self._retention_hours = retention_hours
        if batch_size > S3_DELETE_BATCH_LIMIT:
            raise IceGuardConfigError(
                message=(
                    f"batch_size must be at most {S3_DELETE_BATCH_LIMIT} "
                    f"(S3 delete_objects limit), got {batch_size}"
                ),
                field="batch_size",
                value=batch_size,
                valid_range=(1, S3_DELETE_BATCH_LIMIT),
            )
        self._batch_size = batch_size
        if self._batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self._metrics = metrics_emitter or NullMetricsEmitter()
        self._s3_client = s3_client
        self._list_candidates = list_candidates
        self._delete_uri = delete_uri

    def _resolve_list(self, table_path: str) -> List[FileEntryMeta]:
        if self._list_candidates is not None:
            return self._list_candidates(table_path)
        if table_path.startswith("s3://"):
            return list_parquet_candidates(table_path, s3_client=self._s3_client)
        logger.debug("No list_candidates and non-s3 path %s; empty scan", table_path)
        return []

    def _resolve_delete(self, uri: str) -> bool:
        if self._delete_uri is not None:
            self._delete_uri(uri)
            return True
        if uri.startswith("s3://"):
            delete_s3_uri(uri, s3_client=self._s3_client)
            return True
        logger.info("delete_uri not configured and uri is not s3://; skip %s", uri)
        return False

    def scan(self, table_path: str) -> ScanResult:
        start = time.perf_counter()
        candidates = self._resolve_list(table_path)

        committed = self._adapter.list_committed_files(table_path)
        orphan_files: List[str] = []
        total_bytes = 0
        processed = 0
        for batch_start in range(0, len(candidates), self._batch_size):
            batch = candidates[batch_start : batch_start + self._batch_size]
            processed += len(batch)
            for uri, age_h, size_b in batch:
                if uri not in committed and age_h >= self._retention_hours:
                    orphan_files.append(uri)
                    total_bytes += size_b

        if self._metrics is not None:
            self._metrics.emit_orphan_scan(
                found=len(orphan_files), deleted=0, total_bytes=total_bytes
            )
        return ScanResult(
            orphan_files=orphan_files,
            files_scanned=processed,
            total_orphan_bytes=total_bytes,
        )

    def delete_orphans(self, orphan_files: List[str]) -> DeleteResult:
        deleted = 0
        failed = 0
        for batch_start in range(0, len(orphan_files), self._batch_size):
            batch = orphan_files[batch_start : batch_start + self._batch_size]
            for uri in batch:
                try:
                    if self._resolve_delete(uri):
                        deleted += 1
                except PermissionError as e:
                    logger.error("Permission denied deleting orphan %s: %s", uri, e)
                    failed += 1
                except OSError as e:
                    if getattr(e, "errno", None) == 13:
                        logger.error("Permission denied deleting orphan %s: %s", uri, e)
                        failed += 1
                    else:
                        logger.error("Failed deleting orphan %s: %s", uri, e)
                        failed += 1
                except Exception as e:
                    logger.error("Failed deleting orphan %s: %s", uri, e)
                    failed += 1
        return DeleteResult(deleted=deleted, failed=failed)
