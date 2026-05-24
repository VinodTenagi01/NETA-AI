# NETA AI — Developer Session Guidelines

This guide details the development workflow for the NETA AI Political Campaign Intelligence Platform. Follow these steps to set up your environment, launch context-constrained development sessions using `neta-sessions.ps1`, and manage the Claude Code CLI token lifecycle.

---

## 1. Initial Machine Setup

Before starting, ensure all PowerShell script execution permissions are unblocked and the appropriate execution policies are configured.

### Step 1.1: Unblock PowerShell Scripts
Unblock all generated session and setup scripts in the repository:
```powershell
Get-ChildItem -Filter *.ps1 -Recurse | Unblock-File
```

### Step 1.2: Set Execution Policy
Enable script execution for your active PowerShell process:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

---

## 2. Listing & Running Sessions

All feature implementation is divided into chronological, isolated sessions to keep Claude Code focused and prevent context pollution.

### Step 2.1: View Available Sessions
List all chronological sessions, their corresponding task numbers, descriptions, and target AI models:
```powershell
.\neta-sessions.ps1 -Session list
```

### Step 2.2: Launch a Development Session
To begin work on a module, run the session launcher. 
> [!IMPORTANT]
> **To avoid typographical errors, always ask Antigravity (or Claude Code) for the exact session parameter command to run.**

For example, to start the first database schema phase:
```powershell
.\neta-sessions.ps1 -Session 01-database-design
```

When you execute a session:
1. The script extracts the relevant specifications from the PRD.
2. It generates a custom development prompt containing the stack, module scope, task file location, and PRD rules.
3. It copies this custom prompt to your clipboard automatically.
4. It sets the appropriate environment variables and launches the Claude Code CLI using the designated model (e.g., `claude-haiku` for mechanical schema/boilerplate, `claude-sonnet` for core logic).
5. **Action Required**: Once Claude Code loads, simply paste the clipboard contents (`Ctrl+V` or right-click) to initialize the session context.

---

## 3. Claude Code Lifecycle & The 80% Rule

To ensure reliability, avoid code degradation, and save token costs, you must strictly manage Claude Code's context window.

> [!WARNING]
> **NEVER use the `/compact` command. It poisons the session memory and degrades model intelligence. Instead, follow the exit and refresh cycle below.**

### The 80% Context Reset Cycle
1. **Monitor Context usage**: Watch the context usage percentage (e.g., `80%`) displayed on your terminal status line (provided by `cc-status-line`).
2. **Trigger Limit**: As soon as context usage reaches **80%**:
   - Save your work.
   - Exit Claude Code (press `Esc` or type `exit`).
3. **Persist State**: Update the project's memory file (`/memory` or memory MCP state) with the latest changes, decisions, schema edits, and outstanding tasks.
4. **Git Synchronization**:
   Commit and push your current progress:
   ```powershell
   git status
   git diff
   git add .
   git commit -m "[TASK-XXX] verb: brief description of changes"
   git push origin <your-feature-branch>
   git pull origin <your-feature-branch>
   ```
5. **Resume**: Restart the session script (or ask for the command for the next session/sub-task) and paste the prompt again. This starts a fresh, 0-token context window with clean memory.

---

## 4. Troubleshooting & Debugging

### Interactive Debug Mode
If you encounter a build error or test failure, launch the debug session:
```powershell
.\neta-sessions.ps1 -Session debug
```
This copies the standard single-error troubleshooting prompt to your clipboard.

**Standard Debugging Rules**:
1. Paste the full traceback.
2. Paste **only** the specific function or code block throwing the error. Do not feed entire files into the CLI to conserve tokens.

### Project Status Audit
Audit the status of directories, tasks, and configurations to evaluate the overall completion percentage of the project:
```powershell
.\neta-sessions.ps1 -Session audit
```
This will check all folder structures, config files, and task completion records in the `tasks/` directory, outputting a real-time completion percentage score.
