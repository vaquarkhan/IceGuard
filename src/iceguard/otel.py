"""OpenTelemetry metrics integration (optional dependency)."""

from __future__ import annotations

import logging
logger = logging.getLogger(__name__)


class OpenTelemetryMetricsEmitter:
    """Emit IceGuard metrics via OpenTelemetry meters (non-blocking counters)."""

    def __init__(self, meter_name: str = "iceguard") -> None:
        try:
            from opentelemetry import metrics
        except ImportError as e:
            raise ImportError(
                'OpenTelemetry is optional. Install with: pip install "iceguard[otel]"'
            ) from e

        meter = metrics.get_meter(meter_name)
        self._write_outcome = meter.create_counter(
            "iceguard.write.outcome",
            description="Write outcomes (success, rollback, failure)",
        )
        self._near_miss = meter.create_counter(
            "iceguard.watchdog.near_miss",
            description="Watchdog near-miss events",
        )
        self._orphan_found = meter.create_counter(
            "iceguard.orphan.found",
            description="Orphan files discovered",
        )
        self._orphan_deleted = meter.create_counter(
            "iceguard.orphan.deleted",
            description="Orphan files deleted",
        )
        self._checkpoint_resume = meter.create_counter(
            "iceguard.checkpoint.resume_records",
            description="Records skipped on resume",
        )
        self._coordination = meter.create_counter(
            "iceguard.coordination.outcome",
            description="Multi-Lambda coordination outcomes",
        )

    def emit_write_outcome(
        self, table_name: str, table_format: str, outcome: str, function_name: str
    ) -> None:
        self._write_outcome.add(
            1,
            {
                "table.name": table_name,
                "table.format": table_format,
                "outcome": outcome,
                "function.name": function_name,
            },
        )

    def emit_near_miss(
        self,
        remaining_time_ms: int,
        *,
        threshold_ms: int = 0,
        table_name: str = "",
        function_name: str = "",
    ) -> None:
        self._near_miss.add(
            1,
            {
                "remaining_time_ms": str(remaining_time_ms),
                "threshold_ms": str(threshold_ms),
                "table.name": table_name,
                "function.name": function_name,
            },
        )

    def emit_orphan_scan(self, found: int, deleted: int, total_bytes: int) -> None:
        self._orphan_found.add(found, {"total_bytes": str(total_bytes)})
        self._orphan_deleted.add(deleted, {})

    def emit_checkpoint_resume(self, records_skipped: int) -> None:
        self._checkpoint_resume.add(records_skipped, {})

    def emit_coordination_outcome(
        self, transaction_id: str, outcome: str, participant_count: int
    ) -> None:
        self._coordination.add(
            1,
            {
                "transaction.id": transaction_id,
                "outcome": outcome,
                "participant.count": str(participant_count),
            },
        )
