# Variables for AI DriveThru Infrastructure

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ai-drivethru"
}

# Database variables
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

# App Runner variables
# ECS Configuration (replaces App Runner)
# ECS uses Fargate with auto-scaling - no variables needed

# Redis Configuration
variable "enable_redis" {
  description = "Enable ElastiCache Redis (set to false to save costs)"
  type        = bool
  default     = false
}

# GitHub Repository
variable "github_repository_url" {
  description = "GitHub repository URL for Amplify"
  type        = string
  default     = ""
}

variable "github_token" {
  description = "GitHub personal access token for Amplify"
  type        = string
  default     = ""
  sensitive   = true
}

# Domain variables (optional)
variable "domain_name" {
  description = "Custom domain name (optional)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "SSL certificate ARN (optional)"
  type        = string
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API key for AI services"
  type        = string
  default     = ""
  sensitive   = true
}