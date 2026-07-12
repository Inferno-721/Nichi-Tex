# ============================================================
#  Nichi-Tex - Run Script (Backend + Frontend)
#  Handles first-time setup and launches both servers.
# ============================================================

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Nichi-Tex - Starting Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ----- Prerequisite checks -------------------------------------------------
function Test-Command($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

if (-not (Test-Command "python")) {
    Write-Host "ERROR: Python is not installed or not on PATH." -ForegroundColor Red
    exit 1
}
if (-not (Test-Command "npm")) {
    Write-Host "ERROR: Node.js/npm is not installed or not on PATH." -ForegroundColor Red
    exit 1
}

# ----- Backend setup -------------------------------------------------------
$venvActivate = Join-Path $scriptDir "venv\Scripts\Activate.ps1"
$venvPython   = Join-Path $scriptDir "venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "[setup] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv (Join-Path $scriptDir "venv")
    Write-Host "[setup] Installing backend dependencies..." -ForegroundColor Yellow
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r (Join-Path $scriptDir "requirements.txt")
} else {
    Write-Host "[setup] Python virtual environment found." -ForegroundColor Green
}

# Warn if .env is missing (Gemini API key etc.)
if (-not (Test-Path (Join-Path $scriptDir ".env"))) {
    Write-Host "[warn] No .env file found. Copy .env.example to .env and add your API key." -ForegroundColor Yellow
}

# ----- Frontend setup ------------------------------------------------------
$frontendDir = Join-Path $scriptDir "frontend"
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "[setup] Installing frontend dependencies (npm install)..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
} else {
    Write-Host "[setup] Frontend dependencies found." -ForegroundColor Green
}

# ----- Launch servers ------------------------------------------------------
Write-Host ""
Write-Host "[1/2] Starting Backend (FastAPI) on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$scriptDir'; & '$venvActivate'; python main.py"

# Give the backend a moment to come up
Start-Sleep -Seconds 4

Write-Host "[2/2] Starting Frontend (Next.js) on http://localhost:3000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$frontendDir'; npm run dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Both servers are starting!" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "  API docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Each server runs in its own window. Close those windows to stop them." -ForegroundColor Gray
