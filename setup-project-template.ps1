# ==============================================================================
# setup-project-template.ps1
# Copy this, rename setup-<project>.ps1, fill the 5 variables.
# Owner: Srinivas / Fidelitus Corp
# ==============================================================================

# ── FILL THESE 5 VARIABLES ────────────────────────────────────────────────────
$PROJECT_NAME  = "your-project-name"
$PROJECT_ROOT  = "D:\staging\your-project"
$STACK         = "Python 3.13, FastAPI, PostgreSQL, Docker"
$MODULES       = @("module1", "module2", "module3")
$PHASE_CURRENT = 0
# ─────────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   $PROJECT_NAME — PROJECT BOOTSTRAP" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

if (-not (Test-Path $PROJECT_ROOT)) {
    New-Item -ItemType Directory -Path $PROJECT_ROOT | Out-Null
}
Set-Location $PROJECT_ROOT

Write-Host "[ 1/6 ] Creating folder structure..." -ForegroundColor Yellow
$folders = @("tasks","docs","docs\plans","tests",".claude\skills") + ($MODULES | ForEach-Object { "app\$_" })
foreach ($f in $folders) {
    $path = Join-Path $PROJECT_ROOT $f
    if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null; Write-Host "  ✓ $f" -ForegroundColor Green }
    else { Write-Host "  · $f (exists)" -ForegroundColor DarkGray }
}

Write-Host ""; Write-Host "[ 2/6 ] Writing CLAUDE.md..." -ForegroundColor Yellow
$moduleMap = ($MODULES | ForEach-Object { "  Session → $_`t: app\$_\ only" }) -join "`n"
@"
# CLAUDE.md — $PROJECT_NAME
# Extends ~/.claude/CLAUDE.md.

## Stack
$STACK

## Current Phase: $PHASE_CURRENT

## Module Boundaries
$moduleMap
  Session → debug   : one error + one file per session

## Key Config
[Fill in: env vars, thresholds, IDs, endpoints]

## Git
  main / dev / feature/TASK-XXX
  Format: [TASK-XXX] verb: what changed
"@ | Set-Content "$PROJECT_ROOT\CLAUDE.md" -Encoding UTF8
Write-Host "  ✓ CLAUDE.md written. Fill in Key Config section." -ForegroundColor Green

Write-Host ""; Write-Host "[ 3/6 ] Writing TOOLS.md..." -ForegroundColor Yellow
@"
# TOOLS.md — $PROJECT_NAME

## Plugins: superpowers, context7, code-simplifier, context-mode
## MCPs: filesystem, memory, sequential-thinking

## Session Launcher
  .\${PROJECT_NAME}-sessions.ps1 -Session list

## Test Commands
  [Fill in]
"@ | Set-Content "$PROJECT_ROOT\TOOLS.md" -Encoding UTF8
Write-Host "  ✓ TOOLS.md written." -ForegroundColor Green

Write-Host ""; Write-Host "[ 4/6 ] Writing SKILLS.md + task-create skill..." -ForegroundColor Yellow
@"
# SKILLS.md — $PROJECT_NAME

| Command      | File                          | What it does                  |
|--------------|-------------------------------|-------------------------------|
| task-create  | .claude/skills/task-create.md | Create a new TASK-XXX.md      |
"@ | Set-Content "$PROJECT_ROOT\SKILLS.md" -Encoding UTF8

@'
# Skill: task-create
1. Ask: task title + phase
2. Find next TASK number in tasks/
3. Create tasks/TASK-XXX-<slug>.md with PDCA template
4. Create branch: feature/TASK-XXX
5. Report path + branch
'@ | Set-Content "$PROJECT_ROOT\.claude\skills\task-create.md" -Encoding UTF8
Write-Host "  ✓ SKILLS.md + task-create written." -ForegroundColor Green

Write-Host ""; Write-Host "[ 5/6 ] Creating TASK-000..." -ForegroundColor Yellow
@"
# TASK-000: Repo Init

## Status: PLANNING
## Phase: 0
## Objective
[What does done look like?]

## PDCA Log
### Cycle 1
**Plan:**
**Approved:** Pending
**Do:**
**Check:**
**Act:**

## Checkpoints
| Step | Status | Git Commit | Notes |
|------|--------|------------|-------|
"@ | Set-Content "$PROJECT_ROOT\tasks\TASK-000-repo-init.md" -Encoding UTF8
Write-Host "  ✓ tasks/TASK-000-repo-init.md" -ForegroundColor Green

Write-Host ""; Write-Host "[ 6/6 ] Writing .mcp.json..." -ForegroundColor Yellow
$npmGlobalRoot = (npm root -g 2>$null).Trim()
@"
{
  "mcpServers": {
    "filesystem": { "command": "node", "args": ["$npmGlobalRoot\\@modelcontextprotocol\\server-filesystem\\dist\\index.js", "$PROJECT_ROOT"] },
    "memory": { "command": "node", "args": ["$npmGlobalRoot\\@modelcontextprotocol\\server-memory\\dist\\index.js"] },
    "sequential-thinking": { "command": "node", "args": ["$npmGlobalRoot\\@modelcontextprotocol\\server-sequential-thinking\\dist\\index.js"] }
  }
}
"@ | Set-Content "$PROJECT_ROOT\.mcp.json" -Encoding UTF8
Write-Host "  ✓ .mcp.json written." -ForegroundColor Green

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✓ $PROJECT_NAME bootstrap complete." -ForegroundColor Green
Write-Host "  Next: open CLAUDE.md, fill Key Config, then create sessions script." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
