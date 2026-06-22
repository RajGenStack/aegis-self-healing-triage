# -----------------------------------------------------------------------------
# Packaging Lambda Functions
# -----------------------------------------------------------------------------
data "archive_file" "processor_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../../lambdas/triage_processor"
  output_path = "${path.module}/vitals_processor.zip"
}

data "archive_file" "api_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../../lambdas/dashboard_api"
  output_path = "${path.module}/triage_api.zip"
}

# -----------------------------------------------------------------------------
# Processor Lambda: SQS -> DynamoDB
# -----------------------------------------------------------------------------
resource "aws_iam_role" "processor_role" {
  name = "${var.resource_prefix}-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "processor_policy" {
  name        = "${var.resource_prefix}-processor-policy"
  description = "Permissions for processing SQS vitals events and writing to DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logs permissions
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      # SQS Queue consumer permissions
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.sqs_queue_arn
      },
      # DynamoDB Write permissions
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem"
        ]
        Resource = var.dynamodb_table_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "processor_attach" {
  role       = aws_iam_role.processor_role.name
  policy_arn = aws_iam_policy.processor_policy.arn
}

resource "aws_lambda_function" "processor_function" {
  filename         = data.archive_file.processor_zip.output_path
  source_code_hash = data.archive_file.processor_zip.output_base64sha256
  function_name    = "${var.resource_prefix}-vitals-processor"
  role             = aws_iam_role.processor_role.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 15

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.processor_attach
  ]
}

# Event Source Mapping connecting SQS Queue to Processor Lambda
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = var.sqs_queue_arn
  function_name    = aws_lambda_function.processor_function.arn
  batch_size       = 10
  enabled          = true
}

# -----------------------------------------------------------------------------
# API Lambda: Reads DynamoDB and Serves via Function URL
# -----------------------------------------------------------------------------
resource "aws_iam_role" "api_role" {
  name = "${var.resource_prefix}-api-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "api_policy" {
  name        = "${var.resource_prefix}-api-policy"
  description = "Permissions for reading patient scores from DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logs permissions
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      # DynamoDB Read permissions
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Scan",
          "dynamodb:Query"
        ]
        Resource = var.dynamodb_table_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_attach" {
  role       = aws_iam_role.api_role.name
  policy_arn = aws_iam_policy.api_policy.arn
}

resource "aws_lambda_function" "api_function" {
  filename         = data.archive_file.api_zip.output_path
  source_code_hash = data.archive_file.api_zip.output_base64sha256
  function_name    = "${var.resource_prefix}-triage-api"
  role             = aws_iam_role.api_role.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 10

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.api_attach
  ]
}

# Publicly exposed Lambda Function URL (CORS enabled)
resource "aws_lambda_function_url" "api_function_url" {
  function_name      = aws_lambda_function.api_function.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["*"]
    allow_headers     = ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token"]
    expose_headers    = ["*"]
    max_age           = 86400
  }
}

# Resource-based policies required to grant public access to the URL
resource "aws_lambda_permission" "allow_public_access_invoke" {
  statement_id           = "InvokeFunctionAllowPublicAccess"
  action                 = "lambda:InvokeFunction"
  function_name          = aws_lambda_function.api_function.function_name
  principal              = "*"
}
