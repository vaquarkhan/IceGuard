resource "aws_kms_key" "iceguard" {
  description             = "IceGuard checkpoint and lake encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = merge(var.tags, { Name = "${var.name_prefix}-iceguard" })
}

resource "aws_kms_alias" "iceguard" {
  name          = "alias/${var.name_prefix}-iceguard"
  target_key_id = aws_kms_key.iceguard.key_id
}

resource "aws_kms_key_policy" "iceguard" {
  key_id = aws_kms_key.iceguard.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableRootPermissions"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
    ]
  })
}

data "aws_caller_identity" "current" {}
