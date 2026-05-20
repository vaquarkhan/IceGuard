"""SAM Lambda handler — real IceGuard chunked write with S3 path tracking."""

import os

import iceguard
from iceguard.s3_track import s3_track_paths_factory


def lambda_handler(event, context):
    bucket = os.environ["ICEGUARD_CHECKPOINT_BUCKET"]
    table_path = event.get("table_path", "s3://example/lake/table")
    total = int(event.get("total_records", 1000))
    interval = int(event.get("checkpoint_interval", 5000))

    with iceguard.protect(
        context,
        s3_bucket=bucket,
        table_format=event.get("table_format", "iceberg"),
        checkpoint_interval=interval,
        rollback_threshold_ms=int(os.environ.get("ICEGUARD_ROLLBACK_THRESHOLD_MS", "30000")),
        enable_cloudwatch_metrics=event.get("enable_metrics", False),
        durable_context=getattr(context, "durable_execution", None),
    ) as writer:
        track = None
        if table_path.startswith("s3://"):
            track = s3_track_paths_factory(table_path)

        writer.write(
            path=table_path,
            total_records=total,
            batch_writer=lambda s, e: write_chunk(event, s, e),
            track_paths=track,
        )
    return {"status": "ok", "records": total, "table": table_path}


def write_chunk(event, start: int, end: int) -> None:
    """Replace with Spark or boto3 Parquet write in production."""
    import boto3

    table_path = event.get("table_path", "")
    if not table_path.startswith("s3://"):
        return
    bucket = table_path.split("/")[2]
    prefix = "/".join(table_path.split("/")[3:]).rstrip("/")
    key = f"{prefix}/part-{start}-{end}.parquet"
    boto3.client("s3").put_object(Bucket=bucket, Key=key, Body=b"chunk")
