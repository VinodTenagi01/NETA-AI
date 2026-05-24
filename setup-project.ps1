# ==============================================================================
# setup-project.ps1
# Automates directory creation, config file setups, parses the docx PRD,
# and generates neta-sessions.ps1 with chronological sessions.
# Owner: Srinivas / Fidelitus Corp
# ==============================================================================

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
$PROJECT_NAME  = "neta"
$PROJECT_ROOT  = "E:\NETA"
$STACK         = "Python 3.11, FastAPI, PostgreSQL (PostGIS), Redis, Docker, Celery"
$MODULES       = @(
    "database-design", "security-auth", "geojson-mapping", "ground-operations",
    "news-intelligence", "booth-management", "prediction-sentiment",
    "opposition-intelligence", "whatsapp-integration", "devops-deployment"
)
$PHASE_CURRENT = 1
# ──────────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   NETA AI — PROJECT BOOTSTRAP WITH PRD PARSING               ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# ── 1. Create Folder Structure ────────────────────────────────────────────────
Write-Host "[ 1/5 ] Creating folder structure..." -ForegroundColor Yellow
$folders = @("tasks", "docs", "docs\plans", "tests", ".claude\skills") + ($MODULES | ForEach-Object { "app\$_" })
foreach ($f in $folders) {
    $path = Join-Path $PROJECT_ROOT $f
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
        Write-Host "  ✓ $f" -ForegroundColor Green
    } else {
        Write-Host "  · $f (exists)" -ForegroundColor DarkGray
    }
}

# ── 2. Writing Config Files ───────────────────────────────────────────────────
Write-Host ""; Write-Host "[ 2/5 ] Writing CLAUDE.md, TOOLS.md, and SKILLS.md..." -ForegroundColor Yellow

# Write CLAUDE.md
$moduleMap = ($MODULES | ForEach-Object { "  Session → $_`t: app\$_ only" }) -join "`n"
$claudeContent = @"
# CLAUDE.md — NETA AI
# Extends ~/.claude/CLAUDE.md.

## Stack
$STACK

## Current Phase: $PHASE_CURRENT

## Module Boundaries
$moduleMap
  Session → debug   : one error + one file per session

## Key Config
  DATABASE_URL=postgresql+asyncpg://netaai_app:netaai_password@localhost:5432/netaai_prod
  REDIS_URL=redis://:redis_password@localhost:6379/0
  JWT_ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=15
  NLP_MODEL_PATH=/models/indic-bert-political

## Git
  main / dev / feature/TASK-XXX
  Format: [TASK-XXX] verb: what changed
"@
$claudeContent | Set-Content "$PROJECT_ROOT\CLAUDE.md" -Encoding UTF8
Write-Host "  ✓ CLAUDE.md written." -ForegroundColor Green

# Write TOOLS.md
$toolsContent = @"
# TOOLS.md — NETA AI

## Plugins: superpowers, context7, code-simplifier, context-mode
## MCPs: filesystem, memory, sequential-thinking

## Session Launcher
  .\neta-sessions.ps1 -Session list

## Test Commands
  pytest tests/
"@
$toolsContent | Set-Content "$PROJECT_ROOT\TOOLS.md" -Encoding UTF8
Write-Host "  ✓ TOOLS.md written." -ForegroundColor Green

# Write SKILLS.md & task-create skill
$skillsMdContent = @"
# SKILLS.md — NETA AI

| Command      | File                          | What it does                  |
|--------------|-------------------------------|-------------------------------|
| task-create  | .claude/skills/task-create.md | Create a new TASK-XXX.md      |
"@
$skillsMdContent | Set-Content "$PROJECT_ROOT\SKILLS.md" -Encoding UTF8

$taskCreateSkillContent = @'
# Skill: task-create
1. Ask: task title + phase
2. Find next TASK number in tasks/
3. Create tasks/TASK-XXX-<slug>.md with PDCA template
4. Create branch: feature/TASK-XXX
5. Report path + branch
'@
$taskCreateSkillContent | Set-Content "$PROJECT_ROOT\.claude\skills\task-create.md" -Encoding UTF8
Write-Host "  ✓ SKILLS.md + task-create written." -ForegroundColor Green

# Write TASK-000
$task000Content = @"
# TASK-000: Repo Init

