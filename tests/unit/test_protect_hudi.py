"""protect() with Hudi table format."""

from unittest.mock import MagicMock

import iceguard
from iceguard.adapters import HudiAdapter
from iceguard.enums import TableFormat


def test_protect_hudi_uses_hudi_adapter():
    ctx = MagicMock()
    ctx.get_remaining_time_in_millis.return_value = 600_000
    ctx.aws_request_id = "r"
    sw = iceguard.protect(ctx, table_format="hudi")
    assert isinstance(sw._adapter, HudiAdapter)
    assert sw._config.table_format == TableFormat.HUDI
