"""Integration: Delta rollback with mocked log."""

from unittest.mock import MagicMock

from iceguard.adapters import DeltaLakeAdapter


def test_delta_abort_and_delete_with_mock_log():
    log = MagicMock()
    a = DeltaLakeAdapter(log=log)
    a.abort_transaction("tx-2")
    log.abort_transaction.assert_called_once_with("tx-2")
    a.delete_uncommitted_files(["s3://l/p1"])
    log.delete_files.assert_called_once_with(["s3://l/p1"])
