# Lambda Durable Execution

AWS Lambda **Durable Functions** provide checkpoint/replay semantics for long-running workflows.

IceGuard bridges S3 checkpoints (durable across invocations) with the runtime durable checkpoint API:

```python
with iceguard.protect(
    context,
    s3_bucket="checkpoints-bucket",
    durable_context=durable_execution_context,
) as writer:
    writer.write(...)
```

`DurableCheckpointBridge`:

1. Always writes to S3 via `CheckpointStore`
2. Calls `durable_context.checkpoint(payload)` when available
3. On resume, loads from S3 first, then `restore_checkpoint()` fallback

If the durable API is absent, behavior degrades to S3-only checkpoints (existing IceGuard semantics).
