# NETA AI On-Call Engineer Runbook

**Version:** 1.0  
**Last Updated:** 2026-05-24  
**Maintained by:** DevOps Team

---

## Quick Access

- **Status Page:** https://status.netaai.in
- **Slack:** #neta-ai-oncall
- **PagerDuty:** https://netaai.pagerduty.com
- **Grafana Dashboards:** https://grafana.netaai.in
- **Logs:** https://logs.netaai.in (ELK Stack)

---

## Incident Response Framework

### 1. Initial Assessment (0-5 minutes)
1. **Acknowledge alert** in PagerDuty
2. **Check status page** for known incidents
3. **Review Grafana dashboard** for resource usage and error rates
4. **Read recent logs** in ELK for error patterns
5. **Assess severity:**
   - **P1 (Critical):** API down, data loss, security breach
   - **P2 (High):** API slow (>5s), feature broken, high error rate
   - **P3 (Medium):** Feature degraded, non-critical service down
   - **P4 (Low):** Warnings, cosmetic issues, performance <10% degradation

### 2. Communication (Immediate)
- **P1/P2:** Notify team lead + engineering manager
- **P1:** Post to #neta-ai-incident Slack channel
- **Status Update:** Update status page every 15 minutes

### 3. Mitigation (5-30 minutes)
- Follow runbooks below for your scenario
- If unsure, **escalate to on-call engineer** (don't wait)
- Document all actions taken (for post-incident review)

### 4. Resolution & Follow-up
- Once resolved, update PagerDuty with resolution time
- Create incident post-mortem (P1/P2 only)
- Update runbooks based on lessons learned

---

## Common Scenarios

### Scenario 1: API Returning 502 Bad Gateway

**Severity:** P2  
**Time to Resolve:** 5 minutes  
**Root Causes:** API crashed, database unreachable, out of memory

**Steps:**
```bash
# 1. Check API service status
docker-compose ps api
# Expected: service should be "Up" with healthy status

# 2. Check recent logs for crash reason
docker-compose logs api | tail -50

# 3. Check if database is responding
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "SELECT 1"

# 4. Check API memory usage
docker stats neta_api --no-stream

# If memory > 90%:
# → Restart API service
docker-compose restart api
# → Wait 30s for startup
sleep 30
# → Verify health
curl http://localhost:8000/api/health

# If database error:
# → Check database logs
docker-compose logs postgres | tail -50
# → If connection pool exhausted, increase pool size (see DEPLOYMENT.md)
# → Restart database
docker-compose restart postgres
```

**Prevention:**
- Set memory limits in docker-compose.prod.yml (2G for API)
- Monitor memory trend in Grafana
- Alert if error rate > 1%

---

### Scenario 2: High Response Time (API Slow > 5 seconds)

**Severity:** P2  
**Time to Resolve:** 10-15 minutes  
**Root Causes:** Slow database query, network latency, resource contention

**Steps:**
```bash
# 1. Check resource usage
docker stats

# 2. Identify slow database queries
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# 3. Check for database locks
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "SELECT * FROM pg_locks WHERE NOT granted;"

# 4. If locks exist, find blocking queries:
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# 5. If query is stuck, gracefully terminate it (DON'T force kill)
# SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE query LIKE '%slow_query%';

# 6. Check network latency
docker-compose exec api ping redis
docker-compose exec api ping postgres

# 7. Add database query to slow query log:
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "ALTER DATABASE netaai_prod SET log_min_duration_statement = 1000;"  # Log queries > 1s

# 8. Increase Celery worker concurrency if processing alerts is slow
docker-compose exec celery-worker celery -A app.whatsapp_integration.celery_tasks \
  control pool_restart --all
```

**Prevention:**
- Review slow query logs daily
- Add indexes for frequently filtered columns
- Tune SQLALCHEMY_POOL_SIZE based on concurrency (start at 50)

---

### Scenario 3: Celery Worker Not Processing Tasks

**Severity:** P2  
**Time to Resolve:** 5-10 minutes  
**Root Causes:** Worker crashed, Redis connection lost, task queue backlog

**Steps:**
```bash
# 1. Check worker status
docker-compose exec celery-worker celery -A app.whatsapp_integration.celery_tasks inspect active

# 2. If no response, check Redis connectivity
docker-compose exec redis redis-cli ping
# Expected: PONG

# 3. Check if worker process is actually running
docker-compose ps celery-worker
# Expected: status "Up"

# 4. Check recent worker logs
docker-compose logs celery-worker | tail -50

# 5. Check queue depth (how many tasks pending)
docker-compose exec redis redis-cli LLEN notification_queue:pending

# 6. If queue is deep (>1000), worker might be overwhelmed
# → Increase worker concurrency
docker-compose exec celery-worker celery -A app.whatsapp_integration.celery_tasks control pool_resize 16

# 7. Restart worker if stuck
docker-compose restart celery-worker

# 8. Monitor recovery
docker-compose logs celery-worker -f
```

**Prevention:**
- Monitor queue depth in Grafana (alert if > 5000)
- Check worker logs daily for task failures
- Set task timeout limits to prevent hung tasks

---

### Scenario 4: Database Disk Space Full (100%)

**Severity:** P1  
**Time to Resolve:** 20-30 minutes  
**Root Causes:** Large tables, too many logs, old backups

**Steps:**
```bash
# 1. Check overall disk usage
df -h

# 2. Check Docker volume usage
du -sh /var/lib/docker/volumes/*

# 3. Check database size
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "SELECT pg_size_pretty(pg_database_size('netaai_prod'));"

# 4. Find large tables
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"

# 5. Clean up old logs (if stored in database)
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days';"

# 6. Vacuum and analyze to reclaim space
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "VACUUM ANALYZE; SELECT pg_size_pretty(pg_database_size('netaai_prod'));"

# 7. If still full, check backup directory
du -sh /app/backups/

# 8. Delete old backups if needed
find /app/backups/ -name "*.sql.gz" -mtime +30 -delete

# 9. Check Docker logs (might be huge)
du -sh /var/lib/docker/containers/*/

# If logs are huge, restart services (rotates logs)
docker-compose restart api celery-worker celery-beat

# 10. Monitor recovery
df -h
```

**Prevention:**
- Set up log rotation in docker-compose.prod.yml (max-size: 10m, max-file: 3)
- Archive/delete alerts older than 90 days monthly
- Monitor disk usage in Grafana (alert at 80%)

---

### Scenario 5: Redis Connection Lost

**Severity:** P2  
**Time to Resolve:** 5 minutes  
**Root Causes:** Redis crashed, password changed, port conflict

**Steps:**
```bash
# 1. Check Redis status
docker-compose ps redis

# 2. Try to ping Redis
docker-compose exec redis redis-cli ping

# 3. Check Redis logs
docker-compose logs redis | tail -50

# 4. Check if Redis is listening on correct port
docker-compose exec redis redis-cli INFO server | grep port

# 5. Verify Redis password in .env
grep REDIS_PASSWORD .env

# 6. If password mismatch, update .env and restart
docker-compose restart redis

# 7. Wait for Redis to be healthy
sleep 5
docker-compose exec redis redis-cli ping

# 8. After Redis is back, check Celery and API connectivity
docker-compose restart celery-worker celery-beat api

# 9. Verify all services are running
docker-compose ps
```

**Prevention:**
- Monitor Redis memory usage (alert at 80%)
- Set Redis maxmemory policy to allkeys-lru (evict oldest)
- Monitor Redis replication lag if using sentinel

---

### Scenario 6: Database Connection Pool Exhausted

**Severity:** P2  
**Time to Resolve:** 10 minutes  
**Root Causes:** Connection leak, long-running queries, traffic spike

**Steps:**
```bash
# 1. Check current connection count
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "SELECT count(*) FROM pg_stat_activity;"

# 2. Check max_connections setting
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "SHOW max_connections;"

# 3. If approaching limit (e.g., 95/100), identify idle connections
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "SELECT pid, usename, state, query_start FROM pg_stat_activity WHERE state = 'idle' ORDER BY query_start ASC;"

# 4. Gracefully close idle connections (>5 minutes)
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < NOW() - INTERVAL '5 minutes';"

# 5. Restart API service to reset its connection pool
docker-compose restart api

# 6. Increase max_connections in docker-compose.yml
# Edit docker-compose.yml, add to postgres service:
# command: postgres -c max_connections=200

# 7. Apply changes
docker-compose up -d postgres

# 8. Verify new limit
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "SHOW max_connections;"

# 9. Monitor connection pool in Grafana
```

**Prevention:**
- Set SQLALCHEMY_POOL_RECYCLE = 3600 (recycle connections every hour)
- Monitor connection pool in Grafana (alert at 80%)
- Review for connection leaks in application code

---

### Scenario 7: Celery Task Timeout / SoftTimeLimitExceeded

**Severity:** P3  
**Time to Resolve:** 15-30 minutes  
**Root Causes:** Long-running task, slow database query, resource bottleneck

**Steps:**
```bash
# 1. Check Celery logs for timeout messages
docker-compose logs celery-worker | grep -i timeout | tail -20

# 2. Identify the slow task
docker-compose logs celery-worker | grep "SoftTimeLimitExceeded" | awk '{print $NF}' | sort | uniq -c

# 3. Increase task timeout in celeryconfig.py
# Current: soft=600s, hard=900s (10 min / 15 min)
# Change to: soft=1200s, hard=1800s (20 min / 30 min) for long tasks

# 4. Rebuild Docker image with updated config
docker-compose build celery-worker

# 5. Restart worker
docker-compose restart celery-worker

# 6. Monitor task completion in Celery Flower
celery -A app.whatsapp_integration.celery_tasks flower
# Access at http://localhost:5555

# 7. Profile the slow task
# Add timing logs in the task code to identify bottleneck
# Re-optimize the query or split into sub-tasks
```

**Prevention:**
- Break long tasks into smaller sub-tasks
- Optimize slow database queries
- Cache frequently accessed data (Redis)
- Monitor task execution time in Flower/Grafana

---

### Scenario 8: Out of Memory (OOM Killed)

**Severity:** P1  
**Time to Resolve:** 10-15 minutes  
**Root Causes:** Memory leak, inefficient query, traffic spike

**Steps:**
```bash
# 1. Check container memory usage
docker stats --no-stream

# 2. Identify which service is consuming memory
docker stats neta_api --no-stream
docker stats neta_postgres --no-stream
docker stats neta_celery_worker --no-stream

# 3. Check if service was killed by OOM
docker inspect neta_api | grep -i oom
# Look for "OOMKilled": true

# 4. Increase memory limit in docker-compose.prod.yml
# Current: api (2G), postgres (2G), celery-worker (1G)
# Example:
# services:
#   api:
#     deploy:
#       resources:
#         limits:
#           memory: 4G  # Increase from 2G

# 5. Restart the service
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 6. Monitor memory trend
docker stats neta_api --no-stream
watch docker stats

# 7. If memory keeps growing, check for memory leak
docker-compose logs api | grep -i "memory"
# Look for warnings about increasing memory usage

# 8. Restart API after a few minutes if memory is still growing
docker-compose restart api
```

**Prevention:**
- Set memory limits in production (2G for API, 2G for DB, 1G for worker)
- Monitor memory trend in Grafana (alert at 80%)
- Review code for connection leaks, unclosed file handles
- Set SQLALCHEMY_POOL_RECYCLE to prevent connection leaks

---

### Scenario 9: Application Crash Loop (Restart Loop)

**Severity:** P1  
**Time to Resolve:** 15-20 minutes  
**Root Causes:** Bad deployment, database migration failure, config error

**Steps:**
```bash
# 1. Check service status
docker-compose ps api

# 2. Check recent logs for crash reason
docker-compose logs api --tail 100

# Common crash reasons:
# - "SyntaxError" or "ImportError" → code issue, check recent commits
# - "alembic.util.exc.CommandError" → migration failure
# - "DATABASE_URL not configured" → environment variable missing

# 3. If migration failed, check current migration state
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "SELECT * FROM alembic_version ORDER BY version_num DESC LIMIT 5;"

# 4. Rollback last migration
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c \
  "DELETE FROM alembic_version ORDER BY version_num DESC LIMIT 1;"

# 5. Retry startup
docker-compose restart api

# 6. If still failing, check .env configuration
grep -E "DATABASE_URL|REDIS_URL|SECRET_KEY" .env
# Ensure all required variables are set

# 7. If issue is code-related, rollback to previous Docker image
# From git history:
git log --oneline | head -5
# Find the last known-good commit
git checkout <commit-hash>

# Rebuild image
docker-compose build api
docker-compose restart api

# 8. Once stable, investigate root cause in development
```

**Prevention:**
- Always test migrations in staging before production
- Run CI/CD tests before merging to main
- Monitor application logs for warnings
- Have a quick rollback procedure

---

### Scenario 10: Deployment Failed (Smoke Tests Failing)

**Severity:** P1  
**Time to Resolve:** 20-30 minutes  
**Root Causes:** API not healthy, database migration failed, backwards incompatibility

**Steps:**
```bash
# 1. Check smoke test results in GitHub Actions
# Go to: https://github.com/your-org/neta-ai/actions

# 2. Check API health endpoint
curl -v http://localhost:8000/api/health

# Expected response:
# {
#   "status": "ok",
#   "service": "neta-api",
#   "version": "1.0.0",
#   "dependencies": {
#     "database": "ok",
#     "redis": "ok",
#     "celery": "ok"
#   }
# }

# 3. If health check failing, check logs
docker-compose logs api | tail -50

# 4. Check if database is healthy
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "SELECT 1"

# 5. Check if migrations succeeded
docker-compose exec api alembic current

# 6. If migration is behind, manually upgrade
docker-compose exec api alembic upgrade head

# 7. If still failing, check recent code changes
git log --oneline -10

# 8. Rollback to previous version (if enabled in deployment)
# From GitHub Actions workflow, select "Enable Rollback" and approve

# OR manually:
git revert <failing-commit-hash>
git push
# Wait for CI/CD to rebuild and deploy

# 9. Once rolled back, investigate issue in development
```

**Prevention:**
- Run full test suite locally before pushing
- Test database migrations in staging
- Have a staging environment that mirrors production
- Always test backwards compatibility

---

## Escalation Path

**Level 1 (You):** Initial assessment, follow runbooks
- **Action Time:** 5 minutes
- **If Resolved:** Document in incident log, close ticket
- **If Unresolved:** Escalate to Level 2

**Level 2 (On-Call Lead):** Senior engineer, infrastructure decisions
- **Action Time:** 10 minutes (from Level 1 escalation)
- **Resources:** Can restart services, modify configs, access prod directly
- **If Resolved:** Post-mortem + lessons learned
- **If Unresolved:** Escalate to Level 3

**Level 3 (Engineering Manager):** Major decisions, customer communication
- **Action Time:** 15 minutes (from Level 2 escalation)
- **Resources:** Can approve emergency changes, notify customers
- **Decision:** Continue mitigation OR rollback to last known-good state

**Escalation Contact:**
- **On-Call Lead:** PagerDuty (automatic page)
- **Manager:** +91-XXXXXXXXXX (emergency phone)
- **Status Page:** Update at each escalation level

---

## Key Commands Cheat Sheet

```bash
# Service Management
docker-compose ps                      # View all service status
docker-compose logs -f SERVICE         # Follow logs for a service
docker-compose restart SERVICE         # Restart a service
docker-compose exec SERVICE COMMAND    # Run command in container

# Database
psql -h postgres -U netaai_app -d netaai_prod  # Connect to database
SELECT * FROM pg_stat_activity;                # Current connections
SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
VACUUM ANALYZE;                                # Reclaim disk space

# Redis
redis-cli ping                         # Test Redis connectivity
redis-cli LLEN notification_queue:pending  # Check queue depth
redis-cli FLUSHALL                     # Clear all data (USE WITH CAUTION)

# Celery
celery -A app.whatsapp_integration.celery_tasks inspect active   # Active tasks
celery -A app.whatsapp_integration.celery_tasks inspect ping     # Worker alive?
celery -A app.whatsapp_integration.celery_tasks control pool_resize 16  # Scale workers

# Health Checks
curl http://localhost:8000/api/health  # API health
docker-compose exec api alembic current # Migration status
docker stats                            # Resource usage
df -h                                   # Disk usage
```

---

## Useful Links

- **DEPLOYMENT.md** - Full deployment guide
- **TROUBLESHOOTING.md** - Detailed troubleshooting steps
- **docker-compose.yml** - Service configuration
- **GitHub Actions** - CI/CD workflows
- **Grafana** - Monitoring dashboards
- **ELK Stack** - Log aggregation
- **PagerDuty** - Alert routing

---

## Post-Incident Review

After resolving a P1/P2 incident:

1. **Write incident post-mortem** (within 24 hours)
   - Timeline: What happened and when
   - Root cause: Why did it happen
   - Impact: How many users affected, how long
   - Fix: What was done to resolve
   - Prevention: How to avoid in future

2. **Update runbooks** based on lessons learned

3. **Create GitHub issue** for permanent fix if needed

4. **Review with team** in next standup

---

**Last Updated:** 2026-05-24  
**Maintained by:** DevOps Team  
**Contact:** #neta-ai-oncall on Slack
