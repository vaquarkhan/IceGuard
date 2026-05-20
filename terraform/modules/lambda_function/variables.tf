variable "function_name" {
  type = string
}

variable "role_arn" {
  type = string
}

variable "handler" {
  type    = string
  default = "handler.lambda_handler"
}

variable "runtime" {
  type    = string
  default = "python3.12"
}

variable "timeout" {
  type    = number
  default = 900
}

variable "memory_size" {
  type    = number
  default = 3008
}

variable "s3_bucket" {
  type = string
}

variable "s3_key" {
  type = string
}

variable "layer_arns" {
  type    = list(string)
  default = []
}

variable "checkpoint_bucket_name" {
  type = string
}

variable "environment" {
  type    = map(string)
  default = {}
}

variable "tags" {
  type    = map(string)
  default = {}
}
