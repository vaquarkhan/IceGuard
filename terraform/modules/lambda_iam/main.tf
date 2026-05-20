data "aws_iam_policy_document" "assume_lambda" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "iceguard_lambda" {
  name               = var.role_name
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
  tags               = var.tags
}

data "aws_iam_policy_document" "iceguard_lambda" {
  statement {
    sid    = "CheckpointBucket"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      var.checkpoint_bucket_arn,
      "${var.checkpoint_bucket_arn}/*",
    ]
  }

  dynamic "statement" {
    for_each = length(var.data_bucket_arns) > 0 ? [1] : []
    content {
      sid    = "DataBuckets"
      effect = "Allow"
      actions = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
      ]
      resources = flatten([
        for arn in var.data_bucket_arns : [arn, "${arn}/*"]
      ])
    }
  }

  dynamic "statement" {
    for_each = var.enable_cloudwatch_metrics ? [1] : []
    content {
      sid       = "CloudWatchMetrics"
      effect    = "Allow"
      actions   = ["cloudwatch:PutMetricData"]
      resources = ["*"]
    }
  }
}

resource "aws_iam_role_policy" "iceguard_lambda" {
  name   = "${var.role_name}-policy"
  role   = aws_iam_role.iceguard_lambda.id
  policy = data.aws_iam_policy_document.iceguard_lambda.json
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.iceguard_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
