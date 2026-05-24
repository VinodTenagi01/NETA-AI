# NETA AI Kubernetes Manifests

Production-grade Kubernetes deployment manifests for NETA AI political campaign intelligence platform.

## Overview

This directory contains all necessary Kubernetes manifests for deploying NETA AI to production clusters (EKS, GKE, AKS, or on-premises).

**Architecture:**
- 3x API Pod Replicas (auto-scaling 3-10 based on CPU/memory)
- 2x Celery Worker Replicas (background task processing)
- 1x Celery Beat Pod (periodic task scheduling)
- 1x PostgreSQL StatefulSet (15.3 with PostGIS)
- 1x Redis Deployment (message broker, caching)
- Nginx Ingress Controller (TLS termination, rate limiting)
- Prometheus monitoring + Grafana dashboards
- Network policies for security isolation
- RBAC for least-privilege access

## Files

### Core Deployments

- **api-deployment.yaml** — 3-replica FastAPI application
  - Service: ClusterIP on port 8000
  - HPA: Auto-scales 3-10 replicas based on CPU (70%) / memory (80%)
  - PDB: Maintains minimum 2 available replicas
  - Resources: requests (256m CPU, 512Mi mem) / limits (500m CPU, 1Gi mem)
  - Health checks: liveness (30s), readiness (10s), startup (40s)

- **celery-deployment.yaml** — Celery worker pods
  - 2 replicas handling task queues: alerts, notifications, monitoring, maintenance
  - Pod anti-affinity: spreads across nodes
  - Concurrency: 8 workers per pod
  - Resources: requests (250m CPU, 256Mi mem) / limits (500m CPU, 1Gi mem)

- **celery-beat-deployment.yaml** — Celery Beat scheduler
  - 1 replica (scheduler is single-instance)
  - PersistentVolume for beat schedule state
  - Runs periodic tasks: check-delivery-status (5m), cleanup-old-alerts (daily 2 AM UTC)

- **postgres-statefulset.yaml** — PostgreSQL database
  - 1 replica (can scale to 3 with replication setup)
  - PersistentVolume: 50Gi storage
  - Configuration: max_connections=200, PostGIS extension
  - Resources: requests (500m CPU, 1Gi mem) / limits (1000m CPU, 2Gi mem)

- **redis-deployment.yaml** — Redis message broker & cache
  - 1 replica (can add Sentinel for HA)
  - PersistentVolume: 10Gi with AOF persistence
  - maxmemory: 512Mi with allkeys-lru eviction policy
  - Resources: requests (100m CPU, 256Mi mem) / limits (500m CPU, 1Gi mem)

### Configuration & Secrets

- **configmap.yaml** — Application configuration
  - Environment variables (ENVIRONMENT, LOG_LEVEL, timeouts, thresholds)
  - Nginx reverse proxy configuration (TLS, rate limiting, security headers)
  - Logging configuration (JSON format, log rotation)

- **secret-template.yaml** — Kubernetes Secrets template
  - Database credentials (PostgreSQL password, connection URL)
  - Redis password
  - Application secrets (SECRET_KEY, JWT tokens)
  - WhatsApp API credentials
  - Celery broker/result backend URLs
  - AWS/GCS credentials for backups
  - Includes External Secrets Operator integration for automatic sync from AWS Secrets Manager

### Networking & Security

- **ingress.yaml** — Production ingress configuration
  - Hosts: api.netaai.in, staging-api.netaai.in
  - TLS: Let's Encrypt certificates (automatic renewal via cert-manager)
  - Rate limiting: 100 requests/minute per IP
  - Security: CORS, MODSECURITY, OWASP rules
  - Network Policies: restrict pod-to-pod communication

### Monitoring

- **monitoring.yaml** — Prometheus + Grafana
  - Prometheus rules: alerts for API down, high error rate, high latency, disk space, memory, CPU
  - ServiceMonitor: scrapes /metrics endpoint every 30s
  - PrometheusRule: defines 15+ alert rules
  - Grafana dashboard: API request rate, error rate, latency, active connections

## Deployment Instructions

### Prerequisites

```bash
# Kubernetes cluster 1.24+ with these components installed:
# - Ingress Controller (nginx): kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/...
# - Cert-Manager: helm install cert-manager jetstack/cert-manager
# - Prometheus Operator (optional): helm install prometheus prometheus-community/kube-prometheus-stack
# - External Secrets Operator (optional): helm install external-secrets external-secrets/external-secrets
```

### 1. Create Namespace

```bash
kubectl create namespace neta-ai
kubectl label namespace neta-ai managed-by=neta-platform
```

### 2. Create Secrets

**Option A: Manually (for development)**

