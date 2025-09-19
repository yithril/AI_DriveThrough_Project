# Outputs for AI DriveThru Infrastructure

# ECS Service URL (Direct Access)
output "backend_url" {
  description = "ECS backend URL (direct access)"
  value       = "Check ECS console for the public IP of the running task"
}

# S3 Static Website URL
output "frontend_url" {
  description = "Frontend URL (S3 Static Website)"
  value       = "https://${aws_s3_bucket.frontend.bucket}.s3-website.${var.aws_region}.amazonaws.com"
}

# Database Endpoint
output "database_endpoint" {
  description = "RDS Database endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

# S3 Bucket Name
output "s3_bucket_name" {
  description = "S3 bucket name for file storage"
  value       = aws_s3_bucket.main.bucket
}

# Redis Endpoint (DISABLED - Expensive!)
# output "redis_endpoint" {
#   description = "Redis endpoint (if enabled)"
#   value       = var.enable_redis ? aws_elasticache_replication_group.redis[0].configuration_endpoint_address : null
# }

# Secrets Manager ARNs
output "secrets_arns" {
  description = "Secrets Manager ARNs"
  value = {
    openai_api_key = aws_secretsmanager_secret.openai_api_key.arn
    db_password    = aws_secretsmanager_secret.db_password.arn
  }
  sensitive = true
}

# ECR Repository URL
output "ecr_repository_url" {
  description = "ECR repository URL for backend"
  value       = aws_ecr_repository.backend.repository_url
}
