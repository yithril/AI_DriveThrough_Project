# ECS Fargate Configuration for AI DriveThru Backend

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${local.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.common_tags
}

# ECS Task Definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.project_name}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256  # 0.25 vCPU
  memory                   = 512  # 0.5 GB
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "${aws_ecr_repository.backend.repository_url}:latest"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "DATABASE_URL"
          value = "postgresql://postgres:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/ai_drivethru"
        },
        {
          name  = "REDIS_URL"
          value = ""  # Redis disabled to save costs
        },
        {
          name  = "S3_BUCKET"
          value = aws_s3_bucket.main.bucket
        },
        {
          name  = "S3_REGION"
          value = var.aws_region
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "DEBUG"
          value = "False"
        },
        {
          name  = "LOG_LEVEL"
          value = "INFO"
        },
        {
          name  = "JWT_SECRET"
          value = var.jwt_secret
        },
        {
          name  = "NEXTAUTH_SECRET"
          value = var.nextauth_secret
        },
        {
          name  = "NEXTAUTH_URL"
          value = "https://ai-drivethru-frontend.s3-website.us-east-2.amazonaws.com"
        }
      ]

      secrets = [
        {
          name      = "OPENAI_API_KEY"
          valueFrom = aws_secretsmanager_secret.openai_api_key.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = local.common_tags
}

# ECS Service
resource "aws_ecs_service" "backend" {
  name            = "${local.project_name}-backend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  
  # Enable ECS Exec for running commands inside containers
  enable_execute_command = true

  network_configuration {
    subnets          = aws_subnet.public[*].id  # Use public subnets for direct access
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true  # Enable public IP for direct access
  }

  tags = local.common_tags
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = 0  # Scale to zero when idle
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = local.common_tags
}

# Auto Scaling Policy - Scale Out
resource "aws_appautoscaling_policy" "ecs_scale_out" {
  name               = "${local.project_name}-ecs-scale-out"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 70.0

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# Auto Scaling Policy - Scale In
resource "aws_appautoscaling_policy" "ecs_scale_in" {
  name               = "${local.project_name}-ecs-scale-in"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 30.0

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${local.project_name}"
  retention_in_days = 7

  tags = local.common_tags
}
