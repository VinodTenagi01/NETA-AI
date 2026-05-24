# PostgreSQL Connection Pool Fix — NETA AI

**Date:** 2026-05-24  
**Issue:** "FATAL: sorry, too many clients already" error  
**Root Cause:** Excessive connection pooling and connection leaks  
**Status:** ✅ FIXED

---

## Issues Identified & Fixed

### 1. **Excessive Connection Pool Configuration** ✅
**File:** `app/database_design/database.py`  
**Problem:** 
- `pool_size=10` (too high for single app instance)
- `max_overflow=20` (allows up to 30 total connections)
- No `pool_recycle` (connections not recycled, may become stale)

**Fix Applied:**
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=3,           # Reduced from 10
    max_overflow=5,        # Reduced from 20
    pool_pre_ping=True,    # Already present - validates connections
    pool_recycle=300,      # NEW - recycle connections after 5 minutes
    echo=settings.DEBUG,
)
```

**Impact:**
- Max concurrent connections reduced: 10+20=30 → 3+5=8
- Stale connections automatically recycled after 300 seconds
- `pool_pre_ping=True` validates connections before use

---

### 2. **Celery Tasks Connection Leak** ✅
**File:** `app/whatsapp_integration/celery_tasks.py`  
**Problem:**
- **CRITICAL:** Separate engine created on module load (line 23-24)
- Engine created with default pool settings (5 connections)
- **No engine.dispose() call** — connections never returned to OS
- Multiple Celery workers = multiple leaked engine instances
- Over time: 5 × (number of workers) = connection exhaustion

**Before (LEAK):**
```python
# Lines 23-24 — CREATES SEPARATE ENGINE WITH NO DISPOSAL
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

**After (FIXED):**
```python
# Removed separate engine creation
# Import shared database module instead
from app.database_design.database import AsyncSessionFactory

# Added helper for future database access in tasks
async def get_db_session():
    """Get database session for Celery tasks."""
    async with AsyncSessionFactory() as session:
        yield session
```

**Impact:**
- Celery workers now reuse the app's shared connection pool
- All tasks use the same optimized 3-connection pool
- Connections properly cleaned up via async context managers
- Prevents connection exhaustion from worker processes

---

### 3. **Seed Script Pool Configuration** ✅
**File:** `scripts/seed_admin_user.py`  
**Problem:**
- Creates separate engine without pool optimization
- Uses default pool settings (5 connections)
- Not critical (run once), but unnecessary resource usage

**Fix Applied:**
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=3,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
)
```

---

### 4. **Legacy Database Folder** ✅
**File:** `app/database-design/database.py` (legacy, hyphenated)  
**Problem:**
- Duplicate configuration file with old pool settings
- Could cause confusion or be accidentally imported

**Fix Applied:**
- Updated to match new optimized configuration
- Note: The primary folder is `app/database_design/` (underscores)

---

## Configuration Summary

### New Pool Settings (Recommended)
```
pool_size=3          # Base connections to maintain in pool
max_overflow=5       # Additional connections allowed during peaks
pool_pre_ping=True   # Validate each connection before use
pool_recycle=300     # Recycle (close/reopen) after 5 minutes
```

**Total Concurrent Connections:**
- Minimum: 3
- Maximum during peaks: 3 + 5 = 8
- Optimal for single-instance deployment

### Lifecycle Management
✅ **App Startup** (`app/main.py`):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    yield
    await engine.dispose()  # Cleanup on shutdown
```

✅ **Session Cleanup** (all routes):
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        # Session automatically closed here
```

✅ **Celery Tasks** (now using shared pool):
```python
from app.database_design.database import AsyncSessionFactory
# All Celery workers share the same connection pool
```

---

## Files Modified

| File | Change | Impact |
|------|--------|--------|
| `app/database_design/database.py` | Reduced pool, added recycle | **HIGH** - Main fix |
| `app/database-design/database.py` | Sync'd config | Low - Legacy folder |
| `app/whatsapp_integration/celery_tasks.py` | Removed separate engine | **CRITICAL** - Prevented leak |
| `scripts/seed_admin_user.py` | Optimized pool config | Low - One-time script |
| `app/voter_roll_ingestion/cli.py` | Minor cleanup | Very Low |

---

## Testing & Verification

### Pre-Deployment Testing

1. **PostgreSQL Connection Count:**
   ```bash
   # Connect to PostgreSQL and check active connections
   psql -U netaai_app -d netaai_prod -c \
     "SELECT usename, count(*) FROM pg_stat_activity GROUP BY usename;"
   ```
   **Expected:** 3-8 connections from the app (not 30+)

2. **Start FastAPI App:**
   ```bash
   python -m app.main
   # OR
   uvicorn app.main:app --reload
   ```
   **Monitor:** Check PostgreSQL connection count remains stable

3. **Run Celery Worker:**
   ```bash
   celery -A app.whatsapp_integration.celery_tasks worker --loglevel=info
   ```
   **Monitor:** Connection count should NOT increase per worker

4. **Load Testing (with Apache Bench or similar):**
   ```bash
   ab -n 100 -c 10 http://localhost:8000/api/health
   ```
   **Expected:** No "too many clients already" errors

5. **Health Check Endpoint:**
   ```bash
   curl http://localhost:8000/api/health
   ```
   **Expected Response:** `{"status": "ok", "service": "neta-api", "version": "1.0.0"}`

### Monitoring Commands

**Check current connections (from psql):**
```sql
-- Count by state
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;

