# NETA.AI — Deployment Guide

## Overview

NETA.AI is a FastAPI + PostgreSQL + Redis + Celery + React stack.
Production deployment uses **Docker Compose** on a Linux VPS with **nginx** as reverse proxy and **Let's Encrypt** TLS.

---

## Local Development Stack

### Prerequisites
- Windows 11 + Docker Desktop (WSL2 backend)
- Node.js 18+ (for frontend builds)

### Start
```powershell
cd D:\NETA.AI
.\scripts\stack-start.ps1
```

### Stop
```powershell
.\scripts\stack-stop.ps1
```

### Health check
```powershell
.\scripts\stack-health.ps1
```

### After Windows reboot
```powershell
.\scripts\recovery-check.ps1 -AutoRecover
```

---

## Production Deployment (VPS)

### Architecture

```
Internet
  ↓  443 / 80
nginx (system service)
  ├── /api/*  → localhost:8000 (neta_api container)
  └── /*      → /var/www/neta-frontend (React static files)

Docker Compose
  ├── neta_api          (FastAPI, port 8000)
  ├── neta_postgres     (PostGIS 15, port 5432, volume: postgres_data)
  ├── neta_redis        (Redis 7, port 6379, volume: redis_data)
  ├── neta_celery_worker
  └── neta_celery_beat
```

### VPS Requirements
- Ubuntu 22.04 or 24.04 LTS
- 4 vCPU / 8 GB RAM / 40 GB SSD (minimum)
- Inbound ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Domain A record pointing to VPS IP (e.g. `app.netaai.in`)

### Step-by-step

#### 1. Provision VPS and point DNS
```
A record: app.netaai.in → <VPS public IP>
```
Wait for DNS to propagate (typically 5–30 minutes).

#### 2. Upload project to VPS
```bash
# From Windows (PowerShell)
scp -r D:\NETA.AI ubuntu@<VPS_IP>:/opt/neta-ai
```
Or use git:
```bash
git clone <your-repo-url> /opt/neta-ai
```

#### 3. Create production .env on VPS
```bash
cd /opt/neta-ai
cp .env.example .env
nano .env   # fill in secrets (see PROD_ENV_TEMPLATE.env)
```

#### 4. Run VPS setup script
```bash
cd /opt/neta-ai
sudo bash scripts/setup-vps.sh app.netaai.in
```
This installs Docker, nginx, certbot, obtains SSL cert, and starts the stack.

#### 5. Deploy frontend
Build on Windows:
```powershell
cd D:\NETA.AI\frontend
npm run build
```
Upload to VPS:
```powershell
scp -r dist\* ubuntu@<VPS_IP>:/var/www/neta-frontend/
```

#### 6. Verify
```
https://app.netaai.in/api/health  →  {"status":"ok"}
https://app.netaai.in             →  React frontend
https://app.netaai.in/api/docs    →  API documentation
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | 64-char hex JWT signing key |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password |
| `REDIS_PASSWORD` | Yes | Redis AUTH password |
| `ALLOWED_ORIGINS` | Yes | CORS origins (JSON array) |
| `WHATSAPP_API_TOKEN` | No | Meta Cloud API token |
| `WHATSAPP_PHONE_ID` | No | Meta phone number ID |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | No | Webhook verification token |

Generate secrets:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"        # SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"    # passwords
```

---

## Production Compose Commands

```bash
# Start (production mode with resource limits and logging)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Stop (data preserved)
docker compose stop

# View logs
docker compose logs -f --tail=100 api

# Restart single service
docker compose restart api
```

---

## Updating the Application

```bash
# On VPS
cd /opt/neta-ai
git pull
docker compose build api celery-worker celery-beat
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps api celery-worker celery-beat
```

Frontend update:
```bash
# Build on Windows, upload to VPS
scp -r dist/* ubuntu@<VPS_IP>:/var/www/neta-frontend/
```

---

## Monitoring

```bash
# Container health
docker compose ps

# API logs
docker compose logs -f api

# Postgres activity
docker exec neta_postgres psql -U netaai_app -d netaai_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Redis info
docker exec neta_redis redis-cli -a "$REDIS_PASSWORD" info server

# Disk usage
df -h /var/lib/docker
```
