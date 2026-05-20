# E2E tests (optional AWS)

Default CI skips these. To run against real S3:

```bash
export ICEGUARD_AWS_E2E=1
export ICEGUARD_E2E_BUCKET=your-checkpoint-bucket
pytest tests/e2e -m aws -v
```

For PySpark + Iceberg live test, add Spark and Iceberg catalog env vars (future: `ICEGUARD_E2E_ICEBERG=1`).
