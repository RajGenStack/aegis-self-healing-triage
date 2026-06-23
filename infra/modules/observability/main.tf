# -----------------------------------------------------------------------------
# SNS Topic for Alarms
# -----------------------------------------------------------------------------
resource "aws_sns_topic" "alerts" {
  name = "${var.resource_prefix}-alerts-topic"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms: SQS Queue
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "sqs_backlog" {
  alarm_name          = "${var.resource_prefix}-sqs-backlog-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Maximum"
  threshold           = 50
  alarm_description   = "Alarm when SQS queue backlog is high (messages visible > 50 for 2 consecutive minutes)"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    QueueName = var.sqs_queue_name
  }
}

resource "aws_cloudwatch_metric_alarm" "sqs_latency" {
  alarm_name          = "${var.resource_prefix}-sqs-latency-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Maximum"
  threshold           = 60
  alarm_description   = "Alarm when SQS messages are older than 60 seconds (indicates processing delays)"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    QueueName = var.sqs_queue_name
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms: Processor Lambda (SQS -> DynamoDB)
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "processor_errors" {
  alarm_name          = "${var.resource_prefix}-processor-errors-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alarm when the Vitals Processor Lambda encounters any errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = var.processor_function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "processor_duration" {
  alarm_name          = "${var.resource_prefix}-processor-duration-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Average"
  threshold           = 5000
  alarm_description   = "Alarm when the Vitals Processor Lambda average duration exceeds 5 seconds"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = var.processor_function_name
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms: API Lambda
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "api_errors" {
  alarm_name          = "${var.resource_prefix}-api-errors-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 2
  alarm_description   = "Alarm when the Dashboard API Lambda encounters more than 2 errors in 5 minutes"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = var.api_function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "api_duration" {
  alarm_name          = "${var.resource_prefix}-api-duration-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = 3000
  alarm_description   = "Alarm when the Dashboard API Lambda average duration exceeds 3 seconds"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = var.api_function_name
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms: DynamoDB Table
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "dynamodb_write_throttling" {
  alarm_name          = "${var.resource_prefix}-dynamodb-write-throttling-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "WriteThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alarm when DynamoDB table experiences write throttling events"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    TableName = var.dynamodb_table_name
  }
}

resource "aws_cloudwatch_metric_alarm" "dynamodb_read_throttling" {
  alarm_name          = "${var.resource_prefix}-dynamodb-read-throttling-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ReadThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alarm when DynamoDB table experiences read throttling events"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    TableName = var.dynamodb_table_name
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Dashboard
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_dashboard" "dashboard" {
  dashboard_name = "${var.resource_prefix}-triage-dashboard"

  dashboard_body = <<EOF
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", "${var.sqs_queue_name}", { "yAxis": "left" } ],
          [ "AWS/SQS", "ApproximateAgeOfOldestMessage", "QueueName", "${var.sqs_queue_name}", { "yAxis": "right" } ]
        ],
        "period": 60,
        "stat": "Maximum",
        "region": "${var.aws_region}",
        "title": "SQS Queue Backlog & Message Age"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/SQS", "NumberOfMessagesSent", "QueueName", "${var.sqs_queue_name}" ],
          [ "AWS/SQS", "NumberOfMessagesReceived", "QueueName", "${var.sqs_queue_name}" ]
        ],
        "period": 60,
        "stat": "Sum",
        "region": "${var.aws_region}",
        "title": "SQS Queue Message Throughput"
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 8,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Invocations", "FunctionName", "${var.processor_function_name}", { "stat": "Sum" } ],
          [ "AWS/Lambda", "Errors", "FunctionName", "${var.processor_function_name}", { "stat": "Sum", "color": "#d13212" } ]
        ],
        "period": 60,
        "region": "${var.aws_region}",
        "title": "Processor Lambda Invocations & Errors"
      }
    },
    {
      "type": "metric",
      "x": 8,
      "y": 6,
      "width": 8,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Duration", "FunctionName", "${var.processor_function_name}", { "stat": "Average" } ],
          [ "AWS/Lambda", "Duration", "FunctionName", "${var.processor_function_name}", { "stat": "p95" } ],
          [ "AWS/Lambda", "Duration", "FunctionName", "${var.processor_function_name}", { "stat": "Maximum" } ]
        ],
        "period": 60,
        "region": "${var.aws_region}",
        "title": "Processor Lambda Duration (ms)"
      }
    },
    {
      "type": "metric",
      "x": 16,
      "y": 6,
      "width": 8,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Throttles", "FunctionName", "${var.processor_function_name}", { "stat": "Sum" } ]
        ],
        "period": 60,
        "region": "${var.aws_region}",
        "title": "Processor Lambda Throttles"
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 12,
      "width": 8,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Invocations", "FunctionName", "${var.api_function_name}", { "stat": "Sum" } ],
          [ "AWS/Lambda", "Errors", "FunctionName", "${var.api_function_name}", { "stat": "Sum", "color": "#d13212" } ]
        ],
        "period": 60,
        "region": "${var.aws_region}",
        "title": "API Lambda Invocations & Errors"
      }
    },
    {
      "type": "metric",
      "x": 8,
      "y": 12,
      "width": 8,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Duration", "FunctionName", "${var.api_function_name}", { "stat": "Average" } ],
          [ "AWS/Lambda", "Duration", "FunctionName", "${var.api_function_name}", { "stat": "p95" } ],
          [ "AWS/Lambda", "Duration", "FunctionName", "${var.api_function_name}", { "stat": "Maximum" } ]
        ],
        "period": 60,
        "region": "${var.aws_region}",
        "title": "API Lambda Duration (ms)"
      }
    },
    {
      "type": "metric",
      "x": 16,
      "y": 12,
      "width": 8,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Throttles", "FunctionName", "${var.api_function_name}", { "stat": "Sum" } ]
        ],
        "period": 60,
        "region": "${var.aws_region}",
        "title": "API Lambda Throttles"
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 18,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", "${var.dynamodb_table_name}", { "stat": "Sum" } ],
          [ "AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "${var.dynamodb_table_name}", { "stat": "Sum" } ]
        ],
        "period": 60,
        "region": "${var.aws_region}",
        "title": "DynamoDB Consumed Capacity"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 18,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/DynamoDB", "WriteThrottleEvents", "TableName", "${var.dynamodb_table_name}", { "stat": "Sum" } ],
          [ "AWS/DynamoDB", "ReadThrottleEvents", "TableName", "${var.dynamodb_table_name}", { "stat": "Sum" } ],
          [ "AWS/DynamoDB", "SystemErrors", "TableName", "${var.dynamodb_table_name}", { "stat": "Sum", "color": "#d13212" } ],
          [ "AWS/DynamoDB", "UserErrors", "TableName", "${var.dynamodb_table_name}", { "stat": "Sum" } ]
        ],
        "period": 60,
        "region": "${var.aws_region}",
        "title": "DynamoDB Throttling & Errors"
      }
    }
  ]
}
EOF
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "dashboard_name" {
  description = "The name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.dashboard.dashboard_name
}

output "sns_topic_arn" {
  description = "The ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}
