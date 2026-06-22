output "queue_url" {
  description = "The URL of the vitals queue"
  value       = aws_sqs_queue.vitals_queue.id
}

output "queue_arn" {
  description = "The ARN of the vitals queue"
  value       = aws_sqs_queue.vitals_queue.arn
}
