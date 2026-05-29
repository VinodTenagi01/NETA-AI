# backup-db.ps1 — PostgreSQL backup to local directory
# Usage: .\scripts\backup-db.ps1 [-BackupDir D:\NETA.AI\backups] [-Keep 30]
# Creates compressed .sql.gz backup inside the running postgres container and copies it out.
# SAFE: read-only operation. Never touches volumes or data files.

param(
    [string]$BackupDir = "D:\NETA.AI\backups",
    [int]$Keep = 30          # days of backups to retain
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Write-Step([string]$msg) { Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor Cyan }
function Write-OK([string]$msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Fail([string]$msg) { Write-Host "  !!  $msg" -ForegroundColor Red; exit 1 }

# ── Load env vars for DB credentials ─────────────────────────────────────────
if (Test-Path "$ProjectRoot\.env") {
    Get-Content "$ProjectRoot\.env" | Where-Object { $_ -match "^[A-Z_]+=.+" } | ForEach-Object {
        $kv = $_ -split "=", 2
        if (-not [System.Environment]::GetEnvironmentVariable($kv[0])) {
            [System.Environment]::SetEnvironmentVariable($kv[0], $kv[1])
        }
    }
}

$PG_USER = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "netaai_app" }
$PG_DB   = if ($env:POSTGRES_DB)   { $env:POSTGRES_DB }   else { "netaai_prod" }
$PG_PASS = if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { "netaai_password" }

# ── Verify postgres container is running ─────────────────────────────────────
Write-Step "Verifying postgres container..."
$state = docker inspect neta_postgres --format "{{.State.Status}}" 2>&1
if ($state -ne "running") { Write-Fail "neta_postgres is not running (state: $state)" }
Write-OK "neta_postgres running"

# ── Create backup directory ───────────────────────────────────────────────────
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
    Write-OK "Created backup dir: $BackupDir"
}

# ── Run pg_dump inside container ─────────────────────────────────────────────
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$containerDumpPath = "/tmp/neta_backup_$timestamp.sql.gz"
$localDumpPath = Join-Path $BackupDir "neta_backup_$timestamp.sql.gz"

Write-Step "Running pg_dump (PGPASSWORD masked)..."
$dumpCmd = "PGPASSWORD=`"$PG_PASS`" pg_dump -U $PG_USER -d $PG_DB --format=plain | gzip > $containerDumpPath"
docker exec neta_postgres sh -c $dumpCmd 2>&1
if ($LASTEXITCODE -ne 0) { Write-Fail "pg_dump failed (exit $LASTEXITCODE)" }
Write-OK "Dump complete inside container: $containerDumpPath"

# ── Copy backup out of container ─────────────────────────────────────────────
Write-Step "Copying backup to $localDumpPath..."
docker cp "neta_postgres:$containerDumpPath" $localDumpPath 2>&1
if ($LASTEXITCODE -ne 0) { Write-Fail "docker cp failed" }

# Remove temp file inside container
docker exec neta_postgres rm -f $containerDumpPath 2>&1 | Out-Null

$size = (Get-Item $localDumpPath).Length / 1MB
Write-OK "Backup saved: $localDumpPath ($([Math]::Round($size,2)) MB)"

# ── Prune old backups ─────────────────────────────────────────────────────────
Write-Step "Pruning backups older than $Keep days..."
$cutoff = (Get-Date).AddDays(-$Keep)
$old = Get-ChildItem $BackupDir -Filter "neta_backup_*.sql.gz" | Where-Object { $_.LastWriteTime -lt $cutoff }
$old | Remove-Item -Force
if ($old.Count -gt 0) { Write-OK "Removed $($old.Count) old backup(s)" }
else { Write-OK "No old backups to prune" }

$remaining = (Get-ChildItem $BackupDir -Filter "neta_backup_*.sql.gz").Count
Write-Host "`n=====================================================" -ForegroundColor Green
Write-Host "  Backup complete: $localDumpPath" -ForegroundColor Green
Write-Host "  Total backups in $BackupDir`: $remaining" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
