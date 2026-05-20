# Validation report (bug audit)

Audit date aligned with release **0.2.2**. Use this when re-checking fixes.

## Fixed in codebase (bugs 1–9)

| # | Issue | Status in `main` |
|---|--------|------------------|
| 1 | Watchdog `started_ok()` uses `_ever_started` flag | Fixed — `watchdog.py` |
| 2 | `SafeWriter.__enter__` checks `_rollback.is_set()` after start | Fixed — lines 135–142 |
| 3 | Default metrics → real CloudWatch client | Fixed — `NullMetricsEmitter` default |
| 4 | Sync CloudWatch on write path | Fixed — `BackgroundMetricsEmitter` when enabled |
| 5 | Adapter delete without catalog | Fixed — S3 delete via `delete_s3_uri` |
| 6 | Orphan scanner no list_candidates | Fixed — default S3 list for `s3://` |
| 7 | `batch_size` > 1000 silent cap | Fixed — raises `IceGuardConfigError` |
| 8 | `IceGuardConfig` string `table_format` | Fixed — `_coerce_table_format()` |
| 9 | Python 3.13 blocked | Fixed — `requires-python = ">=3.9,<3.14"` |

## Bug #10 — `pyproject.toml` / `[project.urls]`

**Not present on current `main`.** `dependencies` is under `[project]` (before `[project.urls]`):

```toml
[project]
...
dependencies = [
    "boto3>=1.28.0",
]

[project.urls]
Homepage = "..."
```

Verify locally:

```bash
python -m build
pip install dist/iceguard-*.whl
```

If you still see `URL dependencies must be a string`, pull latest `main` or check for a stale checkout.

## Bug #11 — `write_dataframe` + `overwrite`

**Fixed (0.2.3+).** Chunked writes only allow `write_mode="append"`. Other modes raise `ValueError` with an explanation.

## Bug #12 — PySpark test on Windows

**Fixed.** `test_pyspark_write_dataframe_respects_checkpoint_interval` is skipped when `sys.platform == "win32"` and `HADOOP_HOME` is unset.

## Re-run validation

```bash
pytest tests -q -m "not aws"
python -m build
twine check dist/*
```
