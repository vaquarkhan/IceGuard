variable "alarm_name_prefix" {
  type = string
}

variable "namespace" {
  type    = string
  default = "iceguard"
}

variable "rollback_threshold" {
  type    = number
  default = 1
}

variable "sns_topic_arn" {
  type    = string
  default = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
