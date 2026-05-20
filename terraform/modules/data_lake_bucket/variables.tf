variable "bucket_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "kms_key_arn" {
  type    = string
  default = null
}

variable "allowed_role_arns" {
  type    = list(string)
  default = []
}
