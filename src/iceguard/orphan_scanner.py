"""Orphan Parquet scanner with batched deletes and metrics."""

from __future__ import annotations

import logging
import time
from typing import Callable, List, Optional, Tuple

from iceguard.adapters import TableFormatAdapter
from iceguard.metrics import MetricsEmitter
from iceguard.models import DeleteResult, ScanResult

logger = logging.getLogger(__name__)

FileEntryMeta = Tuple[str, float, int]  # uri, age_hours, size_bytes


class OrphanScanner:
    """Detect and remove uncommitted Parquet files past retention."""

    def __init__(
        self,
        adapter: TableFormatAdapter,
        retention_hours: int = 72,
        batch_size: int = 1000,
        metrics_emitter: Optional[MetricsEmitter] = None,
        *,
        list_candidates: Optional[Callable[[str], List[FileEntryMeta]]] = None,
        delete_uri: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._adapter = adapter
        self._retention_hours = retention_hours
        self._batch_size = min(batch_size, 1000)
        if self._batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self._metrics = metrics_emitter
        self._list_candidates = list_candidates
        self._delete_uri = delete_uri

    def _default_list(self, table_path: str) -> List[FileEntryMeta]:
        logger.debug("No list_candidates configured; empty scan for %s", table_path)
        return []

    def scan(self, table_path: str) -> ScanResult:
        start = time.perf_counter()
        if self._list_candidates is not None:
            candidates = self._list_candidates(table_path)
        else:
            candidates = self._default_list(table_path)

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

        elapsed_ms = int((time.perf_counter() - start) * 1000)
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
                    if self._delete_uri is None:
                        logger.info("delete_uri not configured; skip %s", uri)
                        continue
                    self._delete_uri(uri)
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
