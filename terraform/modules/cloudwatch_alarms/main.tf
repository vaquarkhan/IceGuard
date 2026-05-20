resource "aws_cloudwatch_metric_alarm" "rollback_spike" {
  alarm_name          = "${var.alarm_name_prefix}-rollback-spike"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "WriteOutcome"
  namespace           = var.namespace
  period              = 300
  statistic           = "Sum"
  threshold           = var.rollback_threshold
  alarm_description   = "IceGuard rollback outcomes exceeded threshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    Outcome = "rollback"
  }

  alarm_actions = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
  ok_actions    = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
  tags          = var.tags
}

resource "aws_cloudwatch_metric_alarm" "near_miss" {
  alarm_name          = "${var.alarm_name_prefix}-near-miss"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "NearMiss"
  namespace           = var.namespace
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "IceGuard watchdog near-miss events detected"
  treat_missing_data  = "notBreaching"

  alarm_actions = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
  tags          = var.tags
}
