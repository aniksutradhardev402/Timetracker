@echo off
setlocal

echo 🚀 Starting Time Tracker...

:: Build and start containers in detached mode
docker-compose up -d --build

echo ⏳ Waiting for application to be ready...
:: Give it a few seconds to initialize
timeout /t 5 /nobreak > nul

:: Open the browser
start http://localhost:8501

echo ✅ Time Tracker is running at http://localhost:8501
echo Leave this window open if you want to see logs, or close it to run in background.
echo To stop the app later, run 'docker-compose down' in this folder.
pause
