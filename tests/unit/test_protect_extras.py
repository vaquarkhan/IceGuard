"""protect() coordinator prefix and scan_orphans API."""

from unittest.mock import MagicMock

import iceguard
from iceguard.adapters import IcebergAdapter


def test_protect_prefixes_idempotency_with_coordinator_id():
    ctx = MagicMock()
    ctx.get_remaining_time_in_millis.return_value = 600_000
    ctx.aws_request_id = "req-1"
    ctx.function_name = "fn"
    sw = iceguard.protect(ctx, coordinator_id="coord-9")
    assert sw._resolve_idempotency_key().startswith("coord-9:")


def test_scan_orphans_returns_scan_result_without_s3():
    adapter = IcebergAdapter(committed_files=set())
    result = iceguard.scan_orphans(
        "file:///tmp/table",
        adapter,
        retention_hours=0,
        batch_size=100,
    )
    assert result.files_scanned == 0
