# stack-start.ps1 — Start the NETA.AI Docker stack safely
# Usage: .\scripts\stack-start.ps1
# Must be run from D:\NETA.AI

param(
    [switch]$Build,    # pass -Build to rebuild images before starting
    [switch]$Prod      # pass -Prod to include docker-compose.prod.yml overrides
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Write-Step([string]$msg) { Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor Cyan }
function Write-OK([string]$msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Fail([string]$msg) { Write-Host "  !!  $msg" -ForegroundColor Red }

# ── 1. Verify Docker engine ───────────────────────────────────────────────────
Write-Step "Checking Docker engine..."
$dockerVer = & docker version --format "{{.Server.Version}}" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Docker engine not responding. Start Docker Desktop and try again."
    exit 1
}
Write-OK "Docker $dockerVer"

# ── 2. Verify .env exists ─────────────────────────────────────────────────────
if (-not (Test-Path "$ProjectRoot\.env")) {
    Write-Fail ".env not found. Copy .env.example to .env and fill in secrets."
    exit 1
}
Write-OK ".env present"

# ── 3. Build images if requested ─────────────────────────────────────────────
if ($Build) {
    Write-Step "Building Docker images..."
    docker compose build 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Fail "Build failed"; exit 1 }
    Write-OK "Images built"
}

# ── 4. Start stack ────────────────────────────────────────────────────────────
Write-Step "Starting stack..."
if ($Prod) {
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d 2>&1
} else {
    docker compose up -d 2>&1
}
if ($LASTEXITCODE -ne 0) { Write-Fail "docker compose up failed"; exit 1 }

# ── 5. Wait for all containers to be healthy ─────────────────────────────────
Write-Step "Waiting for containers to be healthy (max 90s)..."
$deadline = (Get-Date).AddSeconds(90)
$allHealthy = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
    $statuses = (docker compose ps --format "{{.Health}}" 2>&1) -split "`n" | Where-Object { $_ -ne "" }
    $unhealthy = $statuses | Where-Object { $_ -ne "healthy" }
    if ($unhealthy.Count -eq 0 -and $statuses.Count -eq 5) { $allHealthy = $true; break }
}

docker compose ps --format "table {{.Name}}`t{{.Status}}" 2>&1 | ForEach-Object { Write-Host "  $_" }

if (-not $allHealthy) {
    Write-Host "`n  Some containers not yet healthy — check 'docker compose logs'" -ForegroundColor Yellow
} else {
    Write-OK "All 5 containers healthy"
}

# ── 6. Verify API health ──────────────────────────────────────────────────────
Write-Step "Verifying API health..."
$apiOk = $false
for ($i = 0; $i -lt 6; $i++) {
    try {
        $r = Invoke-RestMethod "http://127.0.0.1:8000/api/health" -TimeoutSec 5
        if ($r.status -eq "ok") { $apiOk = $true; break }
    } catch {}
    Start-Sleep -Seconds 5
}

if ($apiOk) { Write-OK "API healthy: http://localhost:8000/api/health" }
else         { Write-Fail "API not responding — check logs: docker compose logs api" }

Write-Host "`n=====================================================" -ForegroundColor Green
Write-Host "  NETA.AI stack is UP" -ForegroundColor Green
Write-Host "  API  : http://localhost:8000" -ForegroundColor Green
Write-Host "  Docs : http://localhost:8000/api/docs" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
