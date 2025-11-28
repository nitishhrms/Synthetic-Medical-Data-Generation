# ecr.tf - Elastic Container Registry for all microservices

# ========== ECR REPOSITORIES ==========

locals {
  services = [
    "api-gateway",
    "edc-service",
    "data-generation-service",
    "analytics-service",
    "quality-service",
    "security-service",
    "daft-analytics-service"
  ]
}

# Create ECR repository for each microservice
resource "aws_ecr_repository" "services" {
  for_each = toset(local.services)

  name                 = "clinical-trials/${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true  # Automatic security scanning
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name        = "clinical-${each.key}"
    Environment = var.environment
    Service     = each.key
  }
}

# Lifecycle policy to keep only recent images
resource "aws_ecr_lifecycle_policy" "services" {
  for_each   = aws_ecr_repository.services
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ========== ECR PULL-THROUGH CACHE (Optional - for base images) ==========

# Disabled - requires Docker Hub credentials in Secrets Manager
# resource "aws_ecr_pull_through_cache_rule" "dockerhub" {
#   ecr_repository_prefix = "docker-hub"
#   upstream_registry_url = "registry-1.docker.io"
# }

# ========== IAM POLICY FOR CI/CD ==========

# IAM policy for GitHub Actions or CI/CD to push images
resource "aws_iam_user" "ecr_push" {
  name = "clinical-trials-ecr-push"

  tags = {
    Name        = "clinical-ecr-push-user"
    Environment = var.environment
  }
}

resource "aws_iam_user_policy" "ecr_push" {
  name = "clinical-ecr-push-policy"
  user = aws_iam_user.ecr_push.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:DescribeRepositories",
          "ecr:ListImages"
        ]
        Resource = "*"
      }
    ]
  })
}

# Create access key for CI/CD (GitHub Actions)
resource "aws_iam_access_key" "ecr_push" {
  user = aws_iam_user.ecr_push.name
}

# ========== OUTPUTS ==========

output "ecr_repositories" {
  description = "Map of ECR repository URLs"
  value = {
    for name, repo in aws_ecr_repository.services :
    name => repo.repository_url
  }
}

output "ecr_registry_url" {
  description = "ECR registry URL"
  value       = split("/", values(aws_ecr_repository.services)[0].repository_url)[0]
}

output "ecr_login_command" {
  description = "Command to login to ECR"
  value       = "aws ecr get-login-password --region ${var.aws_region} --profile terraform-developer | docker login --username AWS --password-stdin ${split("/", values(aws_ecr_repository.services)[0].repository_url)[0]}"
}

output "ecr_push_access_key_id" {
  description = "Access key ID for CI/CD to push to ECR"
  value       = aws_iam_access_key.ecr_push.id
  sensitive   = false
}

output "ecr_push_secret_access_key" {
  description = "Secret access key for CI/CD to push to ECR"
  value       = aws_iam_access_key.ecr_push.secret
  sensitive   = true
}

output "docker_build_and_push_example" {
  description = "Example commands to build and push images"
  value = <<-EOT
    # Login to ECR
    aws ecr get-login-password --region ${var.aws_region} --profile terraform-developer | docker login --username AWS --password-stdin ${split("/", values(aws_ecr_repository.services)[0].repository_url)[0]}

    # Build and push example (API Gateway)
    docker build -t ${aws_ecr_repository.services["api-gateway"].repository_url}:latest ./api-gateway
    docker push ${aws_ecr_repository.services["api-gateway"].repository_url}:latest

    # Or use docker compose with specific image tags
    docker-compose build
    docker tag your-local-image:latest ${aws_ecr_repository.services["api-gateway"].repository_url}:v1.0.0
    docker push ${aws_ecr_repository.services["api-gateway"].repository_url}:v1.0.0
  EOT
}
