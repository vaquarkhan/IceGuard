"""Unit tests for OrphanScanner."""

from unittest.mock import MagicMock

from iceguard.adapters import IcebergAdapter
from iceguard.metrics import MetricsEmitter
from iceguard.orphan_scanner import OrphanScanner


def test_scan_classifies_orphans():
    adapter = IcebergAdapter(committed_files={"s3://t/c"})
    files = [
        ("s3://t/c", 100.0, 10),
        ("s3://t/o1", 80.0, 5),
        ("s3://t/o2", 10.0, 3),
    ]

    def list_candidates(_path):
        return files

    m = MagicMock(spec=MetricsEmitter)
    s = OrphanScanner(adapter, retention_hours=72, metrics_emitter=m, list_candidates=list_candidates)
    r = s.scan("s3://t")
    assert "s3://t/o1" in r.orphan_files
    assert "s3://t/c" not in r.orphan_files
    assert "s3://t/o2" not in r.orphan_files
    m.emit_orphan_scan.assert_called()


def test_delete_permission_denied_logged():
    adapter = IcebergAdapter()

    def deleter(uri):
        raise PermissionError("no")

    s = OrphanScanner(adapter, delete_uri=deleter, list_candidates=lambda _: [])
    r = s.delete_orphans(["s3://a/x"])
    assert r.failed >= 1


def test_batches_over_1000():
    adapter = IcebergAdapter(committed_files=set())
    n = 2500
    files = [(f"s3://b/f{i}", 80.0, 1) for i in range(n)]

    s = OrphanScanner(adapter, batch_size=1000, list_candidates=lambda _: files)
    r = s.scan("s3://b")
    assert r.files_scanned == n
