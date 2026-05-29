# NETA.AI — Production Deployment Guide

**Status:** Code-complete and locally validated  
**Last updated:** 2026-05-28  

---

## Prerequisites

| Requirement | Spec |
|-------------|------|
| VPS OS | Ubuntu 22.04 LTS or 24.04 LTS |
| vCPU | 4+ |
| RAM | 8 GB+ |
| Disk | 50 GB+ SSD |
| Ports | 80, 443 open inbound |

> **CLIENT INFRASTRUCTURE ACCESS REQUIRED** for steps marked with ⛔

---

## Step 0 — Local Preparation (done on dev machine)

```bash
# Confirm frontend is built
ls frontend/dist/index.html          # must exist

# Confirm .env secrets are set
grep -E "SECRET_KEY|POSTGRES_PASSWORD|REDIS_PASSWORD" .env

# Confirm compose syntax
docker compose config --quiet && echo "VALID"
```

---

## Step 1 — VPS Setup ⛔

> **CLIENT INFRASTRUCTURE ACCESS REQUIRED**: SSH access to provisioned VPS

```bash
# SSH to server
ssh ubuntu@<YOUR-SERVER-IP>

# Clone repository
git clone https://github.com/your-org/neta-ai.git
cd neta-ai

# Copy .env (never commit this file)
# scp .env ubuntu@<ip>:/home/ubuntu/neta-ai/.env

# Run automated VPS setup (installs Docker, nginx, certbot)
sudo bash scripts/setup-vps.sh app.netaai.in
```

The `setup-vps.sh` script performs:
1. Docker installation
2. nginx + certbot installation
3. Domain configuration (replaces `REPLACE_WITH_YOUR_DOMAIN` in nginx.conf)
4. SSL certificate acquisition (`certbot --standalone`)
5. nginx start with HTTPS
6. Docker stack startup
7. Certbot auto-renewal cron

---

## Step 2 — DNS Configuration ⛔

> **CLIENT INFRASTRUCTURE ACCESS REQUIRED**: Domain registrar access

```
A record:  app.netaai.in  →  <YOUR-SERVER-IP>
TTL:       300 (5 minutes for initial setup, increase to 3600 after verified)
```

Verify DNS propagation:
```bash
dig app.netaai.in +short        # should return server IP
nslookup app.netaai.in          # alternative check
```

---

## Step 3 — SSL Certificate ⛔

> **CLIENT INFRASTRUCTURE ACCESS REQUIRED**: DNS must be pointing to server first

```bash
# Run on server (handled by setup-vps.sh, or manually):
sudo certbot certonly --standalone -d app.netaai.in

# Verify certificate
sudo certbot certificates
# Expected: Certificate Name: app.netaai.in
#           Expiry Date: (90 days from now)

# Install nginx config
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
sudo nginx -t && sudo systemctl reload nginx

# Test HTTPS
curl -I https://app.netaai.in/api/health
# Expected: HTTP/2 200
```

Auto-renewal is configured by `setup-vps.sh`. To test manually:
```bash
sudo certbot renew --dry-run
```

---

## Step 4 — Docker Stack (on VPS)

```bash
# From project directory on VPS:
cd ~/neta-ai

# Start production stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify all 5 containers are healthy
docker compose ps

# Expected output:
# neta_api            Up (healthy)
# neta_celery_beat    Up (healthy)
# neta_celery_worker  Up (healthy)
# neta_postgres       Up (healthy)
# neta_redis          Up (healthy)

# Tail logs for startup errors
docker compose logs -f --tail=50
```

---

## Step 5 — Frontend Deployment

```bash
# Build frontend (on dev machine, or on VPS if Node is installed)
cd frontend
npm ci
npm run build

# Deploy to nginx web root (on VPS)
sudo mkdir -p /var/www/neta-frontend
sudo cp -r dist/* /var/www/neta-frontend/
sudo chown -R www-data:www-data /var/www/neta-frontend/

# Verify
curl -I https://app.netaai.in/
# Expected: HTTP/2 200, content-type: text/html
```

Or deploy from local machine:
```bash
# From dev machine, copy dist to server
scp -r frontend/dist/* ubuntu@<ip>:/var/www/neta-frontend/
```

---

## Step 6 — Environment (ALLOWED_ORIGINS)

Once domain is live, update `.env` on the server:

```bash
# Edit .env on VPS
nano .env

# Change:
ALLOWED_ORIGINS=["https://app.netaai.in"]

# Restart API to pick up change
docker compose restart api
```

