# recovery-check.ps1 — Diagnose and recover the NETA.AI stack after a Windows reboot or crash.
# Usage: .\scripts\recovery-check.ps1 [-AutoRecover]
# With -AutoRecover: will attempt to start Docker Desktop + stack automatically.
# SAFE: reads-only by default. Will not delete volumes, images, or data.

param(
    [switch]$AutoRecover    # attempt recovery if issues found
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$issues = @()
$fixed  = @()

function Write-Step([string]$msg)  { Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor Cyan }
function Write-Pass([string]$msg)  { Write-Host "  PASS  $msg" -ForegroundColor Green }
function Write-Issue([string]$msg) { Write-Host "  FAIL  $msg" -ForegroundColor Red; $script:issues += $msg }
function Write-Fixed([string]$msg) { Write-Host "  FIXED $msg" -ForegroundColor Yellow; $script:fixed += $msg }

Write-Host "`nNETA.AI Recovery Check — $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan

# ── 1. WSL / Hyper-V ─────────────────────────────────────────────────────────
Write-Step "WSL2 / Hyper-V status"
$vmwp = Get-Process -Name "vmwp" -ErrorAction SilentlyContinue
if ($vmwp) { Write-Pass "WSL2 VM running (vmwp PID=$($vmwp.Id))" }
else { Write-Issue "WSL2 VM not running — Docker Desktop may not have started yet" }

# ── 2. Docker Desktop ────────────────────────────────────────────────────────
Write-Step "Docker Desktop process"
$dd = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if ($dd) { Write-Pass "Docker Desktop running (PID=$($dd[0].Id))" }
else {
    Write-Issue "Docker Desktop not running"
    if ($AutoRecover) {
        Write-Host "  Launching Docker Desktop..." -ForegroundColor Yellow
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        Start-Sleep -Seconds 5
        Write-Fixed "Docker Desktop launch initiated"
    }
}

# ── 3. Docker engine ─────────────────────────────────────────────────────────
Write-Step "Docker engine"
$dockerVer = & docker version --format "{{.Server.Version}}" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Pass "Docker engine v$dockerVer"
} else {
    Write-Issue "Docker engine not responding: $dockerVer"
    if ($AutoRecover) {
        Write-Host "  Waiting up to 90s for engine to start..." -ForegroundColor Yellow
        $deadline = (Get-Date).AddSeconds(90)
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Seconds 10
            $v = & docker version --format "{{.Server.Version}}" 2>&1
            if ($LASTEXITCODE -eq 0) { Write-Fixed "Engine came up: v$v"; break }
            Write-Host "  Still waiting..." -ForegroundColor DarkGray
        }
    }
}

# ── 4. Container states ───────────────────────────────────────────────────────
Write-Step "Container states"
$containers = docker compose ps --format json 2>&1 | ForEach-Object { try { $_ | ConvertFrom-Json } catch {} }
$expected = @("neta_api","neta_postgres","neta_redis","neta_celery_worker","neta_celery_beat")
$notHealthy = @()
foreach ($name in $expected) {
    $c = $containers | Where-Object { $_.Name -eq $name }
    if (-not $c) {
        Write-Issue "Container $name not found"
        $notHealthy += $name
    } elseif ($c.Health -eq "healthy") {
        Write-Pass "$name healthy"
    } else {
        Write-Issue "$name state=$($c.State) health=$($c.Health)"
        $notHealthy += $name
    }
}

if ($notHealthy.Count -gt 0 -and $AutoRecover) {
    Write-Host "`n  Starting stack with: docker compose up -d" -ForegroundColor Yellow
    docker compose up -d 2>&1 | ForEach-Object { Write-Host "  $_" }
    Start-Sleep -Seconds 30
    Write-Fixed "docker compose up -d executed"
}

# ── 5. API health ─────────────────────────────────────────────────────────────
Write-Step "API health endpoint"
try {
    $r = Invoke-RestMethod "http://127.0.0.1:8000/api/health" -TimeoutSec 8
    if ($r.status -eq "ok") { Write-Pass "API healthy (v$($r.version))" }
    else { Write-Issue "API returned unexpected: $($r | ConvertTo-Json -Compress)" }
} catch { Write-Issue "API unreachable: $_" }

# ── 6. Data volumes ───────────────────────────────────────────────────────────
Write-Step "Data volumes"
$vols = docker volume ls --format "{{.Name}}" 2>&1
if ($vols -match "netaai_postgres_data") { Write-Pass "netaai_postgres_data exists" }
else { Write-Issue "netaai_postgres_data volume NOT FOUND" }
if ($vols -match "netaai_redis_data") { Write-Pass "netaai_redis_data exists" }
else { Write-Issue "netaai_redis_data volume NOT FOUND" }

# ── 7. WSL distro health ──────────────────────────────────────────────────────
Write-Step "WSL distros"
$wslList = wsl --list --verbose 2>&1
$wslList | ForEach-Object { Write-Host "  $_" }
$dockerDistro = $wslList | Where-Object { $_ -match "docker-desktop " -and $_ -notmatch "docker-desktop-data" }
if ($dockerDistro) { Write-Pass "docker-desktop distro present" }
else { Write-Issue "docker-desktop distro not found in WSL list" }

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host "`n$("=" * 56)" -ForegroundColor DarkGray
Write-Host "  RECOVERY CHECK SUMMARY" -ForegroundColor White
Write-Host "$("=" * 56)" -ForegroundColor DarkGray

if ($issues.Count -eq 0) {
    Write-Host "  ALL SYSTEMS HEALTHY — no action needed" -ForegroundColor Green
    exit 0
} else {
    Write-Host "  Issues found: $($issues.Count)" -ForegroundColor Red
    $issues | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
    if ($fixed.Count -gt 0) {
        Write-Host "  Recovery actions taken: $($fixed.Count)" -ForegroundColor Yellow
        $fixed | ForEach-Object { Write-Host "    + $_" -ForegroundColor Yellow }
        Write-Host "`n  Re-run this script or .\scripts\stack-health.ps1 to confirm." -ForegroundColor Cyan
    } else {
        Write-Host "`n  Run with -AutoRecover to attempt automatic recovery." -ForegroundColor Cyan
        Write-Host "  Or run: .\scripts\stack-start.ps1" -ForegroundColor Cyan
    }
    exit 1
}
