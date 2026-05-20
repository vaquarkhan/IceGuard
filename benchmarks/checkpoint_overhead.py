#!/usr/bin/env python3
"""Measure checkpoint save/load overhead (local, no AWS required)."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

from iceguard.checkpoint_store import CheckpointStore
from iceguard.models import CheckpointData


def _sample_checkpoint() -> CheckpointData:
    return CheckpointData(
        idempotency_key="bench-key",
        table_path="s3://lake/db/table",
        table_format="iceberg",
        record_offset=5000,
        partition_info={},
        file_manifest=[],
        created_at="2026-01-01T00:00:00+00:00",
        lambda_function_name="bench",
        lambda_request_id="bench-req",
    )


def _mock_store() -> CheckpointStore:
    store: dict[str, bytes] = {}
    client = MagicMock()

    def put_object(**kw):
        store[kw["Key"]] = kw["Body"]

    def get_object(**kw):
        key = kw["Key"]
        if key not in store:
            from botocore.exceptions import ClientError

            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

        class Body:
            def read(self_inner):
                return store[key]

        return {"Body": Body()}

    def delete_object(**kw):
        store.pop(kw["Key"], None)

    client.put_object.side_effect = put_object
    client.get_object.side_effect = get_object
    client.delete_object.side_effect = delete_object
    client.get_paginator.return_value.paginate.return_value = []
    return CheckpointStore("bench-bucket", s3_client=client)


def main() -> None:
    store = _mock_store()
    cp = _sample_checkpoint()
    n = 200

    t0 = time.perf_counter()
    for i in range(n):
        store.save(f"key-{i}", cp)
    save_ms = (time.perf_counter() - t0) * 1000 / n

    t0 = time.perf_counter()
    for i in range(n):
        store.load(f"key-{i}")
    load_ms = (time.perf_counter() - t0) * 1000 / n

    print(f"Checkpoint save avg: {save_ms:.3f} ms (n={n}, mocked S3)")
    print(f"Checkpoint load avg: {load_ms:.3f} ms (n={n}, mocked S3)")


if __name__ == "__main__":
    main()
