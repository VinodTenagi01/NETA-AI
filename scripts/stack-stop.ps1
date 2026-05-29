# stack-stop.ps1 — Gracefully stop the NETA.AI Docker stack
# Usage: .\scripts\stack-stop.ps1
# Data volumes are NEVER removed — postgres_data and redis_data are safe.

param(
    [int]$Timeout = 30   # seconds to wait for graceful shutdown before force-kill
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Write-Step([string]$msg) { Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor Cyan }
function Write-OK([string]$msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }

Write-Step "Stopping NETA.AI stack (data volumes preserved)..."
Write-Host "  Timeout: ${Timeout}s per container"

docker compose stop --timeout $Timeout 2>&1

Write-Step "Container status after stop:"
docker compose ps --format "table {{.Name}}`t{{.Status}}" 2>&1 | ForEach-Object { Write-Host "  $_" }

Write-OK "Stack stopped. Postgres and Redis data volumes intact."
Write-Host "  To restart: .\scripts\stack-start.ps1" -ForegroundColor DarkCyan
