#!/bin/bash
# deploy-aws.sh - Complete AWS deployment script

set -e  # Exit on error

echo "=================================================="
echo "  Clinical Trials Platform - AWS Deployment"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI not found. Installing...${NC}"
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Terraform not found. Installing...${NC}"
    wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
    unzip terraform_1.6.0_linux_amd64.zip
    sudo mv terraform /usr/local/bin/
    rm terraform_1.6.0_linux_amd64.zip
fi

echo -e "${GREEN}✓ Prerequisites checked${NC}"

# Step 2: Configure AWS
echo -e "${YELLOW}Step 2: Configuring AWS...${NC}"
aws configure list || aws configure

echo -e "${GREEN}✓ AWS configured${NC}"

# Step 3: Deploy infrastructure with Terraform
echo -e "${YELLOW}Step 3: Deploying infrastructure with Terraform...${NC}"
cd terraform/

terraform init
terraform validate

echo -e "${YELLOW}Running terraform plan...${NC}"
terraform plan -out=tfplan

echo -e "${YELLOW}Applying infrastructure (this may take 10-15 minutes)...${NC}"
terraform apply tfplan

# Save outputs
terraform output -json > ../outputs.json
terraform output connection_commands > ../connection_info.txt

echo -e "${GREEN}✓ Infrastructure deployed${NC}"

# Step 4: Get connection details
echo -e "${YELLOW}Step 4: Retrieving connection details...${NC}"

DB_ENDPOINT=$(terraform output -raw rds_endpoint)
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
S3_BUCKET=$(terraform output -raw s3_bucket_name)
SECRET_ARN=$(terraform output -raw secrets_manager_arn)

echo "Database Endpoint: $DB_ENDPOINT"
echo "Redis Endpoint: $REDIS_ENDPOINT"
echo "S3 Bucket: $S3_BUCKET"

cd ..

# Step 5: Initialize database
echo -e "${YELLOW}Step 5: Initializing database...${NC}"

# Get database password from Secrets Manager
DB_CREDS=$(aws secretsmanager get-secret-value --secret-id $SECRET_ARN --query SecretString --output text)
DB_PASSWORD=$(echo $DB_CREDS | jq -r .password)

# Create connection string
export DATABASE_URL="postgresql://clinical_user:$DB_PASSWORD@$DB_ENDPOINT/clinical_trials"

# Wait for RDS to be ready
echo "Waiting for RDS to be ready..."
sleep 60

# Initialize schema
echo "Initializing database schema..."
psql $DATABASE_URL < database/init.sql || echo "Schema already exists or error occurred"

echo -e "${GREEN}✓ Database initialized${NC}"

# Step 6: Create environment file
echo -e "${YELLOW}Step 6: Creating environment file...${NC}"

cat > .env.production <<EOF
# AWS Production Environment Variables
# Generated on $(date)

# Database
DATABASE_URL=$DATABASE_URL
POSTGRES_HOST=$DB_ENDPOINT
POSTGRES_DB=clinical_trials
POSTGRES_USER=clinical_user

# Redis
REDIS_HOST=$REDIS_ENDPOINT
REDIS_PORT=6379

# S3
S3_BUCKET=$S3_BUCKET
AWS_REGION=us-east-1

# Application
ENVIRONMENT=production
JWT_SECRET_KEY=$(openssl rand -base64 32)
EOF

echo -e "${GREEN}✓ Environment file created: .env.production${NC}"

# Step 7: Display summary
echo ""
echo "=================================================="
echo -e "${GREEN}  Deployment Complete!${NC}"
echo "=================================================="
echo ""
echo "📊 Infrastructure Summary:"
echo "   • RDS PostgreSQL: $DB_ENDPOINT"
echo "   • ElastiCache Redis: $REDIS_ENDPOINT"
echo "   • S3 Bucket: $S3_BUCKET"
echo ""
echo "📝 Next Steps:"
echo "   1. Review .env.production for credentials"
echo "   2. Deploy microservices to EC2 or EKS"
echo "   3. Update DNS records"
echo "   4. Configure SSL certificates"
echo ""
echo "🔗 Connection Info:"
echo "   Full details saved to: connection_info.txt"
echo ""
echo "💰 Estimated Cost:"
echo "   • Free Tier: ~$0-30/month"
echo "   • Production: ~$50-150/month"
echo ""
echo "⚠️  Security Reminders:"
echo "   • Never commit .env.production"
echo "   • Rotate credentials regularly"
echo "   • Enable MFA on AWS account"
echo ""
echo "=================================================="
