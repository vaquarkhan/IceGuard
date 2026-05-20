output "layer_arn" {
  value = aws_lambda_layer_version.iceguard.arn
}

output "layer_version" {
  value = aws_lambda_layer_version.iceguard.version
}
