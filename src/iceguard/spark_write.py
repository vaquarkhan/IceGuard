"""Spark DataFrame integration for chunked SafeWriter writes."""

from __future__ import annotations

from typing import Any, Callable, List, Optional

from iceguard.safe_writer import SafeWriter
from iceguard.s3_track import s3_track_paths_factory


def write_dataframe(
    writer: SafeWriter,
    df: Any,
    path: str,
    *,
    write_format: str = "iceberg",
    write_mode: str = "append",
    write_options: Optional[dict] = None,
    row_id_column: str = "_iceguard_row_id",
    track_paths: Optional[Callable[[int, int], List[str]]] = None,
    auto_track_s3_paths: bool = True,
) -> None:
    """Write a Spark DataFrame in checkpoint-sized chunks via SafeWriter.write().

    Requires PySpark on the classpath. Each chunk calls ``DataFrame.write`` so the
    watchdog can interrupt between batches (unlike one blocking ``save()``).

    Args:
        writer: Active SafeWriter from ``iceguard.protect()`` context.
        df: ``pyspark.sql.DataFrame`` to write.
        path: Target table path (for example ``s3://lake/db/table``).
        write_format: Spark write format (``iceberg``, ``delta``, etc.).
        write_mode: Spark save mode (typically ``append`` during chunked load).
        write_options: Extra options passed to ``.options(**write_options)``.
        row_id_column: Temporary column used to slice row ranges; dropped before write.
        track_paths: Optional callback returning new file URIs per chunk for rollback.
        auto_track_s3_paths: When True and ``path`` is ``s3://``, diff Parquet keys per chunk.
    """
    try:
        from pyspark.sql import functions as F
        from pyspark.sql.window import Window
    except ImportError as e:
        raise ImportError(
            "write_dataframe requires PySpark. Install pyspark in your Lambda image."
        ) from e

    opts = write_options or {}
    w = Window.orderBy(F.monotonically_increasing_id())
    indexed = df.withColumn(row_id_column, F.row_number().over(w))
    total = int(indexed.count())
    if total == 0:
        return

    def batch_writer(start: int, end: int) -> None:
        part = indexed.filter(
            (F.col(row_id_column) > start) & (F.col(row_id_column) <= end)
        ).drop(row_id_column)
        writer_api = part.write.format(write_format).mode(write_mode)
        if opts:
            writer_api = writer_api.options(**opts)
        writer_api.save(path)

    resolved_track = track_paths
    if resolved_track is None and auto_track_s3_paths and path.startswith("s3://"):
        resolved_track = s3_track_paths_factory(path)

    writer.write(
        path=path,
        total_records=total,
        batch_writer=batch_writer,
        track_paths=resolved_track,
    )
