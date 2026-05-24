#!/bin/bash
# Database restore script for NETA AI
# Restores PostgreSQL database from backup
# Usage: ./restore.sh <backup_file> [drop_existing]

set -e

# Configuration
: ${DATABASE_HOST:=postgres}
: ${DATABASE_PORT:=5432}
: ${POSTGRES_USER:=netaai_app}
: ${POSTGRES_DB:=netaai_prod}
: ${POSTGRES_PASSWORD:=}

BACKUP_FILE="${1:-}"
DROP_EXISTING="${2:-false}"

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

# Function to validate backup file
validate_backup() {
    log "Validating backup file: $BACKUP_FILE"

    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: $BACKUP_FILE"
        return 1
    fi

    # Check if file is gzipped
    if file "$BACKUP_FILE" | grep -q "gzip"; then
        log "✓ Backup file is gzipped"
        return 0
    # Check if file is plain SQL
    elif file "$BACKUP_FILE" | grep -q "text"; then
        log "✓ Backup file is plain SQL"
        return 0
    else
        log_error "Unsupported backup file format"
        return 1
    fi
}

# Function to wait for PostgreSQL
wait_for_postgres() {
    log "Waiting for PostgreSQL to become available..."

    local counter=0
    local max_attempts=30

    until [ $counter -ge $max_attempts ]; do
        if PGPASSWORD="$POSTGRES_PASSWORD" psql \
            -h "$DATABASE_HOST" \
            -p "$DATABASE_PORT" \
            -U "$POSTGRES_USER" \
            -d "postgres" \
            -c "SELECT 1" >/dev/null 2>&1; then
            log "✓ PostgreSQL is available"
            return 0
        fi

        counter=$((counter + 1))
        log "PostgreSQL not available yet... (attempt $counter/$max_attempts)"
        sleep 1
    done

    log_error "PostgreSQL failed to become available"
    return 1
}

# Function to drop existing database
drop_existing_db() {
    log "Dropping existing database: $POSTGRES_DB"

    # Terminate connections to the database
    PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$DATABASE_HOST" \
        -p "$DATABASE_PORT" \
        -U "$POSTGRES_USER" \
        -d "postgres" \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();"

    # Drop the database
    PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$DATABASE_HOST" \
        -p "$DATABASE_PORT" \
        -U "$POSTGRES_USER" \
        -d "postgres" \
        -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"

    if [ $? -eq 0 ]; then
        log "✓ Database dropped successfully"
        return 0
    else
        log_error "Failed to drop database"
        return 1
    fi
}

# Function to create empty database
create_empty_db() {
    log "Creating empty database: $POSTGRES_DB"

    PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$DATABASE_HOST" \
        -p "$DATABASE_PORT" \
        -U "$POSTGRES_USER" \
        -d "postgres" \
        -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;"

    if [ $? -eq 0 ]; then
        log "✓ Database created successfully"
        return 0
    else
        log_error "Failed to create database"
        return 1
    fi
}

# Function to restore from backup
restore_from_backup() {
    log "Restoring database from backup: $BACKUP_FILE"

    # Determine if backup is gzipped
    if file "$BACKUP_FILE" | grep -q "gzip"; then
        log "Using gzip decompression..."
        gunzip -c "$BACKUP_FILE" | PGPASSWORD="$POSTGRES_PASSWORD" psql \
            -h "$DATABASE_HOST" \
            -p "$DATABASE_PORT" \
            -U "$POSTGRES_USER" \
            -d "$POSTGRES_DB" \
            --set ON_ERROR_STOP=on
    else
        log "Restoring from plain SQL file..."
        PGPASSWORD="$POSTGRES_PASSWORD" psql \
            -h "$DATABASE_HOST" \
            -p "$DATABASE_PORT" \
            -U "$POSTGRES_USER" \
            -d "$POSTGRES_DB" \
            --set ON_ERROR_STOP=on \
            -f "$BACKUP_FILE"
    fi

    if [ $? -eq 0 ]; then
        log "✓ Database restored successfully"
        return 0
    else
        log_error "Database restore failed"
        return 1
    fi
}

# Function to verify restore
verify_restore() {
    log "Verifying restored database..."

    # Check table count
    TABLE_COUNT=$(PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$DATABASE_HOST" \
        -p "$DATABASE_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")

    if [ "$TABLE_COUNT" -gt 0 ]; then
        log "✓ Database verification passed (found $TABLE_COUNT tables)"
        return 0
    else
        log_error "Database verification failed (no tables found)"
        return 1
    fi
}

# Main function
main() {
    if [ -z "$BACKUP_FILE" ]; then
        log_error "Usage: ./restore.sh <backup_file> [drop_existing]"
        echo ""
        echo "Arguments:"
        echo "  backup_file     Path to backup file (gzipped or plain SQL)"
        echo "  drop_existing   Drop existing database before restore (true/false, default: false)"
        return 1
    fi

    log "Starting NETA AI database restore..."
    log "Backup file: $BACKUP_FILE"
    log "Target database: $POSTGRES_DB"
    log "Drop existing: $DROP_EXISTING"

    # Validate backup file
    if ! validate_backup; then
        return 1
    fi

    # Wait for PostgreSQL
    if ! wait_for_postgres; then
        return 1
    fi

    # Drop existing database if requested
    if [ "$DROP_EXISTING" = "true" ]; then
        if ! drop_existing_db; then
            return 1
        fi

        # Create empty database
        if ! create_empty_db; then
            return 1
        fi
    fi

    # Restore from backup
    if ! restore_from_backup; then
        return 1
    fi

    # Verify restore
    if ! verify_restore; then
        return 1
    fi

    log "✓ Database restore completed successfully"
    log "Database is ready for use!"
    return 0
}

# Execute main function
main "$@"