```bash
kubectl create secret generic neta-secrets \
  --from-literal=postgres-password='dev-password' \
  --from-literal=redis-password='dev-password' \
  --from-literal=database-url='postgresql+asyncpg://netaai_app:dev-password@postgres:5432/netaai_prod' \
  --from-literal=redis-url='redis://:dev-password@redis:6379/0' \
  --from-literal=secret-key='dev-secret-key-change-in-production' \
  --from-literal=jwt-secret='dev-jwt-secret' \
  --from-literal=whatsapp-api-token='$WHATSAPP_API_TOKEN' \
  --from-literal=whatsapp-phone-id='$WHATSAPP_PHONE_ID' \
  --from-literal=whatsapp-business-account-id='$WHATSAPP_BUSINESS_ACCOUNT_ID' \
  --from-literal=whatsapp-webhook-verify-token='$WHATSAPP_WEBHOOK_VERIFY_TOKEN' \
  --from-literal=celery-broker-url='redis://:dev-password@redis:6379/0' \
  --from-literal=celery-result-backend='redis://:dev-password@redis:6379/1' \
  --from-literal=aws-access-key-id='$AWS_ACCESS_KEY' \
  --from-literal=aws-secret-access-key='$AWS_SECRET_KEY' \
  -n neta-ai
```

**Option B: From AWS Secrets Manager (production)**

```bash
# Using External Secrets Operator (automatic sync)
# Apply ExternalSecret resource in secret-template.yaml
kubectl apply -f k8s/secret-template.yaml

# Or manually pull and create
aws secretsmanager get-secret-value --secret-id neta-ai/production \
  --query SecretString --output text > /tmp/secrets.json

# Create from JSON file
kubectl create secret generic neta-secrets \
  --from-file=/tmp/secrets.json \
  -n neta-ai
```

### 3. Deploy Infrastructure

```bash
# Deploy PostgreSQL first (StatefulSet)
kubectl apply -f k8s/postgres-statefulset.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n neta-ai --timeout=5m

# Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml

# Wait for Redis
kubectl wait --for=condition=ready pod -l app=redis -n neta-ai --timeout=2m

# Deploy API, Celery Worker, Beat
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/celery-deployment.yaml
kubectl apply -f k8s/celery-beat-deployment.yaml

# Deploy networking (Ingress + Network Policies)
kubectl apply -f k8s/ingress.yaml

# Deploy monitoring (Prometheus + Grafana)
kubectl apply -f k8s/monitoring.yaml
```

### 4. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n neta-ai

# Check services are created
kubectl get svc -n neta-ai

# Check ingress is ready
kubectl get ingress -n neta-ai

# Check logs
kubectl logs -f deployment/neta-api -n neta-ai
kubectl logs -f deployment/neta-celery-worker -n neta-ai
kubectl logs -f statefulset/postgres -n neta-ai

# Port forward to test locally
kubectl port-forward svc/neta-api 8000:8000 -n neta-ai
# Test: curl http://localhost:8000/api/health
```

### 5. Run Database Migrations

```bash
# Scale down API to ensure single DB connection during migrations
kubectl scale deployment neta-api --replicas=1 -n neta-ai

# Run migrations in one pod
kubectl exec -it deploy/neta-api -n neta-ai -- alembic upgrade head

# Scale back up
kubectl scale deployment neta-api --replicas=3 -n neta-ai
```

## Configuration

### Environment Variables

All environment variables are defined in `configmap.yaml`. To update:

```bash
# Edit and apply
kubectl edit configmap neta-config -n neta-ai
kubectl rollout restart deployment/neta-api -n neta-ai
```

### Scaling

**API Auto-Scaling (HPA)**

Currently configured to auto-scale 3-10 replicas based on:
- CPU: target 70% utilization
- Memory: target 80% utilization

To modify:

```bash
kubectl edit hpa neta-api-hpa -n neta-ai
# Change minReplicas, maxReplicas, targetCPUUtilizationPercentage
kubectl apply -f k8s/api-deployment.yaml
```

**Manual Scaling**

```bash
# Scale API
kubectl scale deployment neta-api --replicas=5 -n neta-ai

# Scale Celery workers
kubectl scale deployment neta-celery-worker --replicas=4 -n neta-ai
```

### Resource Limits

To increase resource limits for production traffic:

```bash
# Edit deployment
kubectl edit deployment neta-api -n neta-ai

# Change in spec.template.spec.containers[0].resources.limits
# Example: memory: 2Gi (from 1Gi), cpu: 1000m (from 500m)

# Apply changes
kubectl rollout restart deployment/neta-api -n neta-ai
```

## Monitoring & Logging

### Health Checks

```bash
# Check pod health
kubectl get pods -o wide -n neta-ai
# Look at READY column (2/2, 1/1, etc.) and RESTARTS count

# Detailed pod info
kubectl describe pod neta-api-XXXXX -n neta-ai

