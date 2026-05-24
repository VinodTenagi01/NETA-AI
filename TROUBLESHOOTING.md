# NETA AI Troubleshooting Guide

**Version:** 1.0  
**Date:** 2026-05-24

---

## Common Issues & Solutions

### 1. Container Startup Issues

#### Issue: "Port already in use"

**Symptom:** `Error response from daemon: driver failed programming external connectivity on endpoint`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000
# or on macOS
netstat -anv | grep 8000

# Kill the process
kill -9 <PID>

# Or use a different port
docker-compose -p neta up -d --scale api=1
```

#### Issue: "Database connection refused"

**Symptom:** `psycopg2.OperationalError: FATAL: pg_hba.conf rejects connection`

**Solution:**
```bash
# Check PostgreSQL service status
docker-compose logs postgres

# Verify database credentials in .env
grep POSTGRES_ .env

# Restart PostgreSQL
docker-compose restart postgres

# Wait for healthy state
docker-compose ps postgres
```

#### Issue: "Cannot connect to Redis"

**Symptom:** `ConnectionError: Error 111 connecting to localhost:6379`

**Solution:**
```bash
# Check Redis container
docker-compose logs redis

# Verify Redis password
docker-compose exec redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d= -f2) ping

# Restart Redis
docker-compose restart redis
docker-compose exec redis redis-cli ping
```

---

### 2. Database Issues

#### Issue: "Database migration failed"

**Symptom:** `alembic.util.exc.CommandError: Can't find identifier in mappings`

**Solution:**
```bash
# Check migration status
docker-compose exec api alembic current
docker-compose exec api alembic history

# Rollback last migration
docker-compose exec api alembic downgrade -1

# Re-apply all migrations
docker-compose exec api alembic upgrade head

# If corrupted, reset (CAUTION: DESTRUCTIVE)
docker-compose exec api alembic downgrade base
docker-compose exec api alembic upgrade head
```

#### Issue: "Disk space full"

**Symptom:** `ERROR: No space left on device`

**Solution:**
```bash
# Check disk usage
df -h

# Check database size
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "SELECT pg_size_pretty(pg_database_size('netaai_prod'));"

# Check container logs
docker-compose logs api | wc -l

# Clean up old logs
docker system prune -a

# Remove old backups
find /app/backups -mtime +30 -delete
```

#### Issue: "Too many connections"

**Symptom:** `FATAL: remaining connection slots are reserved`

**Solution:**
```bash
# Check connection count
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Increase max connections in docker-compose.yml
# Add to postgres service: -c max_connections=200

# Increase connection pool size
# In app/config.py:
# SQLALCHEMY_POOL_SIZE = 50
# SQLALCHEMY_MAX_OVERFLOW = 20
```

---

### 3. API Issues

#### Issue: "502 Bad Gateway"

**Symptom:** API container running but not responding

**Solution:**
```bash
# Check API logs
docker-compose logs api -f

# Check if API is actually listening
docker-compose exec api curl http://localhost:8000/api/health

# Increase startup timeout
docker-compose up -d --health-cmd-timeout 30s

# Restart API
docker-compose restart api
```

#### Issue: "High response times (>5 seconds)"

**Symptom:** Slow API responses, timeout errors

**Solution:**
```bash
# Check API resource usage
docker stats neta_api

# Check database query performance
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Increase worker count
# In docker-compose.yml or Dockerfile:
# CMD ["uvicorn", "app.main:app", "--workers", "8"]

# Check for database locks
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "SELECT * FROM pg_locks;"
```

#### Issue: "Memory leak - API OOM killed"

**Symptom:** Container repeatedly killed with `137` exit code

**Solution:**
```bash
# Check memory usage trend
docker stats neta_api

# Increase memory limit
# In docker-compose.prod.yml:
# memory: 4G

# Check for unclosed connections
# In app/config.py:
# SQLALCHEMY_POOL_RECYCLE = 3600

# Add max tasks per child
# In Dockerfile:
# CMD ["uvicorn", ..., "--timeout-keep-alive", "60"]

# Restart with memory monitoring
docker-compose restart api
watch docker stats neta_api
```

---

### 4. Celery Issues

#### Issue: "Celery worker not processing tasks"

**Symptom:** Tasks stay in "pending" state indefinitely

**Solution:**
```bash
# Check worker status
docker-compose exec celery-worker celery -A app.whatsapp_integration.celery_tasks inspect active

# Check Redis queue depth
docker-compose exec redis redis-cli LLEN notification_queue:pending

# Restart Celery worker
docker-compose restart celery-worker

# Monitor worker
docker-compose logs celery-worker -f
```

#### Issue: "Task timeout"

**Symptom:** `celery.exceptions.SoftTimeLimitExceeded`

**Solution:**
```bash
# Check task timeout configuration in celeryconfig.py
# Current: soft 10min, hard 15min

# For long-running tasks, increase timeout:
# In task decorator: @app.task(time_limit=1800)

# Check if task is actually slow
docker-compose logs celery-worker | grep task_name

# Optimize the task code
# Consider breaking into smaller tasks
```

#### Issue: "Celery Beat not running periodic tasks"

**Symptom:** Scheduled tasks don't execute at expected times

