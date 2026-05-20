# Roadmap to 10/10

Status key: **Done** | **Partial** | **Planned** | **N/A** (platform limit)

---

## Phase 1: Ship It

| Item | Status | Notes |
|------|--------|-------|
| Fix `pyproject.toml` bug | **Done** | `dependencies` under `[project]` (0.2.0+) |
| Publish to PyPI | **Partial** | Workflow `.github/workflows/publish-pypi.yml`; needs `PYPI_API_TOKEN` + release tag |
| GitHub Actions CI (3.9–3.13) | **Done** | Matrix in `.github/workflows/ci.yml` |
| Complete API documentation | **Done** | [API.md](API.md) + [api-reference.md](api-reference.md) |
| Example Lambda project (SAM) | **Done** | [examples/sam/](../examples/sam/) |

---

## Phase 2: Prove It

| Item | Status | Notes |
|------|--------|-------|
| E2E: PySpark + Iceberg + S3 | **Partial** | Local fault-injection + optional `pytest -m aws` live test |
| Chaos / fault-injection suite | **Done** | [tests/chaos/](../tests/chaos/) |
| S3 Express One Zone validation | **Done** | [s3-express-one-zone.md](s3-express-one-zone.md) + `validate_express_bucket()` |
| Performance benchmarks | **Done** | [benchmarks/checkpoint_overhead.py](../benchmarks/checkpoint_overhead.py) |

---

## Phase 3: Differentiate

| Item | Status | Notes |
|------|--------|-------|
| Lambda Durable Functions | **Done** | `DurableCheckpointBridge`, `durable_context=` on `protect()` |
| DLQ for failed writes | **Done** | `dlq_queue_url=` + [dlq.py](../src/iceguard/dlq.py) |
| Hudi adapter | **Done** | `HudiAdapter`, S3 timeline reader |
| CloudWatch dashboard | **Done** | Terraform module + `infra/cloudwatch/dashboard.json` |
| Terraform / CDK | **Done** | 9 Terraform modules + [examples/cdk/](../examples/cdk/) |
| CLI orphan management | **Done** | `iceguard orphans scan|delete` |

---

## Phase 4: Enterprise

| Item | Status | Notes |
|------|--------|-------|
| OpenTelemetry | **Done** | `enable_opentelemetry_metrics=True`, `[otel]` extra |
| Glue Data Catalog integration | **Done** | `GlueCatalogAdapter`, `glue_adapter()` |
| Exactly-once formal verification | **Partial** | [formal-verification.md](formal-verification.md) + TLA+ sketch; machine-checked TLA planned |
| Checkpoint encryption | **Done** | KMS SSE on `CheckpointStore` (`kms_key_id`) |
| Coordinator leader election | **Done** | `S3LeaderLock` in [coordinator_leader.py](../src/iceguard/coordinator_leader.py) |
| Schema evolution handling | **Done** | `CheckpointData.schema_version` + [schema_evolution.py](../src/iceguard/schema_evolution.py) |

---

## Platform limits (not on roadmap as “bugs”)

- Single blocking `df.write.save()` inside `protect()` only — use `write_dataframe` / `writer.write()`.
- True exactly-once without idempotent consumers — IceGuard provides **effectively-once** visible writes + resume.

---

## Suggested release order

1. Tag **v0.2.2** → PyPI publish  
2. Run `pytest tests` + `pytest tests/e2e -m aws` in account with S3  
3. `terraform apply` in dev → run SAM example  
4. `python benchmarks/checkpoint_overhead.py` baseline in CI artifact  
