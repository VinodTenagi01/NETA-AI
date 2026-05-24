# NETA AI Deployment Guide

**Version:** 1.0  
**Date:** 2026-05-24  
**Status:** Production-Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)

---

## Overview

NETA AI is a production-grade political campaign intelligence platform with:

- **9 Modules:** Database, Security, GeoJSON, Ground Ops, News Intelligence, Booth Management, Prediction, Opposition Intelligence, WhatsApp Integration
- **78 REST API Endpoints** with full RBAC
- **243 Passing Tests** (100% pass rate)
- **Real-Time Alert Delivery** via WhatsApp
- **Background Task Processing** with Celery
- **Multi-Environment Support** (Dev, Staging, Production)

**Deployment Options:**
- ✅ **Docker Compose** (recommended for most deployments)
- ✅ **Kubernetes** (for enterprise scaling)
- ✅ **Cloud Platforms** (AWS, GCP, Azure)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB
- OS: Linux (Ubuntu 20.04+, Debian 11+) or macOS

**Recommended (Production):**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 100GB+ (for database growth)
- Managed database (AWS RDS, Cloud SQL)
- Managed Redis (ElastiCache, Memorystore)

### Software Requirements

```bash
# Docker and Docker Compose
docker --version  # >= 20.10
docker-compose --version  # >= 1.29

# Or if using Kubernetes
kubectl --version  # >= 1.24
helm --version  # >= 3.0

# For local development
python --version  # >= 3.11
pip --version  # >= 22.0
```

### Configuration Files

```bash
# Create .env file from template
cp .env.example .env

# For production, create .env.production
# Load from secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
```

---

## Local Development

### Quick Start (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/your-org/neta-ai.git
cd neta-ai

# 2. Create environment file
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Verify health
curl http://localhost:8000/api/health

# 5. Run tests
docker-compose exec api pytest tests/ -v
```

### Detailed Setup

**1. Configure Environment**

```bash
# Edit .env with development values
cat .env
```

**Key variables:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://netaai_app:netaai_password@postgres:5432/netaai_prod
POSTGRES_DB=netaai_prod
POSTGRES_USER=netaai_app
POSTGRES_PASSWORD=netaai_password

# Redis
REDIS_URL=redis://:redis_password@redis:6379/0
REDIS_PASSWORD=redis_password

# App
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=true
ENVIRONMENT=development
```

**2. Start Services**

```bash
# Start all services (API, PostgreSQL, Redis, Celery, Beat)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

**3. Run Database Migrations**

```bash
# Migrations run automatically on container startup
# Verify migration status
docker-compose exec api alembic current
```

**4. Access Services**

```bash
# FastAPI API
http://localhost:8000

# API Documentation
http://localhost:8000/api/docs

# ReDoc Documentation
http://localhost:8000/api/redoc

# PostgreSQL
localhost:5432

# Redis
localhost:6379

# Celery monitoring (install flower)
pip install flower
celery -A app.whatsapp_integration.celery_tasks flower
# http://localhost:5555
```

**5. Run Tests**

```bash
# Run all tests
docker-compose exec api pytest tests/ -v

# Run specific test file
docker-compose exec api pytest tests/test_opposition_intelligence_unit.py -v

# Run with coverage
docker-compose exec api pytest tests/ --cov=app --cov-report=html
```

---

## Docker Deployment

### Architecture

```
┌─────────────────────────────────────────────────┐
│ Docker Compose Environment                      │
├─────────────────────────────────────────────────┤
│ ┌──────────────┐  ┌──────────────┐             │
│ │  PostgreSQL  │  │    Redis     │             │
│ │   (15.3)     │  │   (7.0)      │             │
│ │   Port 5432  │  │  Port 6379   │             │
│ └──────────────┘  └──────────────┘             │
│       ▲                   ▲                     │
│       │                   │                     │
│ ┌─────────────┬──────────────┬─────────────┐   │
│ │  API        │  Celery      │  Celery     │   │
│ │  (4 workers)│  Worker      │  Beat       │   │
│ │  Port 8000  │  (tasks)     │ (scheduler) │   │
│ └─────────────┴──────────────┴─────────────┘   │
└─────────────────────────────────────────────────┘
```

### Building Custom Image

```bash
# Build image
docker build -t neta-ai:latest .

