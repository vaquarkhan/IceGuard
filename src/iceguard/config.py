"""IceGuard configuration with validation.

Provides a frozen dataclass that validates all configuration values
at construction time, raising IceGuardConfigError for invalid inputs.
"""

from dataclasses import dataclass
from typing import Optional, Union

from iceguard.enums import TableFormat
from iceguard.exceptions import IceGuardConfigError

TableFormatInput = Union[TableFormat, str]


@dataclass(frozen=True)
class IceGuardConfig:
    """Validated configuration for IceGuard.

    All fields are validated in __post_init__. Invalid values raise
    IceGuardConfigError with the field name, provided value, and
    valid range or set.

    Attributes:
        rollback_threshold_ms: Time buffer before Lambda timeout at which
            rollback is triggered. Must be in [5000, 300000].
        checkpoint_interval: Number of records between checkpoint persists.
        table_format: The open table format to use (Iceberg or Delta).
        s3_bucket: S3 bucket for checkpoint storage.
        s3_prefix: Key prefix for checkpoint objects.
        orphan_retention_hours: Hours before an uncommitted file is
            considered an orphan.
        orphan_batch_size: Maximum files per orphan scan API call.
        coordinator_timeout_ms: Timeout for participant responses in
            coordinated writes.
        watchdog_poll_interval_ms: Interval at which the watchdog polls
            remaining execution time.
    """

    rollback_threshold_ms: int = 30000
    checkpoint_interval: int = 5000
    table_format: TableFormatInput = TableFormat.ICEBERG
    s3_bucket: Optional[str] = None
    s3_prefix: str = "iceguard/checkpoints/"
    orphan_retention_hours: int = 72
    orphan_batch_size: int = 1000
    coordinator_timeout_ms: int = 60000
    watchdog_poll_interval_ms: int = 500

    def __post_init__(self) -> None:
        """Validate all configuration values at construction time."""
        self._coerce_table_format()
        self._validate_rollback_threshold()
        self._validate_table_format()
        self._validate_checkpoint_interval()
        self._validate_orphan_retention_hours()
        self._validate_orphan_batch_size()
        self._validate_coordinator_timeout_ms()
        self._validate_watchdog_poll_interval_ms()

    def _coerce_table_format(self) -> None:
        """Accept TableFormat enum or string values like protect() does."""
        if isinstance(self.table_format, TableFormat):
            return
        if isinstance(self.table_format, str):
            try:
                coerced = TableFormat(self.table_format.lower())
            except ValueError as e:
                supported = [fmt.value for fmt in TableFormat]
                raise IceGuardConfigError(
                    message=(
                        f"table_format must be one of {supported}, "
                        f"got {self.table_format!r}"
                    ),
                    field="table_format",
                    value=self.table_format,
                    valid_range=supported,
                ) from e
            object.__setattr__(self, "table_format", coerced)
            return
        supported = [fmt.value for fmt in TableFormat]
        raise IceGuardConfigError(
            message=(
                f"table_format must be a TableFormat enum value or string, "
                f"got {self.table_format!r}. Supported formats: {supported}"
            ),
            field="table_format",
            value=self.table_format,
            valid_range=supported,
        )

    def _validate_rollback_threshold(self) -> None:
        """Validate rollback_threshold_ms is in [5000, 300000]."""
        min_val = 5000
        max_val = 300000
        if not isinstance(self.rollback_threshold_ms, int):
            raise IceGuardConfigError(
                message=(
                    f"rollback_threshold_ms must be an integer, "
                    f"got {type(self.rollback_threshold_ms).__name__}"
                ),
                field="rollback_threshold_ms",
                value=self.rollback_threshold_ms,
                valid_range=(min_val, max_val),
            )
        if self.rollback_threshold_ms < min_val or self.rollback_threshold_ms > max_val:
            raise IceGuardConfigError(
                message=(
                    f"rollback_threshold_ms must be between {min_val} and "
                    f"{max_val} (inclusive), got {self.rollback_threshold_ms}"
                ),
                field="rollback_threshold_ms",
                value=self.rollback_threshold_ms,
                valid_range=(min_val, max_val),
            )

    def _validate_table_format(self) -> None:
        """Validate table_format is a supported TableFormat enum value."""
        if not isinstance(self.table_format, TableFormat):
            supported = [fmt.value for fmt in TableFormat]
            raise IceGuardConfigError(
                message=(
                    f"table_format must be a TableFormat enum value, "
                    f"got {self.table_format!r}. "
                    f"Supported formats: {supported}"
                ),
                field="table_format",
                value=self.table_format,
                valid_range=supported,
            )

    def _validate_checkpoint_interval(self) -> None:
        """Validate checkpoint_interval is a positive integer."""
        if not isinstance(self.checkpoint_interval, int) or self.checkpoint_interval <= 0:
            raise IceGuardConfigError(
                message=(
                    f"checkpoint_interval must be a positive integer, "
                    f"got {self.checkpoint_interval}"
                ),
                field="checkpoint_interval",
                value=self.checkpoint_interval,
            )

    def _validate_orphan_retention_hours(self) -> None:
        """Validate orphan_retention_hours is a positive integer."""
        if (
            not isinstance(self.orphan_retention_hours, int)
            or self.orphan_retention_hours <= 0
        ):
            raise IceGuardConfigError(
                message=(
                    f"orphan_retention_hours must be a positive integer, "
                    f"got {self.orphan_retention_hours}"
                ),
                field="orphan_retention_hours",
                value=self.orphan_retention_hours,
            )

    def _validate_orphan_batch_size(self) -> None:
        """Validate orphan_batch_size is a positive integer (max 1000 for S3 API)."""
        max_batch = 1000
        if not isinstance(self.orphan_batch_size, int) or self.orphan_batch_size <= 0:
            raise IceGuardConfigError(
                message=(
                    f"orphan_batch_size must be a positive integer, "
                    f"got {self.orphan_batch_size}"
                ),
                field="orphan_batch_size",
                value=self.orphan_batch_size,
            )
        if self.orphan_batch_size > max_batch:
            raise IceGuardConfigError(
                message=(
                    f"orphan_batch_size must be at most {max_batch} (S3 delete_objects limit), "
                    f"got {self.orphan_batch_size}"
                ),
                field="orphan_batch_size",
                value=self.orphan_batch_size,
                valid_range=(1, max_batch),
            )

    def _validate_coordinator_timeout_ms(self) -> None:
        """Validate coordinator_timeout_ms is a positive integer."""
        if (
            not isinstance(self.coordinator_timeout_ms, int)
            or self.coordinator_timeout_ms <= 0
        ):
            raise IceGuardConfigError(
                message=(
                    f"coordinator_timeout_ms must be a positive integer, "
                    f"got {self.coordinator_timeout_ms}"
                ),
                field="coordinator_timeout_ms",
                value=self.coordinator_timeout_ms,
            )

    def _validate_watchdog_poll_interval_ms(self) -> None:
        """Validate watchdog_poll_interval_ms is in [100, 1000]."""
        min_val = 100
        max_val = 1000
        if not isinstance(self.watchdog_poll_interval_ms, int):
            raise IceGuardConfigError(
                message=(
                    f"watchdog_poll_interval_ms must be an integer, "
                    f"got {type(self.watchdog_poll_interval_ms).__name__}"
                ),
                field="watchdog_poll_interval_ms",
                value=self.watchdog_poll_interval_ms,
                valid_range=(min_val, max_val),
            )
        if (
            self.watchdog_poll_interval_ms < min_val
            or self.watchdog_poll_interval_ms > max_val
        ):
            raise IceGuardConfigError(
                message=(
                    f"watchdog_poll_interval_ms must be between {min_val} and "
                    f"{max_val} (inclusive), got {self.watchdog_poll_interval_ms}"
                ),
                field="watchdog_poll_interval_ms",
                value=self.watchdog_poll_interval_ms,
                valid_range=(min_val, max_val),
            )
