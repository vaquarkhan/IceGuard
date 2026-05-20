"""SAM Lambda handler using IceGuard."""

import os

import iceguard


def lambda_handler(event, context):
    bucket = os.environ["ICEGUARD_CHECKPOINT_BUCKET"]
    table_path = event.get("table_path", "s3://example/lake/table")

    with iceguard.protect(
        context,
        s3_bucket=bucket,
        table_format=event.get("table_format", "iceberg"),
        enable_cloudwatch_metrics=event.get("enable_metrics", False),
    ) as writer:
        total = int(event.get("total_records", 1000))
        writer.write(
            path=table_path,
            total_records=total,
            batch_writer=lambda s, e: None,
            track_paths=lambda s, e: [],
        )
    return {"status": "ok", "records": total}
