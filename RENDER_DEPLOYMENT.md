# NETA.AI — Render Deployment Guide

## Architecture on Render

```
render.com
├── neta-api          (Web Service, Dockerfile.render, ~$25/mo)
├── neta-celery-worker (Background Worker, ~$25/mo)
├── neta-celery-beat  (Background Worker / scheduler, ~$7/mo)
├── neta-frontend     (Static Site, FREE)
├── neta-postgres     (Managed PostgreSQL 15, ~$7/mo)
└── neta-redis        (Managed Redis, ~$10/mo)

Estimated monthly cost: ~$74/mo (Starter/Standard mix)
```

---

## Before You Start

1. Push your project to a GitHub or GitLab repository
2. Ensure `render.yaml`, `Dockerfile.render`, `requirements-render.txt`, `render-entrypoint.sh` exist (all created)
3. Have your secrets ready (see environment variables section below)

---

## Step-by-Step Deployment

### Step 1 — Create Render Account
Sign up at https://render.com. A credit card is required for paid services.

### Step 2 — Connect Repository
- Dashboard → New → Blueprint
- Connect your GitHub/GitLab repo
- Render will detect `render.yaml` and show all services

### Step 3 — Review Blueprint Services
Render will show:
- `neta-postgres` (PostgreSQL database)
- `neta-redis` (Redis)
- `neta-api` (Web Service)
- `neta-celery-worker` (Background Worker)
- `neta-celery-beat` (Background Worker)
- `neta-frontend` (Static Site)

Click **Apply** to create all services.

### Step 4 — Set Secret Environment Variables
Variables marked `sync: false` in render.yaml are NOT set automatically.
Go to each service → **Environment** → fill in:

**For neta-api, neta-celery-worker** (required):
```
SECRET_KEY         = <python3 -c "import secrets; print(secrets.token_hex(32))">
```

**For neta-api** (optional — enable when ready):
```
WHATSAPP_API_TOKEN          = <from Meta Developer Console>
WHATSAPP_PHONE_ID           = <from Meta Developer Console>
WHATSAPP_WEBHOOK_VERIFY_TOKEN = <your chosen token>
TELEGRAM_BOT_TOKEN          = <from @BotFather>
TELEGRAM_CHAT_ID            = <your group/channel chat ID>
```

### Step 5 — Wait for Builds
First build takes 8–15 minutes (compiling GDAL, PostGIS, Python packages).
Watch logs at: Dashboard → neta-api → Logs

### Step 6 — Set ALLOWED_ORIGINS
After neta-api deploys, its URL will be something like `https://neta-api.onrender.com`.
After neta-frontend deploys, its URL will be `https://neta-frontend.onrender.com`.

Go to neta-api → Environment → update:
```
ALLOWED_ORIGINS = ["https://neta-frontend.onrender.com","https://app.netaai.in"]
```

Then **Manual Deploy** to apply.

### Step 7 — Set Frontend API URL
Go to neta-frontend → Environment:
```
VITE_API_URL = https://neta-api.onrender.com
```
Then **Manual Deploy** → this triggers a fresh frontend build with the correct API URL.

### Step 8 — Enable PostGIS Extension
Connect to the managed PostgreSQL and run:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```
Render's managed PostgreSQL supports PostGIS — you just need to enable it.

To connect: Dashboard → neta-postgres → Info → copy the External Connection String → run:
```bash
psql "<connection-string>" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

**Note:** The `render-entrypoint.sh` also tries to create these extensions at startup. But since the API doesn't have superuser access, it may need to be done manually once by a Render database admin.

### Step 9 — Verify
```
https://neta-api.onrender.com/api/health
→ {"status":"ok","service":"neta-api","version":"1.0.0"}

https://neta-api.onrender.com/api/docs
→ Swagger UI

https://neta-frontend.onrender.com
→ React frontend
```

### Step 10 — Create Admin User
The database is fresh on Render (no data migrated from local).
Run the seed script once:
```bash
# From your local machine, target Render's DB
DATABASE_URL="<render-postgres-external-url>" python scripts/seed_admin_user.py
```

