"""Spark DataFrame integration for chunked SafeWriter writes."""

from __future__ import annotations

from typing import Any, Callable, List, Optional

from iceguard.safe_writer import SafeWriter
from iceguard.s3_track import s3_track_paths_factory


def _write_spark_partition(
    part: Any,
    *,
    write_format: str,
    write_mode: str,
    write_options: dict,
    path: Optional[str],
    table_identifier: Optional[str],
) -> None:
    """Write one DataFrame partition via path (.save) or catalog (.insertInto)."""
    writer_api = part.write.format(write_format).mode(write_mode)
    if write_options:
        writer_api = writer_api.options(**write_options)
    if table_identifier:
        writer_api.insertInto(table_identifier)
    elif path:
        writer_api.save(path)
    else:
        raise ValueError(
            "write_dataframe requires path and/or table_identifier for each chunk"
        )


def write_dataframe(
    writer: SafeWriter,
    df: Any,
    path: Optional[str] = None,
    *,
    table_identifier: Optional[str] = None,
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

    Only ``write_mode="append"`` is supported. ``overwrite`` would replace prior
    batches at the same path, so only the last chunk would remain.

    Args:
        writer: Active SafeWriter from ``iceguard.protect()`` context.
        df: ``pyspark.sql.DataFrame`` to write.
        path: Target storage path (e.g. ``s3://lake/db/table``). Used with
            ``.save(path)`` for path-based tables and for S3 orphan tracking.
        table_identifier: Catalog table name (e.g. ``glue_catalog.db.table``).
            When set, each chunk uses ``.insertInto(table_identifier)`` instead of
            ``.save(path)`` — required for Glue/Hive catalog-managed Iceberg,
            Delta, and Hudi tables.
        write_format: Spark write format (``iceberg``, ``delta``, etc.).
        write_mode: Spark save mode (typically ``append`` during chunked load).
        write_options: Extra options passed to ``.options(**write_options)``.
        row_id_column: Temporary column used to slice row ranges; dropped before write.
        track_paths: Optional callback returning new file URIs per chunk for rollback.
        auto_track_s3_paths: When True and ``path`` is ``s3://``, diff Parquet keys per chunk.

    Raises:
        ValueError: If neither ``path`` nor ``table_identifier`` is provided, or
            ``write_mode`` is not ``append``.
    """
    if not path and not table_identifier:
        raise ValueError(
            "write_dataframe requires at least one of path or table_identifier. "
            "Use table_identifier for catalog-managed tables (e.g. glue_catalog.db.table); "
            "use path for path-based writes (e.g. s3://bucket/table)."
        )

    try:
        from pyspark.sql import functions as F
        from pyspark.sql.window import Window
    except ImportError as e:
        raise ImportError(
            "write_dataframe requires PySpark. Install pyspark in your Lambda image."
        ) from e

    mode = str(write_mode).strip().lower()
    logical_path = path or table_identifier
    if mode != "append":
        raise ValueError(
            f"write_dataframe only supports write_mode='append' for chunked writes "
            f"(each batch writes a slice of rows). Got {write_mode!r}; 'overwrite' would "
            f"replace earlier batches at {logical_path!r} and leave only the last chunk visible."
        )

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
        _write_spark_partition(
            part,
            write_format=write_format,
            write_mode=mode,
            write_options=opts,
            path=path,
            table_identifier=table_identifier,
        )

    resolved_track = track_paths
    if resolved_track is None and auto_track_s3_paths and path and path.startswith("s3://"):
        resolved_track = s3_track_paths_factory(path)

    writer.write(
        path=logical_path,
        total_records=total,
        batch_writer=batch_writer,
        track_paths=resolved_track,
    )
