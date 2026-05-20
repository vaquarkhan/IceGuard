variable "name_prefix" {
  type = string
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "checkpoint_bucket_name" {
  type = string
}

variable "data_lake_bucket_name" {
  type    = string
  default = null
}

variable "enable_kms" {
  type    = bool
  default = true
}

variable "enable_alarms" {
  type    = bool
  default = true
}

variable "sns_alert_topic_arn" {
  type    = string
  default = null
}

variable "deploy_lambda" {
  type    = bool
  default = false
}

variable "lambda_artifact_bucket" {
  type    = string
  default = null
}

variable "lambda_artifact_key" {
  type    = string
  default = null
}

variable "lambda_layer_artifact_key" {
  type    = string
  default = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
