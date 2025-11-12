# main.tf - Complete AWS infrastructure for Clinical Trials Platform

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ========== DATA SOURCES ==========

data "aws_availability_zones" "available" {
  state = "available"
}

# ========== NETWORKING ==========

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "clinical-trials-vpc"
    Environment = var.environment
    Project     = "clinical-trials"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "clinical-igw"
  }
}

# Public Subnets (for ALB)
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "clinical-public-${count.index + 1}"
  }
}

# Private Subnets (for EKS and RDS)
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "clinical-private-${count.index + 1}"
  }
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "clinical-public-rt"
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# NAT Gateway (for private subnets)
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "clinical-nat-eip"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "clinical-nat"
  }

  depends_on = [aws_internet_gateway.main]
}

# Private Route Table
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "clinical-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# ========== RDS POSTGRESQL ==========

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "clinical-db-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "clinical-db-subnet-group"
  }
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name   = "clinical-rds-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    description = "PostgreSQL from VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "clinical-rds-sg"
  }
}

# Random password for RDS
resource "random_password" "db_password" {
  length  = 16
  special = true
}

# RDS Instance
resource "aws_db_instance" "postgres" {
  identifier = "clinical-trials-db"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  allocated_storage     = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "clinical_trials"
  username = "clinical_user"
  password = random_password.db_password.result

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  multi_az = var.environment == "production" ? true : false

  performance_insights_enabled = true

  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "clinical-trials-final-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  tags = {
    Name        = "clinical-trials-postgres"
    Environment = var.environment
  }
}

# ========== ELASTICACHE REDIS ==========

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "clinical-cache-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "clinical-cache-subnet-group"
  }
}

# Security Group for Redis
resource "aws_security_group" "redis" {
  name   = "clinical-redis-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    description = "Redis from VPC"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "clinical-redis-sg"
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "clinical-redis"
  replication_group_description = "Redis cache for clinical trials"

  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_clusters   = var.environment == "production" ? 2 : 1

  port = 6379
  parameter_group_name = "default.redis7"

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  automatic_failover_enabled = var.environment == "production" ? true : false

  at_rest_encryption_enabled = true
  transit_encryption_enabled = false  # Set to true for production with auth token

  snapshot_retention_limit = 3
  snapshot_window         = "03:00-05:00"

  tags = {
    Name        = "clinical-redis"
    Environment = var.environment
  }
}

# ========== S3 BUCKETS ==========

# Random suffix for S3 bucket
resource "random_id" "bucket_suffix" {
  byte_length = 8
}

# Documents bucket
resource "aws_s3_bucket" "documents" {
  bucket = "clinical-trials-documents-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "clinical-documents"
    Environment = var.environment
  }
}

# Enable versioning
resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ========== SECRETS MANAGER ==========

# Store RDS password
resource "aws_secretsmanager_secret" "db_password" {
  name = "clinical-trials-db-password-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "clinical-db-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = "clinical_user"
    password = random_password.db_password.result
    host     = aws_db_instance.postgres.endpoint
    port     = 5432
    dbname   = "clinical_trials"
  })
}

# ========== OUTPUTS ==========

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = aws_elasticache_replication_group.redis.configuration_endpoint_address
}

output "s3_bucket_name" {
  description = "S3 bucket for documents"
  value       = aws_s3_bucket.documents.id
}

output "database_connection_string" {
  description = "Database connection string"
  value       = "postgresql://clinical_user:${random_password.db_password.result}@${aws_db_instance.postgres.endpoint}/clinical_trials"
  sensitive   = true
}

output "secrets_manager_arn" {
  description = "Secrets Manager ARN for database credentials"
  value       = aws_secretsmanager_secret.db_password.arn
}
