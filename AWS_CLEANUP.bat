@echo off
echo ========================================
echo AWS EKS Cleanup and Stabilization
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Disabling problematic services...
echo   - Scaling down quality-service (database issue)
kubectl scale deployment quality-service --replicas=0 -n clinical-trials

echo   - Scaling down daft-analytics-service (resource issue)
kubectl scale deployment daft-analytics-service --replicas=0 -n clinical-trials

echo   - Scaling down analytics-service (database issue)
kubectl scale deployment analytics-service --replicas=0 -n clinical-trials

echo.
echo Step 2: Cleaning up old crashed pods...
kubectl delete pod api-gateway-57cbb66dbc-jjfd7 -n clinical-trials 2>nul

echo.
echo Step 3: Waiting for stabilization (30 seconds)...
timeout /t 30 /nobreak

echo.
echo Step 4: Checking pod status...
kubectl get pods -n clinical-trials

echo.
echo Step 5: Getting your public API URL...
echo.
kubectl get service api-gateway -n clinical-trials

echo.
echo ========================================
echo Next Steps:
echo 1. Look for EXTERNAL-IP in the output above
echo 2. If it shows a URL like "xxxx.elb.amazonaws.com", copy it
echo 3. Test it with: curl http://YOUR-URL/health
echo ========================================
pause
