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

## Lambda deployment

Package `iceguard` into a Lambda layer (`pip install iceguard -t python/`). For Spark, add JVM + PySpark in a separate layer or container image.
