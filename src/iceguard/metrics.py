"""CloudWatch metrics emitter, background wrapper, and no-op implementation."""

from __future__ import annotations

import logging
import queue
import threading
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

DEFAULT_NAMESPACE = "iceguard"


@runtime_checkable
class MetricsEmitterProtocol(Protocol):
    """Metrics surface used by SafeWriter, OrphanScanner, and Coordinator."""

    def emit_write_outcome(
        self, table_name: str, table_format: str, outcome: str, function_name: str
    ) -> None: ...

    def emit_near_miss(
        self,
        remaining_time_ms: int,
        *,
        threshold_ms: int = 0,
        table_name: str = "",
        function_name: str = "",
    ) -> None: ...

    def emit_orphan_scan(self, found: int, deleted: int, total_bytes: int) -> None: ...

    def emit_checkpoint_resume(self, records_skipped: int) -> None: ...

    def emit_coordination_outcome(
        self, transaction_id: str, outcome: str, participant_count: int
    ) -> None: ...


class NullMetricsEmitter:
    """No-op metrics (default for SafeWriter to avoid accidental AWS calls)."""

    def emit_write_outcome(
        self, table_name: str, table_format: str, outcome: str, function_name: str
    ) -> None:
        pass

    def emit_near_miss(
        self,
        remaining_time_ms: int,
        *,
        threshold_ms: int = 0,
        table_name: str = "",
        function_name: str = "",
    ) -> None:
        pass

    def emit_orphan_scan(self, found: int, deleted: int, total_bytes: int) -> None:
        pass

    def emit_checkpoint_resume(self, records_skipped: int) -> None:
        pass

    def emit_coordination_outcome(
        self, transaction_id: str, outcome: str, participant_count: int
    ) -> None:
        pass


class MetricsEmitter:
    """Publish structured metrics to CloudWatch (synchronous boto3 calls).

    :class:`SafeWriter` wraps this in :class:`BackgroundMetricsEmitter` when
    ``enable_cloudwatch_metrics=True`` so the write loop is not blocked.
    """

    def __init__(
        self,
        namespace: str = DEFAULT_NAMESPACE,
        *,
        cloudwatch_client: Optional[Any] = None,
    ) -> None:
        self._namespace = namespace
        if cloudwatch_client is not None:
            self._cw = cloudwatch_client
        else:
            import boto3

            self._cw = boto3.client("cloudwatch")

    def _put(self, metric_name: str, value: float, dimensions: List[Dict[str, str]]) -> None:
        try:
            self._cw.put_metric_data(
                Namespace=self._namespace,
                MetricData=[
                    {
                        "MetricName": metric_name,
                        "Timestamp": datetime.now(timezone.utc),
                        "Value": value,
                        "Unit": "Count",
                        "Dimensions": [
                            {"Name": name, "Value": val}
                            for name, val in self._flatten_dims(dimensions)
                        ],
                    }
                ],
            )
        except Exception as e:
            logger.error("CloudWatch publish failed for %s: %s", metric_name, e)

    @staticmethod
    def _flatten_dims(dims: List[Dict[str, str]]) -> List[tuple]:
        out: List[tuple] = []
        for d in dims:
            for k, v in d.items():
                out.append((k, str(v)))
        return out

    def emit_write_outcome(
        self,
        table_name: str,
        table_format: str,
        outcome: str,
        function_name: str,
    ) -> None:
        self._put(
            "WriteOutcome",
            1.0,
            [
                {"TableName": table_name},
                {"TableFormat": table_format},
                {"Outcome": outcome},
                {"FunctionName": function_name},
            ],
        )

    def emit_near_miss(
        self,
        remaining_time_ms: int,
        *,
        threshold_ms: int = 0,
        table_name: str = "",
        function_name: str = "",
    ) -> None:
        dims: List[Dict[str, str]] = [
            {"RemainingTimeMs": str(remaining_time_ms)},
            {"ThresholdMs": str(threshold_ms)},
        ]
        if table_name:
            dims.append({"TableName": table_name})
        if function_name:
            dims.append({"FunctionName": function_name})
        self._put("NearMiss", float(remaining_time_ms), dims)

    def emit_orphan_scan(
        self, found: int, deleted: int, total_bytes: int
    ) -> None:
        self._put("OrphanScanFound", float(found), [{"FilesFound": str(found)}])
        self._put("OrphanScanDeleted", float(deleted), [{"FilesDeleted": str(deleted)}])
        self._put("OrphanScanBytes", float(total_bytes), [{"TotalBytes": str(total_bytes)}])

    def emit_checkpoint_resume(self, records_skipped: int) -> None:
        self._put(
            "CheckpointResume",
            float(records_skipped),
            [{"RecordsSkipped": str(records_skipped)}],
        )

    def emit_coordination_outcome(
        self, transaction_id: str, outcome: str, participant_count: int
    ) -> None:
        self._put(
            "CoordinationOutcome",
            1.0,
            [
                {"TransactionId": transaction_id},
                {"Outcome": outcome},
                {"ParticipantCount": str(participant_count)},
            ],
        )


class BackgroundMetricsEmitter:
    """Enqueue metric publishes on a daemon thread so the write path is not blocked."""

    def __init__(self, delegate: MetricsEmitterProtocol) -> None:
        self._delegate = delegate
        self._queue: queue.SimpleQueue = queue.SimpleQueue()
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._worker, name="iceguard-metrics", daemon=True
        )
        self._thread.start()

    def _enqueue(self, fn: Callable[..., None], *args: Any, **kwargs: Any) -> None:
        self._queue.put((fn, args, kwargs))

    def _worker(self) -> None:
        while not self._stop.is_set():
            try:
                item = self._queue.get(timeout=0.25)
            except queue.Empty:
                continue
            if item is None:
                break
            fn, args, kwargs = item
            try:
                fn(*args, **kwargs)
            except Exception as e:
                logger.error("Background metric publish failed: %s", e)

    def close(self, timeout_s: float = 2.0) -> None:
        """Drain queued metrics then stop the worker."""
        self._stop.set()
        self._queue.put(None)
        if self._thread.is_alive():
            self._thread.join(timeout=timeout_s)

    def emit_write_outcome(
        self, table_name: str, table_format: str, outcome: str, function_name: str
    ) -> None:
        self._enqueue(
            self._delegate.emit_write_outcome,
            table_name,
            table_format,
            outcome,
            function_name,
        )

    def emit_near_miss(
        self,
        remaining_time_ms: int,
        *,
        threshold_ms: int = 0,
        table_name: str = "",
        function_name: str = "",
    ) -> None:
        self._enqueue(
            self._delegate.emit_near_miss,
            remaining_time_ms,
            threshold_ms=threshold_ms,
            table_name=table_name,
            function_name=function_name,
        )

    def emit_orphan_scan(self, found: int, deleted: int, total_bytes: int) -> None:
        self._enqueue(self._delegate.emit_orphan_scan, found, deleted, total_bytes)

    def emit_checkpoint_resume(self, records_skipped: int) -> None:
        self._enqueue(self._delegate.emit_checkpoint_resume, records_skipped)

    def emit_coordination_outcome(
        self, transaction_id: str, outcome: str, participant_count: int
    ) -> None:
        self._enqueue(
            self._delegate.emit_coordination_outcome,
            transaction_id,
            outcome,
            participant_count,
        )
