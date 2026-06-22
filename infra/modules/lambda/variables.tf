variable "resource_prefix" {
  type        = string
  description = "Prefix for naming resources to ensure uniqueness"
}

variable "dynamodb_table_name" {
  type        = string
  description = "The name of the DynamoDB table"
}

variable "dynamodb_table_arn" {
  type        = string
  description = "The ARN of the DynamoDB table"
}

variable "sqs_queue_arn" {
  type        = string
  description = "The ARN of the SQS queue"
}
