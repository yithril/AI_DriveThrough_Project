# One-time migration task for database updates
resource "aws_ecs_task_definition" "migration" {
  family                   = "${local.project_name}-migration"
  cpu                      = "256"
  memory                   = "512"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name        = "migration"
      image       = "${aws_ecr_repository.backend.repository_url}:latest"
      cpu         = 256
      memory      = 512
      essential   = true
      environment = [
        { name = "DATABASE_URL", value = "postgresql://postgres:${random_password.db_password.result}@${aws_db_instance.main.endpoint}:5432/ai_drivethru" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "ENVIRONMENT", value = var.environment }
      ]
      secrets = [
        { name = "OPENAI_API_KEY", valueFrom = aws_secretsmanager_secret.openai_api_key.arn },
      ]
      command = ["poetry", "run", "alembic", "upgrade", "head"]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ai-drivethru-migration"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
  tags = local.common_tags
}

# CloudWatch Log Group for Migration Tasks
resource "aws_cloudwatch_log_group" "migration" {
  name              = "/ecs/${local.project_name}-migration"
  retention_in_days = 7
  tags              = local.common_tags
}