# Tag for registry
docker tag neta-ai:latest ghcr.io/your-org/neta-ai:latest

# Push to registry
docker push ghcr.io/your-org/neta-ai:latest
```

### Running Services

**Development Environment**

```bash
# Start services
docker-compose -f docker-compose.yml up -d

# View service status
docker-compose ps

# View logs
docker-compose logs -f
```

**Production Environment**

```bash
# Start with production overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Production environment includes:
# - Resource limits (CPU, memory)
# - Restart policies
# - JSON file logging
# - Health checks
```

### Container Management

```bash
# Restart a service
docker-compose restart api

# Rebuild image
docker-compose build --no-cache api

# Remove all containers and volumes
docker-compose down -v

# Execute command in container
docker-compose exec api python -c "import app; print(app.__version__)"

# View container logs
docker logs neta_api -f

# Inspect container
docker inspect neta_api
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] .env.production configured with production credentials
- [ ] Database backups tested and verified
- [ ] SSL/TLS certificates obtained and configured
- [ ] DNS records pointing to deployment
- [ ] Secrets manager (AWS Secrets Manager, Vault) configured
- [ ] Monitoring and alerting configured (Prometheus, Grafana, PagerDuty)
- [ ] Log aggregation configured (ELK, CloudWatch, Splunk)
- [ ] Team trained on deployment and rollback procedures

### Deployment Steps

**1. Prepare Infrastructure**

```bash
# Create VPC, subnets, security groups
# Create RDS PostgreSQL instance
# Create ElastiCache Redis instance
# Create S3 bucket for backups

# Set up environment variables in AWS Secrets Manager
aws secretsmanager create-secret \
  --name neta-ai/production \
  --secret-string file://secrets.json
```

**2. Deploy Application**

```bash
# SSH to deployment server
ssh ubuntu@production-server

# Clone repository
git clone https://github.com/your-org/neta-ai.git
cd neta-ai

# Pull latest production image
docker pull ghcr.io/your-org/neta-ai:v1.0.0

# Start services with production overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify deployment
curl https://api.netaai.in/api/health
```

**3. Run Database Migrations**

```bash
# Automatic on startup, or manually:
docker-compose exec api alembic upgrade head
```

**4. Verify Health**

```bash
# Check all services
docker-compose ps

# Verify API
curl https://api.netaai.in/api/health

# Check database
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "\dt"

# Check Celery
docker-compose exec celery-worker celery -A app.whatsapp_integration.celery_tasks inspect active
```

### Scaling

**Horizontal Scaling (Multiple API Instances)**

```bash
# Update docker-compose.yml to run multiple API instances
# Use Nginx or load balancer to route requests
```

**Resource Optimization**

```bash
# Monitor resource usage
docker stats

# Adjust resource limits in docker-compose.prod.yml
# - cpus: '2'
# - memory: 2G
```

---

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
kubectl version --client

# Install Helm
helm version

# Create namespace
kubectl create namespace neta-ai
```

### Deploying to Kubernetes

```bash
# 1. Create secrets
kubectl create secret generic neta-secrets \
  --from-literal=database_url="postgresql://..." \
  --from-literal=redis_url="redis://..." \
  -n neta-ai

# 2. Create ConfigMap
kubectl create configmap neta-config \
  --from-file=.env.production \
  -n neta-ai

# 3. Apply manifests
kubectl apply -f k8s/ -n neta-ai

# 4. Verify deployment
kubectl get pods -n neta-ai
kubectl logs -f deployment/neta-api -n neta-ai
```

### Kubernetes Best Practices

```yaml
# Resource requests and limits
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"

# Health checks
livenessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 60
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## Monitoring & Logging

### Health Checks

```bash
# API health endpoint
curl http://localhost:8000/api/health
# Response: {"status": "ok", "service": "neta-api", "version": "1.0.0"}

# Enhanced health check script
python scripts/healthcheck.py
# Checks: API, Database, Redis, Celery, System resources
```

### Logging

**Structured JSON Logging**

All logs are JSON-formatted for easy parsing and aggregation:

```json
{
  "timestamp": "2026-05-24T15:30:00Z",
  "level": "INFO",
  "service": "neta-api",
  "request_id": "abc123",
  "message": "Alert delivery queued",
  "data": {
    "alert_id": "...",
    "user_id": "...",
    "delivery_id": "..."
  }
}
```

