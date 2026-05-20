resource "aws_lambda_function" "writer" {
  function_name = var.function_name
  role          = var.role_arn
  handler       = var.handler
  runtime       = var.runtime
  timeout       = var.timeout
  memory_size   = var.memory_size
  layers        = var.layer_arns

  s3_bucket = var.s3_bucket
  s3_key    = var.s3_key

  environment {
    variables = merge(
      {
        ICEGUARD_CHECKPOINT_BUCKET = var.checkpoint_bucket_name
        ICEGUARD_ROLLBACK_THRESHOLD_MS = "30000"
        ICEGUARD_CHECKPOINT_INTERVAL     = "5000"
      },
      var.environment,
    )
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "writer" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 30
  tags              = var.tags
}
