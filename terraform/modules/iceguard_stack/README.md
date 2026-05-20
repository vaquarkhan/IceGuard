# iceguard_stack

Composition module wiring all IceGuard infrastructure:

- `kms` (optional)
- `checkpoint_bucket`
- `data_lake_bucket` (optional)
- `lambda_iam`
- `cloudwatch_dashboard`
- `cloudwatch_alarms` (optional)
- `lambda_layer` + `lambda_function` (optional, when artifacts uploaded to S3)

Use from `environments/dev` or `environments/prod`.
