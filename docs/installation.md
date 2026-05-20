# Installation

## From PyPI (recommended)

https://pypi.org/project/iceguard/

```bash
pip install iceguard
pip install "iceguard[spark,iceberg,otel]==1.0.0"
```

## From GitHub

```bash
pip install "git+https://github.com/vaquarkhan/IceGuard.git@v1.0.0"
pip install "git+https://github.com/vaquarkhan/IceGuard.git@v1.0.0#egg=iceguard[spark,iceberg,hudi,otel,dev]"
```

## Extras

| Extra | Packages |
|-------|----------|
| `spark` | PySpark |
| `iceberg` | PyIceberg |
| `delta` | delta-spark |
| `hudi` | PySpark (Hudi via Spark) |
| `otel` | OpenTelemetry API/SDK |
| `dev` | pytest, hypothesis, coverage |

## Docker (GHCR)

Pre-built Lambda + PySpark image (see [docker.md](docker.md)):

```bash
docker pull ghcr.io/vaquarkhan/iceguard:1.0.0
```

```dockerfile
FROM ghcr.io/vaquarkhan/iceguard:1.0.0
COPY my_handler.py ${LAMBDA_TASK_ROOT}/
CMD ["my_handler.lambda_handler"]
```

Package page: https://github.com/vaquarkhan/IceGuard/pkgs/container/iceguard

## Lambda deployment

**Option A — container image (recommended for Spark):** use `ghcr.io/vaquarkhan/iceguard` as in [docker.md](docker.md).

**Option B — layers:** package `iceguard` into a Lambda layer (`pip install iceguard -t python/`). For Spark, add JVM + PySpark in a separate layer or your own container image.
