# ==============================================================================
# sessions-template.ps1
# Copy this, rename <project>-sessions.ps1, fill in sessions hashtable.
# Owner: Srinivas / Fidelitus Corp
# ==============================================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("module1","module2","debug","list")]
    [string]$Session
)

$PROJECT_ROOT = "D:\staging\your-project"
$HAIKU        = "claude-haiku-4-5-20251001"
$SONNET       = "claude-sonnet-4-6"

$sessions = @{

    module1 = @{
        model = $HAIKU           # Haiku for mechanical: config, CRUD, schema
        task  = "TASK-001"
        label = "Session 1 · Module 1 name"
        prompt = @'
Stack: [your stack]
Task file: tasks/TASK-001-[slug].md
Module scope: app/module1/ ONLY.

Key facts:
- [fact 1]
- [fact 2]

Context7: use for [library] API.
PDCA: present plan before touching any file.
'@
    }

    module2 = @{
        model = $SONNET          # Sonnet for real logic, APIs, complex code
        task  = "TASK-002"
        label = "Session 2 · Module 2 name"
        prompt = @'
Stack: [your stack]
Task file: tasks/TASK-002-[slug].md
Module scope: app/module2/ ONLY.

Key facts:
- [fact 1]

Context7: use for [library] API.
PDCA: present plan before touching any file.
'@
    }

    debug = @{
        model = $SONNET
        task  = "TASK-???"
        label = "Debug Session"
        prompt = @'
Stack: [your stack]
Task: one error, one file, one session.
Paste: (1) full traceback (2) only the function that threw it.
Known gotchas: [list project-specific gotchas]
'@
    }
}

if ($Session -eq "list") {
    Write-Host ""; Write-Host "  Available sessions:" -ForegroundColor Cyan; Write-Host ""
    foreach ($key in $sessions.Keys | Sort-Object) {
        $s = $sessions[$key]
        $tag = if ($s.model -like "*haiku*") { "Haiku  🟢" } else { "Sonnet 🔵" }
        Write-Host ("  {0,-14} {1,-40} [{2}]" -f $key, $s.label, $tag)
    }
    Write-Host ""; exit 0
}

$s = $sessions[$Session]
Write-Host ""
Write-Host "  ┌──────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host ("  │  {0,-44}│" -f $s.label) -ForegroundColor Cyan
Write-Host ("  │  Model: {0,-38}│" -f $s.model) -ForegroundColor Cyan
Write-Host "  └──────────────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""
Write-Host $s.prompt -ForegroundColor White
Write-Host ""
$s.prompt | Set-Clipboard
Write-Host "  ✓ Copied to clipboard. Paste then: superpowers brainstorm" -ForegroundColor Green
Write-Host ""
Set-Location $PROJECT_ROOT
$env:ANTHROPIC_MODEL = $s.model
claude --model $s.model
