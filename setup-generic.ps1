# ==============================================================================
# setup-generic.ps1
# One-time Claude Code machine bootstrap — run before ANY new project.
# Owner: Srinivas / Fidelitus Corp
# ==============================================================================

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   CLAUDE CODE — GENERIC MACHINE BOOTSTRAP                   ║" -ForegroundColor Cyan
Write-Host "║   Run once per machine. Safe to re-run.                      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 1. Prerequisites ───────────────────────────────────────────────────────────
Write-Host "[ 1/6 ] Checking prerequisites..." -ForegroundColor Yellow
$missing = @()
if (-not (Get-Command node   -ErrorAction SilentlyContinue)) { $missing += "Node.js    → https://nodejs.org" }
if (-not (Get-Command npm    -ErrorAction SilentlyContinue)) { $missing += "npm        → comes with Node.js" }
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { $missing += "Claude CLI → npm install -g @anthropic-ai/claude-code" }
if (-not (Get-Command git    -ErrorAction SilentlyContinue)) { $missing += "Git        → https://git-scm.com" }
if ($missing.Count -gt 0) {
    Write-Host "  ✗ Missing prerequisites:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "      $_" -ForegroundColor Red }
    exit 1
}
Write-Host "  ✓ Node, npm, Claude CLI, Git all present." -ForegroundColor Green

# ── 2. cc-status-line ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ 2/6 ] Installing cc-status-line..." -ForegroundColor Yellow
Write-Host "  Shows context%, model, cost, clock. Hard rule: never exceed 50%." -ForegroundColor DarkGray
npx cc-status-line@latest --install 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ cc-status-line installed." -ForegroundColor Green
} else {
    Write-Host "  ⚠ Run manually: npx cc-status-line@latest" -ForegroundColor Yellow
}
Write-Host "  Recommended status bar:" -ForegroundColor DarkGray
Write-Host "    Line 1: model | context_pct | session_cost | session_clock" -ForegroundColor White
Write-Host "    Line 2: git_branch | git_worktree" -ForegroundColor White

# ── 3. Global MCP servers ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ 3/6 ] Installing global MCP servers..." -ForegroundColor Yellow
$mcpPackages = @(
    "@modelcontextprotocol/server-filesystem",
    "@modelcontextprotocol/server-memory",
    "@modelcontextprotocol/server-sequential-thinking"
)
foreach ($pkg in $mcpPackages) {
    Write-Host "  → $pkg" -ForegroundColor DarkGray
    npm install -g $pkg 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "    ✓" -ForegroundColor Green }
    else { Write-Host "    ✗ Run manually: npm install -g $pkg" -ForegroundColor Red }
}

$claudeDir = "$env:USERPROFILE\.claude"
if (-not (Test-Path $claudeDir)) { New-Item -ItemType Directory -Path $claudeDir | Out-Null }
$npmGlobalRoot = (npm root -g 2>$null).Trim()

@"
{
  "mcpServers": {
    "filesystem": {
      "command": "node",
      "args": ["$npmGlobalRoot\\@modelcontextprotocol\\server-filesystem\\dist\\index.js", "C:\\"]
    },
    "memory": {
      "command": "node",
      "args": ["$npmGlobalRoot\\@modelcontextprotocol\\server-memory\\dist\\index.js"]
    },
    "sequential-thinking": {
      "command": "node",
      "args": ["$npmGlobalRoot\\@modelcontextprotocol\\server-sequential-thinking\\dist\\index.js"]
    }
  }
}
"@ | Set-Content "$claudeDir\.mcp.json" -Encoding UTF8
Write-Host "  ✓ Written: $claudeDir\.mcp.json" -ForegroundColor Green

# ── 4. Global CLAUDE.md ───────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ 4/6 ] Writing ~/.claude/CLAUDE.md..." -ForegroundColor Yellow

@'
# ~/.claude/CLAUDE.md — Global Rules (All Projects)
# Owner: Srinivas / Fidelitus Corp
# Project CLAUDE.md extends these. Never contradicts them.

## Model Tiers

| Task                                          | Model  |
|-----------------------------------------------|--------|
| Boilerplate, config, CRUD, JSON, renaming     | Haiku  |
| Real coding, APIs, debugging, Docker, docs    | Sonnet |
| Failed twice on Sonnet, hard architecture     | Opus   |

Default = Sonnet. Haiku for mechanical. Opus = last resort only.

## Context Window (CRITICAL)

- Watch context % in status bar at all times.
- At 50% → finish current unit → /clear → new session.
- NEVER /compact. Poisons context without clearing it.
- One session = one module = one file scope.

## Superpowers Workflow

1. superpowers brainstorm   → clarify, approaches, spec doc
2. superpowers write plan   → spec to implementation plan
3. superpowers execute plan → sub-agents in isolated context windows

Sub-agents: one task, one file, report summary only.

## Tool Policy

| Tool                | When                                              |
|---------------------|---------------------------------------------------|
| context7            | Any library/API — prevents hallucinated calls     |
| sequential-thinking | Architecture, complex debugging                   |
| memory MCP          | Persist decisions, schema, open questions         |
| filesystem MCP      | Read files — never paste entire files into chat   |
| context-mode        | Large outputs — 98% context savings               |

## PDCA

Plan → present → approval → Do → Check → Act (commit or re-plan).
No scope creep. Every deviation = stop + re-plan.

## Git

- Never commit to main.
- Format: [TASK-XXX] verb: what changed
- Show git diff before every commit.

## Paste Discipline

Paste only the function relevant to the task. Use filesystem MCP for full files.

## Refactor Projects

Read before writing. Always audit first. Never rewrite what works.
'@ | Set-Content "$claudeDir\CLAUDE.md" -Encoding UTF8
Write-Host "  ✓ Written: $claudeDir\CLAUDE.md" -ForegroundColor Green

# ── 5. settings.json ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ 5/6 ] Writing ~/.claude/settings.json..." -ForegroundColor Yellow
@'
{
  "defaultModel": "claude-sonnet-4-6",
  "autoApprove": false,
  "theme": "dark",
  "statusLine": {
    "line1": "model|context_pct|session_cost|session_clock",
    "line2": "git_branch|git_worktree"
  }
}
'@ | Set-Content "$claudeDir\settings.json" -Encoding UTF8
Write-Host "  ✓ Written: $claudeDir\settings.json" -ForegroundColor Green

# ── 6. Manual steps ───────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ 6/6 ] Manual steps (do these inside Claude Code):" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Type /plugin then install each at USER scope:" -ForegroundColor White
Write-Host ""
Write-Host "    superpowers      sub-agent orchestration (brainstorm/plan/execute)" -ForegroundColor Cyan
Write-Host "    code-simplifier  refactor helper" -ForegroundColor Cyan
Write-Host "    context7         live API docs — no hallucinated method names" -ForegroundColor Cyan
Write-Host "    context-mode     98% context savings on large outputs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  WARP TERMINAL  →  https://warp.dev  (Windows supported)" -ForegroundColor Yellow
Write-Host "    Split panels, multiple Claude instances, file viewer" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  HAPPY ENGINEERING  →  https://happy.engineering" -ForegroundColor Yellow
Write-Host "    Full Claude Code on phone — 100% capability" -ForegroundColor DarkGray
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✓ Generic bootstrap complete." -ForegroundColor Green
Write-Host "  Next: cd to your project and run the project setup script." -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
