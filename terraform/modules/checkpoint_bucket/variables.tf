variable "bucket_name" {
  description = "Globally unique S3 bucket name for IceGuard checkpoints"
  type        = string
}

variable "tags" {
  description = "Tags applied to all resources"
  type        = map(string)
  default     = {}
}

variable "noncurrent_version_expiration_days" {
  description = "Expire noncurrent object versions after N days"
  type        = number
  default     = 90
}

variable "kms_key_arn" {
  description = "Optional KMS key ARN for bucket encryption"
  type        = string
  default     = null
}

variable "access_logs_bucket_id" {
  description = "Optional S3 access logs target bucket id"
  type        = string
  default     = null
}

variable "allowed_role_arns" {
  description = "IAM role ARNs allowed to access this bucket (bucket policy)"
  type        = list(string)
  default     = []
}
