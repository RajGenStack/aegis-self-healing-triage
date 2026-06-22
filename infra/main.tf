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
