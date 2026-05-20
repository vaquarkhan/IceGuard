"""Unit tests for Delta adapter S3 metadata integration."""

import json
from io import BytesIO
from unittest.mock import MagicMock

from iceguard.adapters import DeltaLakeAdapter


def test_delta_adapter_lists_committed_from_s3_log():
    log_key = "db/t/_delta_log/00000000000000000001.json"
    client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = [{"Contents": [{"Key": log_key}]}]
    client.get_paginator.return_value = paginator
    client.get_object.return_value = {
        "Body": BytesIO(
            json.dumps({"add": {"path": "db/t/part.parquet"}}).encode()
        )
    }
    adapter = DeltaLakeAdapter(s3_client=client)
    paths = adapter.list_committed_files("s3://lake/db/t")
    assert "s3://lake/db/t/part.parquet" in paths
