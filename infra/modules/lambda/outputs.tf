output "api_function_url" {
  description = "The Function URL for the Triage API Lambda"
  value       = aws_lambda_function_url.api_function_url.function_url
}

output "processor_function_name" {
  description = "The name of the processor Lambda function"
  value       = aws_lambda_function.processor_function.function_name
}

output "api_function_name" {
  description = "The name of the API Lambda function"
  value       = aws_lambda_function.api_function.function_name
}
