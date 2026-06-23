output "sqs_queue_url" {
  description = "URL of the Amazon SQS Queue for patient vitals ingestion"
  value       = module.sqs.queue_url
}

output "sqs_queue_arn" {
  description = "ARN of the Amazon SQS Queue"
  value       = module.sqs.queue_arn
}

output "dynamodb_table_name" {
  description = "Name of the Amazon DynamoDB table storing vitals data"
  value       = module.dynamodb.table_name
}

output "api_function_url" {
  description = "Public HTTP endpoint for the Patient Triage API"
  value       = module.lambda.api_function_url
}

output "cloudwatch_dashboard_name" {
  description = "Name of the CloudWatch dashboard for patient triage monitoring"
  value       = module.observability.dashboard_name
}

output "sns_alerts_topic_arn" {
  description = "ARN of the SNS topic for alarms"
  value       = module.observability.sns_topic_arn
}

output "processor_function_name" {
  description = "Name of the Vitals Processor Lambda function"
  value       = module.lambda.processor_function_name
}

output "api_function_name" {
  description = "Name of the Triage API Lambda function"
  value       = module.lambda.api_function_name
}
