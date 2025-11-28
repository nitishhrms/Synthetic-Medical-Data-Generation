@echo off
echo Removing problematic nul file from git index...

cd /d "%~dp0"

REM Remove from git cache
git rm --cached "microservices\data-generation-service\src\nul" 2>nul

REM Check if physical file exists and delete it
if exist "microservices\data-generation-service\src\nul" (
    echo Deleting physical nul file...
    del /f "microservices\data-generation-service\src\nul"
)

echo Done! Now try:
echo   git add AWS_guide.md
echo   git commit -m "Add AWS integration guide and fixes"
echo   git push
pause
