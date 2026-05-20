# IceGuard API (complete reference)

## Package

```python
import iceguard
iceguard.__version__
```

### `protect(lambda_context, ...) -> SafeWriter`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `table_format` | `str` \| `TableFormat` | `"iceberg"` | `iceberg`, `delta`, `hudi` |
| `rollback_threshold_ms` | `int` | `30000` | Rollback when remaining ms ≤ threshold |
| `checkpoint_interval` | `int` | `5000` | Records per chunk |
| `idempotency_key` | `str?` | request id | Checkpoint key |
| `s3_bucket` | `str?` | None | Checkpoint bucket |
| `coordinator_id` | `str?` | None | Prefix for multi-Lambda keys |
| `orphan_retention_hours` | `int` | `72` | Orphan scanner retention |
| `orphan_batch_size` | `int` | `1000` | Max 1000 (S3 API) |
| `enable_cloudwatch_metrics` | `bool` | `False` | Background CloudWatch |
| `enable_opentelemetry_metrics` | `bool` | `False` | OTel counters |
| `catalog` | `Any?` | None | Iceberg catalog |
| `delta_log` | `Any?` | None | Delta log handle |
| `hudi_commit_client` | `Any?` | None | Hudi commit client |
| `table_identifier` | `str?` | None | PyIceberg table id |
| `adapter` | `TableFormatAdapter?` | None | Override adapter |
| `durable_context` | `Any?` | None | Lambda durable execution context |
| `dlq_queue_url` | `str?` | None | SQS URL for rollback notifications |
| `checkpoint_kms_key_id` | `str?` | None | KMS key for checkpoint SSE |

### `SafeWriter`

Context manager from `protect()`.

**Methods**

- `write(path, total_records, batch_writer, track_paths=None)` — chunked protected write
- `disarm()` — stop watchdog

**Raises**

- `IceGuardRollbackError` — timeout rollback
- `IceGuardInitializationError` — watchdog failed to start
- `IceGuardContextError` — invalid Lambda context

### `write_dataframe(writer, df, path=None, *, table_identifier=None, ...)`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `path` | `None` | Storage path for `.save(path)` and S3 tracking (at least one of `path` / `table_identifier` required) |
| `table_identifier` | `None` | Catalog name for `.insertInto()` (e.g. `glue_catalog.db.table`) |
| `write_format` | `"iceberg"` | Spark format |
| `write_mode` | `"append"` | Spark mode |
| `write_options` | `{}` | Spark `.options()` |
| `row_id_column` | `"_iceguard_row_id"` | Chunk slice column |
| `track_paths` | None | Per-chunk path callback |
| `auto_track_s3_paths` | `True` | Diff S3 Parquet per chunk when `path` is `s3://` |

### `scan_orphans(table_path, adapter, *, retention_hours=72, batch_size=1000, delete=False)`

Returns `ScanResult` or `(ScanResult, DeleteResult)` if `delete=True`.

### Adapters

- `iceberg_adapter(catalog=, table_identifier=, committed_files=, s3_client=)`
- `delta_adapter(log=, committed_files=, s3_client=)`
- `hudi_adapter(commit_client=, committed_files=, s3_client=)`
- `glue_adapter(database=, table_name=, *, catalog=, s3_client=)` — Glue + Iceberg metadata

### `CheckpointStore(bucket, prefix, *, s3_client, kms_key_id=None)`

- `save(key, CheckpointData)`
- `load(key) -> CheckpointData | None`
- `delete(key)`
- `health_check(timeout_ms) -> bool`

### `DurableCheckpointBridge(checkpoint_store, durable_context=None)`

- `save(idempotency_key, CheckpointData)`
- `load(idempotency_key) -> CheckpointData | None`
- `clear_durable_checkpoint()`

### `Coordinator(participants, checkpoint_store, *, transaction_id, timeout_ms, ...)`

Two-phase commit: `prepare()`, `commit()`, `abort()`, `recover(transaction_id)`.

### `S3LeaderLock(checkpoint_store, lock_key, owner_id, lease_seconds=30)`

- `acquire() -> bool`
- `release() -> None`

### CLI

```bash
iceguard orphans scan TABLE_PATH [--table-format iceberg] [--json]
iceguard orphans delete TABLE_PATH [--dry-run]
```

### Exceptions

`IceGuardError`, `IceGuardRollbackError`, `IceGuardConfigError`, `IceGuardContextError`, `IceGuardInitializationError`, `CheckpointCorruptionError`, `CoordinatorTimeoutError`
