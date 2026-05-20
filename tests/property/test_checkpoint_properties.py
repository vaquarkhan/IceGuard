# Feature: iceguard, Property 2: Checkpoint serialization round-trip
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from iceguard.models import CheckpointData, FileEntry


@st.composite
def checkpoint_data(draw):
    n = draw(st.integers(min_value=0, max_value=5))
    files = [
        FileEntry(
            path=draw(st.text(min_size=1, max_size=8, alphabet=st.characters(blacklist_characters="\x00"))),
            size_bytes=draw(st.integers(min_value=0, max_value=10_000)),
            record_count=draw(st.integers(min_value=0, max_value=1000)),
            checksum=draw(st.text(max_size=12)),
        )
        for _ in range(n)
    ]
    return CheckpointData(
        idempotency_key=draw(st.text(min_size=1, max_size=12)),
        table_path=draw(st.text(min_size=1, max_size=16)),
        table_format=draw(st.sampled_from(["iceberg", "delta", "hudi"])),
        record_offset=draw(st.integers(min_value=0, max_value=1_000_000)),
        partition_info=draw(st.dictionaries(st.text(max_size=4), st.integers(), max_size=3)),
        file_manifest=files,
        created_at="2024-01-01T00:00:00+00:00",
        lambda_function_name="fn",
        lambda_request_id="rid",
    )


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(checkpoint_data())
def test_property_checkpoint_roundtrip(cp: CheckpointData) -> None:
    raw = cp.to_json()
    cp2 = CheckpointData.from_json(raw, file_path="mem")
    assert cp2.record_offset == cp.record_offset
    assert cp2.idempotency_key == cp.idempotency_key
    assert len(cp2.file_manifest) == len(cp.file_manifest)
