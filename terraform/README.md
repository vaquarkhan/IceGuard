# IceGuard Terraform

Production-oriented, **modular** infrastructure for IceGuard on AWS Lambda.

## Layout

```
terraform/
  modules/
    checkpoint_bucket/     # S3 bucket for IceGuard checkpoints (versioned, encrypted)
    lambda_iam/            # IAM role/policy for Lambda writers
    cloudwatch_dashboard/  # Pre-built operational dashboard
  environments/
    dev/                   # Dev stack (calls modules)
    prod/                  # Prod stack (stricter settings)
```

## Quick start (dev)

```bash
cd terraform/environments/dev
terraform init
terraform plan -var="project_name=iceguard-dev" -var="checkpoint_bucket_name=iceguard-dev-checkpoints-UNIQUE"
terraform apply -var="project_name=iceguard-dev" -var="checkpoint_bucket_name=iceguard-dev-checkpoints-UNIQUE"
```

## Modules

| Module | Purpose |
|--------|---------|
| `checkpoint_bucket` | Versioned S3, SSE-S3, public access block, lifecycle for old checkpoints |
| `lambda_iam` | Least-privilege policy: S3 checkpoint RW, CloudWatch metrics, table data paths |
| `cloudwatch_dashboard` | Widgets for WriteOutcome, NearMiss, OrphanScan, CheckpointResume |

See [docs/terraform.md](../docs/terraform.md) for variable reference and production checklist.

## State

Use a remote backend in production (S3 + DynamoDB lock). Example in `environments/prod/backend.tf.example`.

## CDK alternative

See [examples/cdk](../examples/cdk/README.md) for an AWS CDK sample that composes the same resources.
