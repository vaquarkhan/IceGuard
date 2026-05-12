# Feature: iceguard, Property 13: Configuration validation — threshold range
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from iceguard.config import IceGuardConfig
from iceguard.exceptions import IceGuardConfigError


@settings(max_examples=100, deadline=None)
@given(st.integers())
def test_property_rollback_threshold_accepted_iff_in_range(v: int) -> None:
    if 5000 <= v <= 300000:
        c = IceGuardConfig(rollback_threshold_ms=v)
        assert c.rollback_threshold_ms == v
    else:
        with pytest.raises(IceGuardConfigError) as ei:
            IceGuardConfig(rollback_threshold_ms=v)
        assert ei.value.field == "rollback_threshold_ms"


# Feature: iceguard, Property 14: Configuration validation — table format
@settings(max_examples=100, deadline=None)
@given(st.text())
def test_property_14_non_enum_table_format_raises(s: str) -> None:
    with pytest.raises(IceGuardConfigError):
        IceGuardConfig(table_format=s)  # type: ignore[arg-type]
