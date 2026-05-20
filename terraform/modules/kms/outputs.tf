output "key_arn" {
  value = aws_kms_key.iceguard.arn
}

output "key_id" {
  value = aws_kms_key.iceguard.key_id
}
