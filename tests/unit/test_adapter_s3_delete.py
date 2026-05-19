"""Adapter S3 delete behavior."""

from unittest.mock import MagicMock

from iceguard.adapters import DeltaLakeAdapter, IcebergAdapter


def test_iceberg_deletes_s3_without_catalog():
    s3 = MagicMock()
    a = IcebergAdapter(s3_client=s3)
    a.delete_uncommitted_files(["s3://bucket/p/f.parquet"])
    s3.delete_object.assert_called_once()
    assert "s3://bucket/p/f.parquet" in a.deleted_paths


def test_delta_deletes_s3_without_log():
    s3 = MagicMock()
    a = DeltaLakeAdapter(s3_client=s3)
    a.delete_uncommitted_files(["s3://bucket/p/f.parquet"])
    s3.delete_object.assert_called_once()
