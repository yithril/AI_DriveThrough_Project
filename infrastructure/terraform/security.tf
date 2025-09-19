# Security Groups for AI DriveThru

# Security Group for ALB (Load Balancer)
resource "aws_security_group" "alb" {
  name_prefix = "${local.project_name}-alb-"
  vpc_id      = aws_vpc.main.id

  # Allow inbound HTTP from public internet
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow inbound HTTPS from public internet
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-alb-sg"
  })
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs" {
  name_prefix = "${local.project_name}-ecs-"
  vpc_id      = aws_vpc.main.id

  # Allow inbound from ALB
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Allow outbound to RDS
  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  # Allow outbound to S3 and Secrets Manager
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-ecs-sg"
  })
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name_prefix = "${local.project_name}-rds-"
  vpc_id      = aws_vpc.main.id

  # Allow inbound from ECS
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-rds-sg"
  })
}

# Security Group for Redis (DISABLED - Expensive!)
# resource "aws_security_group" "redis" {
#   name_prefix = "${local.project_name}-redis-"
#   vpc_id      = aws_vpc.main.id
#   ingress {
#     from_port   = 6379
#     to_port     = 6379
#     protocol    = "tcp"
#     cidr_blocks = ["10.0.0.0/16"]
#   }
#   tags = merge(local.common_tags, {
#     Name = "${local.project_name}-redis-sg"
#   })
# }

# Security Group for Amplify (Frontend)
resource "aws_security_group" "amplify" {
  name_prefix = "${local.project_name}-amplify-"
  vpc_id      = aws_vpc.main.id

  # Allow inbound HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow inbound HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-amplify-sg"
  })
}
