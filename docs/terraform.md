# Terraform

See [terraform/README.md](../terraform/README.md) for the full module catalog.

## Modules (10)

| Module | Description |
|--------|-------------|
| `kms` | CMK + alias + rotation |
| `checkpoint_bucket` | Versioned checkpoints, KMS, logging, bucket policy |
| `data_lake_bucket` | Lake data bucket |
| `lambda_iam` | Writer role + policies |
| `lambda_layer` | Layer from S3 artifact |
| `lambda_function` | Lambda with IceGuard env vars |
| `cloudwatch_dashboard` | Ops dashboard |
| `cloudwatch_alarms` | Rollback / near-miss alarms |
| `iceguard_stack` | **Composes all modules** |

## Environments

| Env | Path | Notes |
|-----|------|-------|
| dev | `environments/dev` | `terraform.tfvars.example` included |
| prod | `environments/prod` | Remote state example, SNS alarms |

## Production checklist

- [ ] Remote state backend (`backend.tf.example`)
- [ ] Unique global bucket name
- [ ] Least-privilege `data_bucket_arns` (table prefixes only)
- [ ] CloudWatch alarms on `NearMiss` and `rollback` outcomes
- [ ] Separate AWS accounts for dev/prod
