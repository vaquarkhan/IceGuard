# IceGuard

Reliability library for Spark-on-AWS-Lambda writes. Prevents silent data loss with timeout-aware rollback, resumable checkpointing, orphan cleanup, multi-Lambda coordination, and CloudWatch observability.

## Installation

```bash
pip install iceguard
```

## Quick Start

```python
import iceguard

with iceguard.protect(lambda_context):
    # Your existing Spark write code here
    df.write.format("iceberg").save("s3://lake/db/table")
```

## Features

- **Timeout-aware rollback**: Watchdog thread monitors Lambda remaining time and triggers format-native rollback before SIGKILL
- **Resumable checkpointing**: Persists progress to S3 Express One Zone for subsequent invocations to resume
- **Orphan cleanup**: Detects and removes uncommitted Parquet files from failed writes
- **Multi-Lambda coordination**: Two-phase commit protocol for atomic writes across multiple Lambdas
- **Observability**: CloudWatch metrics for write outcomes, near-misses, and checkpoint activity

## Requirements

- Python 3.9–3.12
- AWS Lambda execution environment
- boto3