## Status: PLANNING
## Phase: 1
## Objective
Initialize the repository structures, configurations, and session management scripts.

## PDCA Log
### Cycle 1
**Plan:** Setup directories, write configurations, extract PRD specs, and verify sessions runner.
**Approved:** Yes
**Do:** Execute setup-project.ps1
**Check:** Verify neta-sessions.ps1 executes in list, audit, and debug modes.
**Act:** Commit changes.

## Checkpoints
| Step | Status | Git Commit | Notes |
|------|--------|------------|-------|
| 1. Run setup | [x] | | Initial project layout |
"@
$task000Content | Set-Content "$PROJECT_ROOT\tasks\TASK-000-repo-init.md" -Encoding UTF8
Write-Host "  ✓ tasks/TASK-000-repo-init.md created." -ForegroundColor Green

# ── 3. Parse PRD DOCX ──────────────────────────────────────────────────────────
Write-Host ""; Write-Host "[ 3/5 ] Parsing PRD DOCX file..." -ForegroundColor Yellow

$docxPath = Join-Path $PROJECT_ROOT "NETA_AI_PRD_v2.0.docx"
$tempZip = Join-Path $PROJECT_ROOT "temp_parsing.zip"
$tempDir = Join-Path $PROJECT_ROOT "temp_parsing_dir"

if (-not (Test-Path $docxPath)) {
    Write-Error "PRD document not found at: $docxPath"
    exit 1
}

# Copy to zip and extract
Copy-Item $docxPath $tempZip -Force
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force | Out-Null }
Expand-Archive -Path $tempZip -DestinationPath $tempDir -Force

$docXmlPath = Join-Path $tempDir "word\document.xml"
if (-not (Test-Path $docXmlPath)) {
    Write-Error "Invalid docx structure. Could not find word/document.xml."
    Remove-Item $tempZip -Force | Out-Null
    exit 1
}

# Parse XML with explicit UTF-8 decoding
[xml]$doc = New-Object System.Xml.XmlDocument
$docContent = [System.IO.File]::ReadAllText($docXmlPath, [System.Text.Encoding]::UTF8)
$doc.LoadXml($docContent)

$ns = New-Object System.Xml.XmlNamespaceManager($doc.NameTable)
$ns.AddNamespace("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main")

$paragraphs = $doc.SelectNodes("//w:p", $ns) | ForEach-Object {
    $text = ""
    $_.SelectNodes(".//w:t", $ns) | ForEach-Object { $text += $_.InnerText }
    $text
}

Write-Host "  ✓ Parsed $($paragraphs.Count) paragraphs from PRD." -ForegroundColor Green

# Helper function to extract section text
function Get-SectionContent($headingRegex, $pList) {
    $startIndex = -1
    for ($i = 0; $i -lt $pList.Count; $i++) {
        if ($pList[$i] -match $headingRegex) {
            $startIndex = $i
            break
        }
    }
    if ($startIndex -eq -1) { return "Section not found in PRD." }
    
    $content = @()
    for ($i = $startIndex + 1; $i -lt $pList.Count; $i++) {
        if ($pList[$i] -match "^\d+\.\s") {
            break
        }
        if (-not [string]::IsNullOrWhiteSpace($pList[$i])) {
            $content += $pList[$i]
        }
    }
    $result = $content -join "`r`n"
    return $result
}

