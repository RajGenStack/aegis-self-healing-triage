module "sqs" {
  source          = "./modules/sqs"
  resource_prefix = var.resource_prefix
}

module "dynamodb" {
  source          = "./modules/dynamodb"
  resource_prefix = var.resource_prefix
}

module "lambda" {
  source              = "./modules/lambda"
  resource_prefix     = var.resource_prefix
  dynamodb_table_name = module.dynamodb.table_name
  dynamodb_table_arn  = module.dynamodb.table_arn
  sqs_queue_arn       = module.sqs.queue_arn
}

module "observability" {
  source                  = "./modules/observability"
  resource_prefix         = var.resource_prefix
  sqs_queue_name          = module.sqs.queue_name
  dynamodb_table_name     = module.dynamodb.table_name
  processor_function_name = module.lambda.processor_function_name
  api_function_name       = module.lambda.api_function_name
  alert_email             = var.alert_email
  aws_region              = var.aws_region
}
