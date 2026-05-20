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
