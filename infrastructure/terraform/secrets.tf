# AWS Secrets Manager for AI DriveThru

# OpenAI API Key Secret
resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "${local.project_name}-openai-api-key"
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
  name                    = "${local.project_name}-db-password"
  description             = "Database password for AI DriveThru"
  recovery_window_in_days = 7

  tags = local.common_tags
}

# Store database password in Secrets Manager
resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}