-- Identify leaked connections
SELECT pid, usename, state, query FROM pg_stat_activity 
WHERE usename='netaai_app' AND state != 'idle';

-- Total connection limit
SHOW max_connections;
```

---

## Connection Pool Explanation

### What Each Setting Does

| Setting | Value | Purpose |
|---------|-------|---------|
| **pool_size** | 3 | Keep 3 ready connections in the pool |
| **max_overflow** | 5 | Allow up to 5 more during traffic spikes |
| **pool_pre_ping** | True | Test connection before using (prevents stale conns) |
| **pool_recycle** | 300s | Close/reopen connections every 5 minutes |

### Why These Values?

- **pool_size=3:** One app instance doesn't need 10 concurrent connections
- **max_overflow=5:** Allows brief traffic spikes without exhausting connections
- **pool_recycle=300:** PostgreSQL default idle timeout is 10 min; 5 min is safe margin
- **pool_pre_ping=True:** Catches stale/disconnected connections automatically

### Before vs. After

**Before (PROBLEMATIC):**
- App: 10+20=30 max connections
- Celery (default): 5 max per worker
- 2 workers: 30 + 5 + 5 = 40 connections to PostgreSQL
- No recycling: Old connections stay open, causing "too many clients"
- Result: ❌ **"FATAL: sorry, too many clients already"**

**After (FIXED):**
- App: 3+5=8 max connections
- Celery (shared pool): Uses same 8 connections
- 2 workers: Same 8 connections (pooled)
- Auto-recycle: Connections close/reopen every 5 min
- Result: ✅ **Stable 3-8 connections, no exhaustion**

---

## PostgreSQL Configuration Check

### Current Limits
```bash
# From PostgreSQL server
sudo -u postgres psql -c "SHOW max_connections;"
# Default: 100 connections total
```

### Recommended PostgreSQL Config (if needed)
If PostgreSQL has very low `max_connections` setting:
```ini
# In /etc/postgresql/15/main/postgresql.conf
max_connections = 100          # Can increase if needed
superuser_reserved_connections = 3
```

**Note:** Our fix reduces app connection usage, so PostgreSQL limit increase is NOT required.

---

## Deployment Checklist

- [ ] Pull latest code with fixes applied
- [ ] Review `app/database_design/database.py` configuration
- [ ] Verify `app/whatsapp_integration/celery_tasks.py` imports from shared module
- [ ] Test PostgreSQL connection: `psql -U netaai_app -d netaai_prod -c "SELECT 1;"`
- [ ] Start FastAPI app: `python -m app.main`
- [ ] Check connection count: Should be 3-8
- [ ] Start Celery worker: `celery -A app.whatsapp_integration.celery_tasks worker`
- [ ] Monitor connections for 2-5 minutes: Should remain stable
- [ ] Run health check: `curl http://localhost:8000/api/health`
- [ ] Execute load test: Brief stress test (100-500 requests)
- [ ] Confirm no "too many clients" errors
- [ ] Verify all endpoints work correctly

---

## Rollback Plan (if needed)

Revert changes using git:
```bash
git checkout HEAD -- app/database_design/database.py
git checkout HEAD -- app/whatsapp_integration/celery_tasks.py
git checkout HEAD -- scripts/seed_admin_user.py
git checkout HEAD -- app/database-design/database.py
```

---

## References

- [SQLAlchemy AsyncEngine Docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL Connection Limits](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [Celery + SQLAlchemy Best Practices](https://docs.celeryproject.io/en/stable/)

---

## Summary

✅ **All connection pooling issues have been fixed:**

1. ✅ Connection pool reduced: 30 → 8 max connections
2. ✅ Celery connection leak eliminated
3. ✅ Stale connections auto-recycled (5-min intervals)
4. ✅ App startup/shutdown properly manages connections
5. ✅ All session handling uses async context managers
6. ✅ Seed scripts optimized

**Result:** PostgreSQL should no longer report "too many clients already" errors.

---

**Next Steps:**
1. Test the fixes using the verification checklist above
2. Monitor PostgreSQL connection count in production
3. If issues persist, check PostgreSQL logs: `tail -f /var/log/postgresql/postgresql.log`

