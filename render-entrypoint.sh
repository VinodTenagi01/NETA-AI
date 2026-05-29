#!/bin/bash
# render-entrypoint.sh — Render-specific startup script
#
# Key differences from entrypoint.sh (local Docker version):
#   - Parses Render's single DATABASE_URL string (no separate host/port vars)
#   - Rewrites DATABASE_URL for asyncpg compatibility (postgres:// → postgresql+asyncpg://)
#   - Handles SSL query param format difference (sslmode= → ssl=)
#   - Skips migrations for Celery worker/beat (set RUN_MIGRATIONS=false)
#
# DO NOT USE for local Docker Compose — use entrypoint.sh instead.

set -e
set -o pipefail

log()       { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }
log_error() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2; }

# ── 1. Transform DATABASE_URL for asyncpg ────────────────────────────────────
# Render provides: postgres://user:pass@host:port/db?sslmode=require
# asyncpg needs:   postgresql+asyncpg://user:pass@host:port/db?ssl=require
if [ -n "$DATABASE_URL" ]; then
    ASYNCPG_URL=$(echo "$DATABASE_URL" \
        | sed 's|^postgres://|postgresql+asyncpg://|' \
        | sed 's|^postgresql://|postgresql+asyncpg://|' \
        | sed 's|sslmode=require|ssl=require|g')
    export DATABASE_URL="$ASYNCPG_URL"
    log "DATABASE_URL rewritten for asyncpg (SSL preserved)"
fi

# Also expose a sync URL for psql (migrations)
PSQL_URL=$(echo "$DATABASE_URL" \
    | sed 's|^postgresql+asyncpg://|postgresql://|' \
    | sed 's|ssl=require|sslmode=require|g')

# ── 2. Wait for PostgreSQL ────────────────────────────────────────────────────
wait_for_postgres() {
    local attempts=0
    local max=30
    log "Waiting for PostgreSQL..."
    until [ $attempts -ge $max ]; do
        if PGSSLMODE=require psql "$PSQL_URL" -c "SELECT 1" >/dev/null 2>&1; then
            log "PostgreSQL ready"
            return 0
        fi
        attempts=$((attempts + 1))
        log "Waiting... ($attempts/$max)"
        sleep 3
    done
    log_error "PostgreSQL not available after $((max * 3))s"
    return 1
}

# ── 3. Run migrations (API service only) ─────────────────────────────────────
run_migrations() {
    local migration_dir="/app/app/database_design/migrations"
    if [ ! -d "$migration_dir" ]; then
        log "No migration directory — skipping"
        return 0
    fi

    # Ensure PostGIS extension exists
    PGSSLMODE=require psql "$PSQL_URL" -c \
        "CREATE EXTENSION IF NOT EXISTS postgis;" >/dev/null 2>&1 || true
    PGSSLMODE=require psql "$PSQL_URL" -c \
        "CREATE EXTENSION IF NOT EXISTS postgis_topology;" >/dev/null 2>&1 || true

    log "Running SQL migrations from $migration_dir..."
    for f in $(ls "$migration_dir"/*.sql 2>/dev/null | sort); do
        name=$(basename "$f")
        if PGSSLMODE=require psql "$PSQL_URL" -v ON_ERROR_STOP=0 -f "$f" >/dev/null 2>&1; then
            log "Applied: $name"
        else
            log "Skipped (may already exist): $name"
        fi
    done
    log "Migrations complete"
}

# ── 4. Main ───────────────────────────────────────────────────────────────────
log "NETA AI Render entrypoint starting..."
log "Service type: ${SERVICE_TYPE:-web}"

if ! wait_for_postgres; then
    log_error "Cannot start without PostgreSQL"
    exit 1
fi

# Only run migrations for the API web service
if [ "${RUN_MIGRATIONS:-true}" = "true" ] && [ "${SERVICE_TYPE:-web}" = "web" ]; then
    run_migrations
fi

log "Pre-flight checks passed. Starting: $*"
exec "$@"
