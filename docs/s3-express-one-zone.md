# S3 Express One Zone

IceGuard uses standard boto3 S3 operations (`list_objects_v2`, `put_object`, `delete_object`) for checkpoints, orphan scans, and rollback deletes.

## Directory buckets

S3 Express One Zone **directory buckets** use names ending in `--x-s3` (for example `mybucket--use1-az1--x-s3`).

```python
from iceguard.s3_ops import validate_express_one_zone_bucket

validate_express_one_zone_bucket("mybucket--use1-az1--x-s3")  # True
```

## Client configuration

Point the S3 client at the **zonal endpoint** for your availability zone. Example:

```python
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="https://s3express-use1-az1.us-east-1.amazonaws.com",
)
```

Pass `s3_client=s3` into `CheckpointStore`, `OrphanScanner`, and adapters.

## Validation checklist

1. `validate_express_one_zone_bucket(bucket)` returns expected result  
2. `CheckpointStore.health_check()` succeeds against the Express bucket  
3. Chunked write + `track_paths` lists new `.parquet` keys under the table prefix  
4. Rollback deletes uncommitted keys (integration test in CI uses mocked S3)

Live Express validation: set `ICEGUARD_AWS_E2E=1` and use an Express bucket name — see [tests/e2e/README.md](../tests/e2e/README.md).
