![IceGuard](images/snowGuard.jpeg)

# IceGuard

[![PyPI](https://img.shields.io/pypi/v/iceguard)](https://pypi.org/project/iceguard/)
[![PyPI downloads (month)](https://img.shields.io/pypi/dm/iceguard)](https://pypi.org/project/iceguard/)
[![PyPI downloads (week)](https://img.shields.io/pypi/dw/iceguard)](https://pypi.org/project/iceguard/)
[![Python](https://img.shields.io/pypi/pyversions/iceguard)](https://pypi.org/project/iceguard/)
[![License](https://img.shields.io/pypi/l/iceguard)](https://pypi.org/project/iceguard/)
[![Docker](https://img.shields.io/badge/docker-ghcr.io%2Fvaquarkhan%2Ficeguard-blue)](https://github.com/vaquarkhan/IceGuard/pkgs/container/iceguard)

**Published on PyPI:** [pypi.org/project/iceguard](https://pypi.org/project/iceguard/) · **Download stats:** [pepy.tech/project/iceguard](https://pepy.tech/project/iceguard) (aggregated; PyPI does not expose per-version counts in the API)

**Docker (GHCR):** [ghcr.io/vaquarkhan/iceguard](https://github.com/vaquarkhan/IceGuard/pkgs/container/iceguard) — Lambda Python 3.12 + Java + PySpark + IceGuard. See [docs/docker.md](docs/docker.md).

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

# With optional extras
pip install "iceguard[spark,iceberg,hudi,otel]==1.0.0"

# From source (specific tag)
pip install "git+https://github.com/vaquarkhan/IceGuard.git@v1.0.0"
```

Extras: `[spark]`, `[iceberg]`, `[hudi]`, `[otel]`, `[dev]`

## Docker

```bash
docker pull ghcr.io/vaquarkhan/iceguard:1.0.0
docker pull ghcr.io/vaquarkhan/iceguard:latest
```

Extend for your Lambda function:

```dockerfile
FROM ghcr.io/vaquarkhan/iceguard:1.0.0
COPY my_handler.py ${LAMBDA_TASK_ROOT}/
CMD ["my_handler.lambda_handler"]
```

Details: [docs/docker.md](docs/docker.md)

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

## Release status

See [docs/STATUS.md](docs/STATUS.md) for capability checklist. **v1.0.0** is published via GitHub Actions trusted publishing (OIDC) on release tags.

## Documentation

- [API reference (complete)](docs/API.md)
- [Installation](docs/installation.md)
- [Architecture](docs/architecture.md)
- [Terraform](docs/terraform.md)
- [Formal verification](docs/formal-verification.md)
- [Publishing](docs/publishing.md)
- [Docker image](docs/docker.md)

## License

MIT — see [LICENSE](LICENSE).
