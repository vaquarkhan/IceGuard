# checkpoint_bucket

Creates a versioned, encrypted S3 bucket for IceGuard checkpoint JSON objects.

## Inputs

- `bucket_name` (required)
- `tags` (optional)
- `noncurrent_version_expiration_days` (default 90)

## Outputs

- `bucket_id`, `bucket_arn`
