"""Spark DataFrame write protected by IceGuard (run inside Lambda with PySpark)."""

import iceguard


def handler(event, context):
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    df = spark.read.parquet(event["source_path"])

    with iceguard.protect(
        context,
        table_format="iceberg",
        s3_bucket=event["checkpoint_bucket"],
        catalog=event.get("catalog"),
        table_identifier=event.get("table_identifier"),
    ) as writer:
        iceguard.write_dataframe(
            writer,
            df,
            event["table_path"],
            write_format="iceberg",
            write_mode="append",
            track_paths=event.get("track_paths_callable"),
        )
