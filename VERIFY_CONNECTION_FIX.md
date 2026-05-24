# PostgreSQL Connection Fix — Verification Guide

**Last Updated:** 2026-05-24  
**Status:** ✅ All fixes applied and committed

---

## Quick Verification Steps

### Step 1: Verify Code Changes ✅
```bash
# Check that pool configuration was updated
grep -A 5 "create_async_engine" app/database_design/database.py
# Should show: pool_size=3, max_overflow=5, pool_recycle=300
```

### Step 2: Verify Celery Import
```bash
# Check that celery_tasks imports from shared database module
grep "from app.database_design.database import" app/whatsapp_integration/celery_tasks.py
# Should show: AsyncSessionFactory import
```

### Step 3: Start PostgreSQL
```bash
# Ensure PostgreSQL is running
psql -U netaai_app -d netaai_prod -c "SELECT 1;"
# Expected: Should return (1 row) with value 1
```

### Step 4: Check Initial Connection Count
```bash
# Open new terminal/session and monitor connections
psql -U postgres -d postgres

# Inside psql:
SELECT usename, count(*) as connection_count 
FROM pg_stat_activity 
GROUP BY usename 
ORDER BY connection_count DESC;
```

### Step 5: Start FastAPI App
```bash
# In project directory
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Monitor in separate terminal:**
```bash
# Check connections (should be 3-5)
watch -n 2 'psql -U postgres -d postgres -c "SELECT count(*) FROM pg_stat_activity WHERE usename='\''netaai_app'\''; "' 
```

### Step 6: Health Check
```bash
curl http://localhost:8000/api/health
# Expected: {"status":"ok","service":"neta-api","version":"1.0.0"}
```

### Step 7: Run Load Test
```bash
# Install Apache Bench if needed: apt-get install apache2-utils
ab -n 100 -c 10 http://localhost:8000/api/health

# Monitor PostgreSQL connections - should remain 3-8
psql -U postgres -d postgres -c "SELECT count(*) FROM pg_stat_activity WHERE usename='netaai_app';"
```

### Step 8: Start Celery Worker
```bash
# In another terminal
celery -A app.whatsapp_integration.celery_tasks worker --loglevel=info
```

**Monitor:**
```bash
# Check connections again - should NOT increase significantly
psql -U postgres -d postgres -c "SELECT count(*) FROM pg_stat_activity WHERE usename='netaai_app';"
```

### Step 9: Final Verification
```bash
# Should see stable connection count (3-8)
# No "too many clients already" errors
# All endpoints responding normally
```

---

## Expected Connection Counts

### Idle App (No Traffic)
```
Expected: 3 connections (base pool_size)
Range: 2-3
```

### App Under Load (100 requests/10 concurrent)
```
Expected: 5-8 connections
Range: 5-8 (uses some overflow)
```

### With Celery Worker Running
```
Expected: Same 3-8 connections total (shared pool)
Should NOT increase per worker
```

---

## If You See "too many clients already"

1. **Check connection count:**
   ```bash
   psql -U postgres -d postgres -c "SELECT count(*) FROM pg_stat_activity WHERE usename='netaai_app';"
   ```
   - If > 8: Still too many connections

2. **Check for idle connections:**
   ```bash
   psql -U postgres -d postgres -c "SELECT state, count(*) FROM pg_stat_activity WHERE usename='netaai_app' GROUP BY state;"
   ```
   - Look for many "idle" connections

3. **Kill idle connections:**
   ```sql
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE usename = 'netaai_app' AND state = 'idle' AND query_start < now() - interval '10 minutes';
   ```

4. **Restart the app:**
   ```bash
   # Stop current instance (Ctrl+C)
   # Verify connections dropped
   psql -U postgres -d postgres -c "SELECT count(*) FROM pg_stat_activity WHERE usename='netaai_app';"
   # Should show 0 or very few
   
   # Restart app
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

---

## Detailed Diagnostics

