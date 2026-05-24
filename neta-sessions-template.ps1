# ==============================================================================
# neta-sessions.ps1
# Tailored development session runner parsed and generated from PRD requirements.
# Owner: Srinivas / Fidelitus Corp
# ==============================================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet(
        "01-database-design",
        "02-security-auth",
        "03-geojson-mapping",
        "04-ground-operations",
        "05-news-intelligence",
        "06-booth-management",
        "07-prediction-sentiment",
        "08-opposition-intelligence",
        "09-whatsapp-integration",
        "10-devops-deployment",
        "list",
        "debug",
        "audit"
    )]
    [string]$Session
)

$PROJECT_ROOT = "E:\NETA"
$HAIKU        = "claude-haiku-4-5-20251001"
$SONNET       = "claude-sonnet-4-6"

$sessions = @{

    "01-database-design" = @{
        model  = $HAIKU
        task   = "TASK-001"
        label  = "Session 1 · Database Schema & Alembic Setup"
        prompt = @'
Stack: Python 3.11, PostgreSQL (PostGIS), SQLAlchemy 2.0 (async), asyncpg, Alembic, Docker
Task file: tasks/TASK-001-database-design.md
Module scope: app/database-design/ ONLY (migrations & init scripts).

Key requirements extracted from PRD:
@@DB_CONTENT@@

PDCA: present plan before touching any file.
'@
    }

    "02-security-auth" = @{
        model  = $SONNET
        task   = "TASK-002"
        label  = "Session 2 · Security Architecture & JWT Authentication"
        prompt = @'
Stack: Python 3.11, FastAPI, Redis, bcrypt
Task file: tasks/TASK-002-security-auth.md
Module scope: app/security-auth/ ONLY (endpoints, middleware, security configuration).

Key requirements extracted from PRD:
@@SECURITY_CONTENT@@

PDCA: present plan before touching any file.
'@
    }

    "03-geojson-mapping" = @{
        model  = $SONNET
        task   = "TASK-003"
        label  = "Session 3 · GeoJSON Mapping System & Constituency Views"
        prompt = @'
Stack: React 18, Leaflet.js, PostGIS, FastAPI
Task file: tasks/TASK-003-geojson-mapping.md
Module scope: app/geojson-mapping/ and frontend map views ONLY.

Key requirements extracted from PRD:
@@GEOJSON_CONTENT@@

@@CONSTITUENCY_CONTENT@@

PDCA: present plan before touching any file.
'@
    }

    "04-ground-operations" = @{
        model  = $SONNET
        task   = "TASK-004"
        label  = "Session 4 · Ground Pulse & Escalations Workflow"
        prompt = @'
Stack: Python 3.11, FastAPI, React 18 (PWA, IndexedDB)
Task file: tasks/TASK-004-ground-operations.md
Module scope: app/ground-operations/ ONLY (field reports, attendance, escalation SLAs).

Key requirements extracted from PRD:
@@GROUND_CONTENT@@

PDCA: present plan before touching any file.
'@
    }

    "05-news-intelligence" = @{
        model  = $SONNET
        task   = "TASK-005"
        label  = "Session 5 · RSS Ingestion & Multilingual NLP Pipeline"
        prompt = @'
Stack: Python 3.11, Celery, HuggingFace (MuRIL/IndicBERT), spaCy, Scikit-learn
Task file: tasks/TASK-005-news-intelligence.md
Module scope: app/news-intelligence/ ONLY (RSS parser, sentiment model, narrative clustering).

Key requirements extracted from PRD:
@@NEWS_CONTENT@@

PDCA: present plan before touching any file.
'@
    }

    "06-booth-management" = @{
        model  = $SONNET
        task   = "TASK-006"
        label  = "Session 6 · Booth Operations & Nightly Risk Scoring"
        prompt = @'
Stack: Python 3.11, Celery, PostgreSQL, Redis
Task file: tasks/TASK-006-booth-management.md
Module scope: app/booth-management/ ONLY (booth records, risk score calculations, volunteers).

Key requirements extracted from PRD:
@@BOOTH_CONTENT@@

PDCA: present plan before touching any file.
'@
    }

    "07-prediction-sentiment" = @{
        model  = $SONNET
        task   = "TASK-007"
        label  = "Session 7 · Win Probability Model & Sentiment Trends"
        prompt = @'
Stack: Python 3.11, Celery, Redis, PostgreSQL
Task file: tasks/TASK-007-prediction-sentiment.md
Module scope: app/prediction-sentiment/ ONLY (win probability computation, issue severity aggregates).

Key requirements extracted from PRD:
@@PREDICTION_CONTENT@@

PDCA: present plan before touching any file.
'@
    }

    "08-opposition-intelligence" = @{
        model  = $SONNET
        task   = "TASK-008"
        label  = "Session 8 · Opposition Monitoring & Sentiment Comparison"
        prompt = @'
Stack: Python 3.11, React 18, Leaflet.js
Task file: tasks/TASK-008-opposition-intel.md
Module scope: app/opposition-intelligence/ ONLY.

Key requirements extracted from PRD:
@@OPPOSITION_CONTENT@@

PDCA: present plan before touching any file.
'@
    }

    "09-whatsapp-integration" = @{
        model  = $SONNET
        task   = "TASK-009"
        label  = "Session 9 · Meta WhatsApp Business API & Alert Routing"
        prompt = @'
Stack: Python 3.11, Meta Cloud API, Celery
Task file: tasks/TASK-009-whatsapp-integration.md
Module scope: app/whatsapp-integration/ ONLY (status callbacks, alert delivery, templates).

Key requirements extracted from PRD:
@@WHATSAPP_CONTENT@@

PDCA: present plan before touching any file.
'@
    }

    "10-devops-deployment" = @{
        model  = $SONNET
        task   = "TASK-010"
        label  = "Session 10 · Docker Orchestration, Logging & Monitoring"
        prompt = @'
Stack: Docker Compose, Nginx, Prometheus, Grafana, Sentry, Celery Beat/Flower
Task file: tasks/TASK-010-devops-deployment.md
Module scope: root devops configuration, nginx setups, and monitoring scripts ONLY.

Key requirements extracted from PRD:
@@DEVOPS_CONTENT@@

@@DEPLOYMENT_CONTENT@@

@@REDIS_CONTENT@@

@@MONITORING_CONTENT@@

PDCA: present plan before touching any file.
'@
    }
}