**Solution:**
```bash
# Check Beat scheduler status
docker-compose logs celery-beat -f

# Verify beat is connected to Redis
docker-compose exec celery-beat celery -A app.whatsapp_integration.celery_tasks inspect ping

# Check scheduled tasks
docker-compose exec celery-beat celery -A app.whatsapp_integration.celery_tasks inspect scheduled

# Restart Beat
docker-compose restart celery-beat
```

---

### 5. Network Issues

#### Issue: "Cannot connect to external services (WhatsApp API)"

**Symptom:** `ConnectionError: Failed to establish connection to Meta API`

**Solution:**
```bash
# Check DNS resolution
docker-compose exec api nslookup graph.instagram.com

# Check network connectivity
docker-compose exec api curl -I https://graph.instagram.com/v18.0/

# Verify firewall rules
# Check AWS Security Groups / GCP Firewall Rules

# Check API credentials
docker-compose exec api env | grep WHATSAPP

# Test API credentials directly
curl -X GET "https://graph.instagram.com/v18.0/{PHONE_ID}?access_token={TOKEN}"
```

#### Issue: "Intermittent connection failures"

**Symptom:** Occasional `Connection reset by peer` errors

**Solution:**
```bash
# Check Redis connection pooling
# In celeryconfig.py:
app.conf.redis_socket_keepalive = True
app.conf.redis_socket_keepalive_interval = 60

# Check database connection pooling
# In app/config.py:
SQLALCHEMY_POOL_RECYCLE = 3600

# Monitor network from host
docker-compose exec api ping redis
docker-compose exec api ping postgres
```

---

### 6. Monitoring & Alerting

#### Issue: "Health check endpoint returning 500"

**Symptom:** `curl http://localhost:8000/api/health` returns 500 error

**Solution:**
```bash
# Check full error response
curl -v http://localhost:8000/api/health

# Check API logs
docker-compose logs api | tail -50

# Check dependency status
docker-compose ps

# Restart all services
docker-compose restart
```

#### Issue: "Metrics not appearing in Prometheus"

**Symptom:** Prometheus scrape failing or empty metrics

**Solution:**
```bash
# Verify metrics endpoint is exposed
curl http://localhost:8000/metrics

# Check Prometheus configuration
docker-compose logs prometheus

# Verify service discovery
curl http://localhost:9090/api/v1/targets
```

---

### 7. Deployment Issues

#### Issue: "Production deployment failed - rollback needed"

**Symptom:** New version crashed, need to revert quickly

**Solution:**
```bash
# Check if rollback backup exists
docker images | grep neta-api

# Rollback to previous version
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
docker pull ghcr.io/your-org/neta-ai:previous-version
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify health after rollback
curl https://api.netaai.in/api/health
```

#### Issue: "Zero-downtime deployment"

**Solution:**
```bash
# Blue-green deployment with load balancer
# 1. Deploy new version to green environment
# 2. Run smoke tests
# 3. Switch load balancer to green
# 4. Keep blue as fallback

# Rolling update with Kubernetes
kubectl set image deployment/neta-api neta-api=ghcr.io/org/neta-ai:new-version
kubectl rollout status deployment/neta-api
```

---

## Performance Tuning

### Database Optimization

```sql
-- Check slow queries
SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

-- Check missing indexes
SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public';

-- Analyze query plan
EXPLAIN ANALYZE SELECT * FROM alerts WHERE severity = 'CRITICAL';
```

### Redis Optimization

```bash
# Monitor Redis memory usage
docker-compose exec redis redis-cli info memory

# Check Redis slowlog
docker-compose exec redis redis-cli slowlog get 10

# Configure Redis maxmemory policy
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Celery Optimization

```bash
# Monitor worker performance
docker-compose exec celery-worker celery -A app.whatsapp_integration.celery_tasks inspect stats

# Increase concurrency
docker-compose exec celery-worker celery -A app.whatsapp_integration.celery_tasks control shutdown

# Restart with higher concurrency
celery -A app.whatsapp_integration.celery_tasks worker --concurrency=16
```

---

## Monitoring Commands

```bash
# System resources
docker stats

# Service status
docker-compose ps

# Service logs (follow)
docker-compose logs -f api

# Database connections
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "\du"

# Redis keys
docker-compose exec redis redis-cli KEYS "*"

# Celery active tasks
docker-compose exec celery-worker celery -A app.whatsapp_integration.celery_tasks inspect active

# Disk usage
df -h
du -sh /var/lib/docker
```

---

## Emergency Procedures

### Complete Service Reset

```bash
# WARNING: Destructive - removes all data
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
```

### Database Restore

```bash
# See DEPLOYMENT.md -> Backup & Recovery section
./scripts/restore.sh /path/to/backup.sql.gz true
```

### Clear Redis Cache

```bash
docker-compose exec redis redis-cli FLUSHALL
```

### Rebuild Images

```bash
docker-compose build --no-cache api celery-worker celery-beat
```

---

## Support Resources

- **Logs:** `docker-compose logs -f`
- **Health Status:** `python scripts/healthcheck.py`
- **Git Issues:** https://github.com/your-org/neta-ai/issues
- **Slack:** #neta-ai-devops
- **Documentation:** See [DEPLOYMENT.md](DEPLOYMENT.md)
- **On-Call Runbook:** See [ONCALL.md](ONCALL.md)

---

**Last Updated:** 2026-05-24  
**Maintained by:** NETA AI DevOps Team
