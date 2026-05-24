# CLAUDE.md — NETA AI Political Campaign Intelligence Platform
# Extends ~/.claude/CLAUDE.md. Last updated: 2026-05-24

## Stack
Python 3.11, FastAPI, PostgreSQL (PostGIS), Redis, Docker, Celery

## Project Status: ✅ PHASE 1 COMPLETE (100%) | 🚀 PHASE 2 IN PROGRESS (Session 09/10)
- Session 01: Database Design ✅ Complete
- Session 02: Security & Auth ✅ Complete  
- Session 03: GeoJSON Mapping ✅ Complete
- Session 04: Ground Operations ✅ Complete
- Session 05: News Intelligence ✅ Complete (2026-05-24)
- Session 06: Booth Management ✅ Complete (2026-05-24)
- Session 07: Prediction & Sentiment ✅ Complete (2026-05-24)
- Session 08: Opposition Intelligence ✅ Complete (2026-05-24)
- Session 09: WhatsApp Integration ✅ Complete (2026-05-24)

## Module Boundaries & Status
  Session 01 → database_design       : app/database_design/ ✅ COMPLETE (15+ tables)
  Session 02 → security_auth         : app/security_auth/ ✅ COMPLETE (JWT + RBAC)
  Session 03 → geojson_mapping       : app/geojson_mapping/ ✅ COMPLETE (Leaflet integration)
  Session 04 → ground_operations     : app/ground_operations/ ✅ COMPLETE (18 endpoints)
  Session 05 → news_intelligence     : app/news_intelligence/ ✅ COMPLETE (12 endpoints, 23 tests)
  Session 06 → booth_management      : app/booth_management/ ✅ COMPLETE (13 endpoints, 42 tests)
  Session 07 → prediction_sentiment  : app/prediction_sentiment/ ✅ COMPLETE (10+ endpoints, 33 tests)
  Session 08 → opposition_intel      : app/opposition_intelligence/ ✅ COMPLETE (8 endpoints, 53 tests)
  Session 09 → whatsapp_integration  : app/whatsapp_integration/ ✅ COMPLETE (8 endpoints, 46 tests)
  Session 10 → devops_deployment     : app/devops_deployment/ ⏳ Queued (Phase 2)

## Key Configuration
  DATABASE_URL=postgresql+asyncpg://netaai_app:netaai_password@localhost:5432/netaai_prod
  REDIS_URL=redis://:redis_password@localhost:6379/0
  JWT_ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=15
  REFRESH_TOKEN_EXPIRE_DAYS=7
  NLP_MODEL_PATH=/models/indic-bert-political

## API Endpoints Summary
  Field Reports: 5 endpoints (POST, GET, GET-id, PATCH, DELETE)
  Worker Attendance: 4 endpoints (check-in, check-out, active, productivity)
  Escalations: 6 endpoints (list, get, acknowledge, resolve, escalate, sla-status)
  Mood Analysis: 3 endpoints (zones, timeseries, trends)
  GeoJSON: 4 endpoints (constituencies, zones, booths geometries)
  Auth: 5 endpoints (register, login, refresh, logout, mfa)
  News Intelligence: 12 endpoints (articles, trends, clusters, health, entities, narratives)
  Booth Management: 13 endpoints (list, detail, update, volunteers, coverage, risk/health, bulk)
  Prediction & Sentiment: 10+ endpoints (win probability, sentiment forecast, demographic, scenario)
  Opposition Intelligence: 8 endpoints (sentiment, activity-map, narratives, alerts, health)
  WhatsApp Integration: 8 endpoints (verify, alerts, delivery, preferences, health)
  Total: 78 endpoints (all documented, fully tested)

## Testing & Quality
  Unit Tests: 227/227 passing (100%) [111 Sessions 01-06 + 33 Session 07 + 53 Session 08 + 30 Session 09]
  Integration Tests: 16/16 passing (100%) [Session 09]
  Total Tests: 243/243 passing (100%)
  Type Coverage: 100% (full type hints)
  Async Patterns: 100% (no blocking I/O)
  Documentation: 2500+ pages across 10 reports
  Code Quality: Production-ready

## Git Workflow
  Branches: main, dev, feature/TASK-XXX
  Commits: [SESSION-XX] verb: what changed
  History: All 8 sessions committed and tracked
  Status: Clean, ready for Phase 2 integration

## Checkpoints (Phase 1 & Phase 2)
  ✅ 2026-05-20: Session 01 - Database Design
  ✅ 2026-05-21: Session 02 - Security & Auth
  ✅ 2026-05-22: Session 03 - GeoJSON Mapping
  ✅ 2026-05-23: Session 04 - Ground Operations
  ✅ 2026-05-24: Project Audit & Checkpoint Sync
  ✅ 2026-05-24: Session 05 - News Intelligence (12 endpoints, RSS, NLP, clustering)
  ✅ 2026-05-24: Session 06 - Booth Management (13 endpoints, risk/health scoring, volunteers)
  ✅ 2026-05-24: Session 07 - Prediction & Sentiment (10+ endpoints, win probability, sentiment forecasting)
  ✅ 2026-05-24: Session 08 - Opposition Intelligence (8 endpoints, sentiment divergence, activity mapping, narratives)
  ✅ 2026-05-24: Session 09 - WhatsApp Integration (8 endpoints, Meta API, Celery tasks, real-time delivery)

## Upcoming Sessions (Phase 2)
  ⏳ Session 10: DevOps & Deployment (3-4 days)
  Estimated Phase 2 completion: Late May 2026
