# Feature: iceguard, Property 15–17: Metrics emitter
from unittest.mock import MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st

from iceguard.metrics import MetricsEmitter


@settings(max_examples=120, deadline=None)
@given(st.text(min_size=1, max_size=8), st.sampled_from(["iceberg", "delta"]), st.sampled_from(["success", "rollback"]))
def test_property_15_write_metric_dimensions(tname: str, fmt: str, outcome: str) -> None:
    cw = MagicMock()
    m = MetricsEmitter(cloudwatch_client=cw)
    m.emit_write_outcome(tname, fmt, outcome, "fn")
    dims = {d["Name"]: d["Value"] for d in cw.put_metric_data.call_args[1]["MetricData"][0]["Dimensions"]}
    assert dims["TableName"] == tname
    assert dims["TableFormat"] == fmt
    assert dims["Outcome"] == outcome
    assert dims["FunctionName"] == "fn"


@settings(max_examples=120, deadline=None)
@given(st.integers(min_value=0, max_value=900_000))
def test_property_16_near_miss_value_matches_remaining(rem: int) -> None:
    cw = MagicMock()
    m = MetricsEmitter(cloudwatch_client=cw)
    m.emit_near_miss(rem, threshold_ms=30, table_name="t", function_name="f")
    val = cw.put_metric_data.call_args[1]["MetricData"][0]["Value"]
    assert val == float(rem)


@settings(max_examples=120, deadline=None)
@given(st.integers(min_value=0, max_value=5_000_000))
def test_property_17_resume_skip_count(skipped: int) -> None:
    cw = MagicMock()
    m = MetricsEmitter(cloudwatch_client=cw)
    m.emit_checkpoint_resume(skipped)
    val = cw.put_metric_data.call_args[1]["MetricData"][0]["Value"]
    assert val == float(skipped)
