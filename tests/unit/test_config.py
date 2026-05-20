"""Unit tests for IceGuardConfig dataclass validation."""

import pytest

from iceguard.config import IceGuardConfig
from iceguard.enums import TableFormat
from iceguard.exceptions import IceGuardConfigError


class TestIceGuardConfigDefaults:
    """Test that default configuration values are correct."""

    def test_default_config_creates_successfully(self):
        config = IceGuardConfig()
        assert config.rollback_threshold_ms == 30000
        assert config.checkpoint_interval == 5000
        assert config.table_format == TableFormat.ICEBERG
        assert config.s3_bucket is None
        assert config.s3_prefix == "iceguard/checkpoints/"
        assert config.orphan_retention_hours == 72
        assert config.orphan_batch_size == 1000
        assert config.coordinator_timeout_ms == 60000
        assert config.watchdog_poll_interval_ms == 500

    def test_config_is_frozen(self):
        config = IceGuardConfig()
        with pytest.raises(AttributeError):
            config.rollback_threshold_ms = 10000  # type: ignore[misc]


class TestRollbackThresholdValidation:
    """Test rollback_threshold_ms validation."""

    def test_minimum_valid_threshold(self):
        config = IceGuardConfig(rollback_threshold_ms=5000)
        assert config.rollback_threshold_ms == 5000

    def test_maximum_valid_threshold(self):
        config = IceGuardConfig(rollback_threshold_ms=300000)
        assert config.rollback_threshold_ms == 300000

    def test_threshold_below_minimum_raises_error(self):
        with pytest.raises(IceGuardConfigError) as exc_info:
            IceGuardConfig(rollback_threshold_ms=4999)
        assert exc_info.value.field == "rollback_threshold_ms"
        assert exc_info.value.value == 4999
        assert exc_info.value.valid_range == (5000, 300000)

    def test_threshold_above_maximum_raises_error(self):
        with pytest.raises(IceGuardConfigError) as exc_info:
            IceGuardConfig(rollback_threshold_ms=300001)
        assert exc_info.value.field == "rollback_threshold_ms"
        assert exc_info.value.value == 300001
        assert exc_info.value.valid_range == (5000, 300000)

    def test_threshold_zero_raises_error(self):
        with pytest.raises(IceGuardConfigError):
            IceGuardConfig(rollback_threshold_ms=0)

    def test_threshold_negative_raises_error(self):
        with pytest.raises(IceGuardConfigError):
            IceGuardConfig(rollback_threshold_ms=-1000)


class TestTableFormatValidation:
    """Test table_format validation."""

    def test_iceberg_format_accepted(self):
        config = IceGuardConfig(table_format=TableFormat.ICEBERG)
        assert config.table_format == TableFormat.ICEBERG

    def test_delta_format_accepted(self):
        config = IceGuardConfig(table_format=TableFormat.DELTA)
        assert config.table_format == TableFormat.DELTA

    def test_string_table_format_coerced_like_protect(self):
        config = IceGuardConfig(table_format="iceberg")
        assert config.table_format == TableFormat.ICEBERG
        config2 = IceGuardConfig(table_format="delta")
        assert config2.table_format == TableFormat.DELTA

    def test_invalid_string_raises_error(self):
        with pytest.raises(IceGuardConfigError) as exc_info:
            IceGuardConfig(table_format="parquet")  # type: ignore[arg-type]
        assert exc_info.value.field == "table_format"
        assert exc_info.value.value == "parquet"
        assert "iceberg" in exc_info.value.valid_range
        assert "delta" in exc_info.value.valid_range

    def test_none_table_format_raises_error(self):
        with pytest.raises(IceGuardConfigError) as exc_info:
            IceGuardConfig(table_format=None)  # type: ignore[arg-type]
        assert exc_info.value.field == "table_format"


class TestCheckpointIntervalValidation:
    """Test checkpoint_interval validation."""

    def test_valid_interval(self):
        config = IceGuardConfig(checkpoint_interval=1000)
        assert config.checkpoint_interval == 1000

    def test_zero_interval_raises_error(self):
        with pytest.raises(IceGuardConfigError) as exc_info:
            IceGuardConfig(checkpoint_interval=0)
        assert exc_info.value.field == "checkpoint_interval"

    def test_negative_interval_raises_error(self):
        with pytest.raises(IceGuardConfigError) as exc_info:
            IceGuardConfig(checkpoint_interval=-100)
        assert exc_info.value.field == "checkpoint_interval"


class TestWatchdogPollIntervalValidation:
    """Test watchdog_poll_interval_ms validation."""

    def test_minimum_valid_poll_interval(self):
        config = IceGuardConfig(watchdog_poll_interval_ms=100)
        assert config.watchdog_poll_interval_ms == 100

    def test_maximum_valid_poll_interval(self):
        config = IceGuardConfig(watchdog_poll_interval_ms=1000)
        assert config.watchdog_poll_interval_ms == 1000

    def test_poll_interval_below_minimum_raises_error(self):
        with pytest.raises(IceGuardConfigError) as exc_info:
            IceGuardConfig(watchdog_poll_interval_ms=99)
        assert exc_info.value.field == "watchdog_poll_interval_ms"
        assert exc_info.value.valid_range == (100, 1000)

    def test_poll_interval_above_maximum_raises_error(self):
        with pytest.raises(IceGuardConfigError) as exc_info:
            IceGuardConfig(watchdog_poll_interval_ms=1001)
        assert exc_info.value.field == "watchdog_poll_interval_ms"
        assert exc_info.value.valid_range == (100, 1000)


class TestCustomConfiguration:
    """Test creating config with custom valid values."""

    def test_all_custom_values(self):
        config = IceGuardConfig(
            rollback_threshold_ms=10000,
            checkpoint_interval=2000,
            table_format=TableFormat.DELTA,
            s3_bucket="my-bucket",
            s3_prefix="custom/prefix/",
            orphan_retention_hours=24,
            orphan_batch_size=500,
            coordinator_timeout_ms=30000,
            watchdog_poll_interval_ms=250,
        )
        assert config.rollback_threshold_ms == 10000
        assert config.checkpoint_interval == 2000
        assert config.table_format == TableFormat.DELTA
        assert config.s3_bucket == "my-bucket"
        assert config.s3_prefix == "custom/prefix/"
        assert config.orphan_retention_hours == 24
        assert config.orphan_batch_size == 500
        assert config.coordinator_timeout_ms == 30000
        assert config.watchdog_poll_interval_ms == 250


class TestErrorMessages:
    """Test that error messages are descriptive."""

    def test_threshold_error_message_contains_value_and_range(self):
        with pytest.raises(IceGuardConfigError) as exc_info:
            IceGuardConfig(rollback_threshold_ms=1000)
        msg = str(exc_info.value)
        assert "5000" in msg
        assert "300000" in msg
        assert "1000" in msg

    def test_table_format_error_message_lists_supported(self):
        with pytest.raises(IceGuardConfigError) as exc_info:
            IceGuardConfig(table_format="parquet")  # type: ignore[arg-type]
        msg = str(exc_info.value)
        assert "iceberg" in msg
        assert "delta" in msg
        assert "iceberg" in msg
        assert "delta" in msg
        assert "hudi" in msg

    def test_orphan_batch_size_cannot_exceed_1000(self):
        with pytest.raises(IceGuardConfigError) as exc_info:
            IceGuardConfig(orphan_batch_size=1001)
        assert exc_info.value.field == "orphan_batch_size"