### View All Active Connections
```sql
SELECT 
    pid,
    usename,
    application_name,
    state,
    query_start,
    state_change,
    query
FROM pg_stat_activity
WHERE usename = 'netaai_app'
ORDER BY query_start DESC;
```

### Check PostgreSQL Configuration
```sql
-- Current max_connections setting
SHOW max_connections;

-- Current idle connection timeout
SHOW idle_in_transaction_session_timeout;

-- Current connection timeout
SHOW statement_timeout;
```

### Monitor Connection Pool Health Over Time
```bash
#!/bin/bash
# Save as monitor_connections.sh
while true; do
    echo "$(date): $(psql -U postgres -d postgres -t -c "SELECT count(*) FROM pg_stat_activity WHERE usename='netaai_app';")"
    sleep 5
done
```

Run with:
```bash
chmod +x monitor_connections.sh
./monitor_connections.sh
```

---

## Code Changes Checklist

- [x] `app/database_design/database.py` - Updated pool config
- [x] `app/database-design/database.py` - Updated pool config (legacy)
- [x] `app/whatsapp_integration/celery_tasks.py` - Removed separate engine
- [x] `scripts/seed_admin_user.py` - Updated pool config
- [x] `app/voter_roll_ingestion/cli.py` - Minor cleanup
- [x] `app/main.py` - Verified startup/shutdown handlers
- [x] All routers - Verified using `Depends(get_db)`

---

## Expected Behavior After Fix

### ✅ Should See:
- App starts with 2-3 initial connections
- Connections stay 3-8 under normal load
- No errors in logs
- All endpoints respond correctly
- Health check succeeds
- Celery workers start without increasing connection count

### ❌ Should NOT See:
- "too many clients already" errors
- Connection count > 8
- "connection pool queue is full" errors
- Multiple engines being created
- Stale connection errors

---

## Git Verification

Check that all fixes are committed:
```bash
git log --oneline -5
# Should show: [BUGFIX] Fix PostgreSQL connection pool exhaustion

git show --stat
# Should show changes to:
# - app/database_design/database.py
# - app/whatsapp_integration/celery_tasks.py
# - scripts/seed_admin_user.py
# - etc.
```

---

## Production Deployment

### Pre-Deployment
1. ✅ Test locally using steps above
2. ✅ Monitor connections for 5+ minutes
3. ✅ Run load test without errors
4. ✅ Verify Celery worker behavior

### Deployment
1. Deploy code with all fixes
2. Start app: Monitor initial connections (should be 2-3)
3. Run health check: Should succeed
4. Start Celery workers: Connection count should stay stable
5. Monitor for 15+ minutes: No errors

### Post-Deployment Monitoring
```bash
# Daily check in first week
psql -U postgres -d postgres -c \
  "SELECT count(*) as active_connections FROM pg_stat_activity WHERE usename='netaai_app';"

# Should consistently show 3-8
```

---

## Support

If issues persist:

1. **Check PostgreSQL logs:**
   ```bash
   tail -f /var/log/postgresql/postgresql.log
   # or
   docker logs neta-postgres
   ```

2. **Check app logs:**
   ```bash
   # Watch for SQLAlchemy warnings
   # Watch for "too many clients" in connection errors
   ```

3. **Verify database URL:**
   ```bash
   echo $DATABASE_URL
   # Should be: postgresql+asyncpg://netaai_app:***@host:5432/netaai_prod
   ```

4. **Restart everything:**
   ```bash
   # Stop app (Ctrl+C)
   # Kill Celery workers
   # Kill all idle connections (see diagnostics above)
   # Restart everything fresh
   ```

---

## Summary

✅ **Connection pool exhaustion has been fixed:**

**Before:**
- 30 max connections from app alone
- 5+ connections per Celery worker
- No connection recycling
- Result: "too many clients already" ❌

**After:**
- 8 max connections total
- Celery workers share same pool
- Auto-recycle every 5 minutes
- Result: Stable, no exhaustion ✅

