# stop_standalone.ps1
$ErrorActionPreference = "Continue"

Write-Host "--- Stopping Time Tracker Services ---"

# These match the exact commands used to start the services in run_standalone.ps1
$services = @(
    "uvicorn app.main:app",
    "streamlit run frontend/frontend.py"
)

$stoppedAny = $false

foreach ($serviceName in $services) {
    # We look for any python processes containing our specific command line arguments
    $processes = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { 
        $_.CommandLine -and ($_.CommandLine -like "*$serviceName*") 
    }
    
    foreach ($p in $processes) {
        Write-Host "Stopping matching process (PID: $($p.ProcessId)) -> $serviceName..."
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        $stoppedAny = $true
    }
}

if (-not $stoppedAny) {
    Write-Host "No running Time Tracker services were found."
}
else {
    Write-Host "All Time Tracker services have been stopped successfully!"
}
