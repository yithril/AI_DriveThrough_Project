# AWS Amplify for AI DriveThru Frontend

# Amplify App
resource "aws_amplify_app" "frontend" {
  count = var.github_repository_url != "" ? 1 : 0
  
  name       = "${local.project_name}-frontend"
  repository = var.github_repository_url
  
  # GitHub token for authentication
  access_token = var.github_token

  # Build settings
  build_spec = file("${path.module}/amplify-buildspec.yml")

  # Environment variables
  environment_variables = {
    NEXT_PUBLIC_API_URL = "http://${aws_lb.main.dns_name}"
    NEXT_PUBLIC_ENVIRONMENT = var.environment
  }

  # Custom rules for SPA routing
  custom_rule {
    source = "/<*>"
    status = "404"
    target = "/index.html"
  }

  # Enable auto branch creation
  auto_branch_creation_patterns = [
    "*",
    "*/**",
  ]

  auto_branch_creation_config {
    enable_auto_build = true
  }

  tags = local.common_tags
}

# Amplify Branch (main)
resource "aws_amplify_branch" "main" {
  count = var.github_repository_url != "" ? 1 : 0
  
  app_id      = aws_amplify_app.frontend[0].id
  branch_name = "main"

  # Enable auto build
  enable_auto_build = true

  # Environment variables
  environment_variables = {
    NEXT_PUBLIC_API_URL = "http://${aws_lb.main.dns_name}"
  }

  tags = local.common_tags
}

# Amplify Domain Association (if custom domain provided)
resource "aws_amplify_domain_association" "main" {
  count = var.domain_name != "" ? 1 : 0

  app_id      = aws_amplify_app.frontend[0].id
  domain_name = var.domain_name

  sub_domain {
    branch_name = aws_amplify_branch.main[0].branch_name
    prefix      = ""
  }

  sub_domain {
    branch_name = aws_amplify_branch.main[0].branch_name
    prefix      = "www"
  }
}
