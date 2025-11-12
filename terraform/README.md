# AWS Infrastructure with Terraform

This directory contains Terraform configuration for deploying the Clinical Trials platform to AWS.

## Prerequisites

1. **Install Terraform**
   ```bash
   brew install terraform  # macOS
   # or
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

2. **Install AWS CLI**
   ```bash
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

3. **Configure AWS Credentials**
   ```bash
   aws configure
   # Enter your AWS Access Key ID
   # Enter your AWS Secret Access Key
   # Region: us-east-1
   # Output format: json
   ```

## Quick Start

### 1. Initialize Terraform
```bash
cd terraform/
terraform init
```

### 2. Review the Plan
```bash
terraform plan
```

### 3. Deploy Infrastructure
```bash
terraform apply
# Type 'yes' to confirm
```

### 4. Get Outputs
```bash
terraform output
terraform output -json > outputs.json
terraform output database_connection_string
```

## What Gets Deployed

### Free Tier Eligible Resources
- **VPC**: Custom VPC with public/private subnets
- **RDS PostgreSQL**: db.t3.micro (750 hours/month free)
- **ElastiCache Redis**: cache.t3.micro (750 hours/month free)
- **S3 Bucket**: Document storage (5 GB free)
- **NAT Gateway**: For private subnet internet access
- **Secrets Manager**: Secure credential storage

### Estimated Monthly Cost
- **Development**: $0-30 (mostly free tier)
- **Production**: $50-150 (with Multi-AZ and larger instances)

## Environment Variables

### Development
```bash
terraform apply -var="environment=development"
```

### Production
```bash
terraform apply -var="environment=production" -var="db_instance_class=db.t3.medium"
```

## Post-Deployment Steps

### 1. Initialize Database
```bash
# Get database endpoint
export DB_ENDPOINT=$(terraform output -raw rds_endpoint)

# Get password from Secrets Manager
export DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id $(terraform output -raw secrets_manager_arn) \
  --query SecretString --output text | jq -r .password)

# Initialize schema
export DATABASE_URL="postgresql://clinical_user:$DB_PASSWORD@$DB_ENDPOINT/clinical_trials"
psql $DATABASE_URL < ../database/init.sql
```

### 2. Test Connections
```bash
# Test PostgreSQL
psql $DATABASE_URL -c "SELECT version();"

# Test Redis
export REDIS_HOST=$(terraform output -raw redis_endpoint)
redis-cli -h $REDIS_HOST ping
```

### 3. Update Microservices
Update environment variables in your services:
```bash
export DATABASE_URL="postgresql://clinical_user:PASSWORD@ENDPOINT/clinical_trials"
export REDIS_HOST="your-redis-endpoint"
export S3_BUCKET="your-bucket-name"
```

## Destroying Infrastructure

**WARNING**: This will delete all resources and data!

```bash
terraform destroy
# Type 'yes' to confirm
```

## Cost Optimization Tips

1. **Use Free Tier**
   - db.t3.micro for RDS (750 hours/month free)
   - cache.t3.micro for Redis (750 hours/month free)
   - Stop services when not in use

2. **Single-AZ for Development**
   - Set `environment=development` to use single-AZ
   - Use Multi-AZ only for production

3. **Scheduled Scaling**
   - Use AWS Auto Scaling schedules
   - Turn off non-production environments overnight

4. **Monitoring**
   - Enable AWS Cost Explorer
   - Set billing alerts

## Troubleshooting

### Issue: "Error creating DB Instance"
- Check if you have available DB subnet groups
- Verify VPC has at least 2 subnets in different AZs

### Issue: "Resource already exists"
- Run `terraform import` for existing resources
- Or use different resource names

### Issue: "Insufficient permissions"
- Ensure your AWS IAM user has required permissions:
  - AmazonRDSFullAccess
  - AmazonElastiCacheFullAccess
  - AmazonS3FullAccess
  - AmazonVPCFullAccess

## Security Best Practices

1. **Never commit secrets**
   - Use AWS Secrets Manager
   - Use environment variables
   - Add `*.tfvars` to `.gitignore`

2. **Enable encryption**
   - RDS encryption at rest ✓
   - S3 encryption ✓
   - Redis transit encryption (optional)

3. **Network security**
   - Use private subnets for databases ✓
   - Restrict security group rules ✓
   - Use VPN or bastion host for access

## Support

For issues or questions:
- Check Terraform docs: https://www.terraform.io/docs
- AWS Free Tier: https://aws.amazon.com/free
- Project README: ../README.md
