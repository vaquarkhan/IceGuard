variable "name_prefix" {
  type        = string
  description = "Prefix for KMS key and alias"
}

variable "tags" {
  type    = map(string)
  default = {}
}
