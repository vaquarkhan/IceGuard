# IceGuard Terraform

Production-grade **modular** infrastructure for IceGuard on AWS.

## Module catalog

| Module | Purpose |
|--------|---------|
| [kms](modules/kms/) | CMK with rotation |
| [checkpoint_bucket](modules/checkpoint_bucket/) | Versioned checkpoint store (SSE-KMS optional, logging, bucket policy) |
| [data_lake_bucket](modules/data_lake_bucket/) | Lake data bucket with encryption |
| [lambda_iam](modules/lambda_iam/) | Least-privilege Lambda role |
| [lambda_layer](modules/lambda_layer/) | Published dependency layer from S3 zip |
| [lambda_function](modules/lambda_function/) | Writer Lambda with IceGuard env vars |
| [cloudwatch_dashboard](modules/cloudwatch_dashboard/) | Operations dashboard |
| [cloudwatch_alarms](modules/cloudwatch_alarms/) | Rollback + near-miss alarms |
| [iceguard_stack](modules/iceguard_stack/) | **Composition** of all modules |

## Deploy (dev)

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
# edit bucket names (globally unique)
terraform init
terraform plan
terraform apply
```

## Deploy (prod)

```bash
cd terraform/environments/prod
# configure backend.tf from backend.tf.example
terraform init
terraform apply -var-file=prod.tfvars
```

## Lambda artifacts

1. `pip install iceguard -t build/python`
2. Zip `build/python` → upload to S3 as layer artifact
3. Zip `examples/sam/handler.py` + deps → function artifact
4. Set `deploy_lambda = true` and artifact bucket/keys in tfvars

See [docs/terraform.md](../docs/terraform.md).
