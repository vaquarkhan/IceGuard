# IceGuard release status (v1.0.0)

Public summary of what is **done**, **partial**, or **not applicable**.  
Current version in `pyproject.toml`: **1.0.0**.

**PyPI:** https://pypi.org/project/iceguard/ · **Stats:** https://pepy.tech/project/iceguard

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
| **PyPI** | **Published** via trusted publishing on GitHub Release `v1.0.0` |
| **Docker (GHCR)** | `ghcr.io/vaquarkhan/iceguard` — see [docker.md](docker.md) |

---

## Partial (you finish or optional)

| Item | Status | What remains |
|------|--------|----------------|
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

## PyPI publish (automated)

Releases use **trusted publishing** — see [publishing.md](publishing.md).

1. Bump `version` in `pyproject.toml`.
2. Push to `main`.
3. Create GitHub Release tag `vX.Y.Z` (e.g. `v1.0.0`) → `.github/workflows/publish-pypi.yml` uploads to PyPI.

### Verify install

```bash
pip install iceguard==1.0.0
pip install "iceguard[spark,iceberg,otel]==1.0.0"
python -c "import iceguard; print(iceguard.__version__)"
iceguard orphans scan --help
```

---

## Version checklist

| File | Version |
|------|---------|
| `pyproject.toml` | `1.0.0` |
| Git tag | `v1.0.0` |
| PyPI | `iceguard==1.0.0` |
| Docker | `ghcr.io/vaquarkhan/iceguard:1.0.0` |
