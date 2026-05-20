# CLI

Entry point: `iceguard` (installed via `pip install iceguard`).

## Orphan scan

```bash
iceguard orphans scan s3://lake/db/table --table-format iceberg --json
```

## Orphan delete

```bash
iceguard orphans delete s3://lake/db/table --retention-hours 72
iceguard orphans delete s3://lake/db/table --dry-run
```

## Options

| Flag | Description |
|------|-------------|
| `--table-format` | `iceberg`, `delta`, `hudi` |
| `--retention-hours` | Minimum age before file is orphan (default 72) |
| `--batch-size` | Max 1000 (S3 API limit) |
| `--json` | Machine-readable output |

Requires IAM permissions to `ListBucket` / `DeleteObject` on the table path.