# Check specific container logs
kubectl logs neta-api-XXXXX -c api -n neta-ai
```

### Prometheus Metrics

```bash
# Port forward to Prometheus
kubectl port-forward svc/prometheus-operated 9090:9090 -n neta-ai
# Access at http://localhost:9090

# Query examples:
# - up{job="neta-api"} — pod availability
# - rate(http_requests_total[5m]) — request rate
# - histogram_quantile(0.95, http_request_duration_seconds_bucket) — p95 latency
```

### Grafana Dashboards

```bash
# Get Grafana admin password
kubectl get secret grafana -o jsonpath="{.data.admin-password}" -n neta-ai | base64 --decode

# Port forward to Grafana
kubectl port-forward svc/grafana 3000:80 -n neta-ai
# Access at http://localhost:3000 (admin / password)

# Import dashboard: k8s/monitoring.yaml contains dashboard JSON
```

## Troubleshooting

### Pod Crash Loop

```bash
# Check pod events
kubectl describe pod neta-api-XXXXX -n neta-ai

# Check logs
kubectl logs neta-api-XXXXX -n neta-ai --previous
# Look for OOMKilled, CrashLoopBackOff, ImagePullBackOff

# Increase memory if OOMKilled
kubectl edit deployment neta-api -n neta-ai
# Change spec.template.spec.containers[0].resources.limits.memory: 2Gi
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity from pod
kubectl exec -it deploy/neta-api -n neta-ai -- \
  psql -h postgres -U netaai_app -d netaai_prod -c "SELECT version();"

# If error, check database pod
kubectl logs statefulset/postgres -n neta-ai

# Check database service
kubectl get svc postgres -n neta-ai
kubectl exec -it statefulset/postgres -n neta-ai -- \
  psql -U postgres -c "\l"
```

### High Pod Resource Usage

```bash
# Check current usage
kubectl top pods -n neta-ai
kubectl top nodes

# Check for memory leaks (growing over time)
kubectl top pod neta-api-XXXXX --containers -n neta-ai

# If high, restart pod
kubectl delete pod neta-api-XXXXX -n neta-ai
# New pod will be created automatically
```

## Backup & Disaster Recovery

### Database Backup

```bash
# Create PostgreSQL backup manually
kubectl exec -it statefulset/postgres -n neta-ai -- \
  pg_dump -U netaai_app -d netaai_prod | gzip > /tmp/neta-backup.sql.gz

# Upload to S3
aws s3 cp /tmp/neta-backup.sql.gz s3://neta-ai-backups/backups/
```

### Restore from Backup

```bash
# Download backup
aws s3 cp s3://neta-ai-backups/backups/latest.sql.gz /tmp/

# Restore to PostgreSQL
gunzip < /tmp/latest.sql.gz | kubectl exec -i statefulset/postgres -n neta-ai -- \
  psql -U netaai_app -d netaai_prod
```

### PersistentVolume Backup

```bash
# Backup PersistentVolumes (for PostgreSQL, Redis, Beat schedule)
# Using velero (backup/restore tool)

# Install Velero
velero install --provider aws --bucket neta-ai-backups --secret-file credentials-velero

# Create backup
velero backup create neta-ai-backup --include-namespaces neta-ai

# List backups
velero backup get

# Restore from backup
velero restore create --from-backup neta-ai-backup
```

## Maintenance

### Regular Tasks

**Daily:**
- Monitor pod restarts and error rates
- Check Prometheus alerts
- Review logs for warnings/errors

**Weekly:**
- Analyze performance metrics
- Review resource usage trends
- Test scaling policies

**Monthly:**
- Test disaster recovery procedures
- Review and update security policies
- Analyze cost optimization opportunities

### Upgrades

**Application Upgrade**

```bash
# 1. Update Docker image version
kubectl set image deployment/neta-api api=ghcr.io/your-org/neta-ai:v1.1.0 -n neta-ai

# 2. Monitor rollout
kubectl rollout status deployment/neta-api -n neta-ai

# 3. Rollback if needed
kubectl rollout undo deployment/neta-api -n neta-ai
```

**PostgreSQL Upgrade**

```bash
# 1. Create backup before upgrade
velero backup create neta-ai-pre-upgrade

# 2. Update image in StatefulSet
kubectl edit statefulset postgres -n neta-ai
# Change image: postgres:16-alpine

# 3. PostgreSQL will handle migration automatically
# Monitor: kubectl logs -f statefulset/postgres -n neta-ai
```

## Support

For issues:

1. Check logs: `kubectl logs -f POD_NAME -n neta-ai`
2. Describe pod: `kubectl describe pod POD_NAME -n neta-ai`
3. Check events: `kubectl get events -n neta-ai`
4. Review Grafana dashboards for metrics
5. Check DEPLOYMENT.md and TROUBLESHOOTING.md in parent directory

---

**Last Updated:** 2026-05-24  
**Maintained by:** DevOps Team
