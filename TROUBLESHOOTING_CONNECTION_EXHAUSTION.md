# PostgreSQL Connection Exhaustion — Troubleshooting Guide

**Error:** `FATAL: sorry, too many clients already`  
**Status:** Investigating and diagnosing

---

## IMMEDIATE ACTIONS (Do These First)

### Step 1: Stop All Running Processes

```bash
# Kill FastAPI app if running
# Press Ctrl+C in the terminal where you started it

# Kill Celery workers if running
# Press Ctrl+C 

# Kill any other Python processes using PostgreSQL
ps aux | grep python
# Kill any neta-related processes:
# kill -9 <PID>
```

### Step 2: Run Diagnostic Script

```bash
cd D:\NETA.AI
python scripts/diagnose_connection_leak.py
```

This will show:
- How many connections are currently open
- Which users have connections
- How long connections have been idle
- Potential connection leaks

### Step 3: Analyze the Output

Look for:
- **Total connections > 80?** → Critical, need cleanup
- **Idle connections from hours ago?** → Potential leak
- **Long-running queries?** → Process is hung

---

## CLEANUP STRATEGIES

### Option A: Safe Cleanup (Kill Only Idle Connections)

```bash
python scripts/cleanup_db_connections.py --kill-idle
```

**What it does:**
- Terminates connections that have been idle for > 5 minutes
- Safe - app can reconnect
- Should free up connection slots

**Expected outcome:**
- Frees 10-30 connections
- App should be able to connect again

---

### Option B: Full Cleanup (Disconnect Everything)

```bash
python scripts/cleanup_db_connections.py --kill-all
```

**What it does:**
- Terminates ALL connections to the database
- **This disconnects the app completely**
- Forces app to reconnect from scratch

**When to use:**
- When Option A doesn't work
- When you're sure no important queries are running

**Expected outcome:**
- Frees all connections
- App must be restarted
- Fresh connection pool created

---

### Option C: Restart PostgreSQL Entirely

**On Windows:**

```bash
# Using Services Manager
Win+R → services.msc → Find "PostgreSQL" → Right-click → Restart

# Or via command line:
net stop postgresql-x64-16
net start postgresql-x64-16
```

**On Linux/Docker:**

```bash
# Docker
docker restart neta-postgres

# Systemd
sudo systemctl restart postgresql
```

---

## DETAILED TROUBLESHOOTING

### Problem: Still Getting "too many clients" After Cleanup?

**Possible causes:**

1. **App is still running**
   ```bash
   # Find app process
   netstat -ano | findstr :8000
   # Kill it if needed
   taskkill /PID <PID> /F
   ```

2. **Test connection with psql directly**
   ```bash
   # This is what the user is trying to do
   psql -U postgres -h 127.0.0.1
   # If this fails → PostgreSQL itself is at limit
   ```

3. **PostgreSQL needs restart**
   ```bash
   # Restart PostgreSQL completely
   # See "Option C" above
   ```

### Problem: App Connects but Crashes After Few Requests?

**Symptoms:**
- App starts fine
- After 1-2 API calls, connection error
- Always fails at the same place

**Solution:**

Run diagnostic again:
```bash
python scripts/diagnose_connection_leak.py
```

Check for:
- Idle connections accumulating
- Long-running queries that won't release
- Connections stuck in transaction

**Then:**
1. Clean up with `--kill-idle`
2. Restart PostgreSQL
3. Start app fresh
4. Verify with health check

### Problem: Connections Keep Growing Even After App Restart?

**This indicates a leak in the application code.**

**Check:**
1. Are there background processes still running?
   ```bash
   python scripts/diagnose_connection_leak.py
   # Look at "application_name" column - what's creating connections?
   ```

2. Is Celery worker still running?
   ```bash
   ps aux | grep celery
   kill -9 <PID>
   ```

3. Are there test processes running?
   ```bash
   ps aux | grep pytest
   kill -9 <PID>
   ```

4. Multiple app instances?
   ```bash
   ps aux | grep "uvicorn\|main"
   # Should only be ONE running
   ```

---

## ROOT CAUSE ANALYSIS

Once you've cleaned up, let's identify why this happened:

### 1. Check Connection Pool Configuration

