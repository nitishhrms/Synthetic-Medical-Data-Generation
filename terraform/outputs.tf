# outputs.tf - Terraform outputs

output "deployment_info" {
  description = "Complete deployment information"
  value = {
    environment  = var.environment
    region       = var.aws_region
    rds_endpoint = aws_db_instance.postgres.endpoint
    redis_endpoint = aws_elasticache_replication_group.redis.configuration_endpoint_address
    s3_bucket    = aws_s3_bucket.documents.id
    vpc_id       = aws_vpc.main.id
  }
}

output "connection_commands" {
  description = "Commands to connect to services"
  value = <<-EOT
    # PostgreSQL Connection
    export DATABASE_URL="postgresql://clinical_user:${random_password.db_password.result}@${aws_db_instance.postgres.endpoint}/clinical_trials"

    # Redis Connection
    export REDIS_HOST="${aws_elasticache_replication_group.redis.configuration_endpoint_address}"
    export REDIS_PORT="6379"

    # S3 Bucket
    export S3_BUCKET="${aws_s3_bucket.documents.id}"

    # Test PostgreSQL connection
    psql "$DATABASE_URL"

    # Test Redis connection
    redis-cli -h $REDIS_HOST -p $REDIS_PORT ping
  EOT
  sensitive = true
}

output "quick_start_guide" {
  description = "Quick start guide for using the infrastructure"
  value = <<-EOT
    ===== AWS Infrastructure Deployed Successfully =====

    1. Database Connection:
       Host: ${aws_db_instance.postgres.endpoint}
       Database: clinical_trials
       User: clinical_user
       Password: (stored in AWS Secrets Manager)

    2. Redis Cache:
       Endpoint: ${aws_elasticache_replication_group.redis.configuration_endpoint_address}:6379

    3. S3 Storage:
       Bucket: ${aws_s3_bucket.documents.id}

    4. Next Steps:
       - Update your microservices with these endpoints
       - Initialize database: psql < database/init.sql
       - Deploy your services to EKS or EC2
       - Configure environment variables

    5. Get database password:
       aws secretsmanager get-secret-value --secret-id ${aws_secretsmanager_secret.db_password.name} --query SecretString --output text
  EOT
}
