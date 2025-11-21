@echo off
echo ==========================================
echo   Clinical Trials Platform - AWS Deployment
echo ==========================================
echo.

echo Step 1: Verify AWS CLI is configured
aws --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS CLI not found!
    pause
    exit /b 1
)
echo AWS CLI is installed!
echo.

echo Step 2: Configure kubectl for EKS
echo Running: aws eks update-kubeconfig...
aws eks update-kubeconfig --name clinical-trials-cluster --region us-east-1 --profile terraform-developer
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to configure kubectl
    pause
    exit /b 1
)
echo kubectl configured!
echo.

echo Step 3: Verify EKS nodes are running
kubectl get nodes
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Cannot connect to EKS cluster
    pause
    exit /b 1
)
echo.

echo Step 4: Get database password from Secrets Manager
echo Fetching password...
aws secretsmanager get-secret-value --secret-id clinical-trials-db-password-99f5df1683ef3929 --query SecretString --output text --profile terraform-developer > temp_secret.json
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to get database password
    pause
    exit /b 1
)
echo Database password retrieved!
echo IMPORTANT: Edit k8s\02-secrets.yaml and update the DATABASE_PASSWORD with the password from temp_secret.json
echo.
type temp_secret.json
echo.
pause

echo Step 5: Login to ECR
echo Running: aws ecr get-login-password...
aws ecr get-login-password --region us-east-1 --profile terraform-developer | docker login --username AWS --password-stdin 432180555044.dkr.ecr.us-east-1.amazonaws.com
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to login to ECR
    pause
    exit /b 1
)
echo Logged into ECR!
echo.

echo Step 6: Build and push Docker images
echo This will take a while...
echo.

echo Building api-gateway...
docker build -t 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/api-gateway:latest microservices/api-gateway
docker push 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/api-gateway:latest

echo Building edc-service...
docker build -t 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/edc-service:latest microservices/edc-service
docker push 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/edc-service:latest

echo Building data-generation-service...
docker build -t 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/data-generation-service:latest microservices/data-generation-service
docker push 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/data-generation-service:latest

echo Building analytics-service...
docker build -t 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/analytics-service:latest microservices/analytics-service
docker push 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/analytics-service:latest

echo Building quality-service...
docker build -t 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/quality-service:latest microservices/quality-service
docker push 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/quality-service:latest

echo Building security-service...
docker build -t 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/security-service:latest microservices/security-service
docker push 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/security-service:latest

echo Building daft-analytics-service...
docker build -t 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/daft-analytics-service:latest microservices/daft-analytics-service
docker push 432180555044.dkr.ecr.us-east-1.amazonaws.com/clinical-trials/daft-analytics-service:latest

echo.
echo All images built and pushed!
echo.

echo Step 7: Deploy to Kubernetes
echo Applying Kubernetes manifests...
kubectl apply -f k8s/
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to deploy to Kubernetes
    pause
    exit /b 1
)
echo.

echo Step 8: Check deployment status
echo Waiting for pods to start...
timeout /t 10 /nobreak
kubectl get pods -n clinical-trials
echo.

echo Step 9: Get API Gateway public URL
echo.
echo Your API Gateway LoadBalancer URL:
kubectl get service api-gateway -n clinical-trials
echo.

echo ==========================================
echo   Deployment Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Wait for the LoadBalancer to be provisioned (may take 2-3 minutes)
echo 2. Get the EXTERNAL-IP from the service above
echo 3. Access your API at: http://[EXTERNAL-IP]/
echo.
echo To check logs: kubectl logs -f deployment/api-gateway -n clinical-trials
echo To check all pods: kubectl get pods -n clinical-trials -w
echo.
pause