**File:** `app/database_design/database.py`

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=3,           # ✅ Should be 3 (not 10+)
    max_overflow=5,        # ✅ Should be 5 (not 20+)
    pool_pre_ping=True,    # ✅ Must be True
    pool_recycle=300,      # ✅ Must be present (5 min recycle)
    echo=settings.DEBUG,
)
```

**If this is wrong → We'll fix it**

### 2. Check for Multiple Engine Creations

Search for anywhere else `create_async_engine` is used:

```bash
grep -r "create_async_engine\|create_engine" D:/NETA.AI/app --include="*.py" | grep -v __pycache__
```

Expected results:
```
D:/NETA.AI/app/database_design/database.py:    engine = create_async_engine(
```

If you see MULTIPLE (especially in scripts or Celery tasks) → We need to consolidate

### 3. Check All Sessions Use Context Managers

All database sessions should use:
```python
async with AsyncSessionFactory() as session:
    # use session
    # auto-closes here
```

NOT:
```python
session = AsyncSessionFactory()
# If session is never closed, connections leak!
```

### 4. Check App Shutdown Cleanup

**File:** `app/main.py`

Must have:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.execute(...)
    yield
    # Shutdown - CRITICAL
    await engine.dispose()  # ✅ This MUST be here
```

---

## VERIFICATION TESTS

Once you think it's fixed:

### Test 1: PostgreSQL Connectivity

```bash
psql -U postgres -h 127.0.0.1 -c "SELECT 1;"
```

**Should print:**
```
(1 row)
```

### Test 2: App Startup

```bash
cd D:/NETA.AI
python -m uvicorn app.main:app --reload
```

**Should print:**
```
Uvicorn running on http://127.0.0.1:8000
```

**Immediately run in another terminal:**
```bash
python scripts/diagnose_connection_leak.py
```

**Should show:**
- Connection count: 3-5 (NOT 30+)
- No idle connections from hours ago
- App user (netaai_app) should have 2-3 connections

### Test 3: Health Check

```bash
curl http://localhost:8000/api/health
```

**Should return:**
```json
{"status":"ok","service":"neta-api","version":"1.0.0"}
```

### Test 4: Load Test

```bash
# Install Apache Bench if needed
# Then run:
ab -n 50 -c 5 http://localhost:8000/api/health
```

**Should:**
- Complete all requests (100% success)
- Show stable connection count (3-8)
- No "too many clients" errors

**Monitor in another terminal:**
```bash
python scripts/diagnose_connection_leak.py
```

### Test 5: Start Celery Worker

```bash
celery -A app.whatsapp_integration.celery_tasks worker --loglevel=info
```

**Should:**
- Start without errors
- NOT increase connection count significantly
- Still have 3-8 total connections

---

## If Problem Persists

If you've tried all this and still getting errors:

### Enable Debug Logging

**File:** `.env`
```
DEBUG=True
SQLALCHEMY_ECHO=True
```

### Restart app with logging

```bash
python -m uvicorn app.main:app --reload
```

Watch for connection-related errors

### Check for Queries Holding Locks

```bash
python scripts/cleanup_db_connections.py --show-locks
```

Some query might be holding a transaction open

### Possible Causes to Investigate

1. **Race condition in concurrent code**
   - Multiple requests trying to use same session
   - Fix: Ensure all endpoints use `Depends(get_db)`

2. **Background task not closing sessions**
   - Look in all `@app.on_event()` handlers
   - Ensure they close sessions properly

3. **Test process left running**
   - `pytest` or similar test runner left a process
   - Kill all Python processes and restart

4. **Docker networking issue**
   - If PostgreSQL is in Docker, connection string might be wrong
   - Check: `host.docker.internal` vs `localhost` vs IP address

---

## Quick Reference Commands

```bash
# Show all active connections
python scripts/diagnose_connection_leak.py

# Show just the count
psql -U postgres -h 127.0.0.1 -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
python scripts/cleanup_db_connections.py --kill-idle

# Kill everything (dangerous!)
python scripts/cleanup_db_connections.py --kill-all

# Restart app
# 1. Ctrl+C to stop
# 2. Run cleanup script
# 3. python -m uvicorn app.main:app --reload

# Check pool config
grep "pool_size\|max_overflow\|pool_recycle" app/database_design/database.py
```

---

## Summary

**If you see "too many clients":**

1. ✅ Run: `python scripts/diagnose_connection_leak.py`
2. ✅ Stop app (Ctrl+C)
3. ✅ Run: `python scripts/cleanup_db_connections.py --kill-idle`
4. ✅ Verify: `psql -U postgres -h 127.0.0.1 -c "SELECT 1;"`
5. ✅ Restart app
6. ✅ Test: `curl http://localhost:8000/api/health`

**If problem persists:**
1. ✅ Check pool config in `app/database_design/database.py`
2. ✅ Check for multiple engines with `grep -r "create_async_engine"`
3. ✅ Verify all sessions use `async with` context managers
4. ✅ Kill all Python processes and restart PostgreSQL
5. ✅ Ask for help if still stuck

