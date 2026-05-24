#!/bin/bash
set -e

# Enable strict mode for better error handling
set -o pipefail

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

# Default environment variables
: ${DATABASE_HOST:=postgres}
: ${DATABASE_PORT:=5432}
: ${POSTGRES_USER:=netaai_app}
: ${POSTGRES_DB:=netaai_prod}
: ${POSTGRES_PASSWORD:=}
: ${HEALTH_CHECK_TIMEOUT:=30}
: ${MIGRATION_TIMEOUT:=60}

log "Starting NETA AI container entrypoint..."

# Function to wait for PostgreSQL
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

# Function to run database migrations
run_migrations() {
    log "Running database migrations with Alembic..."

    timeout $MIGRATION_TIMEOUT alembic upgrade head || {
        log_error "Database migrations failed"
        return 1
    }

    log "Database migrations completed successfully"
    return 0
}

# Function to verify database connectivity
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

# Main execution flow
main() {
    # Wait for PostgreSQL to be available
    if ! wait_for_postgres; then
        log_error "Cannot proceed without PostgreSQL"
        exit 1
    fi

    # Verify database connectivity
    if ! verify_database; then
        log_error "Cannot proceed without database verification"
        exit 1
    fi

    # Run database migrations
    if ! run_migrations; then
        log_error "Cannot proceed without successful migrations"
        exit 1
    fi

    log "All pre-flight checks passed!"
    log "Starting application with command: $@"

    # Execute the main application command
    exec "$@"
}

# Call main function
main "$@"
