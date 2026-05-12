# Feature: iceguard, Property 3: Malformed JSON raises CheckpointCorruptionError
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from iceguard.exceptions import CheckpointCorruptionError
from iceguard.models import CheckpointData


@settings(max_examples=200, deadline=None)
@given(
    st.sampled_from(
        [
            "{",
            "not json",
            "[]",
            '{"idempotency_key": "k"}',
            '{"idempotency_key":"k","table_path":"t"}',
        ]
    )
)
def test_property_malformed_or_incomplete_json_raises(s: str) -> None:
    with pytest.raises(CheckpointCorruptionError):
        CheckpointData.from_json(s, file_path="s3://b/k.json")
