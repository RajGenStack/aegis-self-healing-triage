variable "aws_region" {
  type        = string
  description = "The AWS region to deploy resources into"
  default     = "us-east-1"
}

variable "resource_prefix" {
  type        = string
  description = "Prefix for naming resources to ensure uniqueness"
  default     = "rajgenstack-triage"
}

variable "alert_email" {
  type        = string
  description = "Email address for SNS alert subscriptions. If left blank, no subscription is created."
  default     = ""
}