---

## Database — Migrating Existing Data to Render

Your local database has real data (315 booths, 608 voters, etc.).
To migrate it to Render:

```powershell
# 1. Dump local database
.\scripts\backup-db.ps1

# 2. Get Render's external database URL from dashboard
# Dashboard → neta-postgres → Info → External Database URL

# 3. Restore to Render (from WSL or Linux terminal)
# gunzip -c backups/neta_backup_YYYYMMDD.sql.gz | \
#   PGSSLMODE=require psql "<render-external-url>"
```

**Important:** Render's managed PostgreSQL external connection requires SSL.
Use `PGSSLMODE=require` with psql.

---

## Environment Variables Reference

| Variable | Source | Required |
|---|---|---|
| `DATABASE_URL` | Auto (fromDatabase) | Yes |
| `REDIS_URL` | Auto (fromService) | Yes |
| `CELERY_BROKER_URL` | Auto (fromService) | Yes |
| `CELERY_RESULT_BACKEND` | Auto (fromService) | Yes |
| `SECRET_KEY` | Manual (sync:false) | Yes |
| `POSTGRES_PASSWORD` | Auto (fromDatabase) | Yes |
| `ENVIRONMENT` | Auto (production) | Yes |
| `ALLOWED_ORIGINS` | Manual after deploy | Yes |
| `VITE_API_URL` | Manual (frontend) | Yes |
| `WHATSAPP_API_TOKEN` | Manual (sync:false) | No |
| `WHATSAPP_PHONE_ID` | Manual (sync:false) | No |
| `TELEGRAM_BOT_TOKEN` | Manual (sync:false) | No |
| `TELEGRAM_CHAT_ID` | Manual (sync:false) | No |
| `TELEGRAM_ENABLED` | Set to "true" when ready | No |

---

## Key Differences from Local Docker Setup

| Aspect | Local Docker | Render |
|---|---|---|
| Port | Hardcoded 8000 | `$PORT` (injected by Render) |
| Dockerfile | `Dockerfile` | `Dockerfile.render` |
| Requirements | `requirements.txt` (with torch) | `requirements-render.txt` (without torch) |
| Entrypoint | `entrypoint.sh` | `render-entrypoint.sh` |
| Database URL | `postgresql+asyncpg://...@postgres:5432/...` | Render provides, entrypoint transforms |
| Redis URL | `redis://:pass@redis:6379/0` | Render provides `rediss://...` (TLS) |
| Database | Local Docker volume | Render Managed PostgreSQL |
| Frontend | `frontend/dist/` via nginx | Render Static Site (rebuilt by Render) |

**Local Docker setup is UNCHANGED. Both work independently.**

---

## Custom Domain (optional)

After verifying the deployment works on `.onrender.com` URLs:

1. Dashboard → neta-api → Settings → Custom Domains → Add `api.netaai.in`
2. Dashboard → neta-frontend → Settings → Custom Domains → Add `app.netaai.in`
3. Update DNS: `CNAME api.netaai.in → neta-api.onrender.com`
4. Update DNS: `CNAME app.netaai.in → neta-frontend.onrender.com`
5. Update `ALLOWED_ORIGINS` in neta-api to include `https://app.netaai.in`
6. Update `VITE_API_URL` in neta-frontend to `https://api.netaai.in`
7. Redeploy frontend

Render handles SSL automatically for custom domains.

---

## Troubleshooting

**Build timeout (15+ min)**
- First build is always slow (GDAL compilation). Subsequent builds are faster.
- If it times out, click **Manual Deploy** again.

**500 on /api/health after deploy**
- Check logs: Dashboard → neta-api → Logs
- Common cause: DATABASE_URL not set, or PostGIS extension not enabled

**"CORS blocked" in browser**
- `ALLOWED_ORIGINS` doesn't include the frontend URL
- Update the env var and redeploy

**Celery worker "Connection refused"**
- Redis service not yet ready — wait 2 min and redeploy worker

**Frontend shows blank page**
- `VITE_API_URL` not set or wrong — update and redeploy static site
