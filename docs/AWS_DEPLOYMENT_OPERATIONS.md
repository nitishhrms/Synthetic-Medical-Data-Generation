# Clinical Trials Platform - AWS Deployment Guide

## Overview

Complete enterprise deployment on AWS EKS with PostgreSQL, Redis, and S3 storage.

## Infrastructure Deployed

### Core Services
- **EKS Cluster**: clinical-trials-cluster (Kubernetes 1.29)
  - 2x t3.small nodes (can scale 1-4)
  - Multi-AZ across us-east-1a and us-east-1b

- **RDS PostgreSQL**: clinical-trials-db.c4lokm6ie8ag.us-east-1.rds.amazonaws.com:5432
  - Version: PostgreSQL 15.x
  - Instance: db.t3.micro
  - Storage: 100GB gp3 encrypted
  - Automated backups enabled

- **ElastiCache Redis**: clinical-redis.c67nel.ng.0001.use1.cache.amazonaws.com:6379
  - Single node (staging)
  - At-rest encryption enabled

- **S3 Bucket**: clinical-trials-documents-99f5df1683ef3929
  - Versioning enabled
  - Server-side encryption (AES256)
  - Public access blocked

### Networking
- **VPC**: vpc-06e14e90c6f18c817 (10.0.0.0/16)
- **Public Subnets**: 2 subnets for Load Balancers
- **Private Subnets**: 2 subnets for EKS nodes and databases
- **NAT Gateway**: For outbound internet access
- **Security Groups**: Configured for EKS ↔ RDS and EKS ↔ Redis

### Container Registry
**ECR Repositories** (all under clinical-trials/):
1. api-gateway
2. edc-service
3. data-generation-service
4. analytics-service
5. quality-service
6. security-service
7. daft-analytics-service

## Quick Start Deployment

### Step 1: Configure kubectl

```powershell
aws eks update-kubeconfig --name clinical-trials-cluster --region us-east-1 --profile terraform-developer
kubectl get nodes
```

### Step 2: Get Database Password

```powershell
aws secretsmanager get-secret-value --secret-id clinical-trials-db-password-99f5df1683ef3929 --query SecretString --output text --profile terraform-developer
```

Update `k8s/02-secrets.yaml` with this password.

### Step 3: Deploy to Kubernetes

```powershell
kubectl apply -f k8s/
```

### Step 4: Get API Gateway URL

```powershell
kubectl get service api-gateway -n clinical-trials
```

Look for the `EXTERNAL-IP` column - this is your public endpoint!

## Building and Pushing Docker Images

### Login to ECR

```powershell
aws ecr get-login-password --region us-east-1 --profile terraform-developer | docker login --username AWS --password-stdin 432180555044.dkr.ecr.us-east-1.amazonaws.com
```

### Build and Push All Services

```powershell
# Example for api-gateway
docker build -t 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/api-gateway:latest ./api-gateway
docker push 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/api-gateway:latest

# Repeat for all 7 services
```

## Monitoring

### View Pod Status

```powershell
kubectl get pods -n clinical-trials -w
```

### View Logs

```powershell
kubectl logs -f deployment/api-gateway -n clinical-trials
```

### View Events

```powershell
kubectl get events -n clinical-trials --sort-by='.lastTimestamp'
```

## Architecture Highlights

### Scalability Features
- **Auto-scaling EKS nodes**: Min 1, Max 4 nodes
- **Horizontal Pod Autoscaling**: Ready to configure
- **Multi-AZ deployment**: High availability across availability zones
- **Load-balanced API Gateway**: AWS ELB distributes traffic

### Security Features
- **Encrypted storage**: RDS, Redis, and S3 all encrypted at rest
- **Private networking**: Services in private subnets
- **Security groups**: Least-privilege network access
- **Secrets management**: AWS Secrets Manager for credentials
- **IAM roles**: Fine-grained permissions for ECR access

### Cost Optimization
- **Right-sized instances**: t3.small for EKS, db.t3.micro for RDS
- **Single-AZ for staging**: Reduces costs while maintaining functionality
- **Efficient caching**: Redis reduces database load

## Connection Strings

### PostgreSQL
```
postgresql://clinical_user:PASSWORD@clinical-trials-db.c4lokm6ie8ag.us-east-1.rds.amazonaws.com:5432/clinical_trials
```

### Redis
```
clinical-redis.c67nel.ng.0001.use1.cache.amazonaws.com:6379
```

### S3 Bucket
```
s3://clinical-trials-documents-99f5df1683ef3929
```

## Useful Commands

### Restart a deployment
```powershell
kubectl rollout restart deployment/api-gateway -n clinical-trials
```

### Scale a service
```powershell
kubectl scale deployment/data-generation-service --replicas=3 -n clinical-trials
```

### Port-forward for debugging
```powershell
kubectl port-forward service/api-gateway 8000:80 -n clinical-trials
```

### Execute into a pod
```powershell
kubectl exec -it deployment/api-gateway -n clinical-trials -- /bin/bash
```

## Troubleshooting

### Pods in CrashLoopBackOff
1. Check logs: `kubectl logs <pod-name> -n clinical-trials`
2. Check image exists in ECR
3. Verify secrets are correct
4. Check database connectivity

### Cannot access API Gateway
1. Get LoadBalancer status: `kubectl describe service api-gateway -n clinical-trials`
2. Check security groups allow inbound traffic
3. Verify pods are running: `kubectl get pods -n clinical-trials`

### Database connection failures
1. Verify security group rules (terraform/main.tf)
2. Check database password in secrets
3. Ensure EKS nodes can reach RDS (private subnet routing)

## Infrastructure Costs (Estimated Monthly)

- **EKS Cluster**: ~$72 (cluster) + ~$30 (2x t3.small nodes) = $102
- **RDS db.t3.micro**: ~$15
- **ElastiCache Redis**: ~$13
- **NAT Gateway**: ~$32
- **S3 + Data transfer**: ~$5
- **Total**: ~$167/month (with $140 credits, ~$27/month)

## Next Steps for Production

1. **Enable Multi-AZ** for RDS and Redis
2. **Set up autoscaling** policies
3. **Configure HTTPS** with AWS Certificate Manager
4. **Add monitoring** with CloudWatch Container Insights
5. **Set up CI/CD** with GitHub Actions
6. **Enable CloudTrail** for audit logging
7. **Configure backup policies**
8. **Set up Ingress controller** for advanced routing

## Support & Documentation

- AWS EKS: https://docs.aws.amazon.com/eks/
- Kubernetes: https://kubernetes.io/docs/
- Terraform AWS Provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
