# TOOLS.md — NETA AI Development Tools
# Last updated: 2026-05-24

## Claude Code Plugins
- superpowers: Enhanced code capabilities
- context7: Extended context awareness
- code-simplifier: Code simplification utilities
- context-mode: Context management

## MCPs (Model Context Protocol)
- filesystem: File system access
- memory: Persistent memory system (C:\Users\Vinod\.claude\projects\D--NETA-AI\memory\)
- sequential-thinking: Logical reasoning chains

## Session Management

### Launch Sessions
```bash
.\neta-sessions.ps1 -session 01-database-design
.\neta-sessions.ps1 -session 02-security-auth
.\neta-sessions.ps1 -session 03-geojson-mapping
.\neta-sessions.ps1 -session 04-ground-operations
```

### List Available Sessions
```bash
.\neta-sessions.ps1 -session list
```

## Development Commands

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_ground_operations_unit.py -v

# Run with coverage
pytest tests/ --cov=app
```

### Code Quality
```bash
# Type checking (requires mypy)
mypy app/

# Linting (requires pylint/flake8)
pylint app/
```

### Development Server
```bash
# Start FastAPI dev server
uvicorn app.main:app --reload

# Access API docs
http://localhost:8000/api/docs (Swagger)
http://localhost:8000/api/redoc (ReDoc)
```

### Database Migrations
```bash
# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"
```

## Project Structure
```
D:\NETA.AI/
├── app/
│   ├── database_design/      ✅ Session 01
│   ├── security_auth/        ✅ Session 02
│   ├── geojson_mapping/      ✅ Session 03
│   ├── ground_operations/    ✅ Session 04
│   ├── main.py               (FastAPI app entry)
│   └── config.py             (Environment config)
├── tests/
│   ├── conftest.py           (Pytest fixtures)
│   └── test_*.py             (Test suites)
├── migrations/               (Alembic versions)
├── data/                     (Sample data, OCR cache)
├── docs/                     (API documentation)
└── README.md
```

## Key Resources

### Completion Reports
- SESSION_01_COMPLETION_REPORT.md (Database Design)
- SESSION_02_COMPLETION_REPORT.md (Security & Auth)
- SESSION_03_COMPLETION_REPORT.md (GeoJSON Mapping)
- SESSION_04_COMPLETION_REPORT.md (Ground Operations)
- PROJECT_AUDIT_SESSION_01-04.md (Comprehensive Audit)

### Memory System
- Location: C:\Users\Vinod\.claude\projects\D--NETA-AI\memory\
- Key files:
  - project_neta_ai.md (Project state & checkpoints)
  - feedback_db_connectivity.md (DB connection tips)
  - MEMORY.md (Index)

## Useful Commands

### Git Workflow
```bash
git log --oneline                    # View commit history
git status                           # Check working tree
git diff                             # Show changes
git add <file>                       # Stage changes
git commit -m "[TASK-XX] message"   # Create commit
```

### Docker (for live DB)
```bash
docker-compose ps                    # Show running containers
docker-compose logs neta_api         # View API logs
docker-compose logs neta_db          # View DB logs
```

### Python Environment
```bash
python -m venv venv                  # Create virtual env
source venv/Scripts/activate         # Activate (Windows PowerShell)
pip install -r requirements.txt      # Install dependencies
```
