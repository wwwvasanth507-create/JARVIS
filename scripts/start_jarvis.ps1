# PowerShell Launcher for JARVIS Desktop Assistant
$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "         JARVIS Desktop Assistant Launcher         " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Locate project directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Resolve-Path "$ScriptDir\.."
Set-Location $ProjectRoot

# Activate virtual environment if present
if (Test-Path "$ProjectRoot\venv\Scripts\Activate.ps1") {
    Write-Host "[INFO] Activating virtual environment (venv)..." -ForegroundColor Green
    & "$ProjectRoot\venv\Scripts\Activate.ps1"
} elseif (Test-Path "$ProjectRoot\.venv\Scripts\Activate.ps1") {
    Write-Host "[INFO] Activating virtual environment (.venv)..." -ForegroundColor Green
    & "$ProjectRoot\.venv\Scripts\Activate.ps1"
}

# Execute JARVIS
Write-Host "[INFO] Starting JARVIS application..." -ForegroundColor Green
python -m jarvis $args