# ── Action: list ──────────────────────────────────────────────────────────────
if ($Session -eq "list") {
    Write-Host ""
    Write-Host "  NETA AI — Available Development Sessions:" -ForegroundColor Cyan
    Write-Host "  =========================================" -ForegroundColor Cyan
    Write-Host ""
    $sortedKeys = $sessions.Keys | Sort-Object
    foreach ($key in $sortedKeys) {
        $s = $sessions[$key]
        $tag = if ($s.model -like "*haiku*") { "Haiku  🟢" } else { "Sonnet 🔵" }
        Write-Host ("  {0,-28} {1,-50} [{2}]" -f $key, $s.label, $tag)
    }
    Write-Host ""
    exit 0
}

# ── Action: debug ─────────────────────────────────────────────────────────────
if ($Session -eq "debug") {
    Write-Host ""
    Write-Host "  ┌──────────────────────────────────────────────┐" -ForegroundColor Yellow
    Write-Host "  │  DEBUG SESSION MODE                          │" -ForegroundColor Yellow
    Write-Host "  └──────────────────────────────────────────────┘" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Rule: One error, one file, one session." -ForegroundColor White
    Write-Host "  Instructions for Claude Code:" -ForegroundColor White
    Write-Host "    1. Paste the full error traceback." -ForegroundColor DarkGray
    Write-Host "    2. Paste ONLY the function/code block throwing the error." -ForegroundColor DarkGray
    Write-Host "    3. Avoid feeding the entire file if possible to save tokens." -ForegroundColor DarkGray
    Write-Host ""
    $debugPrompt = @'
Stack: Python 3.11, FastAPI, React 18, Docker
Task: Debug one specific issue.
Instructions:
- Analyze the traceback and target file.
- Provide the fix.
- Test and verify the fix.
'@
    $debugPrompt | Set-Clipboard
    Write-Host "  ✓ Copied debug prompt to clipboard. Paste in Claude Code to start." -ForegroundColor Green
    Write-Host ""
    exit 0
}

