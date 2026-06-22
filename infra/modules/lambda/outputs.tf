output "api_function_url" {
  description = "The Function URL for the Triage API Lambda"
  value       = aws_lambda_function_url.api_function_url.function_url
}
