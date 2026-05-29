# stack-health.ps1 — Full health check for the NETA.AI stack
# Usage: .\scripts\stack-health.ps1
# Returns exit code 0 if all healthy, 1 if any issues found.

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$issues = @()

function Write-Section([string]$title) {
    Write-Host "`n$("=" * 56)" -ForegroundColor DarkGray
    Write-Host "  $title" -ForegroundColor White
    Write-Host "$("=" * 56)" -ForegroundColor DarkGray
}
function Write-Pass([string]$label, [string]$value = "") {
    Write-Host ("  {0,-28} {1}" -f $label, $value) -ForegroundColor Green
}
function Write-Warn([string]$label, [string]$value = "") {
    Write-Host ("  {0,-28} {1}" -f $label, $value) -ForegroundColor Yellow
    $script:issues += "$label`: $value"
}
function Write-Fail([string]$label, [string]$value = "") {
    Write-Host ("  {0,-28} {1}" -f $label, $value) -ForegroundColor Red
    $script:issues += "$label`: $value"
}

Write-Host "`nNETA.AI Stack Health Check — $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan

# ── Containers ────────────────────────────────────────────────────────────────
Write-Section "CONTAINERS"
$containers = docker compose ps --format json 2>&1 | ForEach-Object { try { $_ | ConvertFrom-Json } catch {} }
$expected = @("neta_api","neta_postgres","neta_redis","neta_celery_worker","neta_celery_beat")
foreach ($name in $expected) {
    $c = $containers | Where-Object { $_.Name -eq $name }
    if (-not $c) { Write-Fail $name "NOT FOUND" }
    elseif ($c.Health -eq "healthy") { Write-Pass $name "healthy" }
    elseif ($c.State -eq "running")  { Write-Warn $name "running (health: $($c.Health))" }
    else { Write-Fail $name "state=$($c.State) health=$($c.Health)" }
}

# ── API Endpoint ──────────────────────────────────────────────────────────────
Write-Section "API"
try {
    $h = Invoke-RestMethod "http://127.0.0.1:8000/api/health" -TimeoutSec 5
    if ($h.status -eq "ok") { Write-Pass "/api/health" "status=ok  version=$($h.version)" }
    else { Write-Fail "/api/health" "unexpected: $($h | ConvertTo-Json -Compress)" }
} catch { Write-Fail "/api/health" "UNREACHABLE: $_" }

try {
    $authBody = '{"email":"admin@netaai.in","password":"Admin123!Secure"}'
    $auth = Invoke-RestMethod "http://127.0.0.1:8000/api/auth/login" -Method POST -Body $authBody -ContentType "application/json" -TimeoutSec 5
    if ($auth.access_token) { Write-Pass "/api/auth/login" "token obtained" }
    $h2 = @{ Authorization = "Bearer $($auth.access_token)" }

    $sys = Invoke-RestMethod "http://127.0.0.1:8000/api/admin/system" -Headers $h2 -TimeoutSec 5
    Write-Pass "/api/admin/system" "db_ok=$($sys.db_ok)  redis_ok=$($sys.redis_ok)  uptime=$($sys.uptime_seconds)s"

    $queues = Invoke-RestMethod "http://127.0.0.1:8000/api/admin/queues" -Headers $h2 -TimeoutSec 5
    $queueStr = ($queues.PSObject.Properties | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join " "
    Write-Pass "/api/admin/queues" $queueStr
} catch { Write-Warn "Auth/Admin" "Skipped: $_" }

# ── Database Direct ───────────────────────────────────────────────────────────
Write-Section "DATABASE"
$pgResult = docker exec neta_postgres psql -U netaai_app -d netaai_prod -t -c `
    "SELECT 'booths', COUNT(*) FROM booths UNION ALL SELECT 'voters', COUNT(*) FROM voters UNION ALL SELECT 'news_articles', COUNT(*) FROM news_articles UNION ALL SELECT 'field_reports', COUNT(*) FROM field_reports UNION ALL SELECT 'alerts', COUNT(*) FROM alerts UNION ALL SELECT 'campaign_zones', COUNT(*) FROM campaign_zones;" 2>&1

$expected_counts = @{ booths=315; voters=608; alerts=9; campaign_zones=7 }
if ($pgResult) {
    $pgResult -split "`n" | Where-Object { $_ -match "\|" } | ForEach-Object {
        $parts = $_.Trim() -split "\s*\|\s*"
        if ($parts.Count -ge 2) {
            $tbl = $parts[0].Trim(); $cnt = $parts[1].Trim()
            $exp = $expected_counts[$tbl]
            if ($exp -and [int]$cnt -ne $exp) { Write-Warn "DB: $tbl" "count=$cnt (expected $exp)" }
            else { Write-Pass "DB: $tbl" "count=$cnt" }
        }
    }
} else { Write-Fail "PostgreSQL" "Could not query" }

# ── Redis ─────────────────────────────────────────────────────────────────────
Write-Section "REDIS"
# Read REDIS_PASSWORD from .env file if not already in environment
if (-not $env:REDIS_PASSWORD -and (Test-Path "$ProjectRoot\.env")) {
    $envLine = Get-Content "$ProjectRoot\.env" | Where-Object { $_ -match "^REDIS_PASSWORD=" } | Select-Object -First 1
    if ($envLine) { $env:REDIS_PASSWORD = ($envLine -split "=", 2)[1].Trim() }
}
$redisPass = if ($env:REDIS_PASSWORD) { $env:REDIS_PASSWORD } else { "redis_password" }
$redisPing = docker exec neta_redis redis-cli -a $redisPass ping 2>&1
if ($redisPing -match "PONG") { Write-Pass "Redis PING" "PONG" }
else {
    # Fall back to checking via docker health status
    $redisHealth = docker inspect neta_redis --format "{{.State.Health.Status}}" 2>&1
    if ($redisHealth -eq "healthy") { Write-Pass "Redis PING" "healthy (via container health)" }
    else { Write-Warn "Redis PING" "Could not verify - container health: $redisHealth" }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Section "SUMMARY"
if ($issues.Count -eq 0) {
    Write-Host "  ALL CHECKS PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host "  $($issues.Count) issue(s) found:" -ForegroundColor Yellow
    $issues | ForEach-Object { Write-Host "    - $_" -ForegroundColor Yellow }
    exit 1
}
