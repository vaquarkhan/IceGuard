# Terraform

Modular stacks under `terraform/`:

## Modules

### `checkpoint_bucket`

- Versioning enabled
- SSE-S3 encryption
- Public access blocked
- Lifecycle rule for noncurrent versions

### `lambda_iam`

- Assume role for `lambda.amazonaws.com`
- S3 RW on checkpoint bucket
- Optional data bucket ARNs
- `cloudwatch:PutMetricData` when metrics enabled
- `AWSLambdaBasicExecutionRole` attached

### `cloudwatch_dashboard`

Dashboard widgets for `iceguard` namespace metrics.

## Environments

| Env | Path | Notes |
|-----|------|-------|
| dev | `environments/dev` | Default tags, 90d noncurrent expiry |
| prod | `environments/prod` | Requires `data_bucket_arns`, 30d expiry |

## Production checklist

- [ ] Remote state backend (`backend.tf.example`)
- [ ] Unique global bucket name
- [ ] Least-privilege `data_bucket_arns` (table prefixes only)
- [ ] CloudWatch alarms on `NearMiss` and `rollback` outcomes
- [ ] Separate AWS accounts for dev/prod
