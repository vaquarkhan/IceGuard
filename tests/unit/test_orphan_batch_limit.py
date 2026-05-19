"""OrphanScanner batch_size must match config limits."""

import pytest

from iceguard.adapters import IcebergAdapter
from iceguard.exceptions import IceGuardConfigError
from iceguard.orphan_scanner import OrphanScanner


def test_orphan_scanner_rejects_batch_size_over_1000():
    with pytest.raises(IceGuardConfigError) as exc_info:
        OrphanScanner(IcebergAdapter(), batch_size=1001)
    assert exc_info.value.field == "batch_size"
