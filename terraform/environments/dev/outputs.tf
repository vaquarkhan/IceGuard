output "checkpoint_bucket_name" {
  value = module.checkpoint_bucket.bucket_id
}

output "lambda_role_arn" {
  value = module.lambda_iam.role_arn
}

output "cloudwatch_dashboard_name" {
  value = module.cloudwatch_dashboard.dashboard_name
}
