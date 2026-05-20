output "checkpoint_bucket_name" {
  value = module.checkpoint_bucket.bucket_id
}

output "checkpoint_bucket_arn" {
  value = module.checkpoint_bucket.bucket_arn
}

output "data_lake_bucket_arn" {
  value = var.data_lake_bucket_name != null ? module.data_lake_bucket[0].bucket_arn : null
}

output "lambda_role_arn" {
  value = module.lambda_iam.role_arn
}

output "kms_key_arn" {
  value = var.enable_kms ? module.kms[0].key_arn : null
}

output "dashboard_name" {
  value = module.cloudwatch_dashboard.dashboard_name
}

output "lambda_function_arn" {
  value = length(module.lambda_function) > 0 ? module.lambda_function[0].function_arn : null
}

output "lambda_layer_arn" {
  value = length(module.lambda_layer) > 0 ? module.lambda_layer[0].layer_arn : null
}
