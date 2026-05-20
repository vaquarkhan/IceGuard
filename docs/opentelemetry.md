# OpenTelemetry

For teams not using CloudWatch as the primary metrics backend:

```bash
pip install "iceguard[otel]"
```

```python
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader

provider = MeterProvider(metric_readers=[PeriodicExportingMetricReader(ConsoleMetricExporter())])

with iceguard.protect(ctx, enable_opentelemetry_metrics=True) as writer:
    ...
```

Metrics emitted:

| Metric | Description |
|--------|-------------|
| `iceguard.write.outcome` | success / rollback |
| `iceguard.watchdog.near_miss` | Threshold approached |
| `iceguard.orphan.found` / `deleted` | Orphan scan |
| `iceguard.checkpoint.resume_records` | Resume skip count |

Wire your OTLP exporter via the global `MeterProvider` before calling `protect()`.
