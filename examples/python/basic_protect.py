"""Minimal IceGuard chunked write (no Spark)."""

from unittest.mock import MagicMock

import iceguard


def lambda_handler(event, context):
    with iceguard.protect(context, s3_bucket="my-checkpoint-bucket") as writer:
        writer.write(
            path="s3://lake/db/table",
            total_records=10_000,
            batch_writer=lambda start, end: write_chunk(start, end),
            track_paths=lambda s, e: list_paths_written(s, e),
        )


def write_chunk(start: int, end: int) -> None:
    print(f"writing records [{start}, {end})")


def list_paths_written(start: int, end: int) -> list[str]:
    return [f"s3://lake/db/table/part-{start}-{end}.parquet"]


if __name__ == "__main__":
    ctx = MagicMock()
    ctx.get_remaining_time_in_millis.return_value = 600_000
    ctx.aws_request_id = "local-req"
    ctx.function_name = "local-fn"
    lambda_handler({}, ctx)
