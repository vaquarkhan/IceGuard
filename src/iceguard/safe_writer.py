"""SafeWriter context manager — core write orchestration."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional

from iceguard.adapters import TableFormatAdapter
from iceguard.checkpoint_store import CheckpointStore
from iceguard.config import IceGuardConfig
from iceguard.exceptions import (
    IceGuardContextError,
    IceGuardInitializationError,
    IceGuardRollbackError,
)
from iceguard.metrics import MetricsEmitter
from iceguard.models import CheckpointData, FileEntry
from iceguard.watchdog import WatchdogThread

logger = logging.getLogger(__name__)


class SafeWriter:
    """Context manager that protects Spark/Lambda writes with watchdog + checkpoints."""

    def __init__(
        self,
        lambda_context: Any,
        config: IceGuardConfig,
        adapter: TableFormatAdapter,
        *,
        idempotency_key: Optional[str] = None,
        table_path: str = "",
        checkpoint_store: Optional[CheckpointStore] = None,
        metrics_emitter: Optional[MetricsEmitter] = None,
    ) -> None:
        self._ctx = lambda_context
        self._config = config
        self._adapter = adapter
        self._idempotency_key = idempotency_key
        self._table_path = table_path
        self._store = checkpoint_store
        self._metrics = metrics_emitter or MetricsEmitter()
        self._rollback = threading.Event()
        self._watchdog: Optional[WatchdogThread] = None
        self._resume_offset = 0
        self._checkpoint: Optional[CheckpointData] = None
        self._uncommitted_paths: List[str] = []
        self._function_name = "unknown"

    def _resolve_idempotency_key(self) -> str:
        if self._idempotency_key:
            return self._idempotency_key
        rid = getattr(self._ctx, "aws_request_id", None)
        if rid:
            return str(rid)
        return str(uuid.uuid4())

    def _validate_context(self) -> None:
        if self._ctx is None:
            raise IceGuardContextError("Lambda context is required")
        fn = getattr(self._ctx, "get_remaining_time_in_millis", None)
        if not callable(fn):
            raise IceGuardContextError(
                "Lambda context must expose get_remaining_time_in_millis()"
            )
        try:
            int(fn())
        except Exception as e:
            raise IceGuardContextError(
                "Lambda context get_remaining_time_in_millis() is not usable"
            ) from e

    def __enter__(self) -> "SafeWriter":
        self._validate_context()
        self._function_name = str(
            getattr(self._ctx, "function_name", None) or "unknown"
        )

        key = self._resolve_idempotency_key()
        if self._store is not None:
            loaded = self._store.load(key)
            if loaded is not None:
                self._checkpoint = loaded
                self._resume_offset = loaded.record_offset
                skipped = loaded.record_offset
                self._metrics.emit_checkpoint_resume(skipped)
                logger.info("Resuming from checkpoint offset %s", skipped)

        def on_timeout() -> None:
            self._rollback.set()

        self._watchdog = WatchdogThread(
            self._ctx,
            self._config.rollback_threshold_ms,
            on_timeout,
            poll_interval_ms=self._config.watchdog_poll_interval_ms,
        )
        self._watchdog.start()
        time.sleep(0.02)
        if not self._watchdog.started_ok():
            raise IceGuardInitializationError("Watchdog thread failed to start")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._watchdog is not None:
            self._watchdog.disarm()
        return False

    def _persist_checkpoint(self, offset: int, path: str, manifest: List[FileEntry]) -> None:
        if self._store is None:
            return
        cp = CheckpointData(
            idempotency_key=self._resolve_idempotency_key(),
            table_path=path,
            table_format=self._config.table_format.value,
            record_offset=offset,
            partition_info={},
            file_manifest=manifest,
            created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            lambda_function_name=self._function_name,
            lambda_request_id=str(getattr(self._ctx, "aws_request_id", "")),
        )
        self._store.save(self._resolve_idempotency_key(), cp)
        self._checkpoint = cp

    def _handle_rollback(self, path: str, remaining_ms: int) -> None:
        manifest_paths = [f.path for f in (self._checkpoint.file_manifest if self._checkpoint else [])]
        manifest_paths.extend(self._uncommitted_paths)
        if self._store is not None:
            try:
                final = CheckpointData(
                    idempotency_key=self._resolve_idempotency_key(),
                    table_path=path,
                    table_format=self._config.table_format.value,
                    record_offset=self._resume_offset,
                    partition_info={"rollback": True},
                    file_manifest=self._checkpoint.file_manifest if self._checkpoint else [],
                    created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                    lambda_function_name=self._function_name,
                    lambda_request_id=str(getattr(self._ctx, "aws_request_id", "")),
                )
                self._store.save(self._resolve_idempotency_key(), final)
            except Exception as e:
                logger.warning("Final checkpoint save failed: %s", e)
        try:
            self._adapter.abort_transaction(None)
        except Exception as e:
            logger.warning("abort_transaction failed: %s", e)
        try:
            if manifest_paths:
                self._adapter.delete_uncommitted_files(list(dict.fromkeys(manifest_paths)))
        except Exception as e:
            logger.warning("delete_uncommitted_files failed: %s", e)
        self._metrics.emit_near_miss(
            remaining_ms,
            threshold_ms=self._config.rollback_threshold_ms,
            table_name=path,
            function_name=self._function_name,
        )
        self._metrics.emit_write_outcome(
            path, self._config.table_format.value, "rollback", self._function_name
        )
        raise IceGuardRollbackError(remaining_ms, self._config.rollback_threshold_ms)

    def write(
        self,
        *,
        path: str,
        total_records: int,
        batch_writer: Callable[[int, int], None],
        track_paths: Optional[Callable[[int, int], List[str]]] = None,
    ) -> None:
        """Write records in checkpoint_interval chunks; respect watchdog rollback.

        ``batch_writer(start, end)`` writes records ``[start, end)``.
        ``track_paths`` optionally returns new file paths per batch for rollback deletion.
        """
        self._table_path = path or self._table_path
        offset = self._resume_offset
        manifest: List[FileEntry] = (
            list(self._checkpoint.file_manifest) if self._checkpoint else []
        )

        while offset < total_records:
            if self._rollback.is_set():
                try:
                    remaining = int(self._ctx.get_remaining_time_in_millis())
                except Exception:
                    remaining = 0
                self._handle_rollback(path, remaining)

            end = min(offset + self._config.checkpoint_interval, total_records)
            batch_writer(offset, end)
            if track_paths is not None:
                self._uncommitted_paths.extend(track_paths(offset, end))
            offset = end
            self._persist_checkpoint(offset, path, manifest)

            if self._rollback.is_set():
                try:
                    remaining = int(self._ctx.get_remaining_time_in_millis())
                except Exception:
                    remaining = 0
                self._handle_rollback(path, remaining)

        if self._watchdog is not None:
            self._watchdog.disarm()
        t0 = time.perf_counter()
        while self._watchdog is not None and self._watchdog.is_armed():
            if (time.perf_counter() - t0) > 0.55:
                break
            time.sleep(0.01)

        if self._store is not None:
            self._store.delete(self._resolve_idempotency_key())
        self._metrics.emit_write_outcome(
            path, self._config.table_format.value, "success", self._function_name
        )

    def disarm(self) -> None:
        """Disarm the watchdog explicitly."""
        if self._watchdog is not None:
            self._watchdog.disarm()
