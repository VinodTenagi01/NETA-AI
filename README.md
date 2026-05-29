# NETA.AI — Political Campaign Intelligence Platform

Real-time AI-powered campaign intelligence for **Serilingampally Assembly Constituency (AC-52)**, Telangana · Election: 28 May 2026.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Demo Login](#demo-login)
4. [Screenshots](#screenshots)
5. [Environment Setup](#environment-setup)
6. [Auth Flow](#auth-flow)
7. [SSE Live Alerts](#sse-live-alerts)
8. [API Overview](#api-overview)
9. [Project Structure](#project-structure)
10. [Dashboard Pages](#dashboard-pages)
11. [Troubleshooting](#troubleshooting)
12. [Production Deployment](#production-deployment)

---

## Architecture Overview

```
Browser (http://127.0.0.1:5176)
  │
  └── Vite Dev Server (port 5176)
        │  /api/* proxy
        └── FastAPI Backend (port 8000)
              ├── PostgreSQL + PostGIS (port 5432)
              ├── Redis (port 6379)
              ├── Celery Worker  ──── background tasks
              └── Celery Beat   ──── scheduled tasks (every 5 min / daily)
```

### Services

| Container | Port | Purpose |
|-----------|------|---------|
| `neta_api` | 8000 | FastAPI REST API + SSE |
| `neta_postgres` | 5432 | PostgreSQL 15 + PostGIS 3.3 |
| `neta_redis` | 6379 | Cache + Celery message broker |
| `neta_celery_worker` | — | Async task processor |
| `neta_celery_beat` | — | Periodic task scheduler |
| Vite Dev Server | 5176 | React 18 + TypeScript frontend |

### Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Axios, Recharts, React Router v6 |
| Backend | FastAPI 0.104, Python 3.11, Pydantic v2, SQLAlchemy 2.x async |
| Database | PostgreSQL 15, PostGIS 3.3, asyncpg |
| Auth | JWT (python-jose), passlib + argon2-cffi |
| Queue | Celery 5 + Redis 7 |
| Infra | Docker Compose, multi-stage Dockerfile |

---

## Quick Start

### Prerequisites

- Docker Desktop (WSL2 backend on Windows)
- Node.js 18+

### Step 1 — Start the backend

```bash
cd D:\NETA.AI
docker-compose up -d
```

Wait ~15 seconds, then verify all containers are healthy:

```bash
docker ps
# neta_api, neta_postgres, neta_redis → "healthy"
# neta_celery_worker, neta_celery_beat → "running"
```

Verify the API:

```bash
curl http://localhost:8000/api/health
# {"status":"ok","service":"neta-api","version":"1.0.0"}
```

### Step 2 — Start the frontend

```bash
cd D:\NETA.AI\frontend
npm install        # only needed first time
npm run dev
# ▶  NETA.AI Phase 2 Dev Server → http://127.0.0.1:5176
```

### Step 3 — Open in browser

```
http://127.0.0.1:5176/login
```

### One-liner startup (PowerShell)

```powershell
Set-Location D:\NETA.AI
docker-compose up -d
Start-Sleep 15
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location D:\NETA.AI\frontend; npm run dev"
Start-Sleep 8
Start-Process "http://127.0.0.1:5176/login"
```

---

## Demo Login

| Field | Value |
|-------|-------|
| URL | `http://127.0.0.1:5176/login` |
| Email | `admin@netaai.in` |
| Password | `Admin123!Secure` |
| Role | `super_admin` |

The login page shows demo credentials automatically in development mode.

---

## Screenshots

> Add screenshots here once deployed. Suggested captures:

| Screenshot | Description |
|-----------|-------------|
| `screenshots/login.png` | Login page with demo credentials |
| `screenshots/command-centre.png` | Command Centre with live alerts and mood trend |
| `screenshots/ground-pulse.png` | Ground Pulse with field report sentiment breakdown |
| `screenshots/booth-management.png` | Booth heatmap with risk/health scores |
| `screenshots/candidate-brief.png` | Daily AI-generated candidate brief |
| `screenshots/opposition-intelligence.png` | Opposition activity timeline |

To capture: open `http://127.0.0.1:5176` in browser → navigate to each page → screenshot.

---

## Environment Setup

### Backend environment — `D:\NETA.AI\.env`

This file is loaded by Docker Compose and overrides defaults. It is gitignored.

```ini
# D:\NETA.AI\.env  (create if missing)
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:5175","http://localhost:5176","http://127.0.0.1:5175","http://127.0.0.1:5176"]
```

Full list of configurable variables (all have defaults in `docker-compose.yml`):

| Variable | Dev Default | Notes |
|----------|-------------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://netaai_app:netaai_password@postgres:5432/netaai_prod` | |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | **Must change for production** |
| `ALLOWED_ORIGINS` | `["http://localhost:5173","http://localhost:5175"]` | Override in `.env` |
| `REDIS_URL` | `redis://:redis_password@redis:6379/0` | |
| `POSTGRES_PASSWORD` | `netaai_password` | **Must change for production** |
| `REDIS_PASSWORD` | `redis_password` | **Must change for production** |
| `ENVIRONMENT` | `development` | Set to `production` in prod |
| `WHATSAPP_API_TOKEN` | `""` | Required for live WhatsApp alerts |
| `WHATSAPP_PHONE_ID` | `""` | Meta Business phone number ID |

### Frontend environment — `D:\NETA.AI\frontend\.env.local`

```ini
VITE_API_URL=http://127.0.0.1:5176
```

This routes all `/api/*` requests through the Vite dev proxy to `http://localhost:8000`, eliminating CORS issues in development.

---

## Auth Flow

```
1. POST /api/auth/login  { email, password }
        ↓
   Returns { access_token (15 min), refresh_token (7 days) }
        ↓
2. Frontend stores both tokens in JS module memory (never localStorage)
        ↓
3. Every request attaches: Authorization: Bearer <access_token>
        ↓
4. On 401 response → interceptor fires:
        a. Sends POST /api/auth/refresh { refresh_token }
        b. Gets new access_token
        c. Retries the original request
        ↓
5. On page reload → tokens lost (in-memory) → user must log in again
   (this is intentional: no token persistence = no XSS token theft)
```

**RBAC Roles** (in order of privilege):

| Role | Access |
|------|--------|
| `super_admin` | All endpoints |
| `campaign_manager` | All except admin management |
| `ground_commander` | Ground ops, booths, reports |
| `data_analyst` | Read-only analytics endpoints |
| `field_worker` | Report submission only |
| `candidate` | Candidate brief, read-only |

---

## SSE Live Alerts

The Command Centre uses Server-Sent Events for push notifications without polling.

**Connection:** `GET /api/sse/alerts?token=<access_token>`

The EventSource API cannot send custom headers, so the JWT is passed as a query parameter.

```javascript
// Frontend usage (hooks/useSSE.js)
const url = `/api/sse/alerts?token=${accessToken}`;
const es = new EventSource(url);

es.addEventListener('connected', e => { /* initial handshake */ });
es.addEventListener('heartbeat', e => { /* keep-alive every 30s */ });
es.addEventListener('alert', e => { /* new alert pushed by backend */ });
```

**Events:**
| Event | Payload | Frequency |
|-------|---------|-----------|
| `connected` | `{ user_id, ts }` | On connect |
| `heartbeat` | `{ ts }` | Every 30 seconds |
| `alert` | Alert object | When new alert is created |

The browser automatically reconnects on disconnect (native EventSource behaviour).

---

## API Overview

Interactive docs: **`http://localhost:8000/api/docs`**

### Authentication — `/api/auth`

| Method | Path | Access | Description |
|--------|------|--------|-------------|
| POST | `/api/auth/login` | Public | Login, returns `access_token` + `refresh_token` |
| POST | `/api/auth/refresh` | Public | Exchange refresh token for new access token |
| GET | `/api/auth/me` | Auth | Current user profile |
| POST | `/api/auth/register` | Public | Register new user |
| PATCH | `/api/auth/change-password` | Auth | Change own password |
| POST | `/api/auth/logout` | Auth | Logout (clears client-side tokens) |

**JWT flow**: Access token expires in 15 min. The frontend automatically refreshes using the in-memory refresh token (7 day expiry). On page reload, the user must log in again.

### Intelligence Aggregation — `/api/intelligence`

Aggregates data from multiple modules into dashboard-ready responses.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/intelligence/command-centre/overview` | Booth coverage, avg mood, alert count, 7-day mood trend |
| GET | `/api/intelligence/alerts/live` | Last 24h unacknowledged alerts |
| PATCH | `/api/intelligence/alerts/{id}/done` | Acknowledge an alert |
| GET | `/api/intelligence/ground-pulse/live` | 4h field report sentiment breakdown |
| GET | `/api/intelligence/booths/heatmap` | All booths with risk/health/contact scores |
| GET | `/api/intelligence/sentiment/trends` | 14-day sentiment trend |
| GET | `/api/intelligence/opposition-intelligence` | 48h opposition activity reports |
| GET | `/api/intelligence/candidate-brief` | Daily summary for candidate |
| POST | `/api/intelligence/briefs/generate` | Queue brief generation |

### Server-Sent Events — `/api/sse`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sse/alerts?token=<jwt>` | Live alert stream (heartbeat every 30s) |

### Ground Operations — `/api/v1/ground`

| Path | Description |
|------|-------------|
| `POST /reports` | Submit field report |
| `GET /reports` | List reports with filters |
| `GET /mood/zones` | Zone mood aggregation |
| `GET /mood/trends` | Constituency mood timeseries |
| `GET /escalations` | Active escalations |
| `PATCH /escalations/{id}/resolve` | Resolve escalation |
| `GET /workers/active` | Active field workers |
| `POST /workers/check-in` | Worker booth check-in |

### Booth Management — `/api/v1/booths`

| Path | Description |
|------|-------------|
| `GET /` | List booths (filter by zone, risk, health) |
| `GET /{id}` | Booth detail |
| `PATCH /{id}` | Update booth |
| `GET /risk-report` | Constituency risk summary |
| `GET /health/status` | Booth health dashboard |
| `GET /{id}/volunteers` | Booth volunteer list |
| `POST /{id}/volunteers` | Assign volunteer |
| `POST /{id}/assign-commander` | Assign booth commander |
| `POST /{id}/recompute-scores` | Recalculate risk/health |

### Other Modules

| Prefix | Module | Key Endpoints |
|--------|--------|---------------|
| `/api/v1/geo` | GeoJSON Mapping | constituency boundary, booth GeoJSON, zone overlays |
| `/api/v1/news` | News Intelligence | articles, sentiment trends, source health |
| `/api/v1/predictions` | Win Probability | win-probability, sentiment-breakdown, scenario analysis |
| `/api/v1/opposition` | Opposition Intel | narratives, sentiment comparison, activity map |
| `/api/v1/notifications` | WhatsApp Alerts | alerts list, delivery status, preferences |

---

## Project Structure

```
D:\NETA.AI\
├── app/
│   ├── main.py                       # FastAPI app entry point, CORS, router registry
│   ├── config.py                     # Pydantic settings (loaded from env)
│   ├── database_design/
│   │   ├── models.py                 # SQLAlchemy ORM models (all tables)
│   │   └── database.py               # Async engine, session factory
│   ├── security_auth/
│   │   ├── router.py                 # Auth endpoints
│   │   ├── dependencies.py           # JWT + RBAC FastAPI dependencies
│   │   └── utils.py                  # hash_password, verify_token, create_access_token
│   ├── intelligence/
│   │   ├── router.py                 # Dashboard aggregation endpoints
│   │   └── sse.py                    # Server-Sent Events live alert stream
│   ├── ground_operations/            # Field reports, mood, escalations, worker attendance
│   ├── booth_management/             # Booth health, risk scoring, volunteers
│   ├── geojson_mapping/              # PostGIS boundary + booth spatial data
│   ├── news_intelligence/            # Article ingest, sentiment NLP
│   ├── prediction_sentiment/         # Win probability model, sentiment forecast
│   ├── opposition_intelligence/      # Opposition narrative monitoring
│   └── whatsapp_integration/         # Meta WhatsApp API, Celery async tasks
├── frontend/
│   ├── src/
│   │   ├── App.tsx                   # Route definitions (14 pages)
│   │   ├── main.tsx                  # React root, providers
│   │   ├── pages/                    # 14 route-level page components
│   │   ├── components/               # Reusable UI (StatCard, WinGauge, AlertFeed…)
│   │   ├── api/                      # Axios API clients per module
│   │   ├── hooks/                    # useAutoRefresh, useSSE, useApi, useResponsive
│   │   └── store/                    # AuthContext (JWT), ToastContext
│   ├── vite.config.ts                # Port 5176, /api proxy → localhost:8000
│   └── .env.local                    # VITE_API_URL=http://127.0.0.1:5176
├── scripts/
│   ├── seed_admin_user.py            # Create/reset admin user
│   └── healthcheck.py                # Service connectivity checks
├── data/                             # SQL seed files, OCR cache
├── celeryconfig.py                   # Celery broker, queues, beat schedule
├── docker-compose.yml                # All backend services
├── docker-compose.prod.yml           # Production overrides
├── Dockerfile                        # Multi-stage Python 3.11 image
└── requirements.txt                  # Python dependencies (pinned)
```

---

## Dashboard Pages

| URL | Page | Data Source |
|-----|------|-------------|
| `/command-centre` | Command Centre | Intelligence aggregation + SSE alerts |
| `/constituency-intelligence` | Constituency Intel | Ground mood, booth heatmap |
| `/ground-pulse` | Ground Pulse | Field reports, worker activity |
| `/booth-management` | Booth Management | Booth list, risk, volunteers |
| `/opposition-intelligence` | Opposition Intel | Narratives, sentiment comparison |
| `/candidate-brief` | Candidate Brief | Daily AI-generated summary |
| `/news-intelligence` | News Intelligence | Articles, sentiment trends |
| `/field-reports` | Field Reports | Report submission + list |
| `/booth-intelligence` | Booth Intelligence | Booth-level analytics |
| `/constituency-demographics` | Demographics | Voter demographic overlays |
| `/data-sources` | Data Sources | Source health, ingestion status |
| `/voter-roll-upload` | Voter Roll Upload | CSV import |
| `/admin` | Admin Dashboard | User management |

---

## Troubleshooting

### Login fails — "Invalid email or password"

The Docker image may be missing `argon2-cffi` (password hashing backend). This happens if the container was started from an older image.

```bash
# Install in running container
docker exec -u root neta_api pip install argon2-cffi==23.1.0
docker restart neta_api

# If still failing, reset the password hash in the database:
# 1. Generate a fresh hash inside the container:
docker exec neta_api python -c "
from app.security_auth.utils import hash_password
print(hash_password('Admin123!Secure'))
"
# 2. Update the database (paste the hash from step 1):
docker exec neta_postgres psql -U netaai_app -d netaai_prod -c \
  "UPDATE users SET password_hash='<paste-hash-here>', login_attempts=0, locked_until=NULL WHERE email='admin@netaai.in';"
```

**Permanent fix — rebuild the image:**
```bash
cd D:\NETA.AI
docker-compose build api
docker-compose up -d --no-deps api
```

### Account locked — "Account is locked due to too many failed login attempts"

```bash
docker exec neta_postgres psql -U netaai_app -d netaai_prod -c \
  "UPDATE users SET login_attempts=0, locked_until=NULL WHERE email='admin@netaai.in';"
```

### Port 5176 already in use

```powershell
# Kill all Node/Vite processes
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
# Restart frontend
Set-Location D:\NETA.AI\frontend; npm run dev
```

### CORS errors in browser

1. Check `D:\NETA.AI\.env` exists and contains `http://127.0.0.1:5176` in `ALLOWED_ORIGINS`
2. Restart the API container: `docker-compose up -d --no-deps api`
3. Confirm the Vite proxy is running and `VITE_API_URL=http://127.0.0.1:5176` in `.env.local`

### Dashboard shows "API unavailable — showing cached data"

The dashboard gracefully falls back to mock data when backend calls fail. Check:
```bash
# Is the backend up?
curl http://localhost:8000/api/health

# Is Vite proxy forwarding?
curl http://127.0.0.1:5176/api/health

# Are there auth errors?
docker logs neta_api --tail 20
```

### Backend Internal Server Error on startup

```bash
docker logs neta_api --tail 30
# Common causes:
# - Database not ready → wait and retry, or: docker restart neta_api
# - Missing env var → check .env file
```

### WSL2 zombie containers intercept ports

Symptom: `localhost:8000` works but `127.0.0.1:8000` doesn't (or vice versa).

```powershell
# Stop all containers
docker stop $(docker ps -q)
# Restart Docker Desktop
# Then: docker-compose up -d
```

### Database connection errors

```bash
docker exec neta_postgres pg_isready -U netaai_app
# If unhealthy:
docker restart neta_postgres
# Wait 10s, then:
docker restart neta_api
```

### Celery tasks not running

```bash
# Check worker is connected and tasks are registered
docker exec neta_celery_worker celery -A celeryconfig inspect registered

# Check for errors
docker logs neta_celery_worker --tail 30
```

---

## Production Deployment

### Environment hardening

Create a production `.env` file (never commit to version control):

```ini
# Secrets — generate with: openssl rand -hex 32
SECRET_KEY=<generated-64-char-hex>
POSTGRES_PASSWORD=<strong-random-password>
REDIS_PASSWORD=<strong-random-password>

# Application
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=["https://your-domain.com"]

# Database
POSTGRES_DB=netaai_prod
POSTGRES_USER=netaai_app
DATABASE_URL=postgresql+asyncpg://netaai_app:<password>@postgres:5432/netaai_prod

# WhatsApp (Meta Business API)
WHATSAPP_API_TOKEN=<meta-api-token>
WHATSAPP_PHONE_ID=<meta-phone-number-id>
```

### Deploy with production compose

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Seed the admin user

```bash
docker exec neta_api python scripts/seed_admin_user.py \
  --email admin@your-domain.com \
  --password '<strong-password>'
```

### Nginx reverse proxy (recommended)

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # SSE support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }

    location / {
        root /var/www/neta-frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

Build the frontend for production:

```bash
cd D:\NETA.AI\frontend
VITE_API_URL=https://your-domain.com npm run build
# Output: frontend/dist/
```

### Production checklist

- [ ] `SECRET_KEY` replaced with `openssl rand -hex 32` output
- [ ] `POSTGRES_PASSWORD`, `REDIS_PASSWORD` set to strong secrets
- [ ] `ENVIRONMENT=production`, `DEBUG=false`
- [ ] `ALLOWED_ORIGINS` set to production domain only
- [ ] HTTPS configured (nginx + Let's Encrypt)
- [ ] `WHATSAPP_API_TOKEN` and `WHATSAPP_PHONE_ID` configured
- [ ] Admin user seeded with a secure password
- [ ] PostgreSQL daily backups configured
- [ ] Log aggregation set up (stdout → Loki / CloudWatch)
- [ ] Uptime monitoring on `GET /api/health`
- [ ] Docker restart policies set (`restart: unless-stopped` — already in compose)
- [ ] `docker-compose.prod.yml` resource limits reviewed
- [ ] Frontend built (`npm run build`) and served via nginx
- [ ] JWT `ACCESS_TOKEN_EXPIRE_MINUTES` reviewed (default: 15 min)
- [ ] Celery `worker_max_memory_per_child` tuned for server RAM

---

*NETA.AI Phase 2 · Sessions 01–10 Complete · Serilingampally AC-52 · 2026 Election*
