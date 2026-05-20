output "bucket_id" {
  value = aws_s3_bucket.checkpoints.id
}

output "bucket_arn" {
  value = aws_s3_bucket.checkpoints.arn
}
