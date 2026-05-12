# Feature: iceguard, Property 1: Watchdog rollback trigger
from unittest.mock import MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st

from iceguard.watchdog import WatchdogThread


@settings(max_examples=40, deadline=None)
@given(
    st.integers(min_value=0, max_value=50_000),
    st.integers(min_value=0, max_value=50_000),
)
def test_property_watchdog_triggers_iff_remaining_lte_threshold(
    remaining_ms: int, threshold_ms: int
) -> None:
    ctx = MagicMock()
    ctx.get_remaining_time_in_millis.return_value = remaining_ms
    fired = []

    def cb():
        fired.append(1)

    w = WatchdogThread(ctx, threshold_ms, cb, poll_interval_ms=100)
    w.start()
    import time

    time.sleep(0.28)
    w.disarm()
    should = remaining_ms <= threshold_ms
    assert (len(fired) >= 1) == should
