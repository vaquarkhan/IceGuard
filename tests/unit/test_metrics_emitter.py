"""Unit tests for MetricsEmitter."""

from unittest.mock import MagicMock

from iceguard.metrics import MetricsEmitter


def test_publish_failure_swallowed():
    cw = MagicMock()
    cw.put_metric_data.side_effect = RuntimeError("cw down")
    m = MetricsEmitter(cloudwatch_client=cw)
    m.emit_write_outcome("t", "iceberg", "success", "fn")
    m.emit_near_miss(100, threshold_ms=30, table_name="t", function_name="fn")
    m.emit_checkpoint_resume(42)
    m.emit_orphan_scan(1, 2, 3)
    m.emit_coordination_outcome("tx", "committed", 2)


def test_write_outcome_dimensions():
    cw = MagicMock()
    m = MetricsEmitter(cloudwatch_client=cw)
    m.emit_write_outcome("mytable", "delta", "rollback", "myfn")
    call = cw.put_metric_data.call_args
    dims = call[1]["MetricData"][0]["Dimensions"]
    names = {d["Name"]: d["Value"] for d in dims}
    assert names["TableName"] == "mytable"
    assert names["TableFormat"] == "delta"
    assert names["Outcome"] == "rollback"
    assert names["FunctionName"] == "myfn"
