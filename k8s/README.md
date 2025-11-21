# Kubernetes Deployment Guide for Clinical Trials Platform

## Prerequisites

1. AWS CLI configured with `terraform-developer` profile
2. kubectl installed
3. Docker images built and pushed to ECR

## Quick Deployment Steps

### 1. Configure kubectl for EKS

```powershell
aws eks update-kubeconfig --name clinical-trials-cluster --region us-east-1 --profile terraform-developer
```

Verify connection:
```powershell
kubectl get nodes
```

You should see 2 nodes running.

### 2. Update Secrets

**IMPORTANT**: Get the database password from AWS Secrets Manager:

```powershell
aws secretsmanager get-secret-value --secret-id clinical-trials-db-password-99f5df1683ef3929 --query SecretString --output text --profile terraform-developer
```

Edit `02-secrets.yaml` and replace `REPLACE_WITH_ACTUAL_PASSWORD` with the actual password.

### 3. Deploy All Services

Deploy in order (the files are numbered):

```powershell
kubectl apply -f k8s/
```

Or deploy individually:

```powershell
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secrets.yaml
kubectl apply -f k8s/03-api-gateway.yaml
kubectl apply -f k8s/04-edc-service.yaml
kubectl apply -f k8s/05-data-generation-service.yaml
kubectl apply -f k8s/06-analytics-service.yaml
kubectl apply -f k8s/07-quality-service.yaml
kubectl apply -f k8s/08-security-service.yaml
kubectl apply -f k8s/09-daft-analytics-service.yaml
```

### 4. Check Deployment Status

```powershell
# Check all pods
kubectl get pods -n clinical-trials

# Check services
kubectl get services -n clinical-trials

# Get LoadBalancer URL for API Gateway
kubectl get service api-gateway -n clinical-trials
```

The API Gateway will have an external LoadBalancer URL (AWS ELB) - this is your public endpoint!

### 5. View Logs

```powershell
# View logs for a specific service
kubectl logs -f deployment/api-gateway -n clinical-trials

# View logs for all containers
kubectl logs -f deployment/data-generation-service -n clinical-trials
```

## Architecture

- **api-gateway**: Public-facing LoadBalancer (port 80)
- **All other services**: Internal ClusterIP services
- **Database**: External RDS PostgreSQL
- **Cache**: External ElastiCache Redis
- **Storage**: S3 bucket for documents

## Service Endpoints (Internal)

- API Gateway: http://api-gateway:8000
- EDC Service: http://edc-service:8001
- Data Generation: http://data-generation-service:8002
- Analytics: http://analytics-service:8003
- Quality: http://quality-service:8004
- Security: http://security-service:8005
- DAFT Analytics: http://daft-analytics-service:8006

## Scaling

```powershell
# Scale a specific service
kubectl scale deployment data-generation-service --replicas=3 -n clinical-trials

# View current replicas
kubectl get deployment -n clinical-trials
```

## Troubleshooting

### Pods not starting

```powershell
kubectl describe pod <pod-name> -n clinical-trials
kubectl logs <pod-name> -n clinical-trials
```

### Cannot connect to database

1. Check security groups allow EKS to RDS (port 5432)
2. Verify database password in secrets
3. Check pod logs for connection errors

### Service discovery issues

All services use internal DNS: `<service-name>.clinical-trials.svc.cluster.local`

Example: `http://edc-service.clinical-trials.svc.cluster.local:8001`

## Clean Up

To delete all resources:

```powershell
kubectl delete namespace clinical-trials
```

This will remove all pods, services, and configs.

## Next Steps

1. Set up monitoring (CloudWatch Container Insights)
2. Configure autoscaling (HPA)
3. Set up Ingress controller for better routing
4. Enable HTTPS with cert-manager
5. Set up CI/CD with GitHub Actions
