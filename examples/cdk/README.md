# CDK example

Minimal Python CDK stack mirroring Terraform modules. Install:

```bash
pip install aws-cdk-lib constructs
cd examples/cdk
cdk deploy
```

Set `CHECKPOINT_BUCKET` context or edit `app.py`. For production, prefer `terraform/environments/prod` with remote state.
