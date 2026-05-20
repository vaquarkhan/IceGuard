resource "aws_cloudwatch_dashboard" "iceguard" {
  dashboard_name = var.dashboard_name
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Write outcomes"
          region = "us-east-1"
          metrics = [
            [var.namespace, "WriteOutcome", "Outcome", "success"],
            [".", ".", ".", "rollback"],
          ]
          stat   = "Sum"
          period = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Watchdog near-miss (remaining ms)"
          region = "us-east-1"
          metrics = [[var.namespace, "NearMiss"]]
          stat   = "SampleCount"
          period = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Orphan scan"
          region = "us-east-1"
          metrics = [
            [var.namespace, "OrphanScanFound"],
            [var.namespace, "OrphanScanDeleted"],
          ]
          stat   = "Sum"
          period = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Checkpoint resume (records skipped)"
          region = "us-east-1"
          metrics = [[var.namespace, "CheckpointResume"]]
          stat   = "Sum"
          period = 300
        }
      },
    ]
  })
}