**Log Aggregation**

```bash
# View logs from Docker Compose
docker-compose logs -f api celery-worker

# View logs from Kubernetes
kubectl logs -f deployment/neta-api -n neta-ai

# Send to CloudWatch
# See logging configuration in logging/logging_config.yaml
```

### Monitoring Dashboards

**Grafana Dashboards** (using Prometheus metrics):

- API Health & Latency
- Error Rates & Status Codes
- Database Query Performance
- Redis Usage
- Celery Task Status
- System Resources (CPU, Memory, Disk)

### Alerting

**PagerDuty Alerting Rules**

- API response time > 5 seconds
- Error rate > 1%
- Database connection failures
- Redis connectivity loss
- Celery worker offline
- Disk usage > 90%

---

## Backup & Recovery

### Automated Backups

```bash
# Daily backups to S3
0 2 * * * /app/scripts/backup.sh s3

# Or Google Cloud Storage
0 2 * * * /app/scripts/backup.sh gcs

# Verify backups
aws s3 ls s3://neta-ai-backups/backups/
```

### Manual Backup

```bash
# Create local backup
./scripts/backup.sh local

# Backup to S3
./scripts/backup.sh s3

# List backups
ls -la /app/backups/
```

### Restore from Backup

```bash
# Restore from backup file
./scripts/restore.sh /app/backups/neta_backup_20260524_020000.sql.gz

# Restore and drop existing database
./scripts/restore.sh /path/to/backup.sql.gz true

# Verify restore
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "\dt"
```

### Backup Verification

**Monthly Restore Testing**

```bash
# 1. Get recent backup from S3
aws s3 cp s3://neta-ai-backups/backups/latest.sql.gz /tmp/

# 2. Restore to staging environment
./scripts/restore.sh /tmp/latest.sql.gz true

# 3. Run smoke tests
curl http://localhost:8000/api/health
pytest tests/test_smoke.py -v

# 4. Verify data integrity
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "SELECT COUNT(*) FROM alerts;"
```

---

## Troubleshooting

### Common Issues

**Issue: Services not starting**

```bash
# Check logs
docker-compose logs api

# Common causes:
# 1. Port already in use
lsof -i :8000

# 2. Environment variables missing
docker-compose exec api env | grep DATABASE_URL

# 3. Database not ready
docker-compose logs postgres
```

**Issue: Database migration failures**

```bash
# Check migration status
docker-compose exec api alembic current

# Rollback migration
docker-compose exec api alembic downgrade -1

# Re-apply migrations
docker-compose exec api alembic upgrade head
```

**Issue: Celery worker not processing tasks**

```bash
# Check worker status
docker-compose exec celery-worker celery -A app.whatsapp_integration.celery_tasks inspect active

# Check queue contents
docker-compose exec redis redis-cli
> LLEN notification_queue:pending

# Restart worker
docker-compose restart celery-worker
```

**Issue: Out of memory**

```bash
# Check memory usage
docker stats

# Increase memory limit in docker-compose.prod.yml
memory: 4G  # Increase from 2G

# Restart services
docker-compose down
docker-compose up -d
```

### Performance Tuning

**Database Connection Pool**

```python
# app/config.py
SQLALCHEMY_POOL_SIZE = 20  # Development
SQLALCHEMY_POOL_SIZE = 50  # Production
SQLALCHEMY_MAX_OVERFLOW = 10
```

**Celery Worker Configuration**

```bash
# Increase worker concurrency
celery -A app.whatsapp_integration.celery_tasks worker \
  --concurrency=8 \
  --max-tasks-per-child=100
```

**API Worker Configuration**

```bash
# Increase Uvicorn workers
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 8
```

### Monitoring Commands

```bash
# Real-time system monitoring
docker stats

# Database query performance
docker-compose exec postgres psql -U netaai_app -d netaai_prod -c "\dt+"

# Redis memory usage
docker-compose exec redis redis-cli info memory

# Celery task stats
docker-compose exec celery-worker celery -A app.whatsapp_integration.celery_tasks inspect stats
```

---

## Support

For issues or questions:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review logs: `docker-compose logs -f`
3. Run health check: `python scripts/healthcheck.py`
4. Check GitHub Issues: https://github.com/your-org/neta-ai/issues

---

**Last Updated:** 2026-05-24  
**Maintained by:** NETA AI Team
