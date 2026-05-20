# IceGuard release status (v0.2.2)

Public summary of what is **done**, **partial**, or **not applicable**.  
Current version in `pyproject.toml`: **0.2.2**.

---

## Done (shipped in code)

| Area | Delivered |
|------|-----------|
| Core | Chunked `SafeWriter.write()`, watchdog rollback, S3 checkpoints, resume |
| Spark | `write_dataframe()`, auto S3 `track_paths` |
| Formats | Iceberg, Delta, Hudi adapters; S3 metadata readers for Delta/Hudi |
| Glue | `glue_adapter()`, `glue_database` / `glue_table` on `protect()` |
| Orphans | `scan_orphans()`, CLI `iceguard orphans scan\|delete` |
| Metrics | CloudWatch (background), OpenTelemetry optional |
| Durable Lambda | `DurableCheckpointBridge`, `durable_context=` |
| DLQ | `dlq_queue_url=` → SQS on rollback |
| Security | `checkpoint_kms_key_id=` for SSE-KMS checkpoints |
| Coordinator | 2PC `Coordinator`, `S3LeaderLock` leader election |
| Schema | `schema_version` + migration on load |
| IaC | Modular Terraform (`terraform/modules/*`), SAM + CDK examples |
| CI | GitHub Actions, Python **3.9–3.13** |
| Tests | 141+ unit/integration/chaos tests (AWS e2e optional) |
| Docs | [API.md](API.md), architecture, installation, terraform |

---

## Partial (you finish or optional)

| Item | Status | What remains |
|------|--------|----------------|
| **PyPI publish** | Not on PyPI yet | Manual steps below (or GitHub Release + `PYPI_API_TOKEN`) |
| **Live E2E** | Code + `pytest -m aws` | Run in your AWS account with `ICEGUARD_AWS_E2E=1` |
| **PySpark + Iceberg live** | Fault-injection + optional spark test | Full live Iceberg table test in your VPC/catalog |
| **Formal verification** | TLA+ sketch in docs | Machine-checked TLA+ model (optional) |
| **S3 Express live** | Helper + docs | Validate against a real Express directory bucket in your AZ |

---

## Not applicable (platform limits)

| Item | Why |
|------|-----|
| Single `df.write.save()` inside `protect()` only | Spark blocks until complete; use `write_dataframe` or `writer.write()` |
| Guaranteed exactly-once for all consumers | IceGuard gives **effectively-once** visible writes + idempotent resume; consumers must be idempotent |

---

## What `pip install iceguard` includes

Only the **`iceguard`** Python package (`src/iceguard/`), plus `README.md` and `LICENSE`.  
Not included in the wheel: `tests/`, `terraform/`, `examples/`, `benchmarks/`, internal roadmap files.

---

## Manual PyPI publish (v0.2.2)

### 1. Prerequisites

- PyPI account: https://pypi.org/account/register/
- API token: https://pypi.org/manage/account/token/ (scope: entire account or project `iceguard`)
- Local tools: `pip install build twine`

### 2. Verify before upload

```bash
cd /path/to/IceGuard
pip install -e ".[dev]"
pytest tests -q -m "not aws"
python validation/run_all.py
python -m build
twine check dist/*
```

You should see `iceguard-0.2.2-py3-none-any.whl` and `iceguard-0.2.2.tar.gz`.

### 3. Upload to TestPyPI (recommended first)

```bash
twine upload --repository testpypi dist/*
# Install test:
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ iceguard==0.2.2
```

### 4. Upload to PyPI (production)

```bash
twine upload dist/*
```

Or set token once (do not commit):

```bash
# PowerShell
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-AgEIcHlwaS5vcmcCJ..."   # your API token

twine upload dist/*
```

### 5. Verify production install

```bash
pip install iceguard==0.2.2
pip install "iceguard[spark,iceberg,otel]==0.2.2"
python -c "import iceguard; print(iceguard.__version__)"
iceguard orphans scan --help
```

### 6. Git tag (match version)

```bash
git tag v0.2.2
git push origin v0.2.2
```

Optional: create a GitHub Release from tag `v0.2.2` to trigger `.github/workflows/publish-pypi.yml` if `PYPI_API_TOKEN` is set in repo secrets.

### 7. After publish — update README install line

Users can use:

```bash
pip install iceguard
```

---

## Version checklist

| File | Version |
|------|---------|
| `pyproject.toml` | `0.2.2` |
| Git tag | `v0.2.2` |
| PyPI | `iceguard==0.2.2` (after upload) |
