variable "role_name" {
  type = string
}

variable "checkpoint_bucket_arn" {
  type = string
}

variable "data_bucket_arns" {
  description = "ARNs of lake data buckets the Lambda may read/write"
  type        = list(string)
  default     = []
}

variable "enable_cloudwatch_metrics" {
  type    = bool
  default = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
