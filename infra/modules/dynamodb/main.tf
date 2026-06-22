resource "aws_dynamodb_table" "vitals_table" {
  name         = "${var.resource_prefix}-vitals-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "patient_id"
  range_key    = "timestamp"

  attribute {
    name = "patient_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  tags = {
    Environment = "production"
    Project     = var.resource_prefix
  }
}
