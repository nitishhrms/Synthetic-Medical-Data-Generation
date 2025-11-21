@echo off
echo ========================================
echo Force Reset API Gateway
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Force deleting all API Gateway pods...
kubectl delete deployment api-gateway -n clinical-trials --force --grace-period=0
timeout /t 5 /nobreak

echo Step 2: Deleting any remaining pods...
for /f "tokens=1" %%i in ('kubectl get pods -n clinical-trials ^| findstr api-gateway ^| findstr -v NAME') do (
    kubectl delete pod %%i -n clinical-trials --force --grace-period=0
)
timeout /t 10 /nobreak

echo Step 3: Applying fixed configuration...
kubectl apply -f k8s/03-api-gateway.yaml

echo Step 4: Waiting 60 seconds for startup...
timeout /t 60 /nobreak

echo Step 5: Checking status...
kubectl get pods -n clinical-trials | findstr api-gateway

echo.
echo Step 6: Getting public URL...
kubectl get service api-gateway -n clinical-trials

echo.
echo ========================================
echo If you see "1/1 Running", test with:
echo curl http://a23bfbab15b4c4cf7abb1fa2bbef9214-1226957914.us-east-1.elb.amazonaws.com/health
echo ========================================
pause
