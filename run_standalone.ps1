# run_standalone.ps1
$ErrorActionPreference = "Continue"

Write-Host "--- Launching Time Tracker ---"

$RootDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($RootDir)) { $RootDir = Get-Location }

if (!(Test-Path "$RootDir\.venv")) {
    Write-Error "Virtual environment not found. Please run .\setup_standalone.ps1 first."
    exit
}

if ([string]::IsNullOrEmpty($env:DATABASE_URL)) {
    $env:DATABASE_URL = "sqlite:///$RootDir/daily_focus.db"
    Write-Host "No DATABASE_URL found. Using default SQLite database at $RootDir/daily_focus.db"
}

# Start Backend (FastAPI)
Write-Host "Starting Backend (FastAPI)..."
$BackendProc = Start-Process -FilePath "$RootDir\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory "$RootDir" -NoNewWindow -PassThru

if ([string]::IsNullOrEmpty($env:API_URL)) {
    $env:API_URL = "http://127.0.0.1:8000"
}

# Start Frontend (Streamlit)
Write-Host "Starting Frontend (Streamlit)..."
$FrontendProc = Start-Process -FilePath "$RootDir\.venv\Scripts\python.exe" -ArgumentList "-m streamlit run frontend/frontend.py --server.headless true --browser.gatherUsageStats false" -WorkingDirectory "$RootDir" -NoNewWindow -PassThru

Write-Host "Services are running!"
Write-Host "Frontend: http://localhost:8501"

try {
    while ($true) { Start-Sleep -Seconds 1 }
}
finally {
    Write-Host "Stopping services..."
    Stop-Process -Id $BackendProc.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $FrontendProc.Id -ErrorAction SilentlyContinue
}
