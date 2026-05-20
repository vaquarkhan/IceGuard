variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type = string
}

variable "checkpoint_bucket_name" {
  type = string
}

variable "data_bucket_arns" {
  type = list(string)
}
