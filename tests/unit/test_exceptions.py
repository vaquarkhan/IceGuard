"""Unit tests for IceGuard exception hierarchy and enums."""

import pytest

from iceguard.exceptions import (
    CheckpointCorruptionError,
    CoordinatorTimeoutError,
    IceGuardConfigError,
    IceGuardContextError,
    IceGuardError,
    IceGuardInitializationError,
    IceGuardRollbackError,
)
from iceguard.enums import TableFormat, TransactionStatus


class TestIceGuardError:
    """Tests for the base IceGuardError exception."""

    def test_is_exception_subclass(self) -> None:
        assert issubclass(IceGuardError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(IceGuardError):
            raise IceGuardError("something went wrong")

    def test_message_preserved(self) -> None:
        err = IceGuardError("test message")
        assert str(err) == "test message"


class TestIceGuardInitializationError:
    """Tests for IceGuardInitializationError."""

    def test_inherits_from_iceguard_error(self) -> None:
        assert issubclass(IceGuardInitializationError, IceGuardError)

    def test_catchable_as_base_error(self) -> None:
        with pytest.raises(IceGuardError):
            raise IceGuardInitializationError("watchdog failed to spawn")


class TestIceGuardContextError:
    """Tests for IceGuardContextError."""

    def test_inherits_from_iceguard_error(self) -> None:
        assert issubclass(IceGuardContextError, IceGuardError)

    def test_catchable_as_base_error(self) -> None:
        with pytest.raises(IceGuardError):
            raise IceGuardContextError("Lambda context is required")


class TestIceGuardConfigError:
    """Tests for IceGuardConfigError."""

    def test_inherits_from_iceguard_error(self) -> None:
        assert issubclass(IceGuardConfigError, IceGuardError)

    def test_stores_field_attribute(self) -> None:
        err = IceGuardConfigError(
            "invalid threshold", field="rollback_threshold_ms", value=100
        )
        assert err.field == "rollback_threshold_ms"

    def test_stores_value_attribute(self) -> None:
        err = IceGuardConfigError(
            "invalid threshold", field="rollback_threshold_ms", value=100
        )
        assert err.value == 100

    def test_stores_valid_range_attribute(self) -> None:
        err = IceGuardConfigError(
            "invalid threshold",
            field="rollback_threshold_ms",
            value=100,
            valid_range=(5000, 300000),
        )
        assert err.valid_range == (5000, 300000)

    def test_valid_range_defaults_to_none(self) -> None:
        err = IceGuardConfigError(
            "unsupported format", field="table_format", value="parquet"
        )
        assert err.valid_range is None

    def test_message_preserved(self) -> None:
        err = IceGuardConfigError(
            "Threshold out of range", field="rollback_threshold_ms", value=100
        )
        assert str(err) == "Threshold out of range"


class TestIceGuardRollbackError:
    """Tests for IceGuardRollbackError."""

    def test_inherits_from_iceguard_error(self) -> None:
        assert issubclass(IceGuardRollbackError, IceGuardError)

    def test_stores_remaining_time_ms(self) -> None:
        err = IceGuardRollbackError(remaining_time_ms=25000, threshold_ms=30000)
        assert err.remaining_time_ms == 25000

    def test_stores_threshold_ms(self) -> None:
        err = IceGuardRollbackError(remaining_time_ms=25000, threshold_ms=30000)
        assert err.threshold_ms == 30000

    def test_message_includes_remaining_time(self) -> None:
        err = IceGuardRollbackError(remaining_time_ms=25000, threshold_ms=30000)
        assert "25000ms remaining" in str(err)

    def test_message_includes_threshold(self) -> None:
        err = IceGuardRollbackError(remaining_time_ms=25000, threshold_ms=30000)
        assert "threshold: 30000ms" in str(err)


class TestCheckpointCorruptionError:
    """Tests for CheckpointCorruptionError."""

    def test_inherits_from_iceguard_error(self) -> None:
        assert issubclass(CheckpointCorruptionError, IceGuardError)

    def test_stores_file_path(self) -> None:
        err = CheckpointCorruptionError(
            file_path="s3://bucket/checkpoints/key.json", reason="invalid JSON"
        )
        assert err.file_path == "s3://bucket/checkpoints/key.json"

    def test_stores_reason(self) -> None:
        err = CheckpointCorruptionError(
            file_path="s3://bucket/key.json", reason="missing required field: offset"
        )
        assert err.reason == "missing required field: offset"

    def test_message_includes_file_path(self) -> None:
        err = CheckpointCorruptionError(
            file_path="s3://bucket/key.json", reason="invalid JSON"
        )
        assert "s3://bucket/key.json" in str(err)

    def test_message_includes_reason(self) -> None:
        err = CheckpointCorruptionError(
            file_path="s3://bucket/key.json", reason="invalid JSON"
        )
        assert "invalid JSON" in str(err)


class TestCoordinatorTimeoutError:
    """Tests for CoordinatorTimeoutError."""

    def test_inherits_from_iceguard_error(self) -> None:
        assert issubclass(CoordinatorTimeoutError, IceGuardError)

    def test_stores_participant_id(self) -> None:
        err = CoordinatorTimeoutError(participant_id="lambda-writer-3", timeout_ms=60000)
        assert err.participant_id == "lambda-writer-3"

    def test_stores_timeout_ms(self) -> None:
        err = CoordinatorTimeoutError(participant_id="lambda-writer-3", timeout_ms=60000)
        assert err.timeout_ms == 60000

    def test_message_includes_participant_id(self) -> None:
        err = CoordinatorTimeoutError(participant_id="lambda-writer-3", timeout_ms=60000)
        assert "lambda-writer-3" in str(err)

    def test_message_includes_timeout(self) -> None:
        err = CoordinatorTimeoutError(participant_id="lambda-writer-3", timeout_ms=60000)
        assert "60000ms" in str(err)


class TestTableFormat:
    """Tests for the TableFormat enum."""

    def test_iceberg_value(self) -> None:
        assert TableFormat.ICEBERG.value == "iceberg"

    def test_delta_value(self) -> None:
        assert TableFormat.DELTA.value == "delta"

    def test_has_exactly_two_members(self) -> None:
        assert len(TableFormat) == 2

    def test_constructable_from_string(self) -> None:
        assert TableFormat("iceberg") == TableFormat.ICEBERG
        assert TableFormat("delta") == TableFormat.DELTA

    def test_invalid_format_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            TableFormat("parquet")


class TestTransactionStatus:
    """Tests for the TransactionStatus enum."""

    def test_all_states_present(self) -> None:
        expected = {
            "INITIATED",
            "PREPARING",
            "PREPARED",
            "COMMITTING",
            "COMMITTED",
            "ABORTING",
            "ABORTED",
        }
        actual = {s.value for s in TransactionStatus}
        assert actual == expected

    def test_has_exactly_seven_members(self) -> None:
        assert len(TransactionStatus) == 7

    def test_constructable_from_string(self) -> None:
        assert TransactionStatus("INITIATED") == TransactionStatus.INITIATED
        assert TransactionStatus("COMMITTED") == TransactionStatus.COMMITTED
        assert TransactionStatus("ABORTED") == TransactionStatus.ABORTED
