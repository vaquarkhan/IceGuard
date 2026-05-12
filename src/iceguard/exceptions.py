"""IceGuard exception hierarchy.

All IceGuard-specific exceptions inherit from IceGuardError,
enabling users to catch all library errors with a single except clause.
"""

from typing import Any, Optional


class IceGuardError(Exception):
    """Base exception for all IceGuard errors."""

    pass


class IceGuardInitializationError(IceGuardError):
    """Raised when IceGuard cannot initialize.

    Examples include watchdog thread failing to spawn or
    critical component setup failures.
    """

    pass


class IceGuardContextError(IceGuardError):
    """Raised when Lambda context is missing or invalid.

    The Lambda execution context is required for IceGuard to monitor
    remaining execution time via get_remaining_time_in_millis().
    """

    pass


class IceGuardConfigError(IceGuardError):
    """Raised when configuration validation fails.

    Attributes:
        field: The configuration field that failed validation.
        value: The invalid value that was provided.
        valid_range: The acceptable range or set of values, if applicable.
    """

    def __init__(
        self,
        message: str,
        field: str,
        value: Any,
        valid_range: Optional[Any] = None,
    ) -> None:
        self.field = field
        self.value = value
        self.valid_range = valid_range
        super().__init__(message)


class IceGuardRollbackError(IceGuardError):
    """Raised when a rollback is triggered by the watchdog.

    This indicates that the watchdog detected remaining execution time
    at or below the configured threshold and initiated a format-native
    rollback to prevent silent data loss.

    Attributes:
        remaining_time_ms: Remaining Lambda execution time when rollback triggered.
        threshold_ms: The configured rollback threshold in milliseconds.
    """

    def __init__(self, remaining_time_ms: int, threshold_ms: int) -> None:
        self.remaining_time_ms = remaining_time_ms
        self.threshold_ms = threshold_ms
        super().__init__(
            f"Rollback triggered: {remaining_time_ms}ms remaining "
            f"(threshold: {threshold_ms}ms)"
        )


class CheckpointCorruptionError(IceGuardError):
    """Raised when checkpoint data cannot be deserialized.

    This occurs when the checkpoint store encounters malformed JSON
    or data that does not conform to the expected CheckpointData schema.

    Attributes:
        file_path: The S3 path of the corrupt checkpoint file.
        reason: A description of the parsing or validation failure.
    """

    def __init__(self, file_path: str, reason: str) -> None:
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Corrupt checkpoint at {file_path}: {reason}")


class CoordinatorTimeoutError(IceGuardError):
    """Raised when a participant fails to respond within timeout.

    This triggers a global abort of the coordinated transaction
    to maintain atomicity across all participants.

    Attributes:
        participant_id: The identifier of the non-responsive participant.
        timeout_ms: The timeout duration in milliseconds that was exceeded.
    """

    def __init__(self, participant_id: str, timeout_ms: int) -> None:
        self.participant_id = participant_id
        self.timeout_ms = timeout_ms
        super().__init__(
            f"Participant {participant_id} timed out after {timeout_ms}ms"
        )
