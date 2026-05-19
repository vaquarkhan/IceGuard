"""Unit tests for S3 orphan helpers."""

from iceguard.s3_ops import parse_s3_uri


def test_parse_s3_directory_prefix():
    bucket, prefix = parse_s3_uri("s3://my-bucket/db/table", directory_prefix=True)
    assert bucket == "my-bucket"
    assert prefix == "db/table/"


def test_parse_s3_object_key():
    bucket, key = parse_s3_uri("s3://my-bucket/db/table/part-0001.parquet")
    assert bucket == "my-bucket"
    assert key == "db/table/part-0001.parquet"
