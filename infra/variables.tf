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
