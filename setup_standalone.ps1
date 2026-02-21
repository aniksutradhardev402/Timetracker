# setup_standalone.ps1
$ErrorActionPreference = "Stop"

Write-Host "--- Setting up Time Tracker standalone environment ---"

$RootDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($RootDir)) { $RootDir = Get-Location }

# 1. Check for Python
if (!(get-command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found. Please install Python 3.10+ and add it to your PATH."
}

# 2. Create Virtual Environment
if (!(Test-Path "$RootDir\.venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv "$RootDir\.venv"
}

# 3. Upgrade Pip
Write-Host "Upgrading pip..."
& "$RootDir\.venv\Scripts\python.exe" -m pip install --upgrade pip

# 4. Install Dependencies
Write-Host "Installing backend dependencies (skipping Postgres)..."
# We skip psycopg2-binary because SQLite doesn't need it and it fails on Python 3.14
& "$RootDir\.venv\Scripts\pip.exe" install fastapi uvicorn[standard] sqlmodel pydantic python-multipart pytest httpx==0.24.1

Write-Host "Installing frontend dependencies..."
# Use flexible versions for Python 3.14 compatibility
& "$RootDir\.venv\Scripts\pip.exe" install streamlit requests pandas plotly streamlit-calendar

Write-Host "Setup Complete!"
Write-Host "Launch with: .\run_standalone.ps1"
