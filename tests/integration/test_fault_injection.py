"""Fault-injection: prove chunked rollback deletes uncommitted paths (Spark-style)."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from iceguard.adapters import IcebergAdapter
from iceguard.config import IceGuardConfig
from iceguard.exceptions import IceGuardRollbackError
from iceguard.metrics import NullMetricsEmitter
from iceguard.safe_writer import SafeWriter


def test_chunked_write_rollback_deletes_tracked_paths():
    """Simulates Spark chunked writes: rollback after chunk 1 removes orphan S3 paths."""
    ctx = MagicMock()
    ctx.get_remaining_time_in_millis.return_value = 600_000
    ctx.aws_request_id = "fault-inject-req"
    ctx.function_name = "fault-inject-fn"
    cfg = IceGuardConfig(rollback_threshold_ms=5000, checkpoint_interval=10)
    adapter = IcebergAdapter()
    deleted_on_s3: list[str] = []

    with patch(
        "iceguard.adapters.delete_s3_uri",
        side_effect=lambda uri, **k: deleted_on_s3.append(uri),
    ):
        sw = SafeWriter(
            ctx,
            cfg,
            adapter,
            metrics_emitter=NullMetricsEmitter(),
        )
        paths_written: list[tuple[int, int]] = []

        with pytest.raises(IceGuardRollbackError):
            with sw:

                def batch_writer(start: int, end: int) -> None:
                    paths_written.append((start, end))
                    if end >= 10:
                        sw._rollback.set()

                sw.write(
                    path="s3://lake/db/orders",
                    total_records=30,
                    batch_writer=batch_writer,
                    track_paths=lambda s, e: [
                        f"s3://lake/db/orders/part-{s}-{e}.parquet"
                    ],
                )

    assert len(paths_written) >= 1
    assert deleted_on_s3
    assert all(p.startswith("s3://") for p in deleted_on_s3)


@pytest.mark.spark
@pytest.mark.skipif(
    sys.platform == "win32" and not os.environ.get("HADOOP_HOME"),
    reason="PySpark on Windows requires HADOOP_HOME (CI uses Linux)",
)
def test_pyspark_write_dataframe_respects_checkpoint_interval():
    """End-to-end with local Spark when pyspark is installed."""
    pytest.importorskip("pyspark")
    from pyspark.sql import SparkSession

    from iceguard.spark_write import write_dataframe

    try:
        spark = (
            SparkSession.builder.master("local[1]")
            .appName("iceguard-fault-injection")
            .config("spark.sql.shuffle.partitions", "2")
            .getOrCreate()
        )
    except (TypeError, RuntimeError) as e:
        pytest.skip(f"PySpark JVM not available in this environment: {e}")
    try:
        df = spark.range(0, 25).toDF("id")
        ctx = MagicMock()
        ctx.get_remaining_time_in_millis.return_value = 600_000
        ctx.aws_request_id = "spark-req"
        ctx.function_name = "spark-fn"
        cfg = IceGuardConfig(checkpoint_interval=10)
        adapter = IcebergAdapter()
        sw = SafeWriter(ctx, cfg, adapter, metrics_emitter=NullMetricsEmitter())
        chunk_ranges: list[tuple[int, int]] = []
        original_write = sw.write

        def counting_write(**kwargs):
            batch_writer = kwargs["batch_writer"]

            def wrapped(start: int, end: int) -> None:
                chunk_ranges.append((start, end))
                batch_writer(start, end)

            kwargs["batch_writer"] = wrapped
            return original_write(**kwargs)

        sw.write = counting_write  # type: ignore[method-assign]
        with sw:
            write_dataframe(
                sw,
                df,
                "file:///tmp/iceguard-fault-table",
                write_format="parquet",
                write_mode="append",
            )
        assert len(chunk_ranges) >= 2, "dataframe should split into multiple chunks"
    finally:
        spark.stop()
