# Installation

## From PyPI (recommended after first release)

```bash
pip install iceguard
pip install "iceguard[spark,iceberg,otel]"
```

## From GitHub

```bash
pip install "git+https://github.com/vaquarkhan/IceGuard.git@v0.2.0"
pip install "git+https://github.com/vaquarkhan/IceGuard.git@v0.2.0#egg=iceguard[spark,iceberg,hudi,otel,dev]"
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
