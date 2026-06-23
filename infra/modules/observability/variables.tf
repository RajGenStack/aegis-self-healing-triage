variable "resource_prefix" {
  type        = string
  description = "Prefix for naming resources to ensure uniqueness"
}

variable "sqs_queue_name" {
  type        = string
  description = "Name of the SQS Queue to monitor"
}

variable "dynamodb_table_name" {
  type        = string
  description = "Name of the DynamoDB table to monitor"
}

variable "processor_function_name" {
  type        = string
  description = "Name of the processor Lambda function to monitor"
}

variable "api_function_name" {
  type        = string
  description = "Name of the API Lambda function to monitor"
}

variable "alert_email" {
  type        = string
  description = "Email address to subscribe to SNS alerts"
  default     = ""
}

variable "aws_region" {
  type        = string
  description = "The AWS region where resources are deployed"
  default     = "us-east-1"
}
