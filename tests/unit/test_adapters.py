"""Unit tests for table format adapters."""

from iceguard.adapters import DeltaLakeAdapter, IcebergAdapter


def test_iceberg_list_and_delete():
    a = IcebergAdapter(committed_files={"s3://x/a"})
    assert a.get_table_metadata_path("s3://x") == "s3://x/metadata"
    assert "s3://x/a" in a.list_committed_files("s3://x")
    a.delete_uncommitted_files(["s3://x/u1"])
    assert "s3://x/u1" in a.deleted_paths
    a.abort_transaction("tx")


def test_delta_list_and_delete():
    a = DeltaLakeAdapter(committed_files={"s3://l/f"})
    assert a.get_table_metadata_path("s3://l").endswith("_delta_log")
    assert "s3://l/f" in a.list_committed_files("s3://l")
    a.delete_uncommitted_files(["s3://l/z"])
    assert "s3://l/z" in a.deleted_paths
