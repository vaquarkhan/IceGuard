"""Integration: CloudWatch metrics wiring (mocked client)."""

from unittest.mock import MagicMock

from iceguard.metrics import MetricsEmitter


def test_cloudwatch_put_metric_data_called():
    cw = MagicMock()
    m = MetricsEmitter(cloudwatch_client=cw)
    m.emit_write_outcome("tbl", "iceberg", "success", "fn")
    cw.put_metric_data.assert_called_once()
    assert cw.put_metric_data.call_args[1]["Namespace"] == "iceguard"
