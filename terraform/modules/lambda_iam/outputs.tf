output "role_arn" {
  value = aws_iam_role.iceguard_lambda.arn
}

output "role_name" {
  value = aws_iam_role.iceguard_lambda.name
}
