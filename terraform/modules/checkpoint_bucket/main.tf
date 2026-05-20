resource "aws_s3_bucket" "checkpoints" {
  bucket = var.bucket_name
  tags   = merge(var.tags, { Component = "iceguard-checkpoints" })
}

resource "aws_s3_bucket_versioning" "checkpoints" {
  bucket = aws_s3_bucket.checkpoints.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "checkpoints" {
  bucket = aws_s3_bucket.checkpoints.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = var.kms_key_arn != null ? true : null
  }
}

resource "aws_s3_bucket_public_access_block" "checkpoints" {
  bucket                  = aws_s3_bucket.checkpoints.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "checkpoints" {
  bucket = aws_s3_bucket.checkpoints.id
  rule {
    id     = "expire-noncurrent"
    status = "Enabled"
    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }
}

resource "aws_s3_bucket_logging" "checkpoints" {
  count  = var.access_logs_bucket_id != null ? 1 : 0
  bucket = aws_s3_bucket.checkpoints.id

  target_bucket = var.access_logs_bucket_id
  target_prefix = "checkpoints/"
}

resource "aws_s3_bucket_policy" "checkpoints" {
  count  = length(var.allowed_role_arns) > 0 ? 1 : 0
  bucket = aws_s3_bucket.checkpoints.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowIceGuardRoles"
        Effect    = "Allow"
        Principal = { AWS = var.allowed_role_arns }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
        ]
        Resource = [
          aws_s3_bucket.checkpoints.arn,
          "${aws_s3_bucket.checkpoints.arn}/*",
        ]
      },
    ]
  })
}