---

## Step 7 — WhatsApp Business Activation ⛔

> **CLIENT INFRASTRUCTURE ACCESS REQUIRED**: Meta Developer Console access

```bash
# On VPS, add to .env:
WHATSAPP_API_TOKEN=<from Meta Developer Console → WhatsApp → API Setup>
WHATSAPP_PHONE_ID=<from Meta Developer Console → WhatsApp → Phone Number ID>

# Restart services
docker compose restart api celery-worker
```

Then in Meta Developer Console:
- Webhook URL: `https://app.netaai.in/api/v1/notifications/webhook`
- Verify Token: `neta_whatsapp_webhook_2024`

Test verification:
```bash
curl "https://app.netaai.in/api/v1/notifications/webhook?\
hub.mode=subscribe&\
hub.verify_token=neta_whatsapp_webhook_2024&\
hub.challenge=test123"
# Expected: test123 (plain text)
```

---

## Step 8 — Final Smoke Test

```bash
# Run the full validation script
bash scripts/validate-production.sh https://app.netaai.in

# Or individually:
curl -s https://app.netaai.in/api/health
# Expected: {"status":"ok","service":"neta-api","version":"1.0.0"}

# Login
curl -X POST https://app.netaai.in/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@netaai.in","password":"Admin123!Secure"}'
# Expected: {"access_token":"...","refresh_token":"..."}
```

---

## Rollback / Recovery Commands

```bash
# Restart a single service
docker compose restart api
docker compose restart celery-worker

# Restart all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View live logs
docker compose logs -f api
docker compose logs -f celery-worker

# Check container health
docker compose ps

# Force-recreate containers (preserves data volumes)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate api

# Hard restart (if Docker networking is stuck)
# WARNING: brief downtime
docker compose down
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Database backup
docker exec neta_postgres pg_dump -U netaai_app netaai_prod > backup_$(date +%Y%m%d).sql

# Restore database
docker exec -i neta_postgres psql -U netaai_app netaai_prod < backup_20260528.sql
```

---

## Local Docker Desktop Recovery (Windows)

If Docker Desktop becomes unresponsive (commands hang):

```powershell
# Option 1: Restart WSL2
wsl --shutdown
# Wait 10 seconds, then restart Docker Desktop from taskbar

# Option 2: Kill orphaned processes blocking ports
# Check for non-Docker processes on port 8000
netstat -ano | findstr ":8000"
# Kill any python/uvicorn processes that aren't Docker
Stop-Process -Id <PID> -Force

# Option 3: Full Docker Desktop restart
# Right-click Docker Desktop icon → Restart
# Wait ~60 seconds

# After recovery, restart the stack
cd D:\NETA.AI
docker compose up -d
```

---

## Port Reference

| Port | Service | Notes |
|------|---------|-------|
| 8000 | FastAPI (Docker) | Internal — not exposed in prod (nginx proxies) |
| 5432 | PostgreSQL | Internal — not exposed in prod |
| 6379 | Redis | Internal — not exposed in prod |
| 80 | nginx | HTTP → HTTPS redirect only |
| 443 | nginx | HTTPS frontend + API |

> In production, ports 8000, 5432, 6379 should be firewall-blocked. Only 80 and 443 should be publicly accessible.

---

## nginx Firewall Setup (on VPS)

```bash
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP (certbot + redirect)
sudo ufw allow 443/tcp    # HTTPS
sudo ufw deny 8000/tcp    # Block direct API access
sudo ufw deny 5432/tcp    # Block direct DB access
sudo ufw deny 6379/tcp    # Block direct Redis access
sudo ufw enable
sudo ufw status
```

---

## Admin Login

| Field | Value |
|-------|-------|
| Email | `admin@netaai.in` |
| Password | `Admin123!Secure` |
| Role | `super_admin` |

---

## Container Resource Limits (production)

| Service | CPU Limit | Memory Limit |
|---------|-----------|-------------|
| PostgreSQL | 2 vCPU | 2 GB |
| Redis | 1 vCPU | 1 GB |
| API (4 workers) | 2 vCPU | 2 GB |
| Celery Worker | 1 vCPU | 1 GB |
| Celery Beat | 0.5 vCPU | 512 MB |
| **Total** | **6.5 vCPU** | **6.5 GB** |

> Minimum VPS: 4 vCPU / 8 GB RAM to leave headroom for the OS and nginx.
