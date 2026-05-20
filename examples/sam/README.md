# SAM example

1. Deploy checkpoint bucket: `terraform/environments/dev`
2. Build layer: `pip install iceguard -t layer/python`
3. `sam build && sam deploy --guided`

Add a **PySpark + Java** layer for real Spark writes; this sample shows the IceGuard Python integration pattern.
