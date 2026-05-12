# Feature: iceguard, Property 6–8: Orphan scanner
from unittest.mock import MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st

from iceguard.adapters import IcebergAdapter
from iceguard.metrics import MetricsEmitter
from iceguard.orphan_scanner import OrphanScanner


@settings(max_examples=100, deadline=None)
@given(st.integers(min_value=1, max_value=12), st.integers(min_value=0, max_value=5))
def test_property_6_orphans_not_committed(n: int, split: int) -> None:
    paths = [f"s3://b/f{i}" for i in range(n)]
    committed = set(paths[:split])

    def list_candidates(_):
        return [(p, 80.0, 10) for p in paths]

    adapter = IcebergAdapter(committed_files=committed)
    s = OrphanScanner(adapter, retention_hours=72, list_candidates=list_candidates)
    r = s.scan("s3://b")
    for o in r.orphan_files:
        assert o not in committed


@settings(max_examples=80, deadline=None)
@given(st.integers(min_value=1, max_value=500))
def test_property_7_scan_counts_all_files(n: int) -> None:
    rows = [(f"s3://t/f{i}", 99.0, 1) for i in range(n)]
    adapter = IcebergAdapter(committed_files=set())

    def list_candidates(_):
        return rows

    s = OrphanScanner(adapter, batch_size=1000, list_candidates=list_candidates)
    r = s.scan("s3://t")
    assert r.files_scanned == n


@settings(max_examples=40, deadline=None)
@given(st.integers(min_value=0, max_value=8))
def test_property_8_emit_called_with_non_negative_counts(k: int) -> None:
    m = MagicMock(spec=MetricsEmitter)
    rows = [(f"s3://x/f{i}", 80.0, 5) for i in range(k)]
    adapter = IcebergAdapter(committed_files=set())

    def list_candidates(_):
        return rows

    s = OrphanScanner(adapter, metrics_emitter=m, list_candidates=list_candidates)
    s.scan("s3://x")
    m.emit_orphan_scan.assert_called_once()
    kwargs = m.emit_orphan_scan.call_args.kwargs
    assert kwargs["found"] >= 0 and kwargs["deleted"] >= 0 and kwargs["total_bytes"] >= 0
