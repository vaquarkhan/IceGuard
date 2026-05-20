"""Hudi adapter tests."""

from unittest.mock import MagicMock

from iceguard.adapters import HudiAdapter, hudi_adapter
from iceguard.enums import TableFormat


def test_hudi_enum_value():
    assert TableFormat.HUDI.value == "hudi"


def test_hudi_adapter_delegates_to_commit_client():
    client = MagicMock()
    a = hudi_adapter(commit_client=client)
    a.abort_transaction("tx")
    client.abort_transaction.assert_called_once_with("tx")
    a.delete_uncommitted_files(["s3://b/f.parquet"])
    client.delete_files.assert_called_once()


def test_hudi_metadata_path():
    assert HudiAdapter().get_table_metadata_path("s3://b/t") == "s3://b/t/.hoodie"