# ── Action: audit ─────────────────────────────────────────────────────────────
if ($Session -eq "audit") {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║   NETA AI — PROJECT STATUS AUDIT                         ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    $checkpoints = @(
        @{ Name = "CLAUDE.md Configured"; Path = "$PROJECT_ROOT\CLAUDE.md" },
        @{ Name = "TOOLS.md Configured"; Path = "$PROJECT_ROOT\TOOLS.md" },
        @{ Name = "SKILLS.md Configured"; Path = "$PROJECT_ROOT\SKILLS.md" },
        @{ Name = "Database Design (Session 1)"; Pattern = "$PROJECT_ROOT\tasks\TASK-001-*.md" },
        @{ Name = "Security & Auth (Session 2)"; Pattern = "$PROJECT_ROOT\tasks\TASK-002-*.md" },
        @{ Name = "GeoJSON Mapping (Session 3)"; Pattern = "$PROJECT_ROOT\tasks\TASK-003-*.md" },
        @{ Name = "Ground Operations (Session 4)"; Pattern = "$PROJECT_ROOT\tasks\TASK-004-*.md" },
        @{ Name = "News Intelligence (Session 5)"; Pattern = "$PROJECT_ROOT\tasks\TASK-005-*.md" },
        @{ Name = "Booth Management (Session 6)"; Pattern = "$PROJECT_ROOT\tasks\TASK-006-*.md" },
        @{ Name = "Prediction & Sentiment (Session 7)"; Pattern = "$PROJECT_ROOT\tasks\TASK-007-*.md" },
        @{ Name = "Opposition Intelligence (Session 8)"; Pattern = "$PROJECT_ROOT\tasks\TASK-008-*.md" },
        @{ Name = "WhatsApp Integration (Session 9)"; Pattern = "$PROJECT_ROOT\tasks\TASK-009-*.md" },
        @{ Name = "DevOps & Deployment (Session 10)"; Pattern = "$PROJECT_ROOT\tasks\TASK-010-*.md" }
    )
    
    $completedCount = 0
    foreach ($item in $checkpoints) {
        $found = $false
        if ($item.Path) {
            $found = Test-Path $item.Path
        } elseif ($item.Pattern) {
            $found = (Resolve-Path $item.Pattern -ErrorAction SilentlyContinue) -ne $null
        }
        
        if ($found) {
            Write-Host ("  [✓] {0,-40} - COMPLETED" -f $item.Name) -ForegroundColor Green
            $completedCount++
        } else {
            Write-Host ("  [ ] {0,-40} - PENDING" -f $item.Name) -ForegroundColor Red
        }
    }
    
    $pct = [Math]::Round(($completedCount / $checkpoints.Count) * 100)
    Write-Host ""
    Write-Host "  Project Completion: $pct% ($completedCount / $($checkpoints.Count) checkpoints)" -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

# ── Execute Session ───────────────────────────────────────────────────────────
$s = $sessions[$Session]
Write-Host ""
Write-Host "  ┌────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host ("  │  {0,-54}│" -f $s.label) -ForegroundColor Cyan
Write-Host ("  │  Model: {0,-47}│" -f $s.model) -ForegroundColor Cyan
Write-Host "  └────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""
Write-Host $s.prompt -ForegroundColor White
Write-Host ""

$s.prompt | Set-Clipboard
Write-Host "  ✓ Copied prompt to clipboard. Paste in Claude Code then brainstorm." -ForegroundColor Green
Write-Host ""

# Support running in tests
if ($env:NETA_TEST -eq "true") {
    Write-Host "  [Sandbox Test Mode] Skipping launch of claude cli." -ForegroundColor Yellow
    exit 0
}

Set-Location $PROJECT_ROOT
$env:ANTHROPIC_MODEL = $s.model
claude --model $s.model
