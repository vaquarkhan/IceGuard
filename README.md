![IceGuard](images/snowGuard.jpeg)

# IceGuard

**Reliability library for Spark-on-AWS-Lambda (SoAL) lakehouse writes.** Chunked writes with timeout rollback, S3 checkpoints, orphan cleanup, and optional CloudWatch or OpenTelemetry metrics.

| Capability | Out of the box | You provide |
|------------|----------------|-------------|
| Timeout rollback between chunks | Yes | — |
| Checkpoint resume (S3) | Yes | S3 bucket |
| S3 path cleanup on rollback | Yes (`track_paths`) | — |
| Iceberg / Delta / **Hudi** adapters | Yes (S3 fallback) | Catalog / commit client for metadata |
| Orphan scan CLI | Yes | IAM on table path |
| Blocking `df.write.save()` in `protect()` only | **No** | Use `write_dataframe` |

## Install

```bash
pip install iceguard
# or until published:
pip install "git+https://github.com/vaquarkhan/IceGuard.git"
```

Extras: `[spark]`, `[iceberg]`, `[hudi]`, `[otel]`, `[dev]`

## Quick start

```python
import iceguard

with iceguard.protect(context, s3_bucket="my-checkpoints") as writer:
    writer.write(
        path="s3://lake/db/table",
        total_records=10_000,
        batch_writer=lambda s, e: write_chunk(s, e),
        track_paths=lambda s, e: new_paths(s, e),
    )
```

Spark: `iceguard.write_dataframe(writer, df, path, write_format="iceberg")`

CLI: `iceguard orphans scan s3://lake/db/table --json`

## Repository layout

| Path | Purpose |
|------|---------|
| [docs/](docs/) | Full documentation |
| [examples/](examples/) | Python, SAM, CDK samples |
| [terraform/](terraform/) | Modular production IaC |
| [infra/cloudwatch/](infra/cloudwatch/) | Dashboard JSON |
| [src/iceguard/](src/iceguard/) | Library source |

## Development

```bash
pip install -e ".[dev]"
pytest tests --cov=iceguard
python validation/run_all.py
```

## Documentation

- [Installation](docs/installation.md)
- [Architecture](docs/architecture.md)
- [Terraform](docs/terraform.md)
- [Formal verification](docs/formal-verification.md)
- [Publishing](docs/publishing.md)

## License

MIT — see [LICENSE](LICENSE).
