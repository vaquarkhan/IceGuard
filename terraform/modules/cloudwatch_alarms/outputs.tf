output "rollback_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.rollback_spike.arn
}

output "near_miss_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.near_miss.arn
}
