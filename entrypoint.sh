#!/bin/bash
set -e
set -o pipefail

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

: ${DATABASE_HOST:=postgres}
: ${DATABASE_PORT:=5432}
: ${POSTGRES_USER:=netaai_app}
: ${POSTGRES_DB:=netaai_prod}
: ${POSTGRES_PASSWORD:=netaai_password}
: ${HEALTH_CHECK_TIMEOUT:=30}
: ${MIGRATION_TIMEOUT:=120}

log "Starting NETA AI container entrypoint..."

wait_for_postgres() {
    local counter=0
    local max_attempts=30

    log "Waiting for PostgreSQL at ${DATABASE_HOST}:${DATABASE_PORT}..."

    until [ $counter -ge $max_attempts ]; do
        if PGPASSWORD="$POSTGRES_PASSWORD" psql \
            -h "$DATABASE_HOST" \
            -p "$DATABASE_PORT" \
            -U "$POSTGRES_USER" \
            -d "$POSTGRES_DB" \
            -c "SELECT 1" >/dev/null 2>&1; then
            log "PostgreSQL is up and ready!"
            return 0
        fi

        counter=$((counter + 1))
        log "PostgreSQL not ready yet... (attempt $counter/$max_attempts)"
        sleep 1
    done

    log_error "PostgreSQL failed to become available after $max_attempts attempts"
    return 1
}

verify_database() {
    log "Verifying database connectivity..."

    if ! PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$DATABASE_HOST" \
        -p "$DATABASE_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -c "SELECT version();" >/dev/null 2>&1; then
        log_error "Database verification failed"
        return 1
    fi

    log "Database connectivity verified"
    return 0
}

run_migrations() {
    local migration_dir="/app/app/database_design/migrations"

    if [ ! -d "$migration_dir" ]; then
        log "No migration directory found at $migration_dir — skipping migrations"
        return 0
    fi

    log "Running SQL migrations from $migration_dir..."

    for migration_file in $(ls "$migration_dir"/*.sql 2>/dev/null | sort); do
        local name
        name=$(basename "$migration_file")
        log "Applying: $name"
        if PGPASSWORD="$POSTGRES_PASSWORD" psql \
            -h "$DATABASE_HOST" \
            -p "$DATABASE_PORT" \
            -U "$POSTGRES_USER" \
            -d "$POSTGRES_DB" \
            -v ON_ERROR_STOP=1 \
            -f "$migration_file" >/dev/null 2>&1; then
            log "Applied: $name"
        else
            log_error "Migration failed: $name — attempting to continue"
        fi
    done

    log "SQL migrations complete"
    return 0
}

main() {
    if ! wait_for_postgres; then
        log_error "Cannot proceed without PostgreSQL"
        exit 1
    fi

    if ! verify_database; then
        log_error "Cannot proceed without database verification"
        exit 1
    fi

    run_migrations

    log "All pre-flight checks passed!"
    log "Starting application: $*"

    exec "$@"
}

main "$@"
