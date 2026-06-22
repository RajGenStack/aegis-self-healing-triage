resource "aws_sqs_queue" "vitals_queue" {
  name                       = "${var.resource_prefix}-vitals-queue"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 86400
}
