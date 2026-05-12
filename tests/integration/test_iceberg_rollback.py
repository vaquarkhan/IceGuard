"""Integration: Iceberg rollback with mocked catalog."""

from unittest.mock import MagicMock

from iceguard.adapters import IcebergAdapter


def test_iceberg_abort_and_delete_with_mock_catalog():
    cat = MagicMock()
    a = IcebergAdapter(catalog=cat)
    a.abort_transaction("tx-1")
    cat.abort_transaction.assert_called_once_with("tx-1")
    a.delete_uncommitted_files(["s3://b/u1"])
    cat.delete_files.assert_called_once_with(["s3://b/u1"])