# Extract sections
$dbContent = Get-SectionContent "^20\.\s+Database\s+Design" $paragraphs
$securityContent = Get-SectionContent "^17\.\s+Security\s+Architecture" $paragraphs
$geojsonContent = Get-SectionContent "^22\.\s+GeoJSON\s+Mapping\s+System" $paragraphs
$constituencyContent = Get-SectionContent "^11\.\s+Constituency\s+Intelligence" $paragraphs
$groundContent = Get-SectionContent "^13\.\s+Ground\s+Operations" $paragraphs
$newsContent = Get-SectionContent "^12\.\s+News\s+Intelligence\s+Engine" $paragraphs
$boothContent = Get-SectionContent "^14\.\s+Booth\s+Management\s+System" $paragraphs
$predictionContent = Get-SectionContent "^15\.\s+Prediction\s+\&\s+Sentiment\s+Systems" $paragraphs
if ($predictionContent -eq "Section not found in PRD.") {
    $predictionContent = Get-SectionContent "^15\.\s+Prediction" $paragraphs
}
$oppositionContent = Get-SectionContent "^16\.\s+Opposition\s+Intelligence" $paragraphs
$whatsappContent = Get-SectionContent "^24\.\s+WhatsApp\s+Integration" $paragraphs
$devopsContent = Get-SectionContent "^19\.\s+DevOps\s+\&\s+CI\/CD" $paragraphs
if ($devopsContent -eq "Section not found in PRD.") {
    $devopsContent = Get-SectionContent "^19\.\s+DevOps" $paragraphs
}
$deploymentContent = Get-SectionContent "^18\.\s+Deployment\s+Architecture" $paragraphs
$redisContent = Get-SectionContent "^21\.\s+Redis\s+\&\s+Celery\s+Architecture" $paragraphs
if ($redisContent -eq "Section not found in PRD.") {
    $redisContent = Get-SectionContent "^21\.\s+Redis" $paragraphs
}
$monitoringContent = Get-SectionContent "^26\.\s+Monitoring\s+\&\s+Logging" $paragraphs
if ($monitoringContent -eq "Section not found in PRD.") {
    $monitoringContent = Get-SectionContent "^26\.\s+Monitoring" $paragraphs
}

# Clean up temp files
Remove-Item $tempZip -Force | Out-Null
Remove-Item $tempDir -Recurse -Force | Out-Null

Write-Host "  ✓ Extraction completed." -ForegroundColor Green

# ── 4. Generate neta-sessions.ps1 ─────────────────────────────────────────────
Write-Host ""; Write-Host "[ 4/5 ] Generating neta-sessions.ps1..." -ForegroundColor Yellow

$templatePath = Join-Path $PROJECT_ROOT "neta-sessions-template.ps1"
if (-not (Test-Path $templatePath)) {
    Write-Error "Template file not found at: $templatePath"
    exit 1
}

$templateContent = [System.IO.File]::ReadAllText($templatePath, [System.Text.Encoding]::UTF8)

# Replace the placeholders
$templateContent = $templateContent.Replace("@@DB_CONTENT@@", $dbContent)
$templateContent = $templateContent.Replace("@@SECURITY_CONTENT@@", $securityContent)
$templateContent = $templateContent.Replace("@@GEOJSON_CONTENT@@", $geojsonContent)
$templateContent = $templateContent.Replace("@@CONSTITUENCY_CONTENT@@", $constituencyContent)
$templateContent = $templateContent.Replace("@@GROUND_CONTENT@@", $groundContent)
$templateContent = $templateContent.Replace("@@NEWS_CONTENT@@", $newsContent)
$templateContent = $templateContent.Replace("@@BOOTH_CONTENT@@", $boothContent)
$templateContent = $templateContent.Replace("@@PREDICTION_CONTENT@@", $predictionContent)
$templateContent = $templateContent.Replace("@@OPPOSITION_CONTENT@@", $oppositionContent)
$templateContent = $templateContent.Replace("@@WHATSAPP_CONTENT@@", $whatsappContent)
$templateContent = $templateContent.Replace("@@DEVOPS_CONTENT@@", $devopsContent)
$templateContent = $templateContent.Replace("@@DEPLOYMENT_CONTENT@@", $deploymentContent)
$templateContent = $templateContent.Replace("@@REDIS_CONTENT@@", $redisContent)
$templateContent = $templateContent.Replace("@@MONITORING_CONTENT@@", $monitoringContent)

$outputPath = Join-Path $PROJECT_ROOT "neta-sessions.ps1"
# Save as UTF-8 with BOM for PowerShell 5.1 compatibility
[System.IO.File]::WriteAllText($outputPath, $templateContent, [System.Text.Encoding]::UTF8)

Write-Host "  ✓ Generated: $outputPath" -ForegroundColor Green

# ── 5. Complete Bootstrap ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✓ $PROJECT_NAME bootstrap complete." -ForegroundColor Green
Write-Host "  Generated neta-sessions.ps1 from template & PRD parsing." -ForegroundColor Green
Write-Host "  Next: Run .\neta-sessions.ps1 -Session list to view sessions." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
