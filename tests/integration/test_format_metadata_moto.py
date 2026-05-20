"""Integration tests for S3 metadata readers (real boto3 client logic, mocked S3 API)."""

import json
from io import BytesIO
from unittest.mock import MagicMock

from iceguard.format_metadata import delta_committed_paths_s3, hudi_committed_paths_s3


def _mock_s3_client(pages: list, objects: dict[str, bytes]) -> MagicMock:
    client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = pages
    client.get_paginator.return_value = paginator

    def get_object(Bucket, Key):
        return {"Body": BytesIO(objects[Key])}

    client.get_object.side_effect = get_object
    return client


def test_delta_committed_paths_reads_transaction_log():
    log_key = "db/table/_delta_log/00000000000000000001.json"
    lines = [
        json.dumps({"add": {"path": "db/table/part-0001.parquet"}}),
        json.dumps({"add": {"path": "db/table/part-0002.parquet"}}),
        json.dumps({"remove": {"path": "db/table/part-0001.parquet"}}),
    ]
    client = _mock_s3_client(
        pages=[{"Contents": [{"Key": log_key}]}],
        objects={log_key: "\n".join(lines).encode()},
    )
    paths = delta_committed_paths_s3("s3://lake/db/table", s3_client=client)
    assert "s3://lake/db/table/part-0002.parquet" in paths
    assert "s3://lake/db/table/part-0001.parquet" not in paths


def test_hudi_committed_paths_heuristic_scan():
    commit_key = "hudi/orders/.hoodie/metadata/00000000000000000001.commit"
    body = b"s3://lake/hudi/orders/data/file1.parquet padding"
    client = _mock_s3_client(
        pages=[{"Contents": [{"Key": commit_key}]}],
        objects={commit_key: body},
    )
    paths = hudi_committed_paths_s3("s3://lake/hudi/orders", s3_client=client)
    assert "s3://lake/hudi/orders/data/file1.parquet" in paths
