module "kms" {
  count  = var.enable_kms ? 1 : 0
  source = "../kms"

  name_prefix = var.name_prefix
  tags        = var.tags
}

locals {
  kms_key_arn              = var.enable_kms ? module.kms[0].key_arn : null
  checkpoint_bucket_arn    = "arn:aws:s3:::${var.checkpoint_bucket_name}"
  data_lake_bucket_arn     = var.data_lake_bucket_name != null ? "arn:aws:s3:::${var.data_lake_bucket_name}" : null
}

module "lambda_iam" {
  source = "../lambda_iam"

  role_name             = "${var.name_prefix}-writer"
  checkpoint_bucket_arn = local.checkpoint_bucket_arn
  data_bucket_arns      = compact([local.checkpoint_bucket_arn, local.data_lake_bucket_arn])
  tags                  = var.tags
}

module "checkpoint_bucket" {
  source = "../checkpoint_bucket"

  bucket_name                        = var.checkpoint_bucket_name
  kms_key_arn                        = local.kms_key_arn
  noncurrent_version_expiration_days = 90
  allowed_role_arns                  = [module.lambda_iam.role_arn]
  tags                               = var.tags
}

module "data_lake_bucket" {
  count  = var.data_lake_bucket_name != null ? 1 : 0
  source = "../data_lake_bucket"

  bucket_name       = var.data_lake_bucket_name
  kms_key_arn       = local.kms_key_arn
  allowed_role_arns = [module.lambda_iam.role_arn]
  tags              = var.tags
}

module "cloudwatch_dashboard" {
  source         = "../cloudwatch_dashboard"
  dashboard_name = "${var.name_prefix}-IceGuard"
}

module "cloudwatch_alarms" {
  count  = var.enable_alarms ? 1 : 0
  source = "../cloudwatch_alarms"

  alarm_name_prefix = var.name_prefix
  sns_topic_arn     = var.sns_alert_topic_arn
  tags              = var.tags
}

module "lambda_layer" {
  count  = var.deploy_lambda && var.lambda_artifact_bucket != null && var.lambda_layer_artifact_key != null ? 1 : 0
  source = "../lambda_layer"

  layer_name = "${var.name_prefix}-iceguard-deps"
  s3_bucket  = var.lambda_artifact_bucket
  s3_key     = var.lambda_layer_artifact_key
}

module "lambda_function" {
  count  = var.deploy_lambda && var.lambda_artifact_bucket != null && var.lambda_artifact_key != null ? 1 : 0
  source = "../lambda_function"

  function_name          = "${var.name_prefix}-writer"
  role_arn               = module.lambda_iam.role_arn
  s3_bucket              = var.lambda_artifact_bucket
  s3_key                 = var.lambda_artifact_key
  checkpoint_bucket_name = module.checkpoint_bucket.bucket_id
  layer_arns             = [module.lambda_layer[0].layer_arn]
  tags                   = var.tags
}
