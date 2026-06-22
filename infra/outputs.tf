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
