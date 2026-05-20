# API reference

## `iceguard.protect(lambda_context, ...)`

Returns `SafeWriter` context manager.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `table_format` | `iceberg` | `iceberg`, `delta`, or `hudi` |
| `rollback_threshold_ms` | 30000 | Rollback when remaining time ≤ threshold |
| `checkpoint_interval` | 5000 | Records per chunk |
| `s3_bucket` | None | Checkpoint bucket (required for resume) |
| `catalog` / `delta_log` / `hudi_commit_client` | None | Format-native hooks |
| `table_identifier` | None | PyIceberg table id for committed file listing |
| `enable_cloudwatch_metrics` | False | Background CloudWatch publisher |
| `enable_opentelemetry_metrics` | False | OTel counters |
| `durable_context` | None | Lambda durable execution context |
| `coordinator_id` | None | Prefix for idempotency keys |

## `SafeWriter.write`

```python
writer.write(
    path="s3://lake/db/t",
    total_records=N,
    batch_writer=lambda start, end: ...,
    track_paths=lambda start, end: ["s3://..."],
)
```

## `iceguard.write_dataframe(writer, df, path=None, *, table_identifier=None, ...)`

Requires PySpark. Splits DataFrame into checkpoint-sized Spark writes.

- **Path-based table:** pass `path="s3://..."` → each chunk uses `.save(path)`.
- **Catalog-managed table:** pass `table_identifier="glue_catalog.db.table"` → each chunk uses `.insertInto(table_identifier)`. Optionally pass `path` as the warehouse URI for S3 orphan tracking.

## `iceguard.scan_orphans(table_path, adapter, delete=False)`

Lists or deletes orphan Parquet under `s3://` paths by default.

## Adapters

- `iceberg_adapter(catalog=..., table_identifier=...)`
- `delta_adapter(log=...)`
- `hudi_adapter(commit_client=...)`
