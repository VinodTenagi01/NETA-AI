# PROJECT-ZERO.md
# Your personal playbook for starting any new project with Claude Code.
# Owner: Srinivas / Fidelitus Corp
# Location: D:\staging\_claude-setup\PROJECT-ZERO.md

---

## PART 1 — One-Time Machine Setup
> Run once. Never again unless you reinstall.

### Step 1 · Run generic bootstrap
```powershell
cd D:\staging\_claude-setup
.\setup-generic.ps1
```

### Step 2 · Install plugins inside Claude Code
Open Claude Code → type `/plugin` → install at **user scope**:

| Plugin          | Purpose                                        |
|-----------------|------------------------------------------------|
| superpowers     | Sub-agent orchestration (brainstorm/plan/exec) |
| code-simplifier | Refactor helper                                |
| context7        | Live API docs — no hallucinated method names   |
| context-mode    | 98% context savings on large outputs           |

### Step 3 · Warp terminal
https://warp.dev — split panels, multiple Claude instances, file viewer.

### Step 4 · Happy Engineering (mobile)
https://happy.engineering — full Claude Code on your phone.

---

## PART 2 — New Project Recipe

### For a FRESH project

1. Copy `templates\setup-project-template.ps1` → rename → fill 5 variables → run
2. Copy `templates\sessions-template.ps1` → rename → fill module prompts
3. Open Claude Code → `superpowers brainstorm`

### For a REFACTOR project (existing codebase)

1. Copy `templates\setup-project-template.ps1` → rename → fill 5 variables → run
2. Copy `templates\sessions-template.ps1` → rename → add audit session FIRST
3. **First session is always audit** — read all files, report what's broken, NO code changes
4. Open Claude Code → run `audit-module` skill → get approval → then fix

### The 5 variables (fill these in every new setup script)

```powershell
$PROJECT_NAME  = "your-project-name"
$PROJECT_ROOT  = "D:\staging\your-project"
$STACK         = "Python 3.13, FastAPI, PostgreSQL, Docker"
$MODULES       = @("module1", "module2", "module3")
$PHASE_CURRENT = 0
```

---

## PART 3 — Per-Session Discipline
> Every time you open Claude Code.

1. Check context % — limit is 50%
2. Run session launcher (not bare `claude`):
   ```powershell
   .\<project>-sessions.ps1 -Session <module>
   ```
3. Paste context template (auto-copied to clipboard)
4. Type: `superpowers brainstorm`

**NEVER /compact. Use /clear between sessions.**

### Model selection
- Haiku  → boilerplate, config, CRUD, JSON, Docker wiring
- Sonnet → real coding, debugging, APIs, LLM calls, UI
- Opus   → absolute last resort (Sonnet failed twice)

---

## PART 4 — Toolkit Structure

```
D:\staging\_claude-setup\
├── PROJECT-ZERO.md                         ← this file
├── setup-generic.ps1                       ← run once per machine
│
├── templates\
│   ├── setup-project-template.ps1          ← copy for every new project
│   └── sessions-template.ps1              ← copy for every new project
│
└── projects\
    ├── travel-agent-docker\
    │   ├── setup-travel-agent.ps1
    │   └── travel-agent-sessions.ps1
    └── resume-finetuner\
        ├── PRD.md                          ← updated v1.1
        ├── setup-resume-finetuner.ps1
        └── resume-finetuner-sessions.ps1
```

---

## PART 5 — Keeping Tools Updated

### Monthly (2 minutes)
```powershell
npm update -g
npm update -g @anthropic-ai/claude-code
```

### When Claude Code major version drops
Re-run `/plugin` inside Claude Code — update superpowers, context7.

### One bookmark only
https://github.com/hesreallyhim/awesome-claude-code — check monthly, ignore the rest.

---

*Last updated: 2026-03*
*Owner: Srinivas / Fidelitus Corp*
