# AWS Secrets Manager for AI DriveThru

# OpenAI API Key Secret
resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "${local.project_name}-openai-api-key-v2"
  description             = "OpenAI API Key for AI DriveThru"
  recovery_window_in_days = 7

  tags = local.common_tags
}

# JWT Secret (removed - not needed for demo)
# resource "aws_secretsmanager_secret" "jwt_secret" {
#   name                    = "${local.project_name}-jwt-secret"
#   description             = "JWT Secret for AI DriveThru"
#   recovery_window_in_days = 7

#   tags = local.common_tags
# }

# Database Password Secret
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${local.project_name}-db-password-v2"
  description             = "Database password for AI DriveThru"
  recovery_window_in_days = 7

  tags = local.common_tags
}

# Store database password in Secrets Manager
resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# Store OpenAI API Key in Secrets Manager
# Uses environment variable for security
resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key != "" ? var.openai_api_key : "your-openai-api-key-here"
}
