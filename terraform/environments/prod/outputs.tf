output "checkpoint_bucket_name" {
  value = module.iceguard.checkpoint_bucket_name
}

output "data_lake_bucket_arn" {
  value = module.iceguard.data_lake_bucket_arn
}

output "lambda_role_arn" {
  value = module.iceguard.lambda_role_arn
}

output "kms_key_arn" {
  value = module.iceguard.kms_key_arn
}

output "cloudwatch_dashboard_name" {
  value = module.iceguard.dashboard_name
}
