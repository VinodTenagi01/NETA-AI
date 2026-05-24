#!/bin/bash
# Database backup script for NETA AI
# Backs up PostgreSQL database to S3/GCS or local storage
# Usage: ./backup.sh [backup_location]

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/app/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
BACKUP_LOCATION="${1:-local}"  # local, s3, or gcs

# Database configuration
: ${DATABASE_HOST:=postgres}
: ${DATABASE_PORT:=5432}
: ${POSTGRES_USER:=netaai_app}
: ${POSTGRES_DB:=netaai_prod}
: ${POSTGRES_PASSWORD:=}

# AWS S3 configuration (if backup_location is s3)
: ${AWS_S3_BUCKET:=}
: ${AWS_S3_REGION:=us-east-1}

# Google Cloud Storage configuration (if backup_location is gcs)
: ${GCS_BUCKET:=}

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

# Function to create local backup
backup_local() {
    log "Starting local PostgreSQL backup..."

    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"

    # Generate backup filename with timestamp
    BACKUP_FILE="$BACKUP_DIR/neta_backup_$(date +%Y%m%d_%H%M%S).sql.gz"

    # Perform backup
    log "Dumping database to $BACKUP_FILE..."
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h "$DATABASE_HOST" \
        -p "$DATABASE_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --verbose \
        --format=plain \
        | gzip > "$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log "✓ Backup completed successfully: $BACKUP_FILE ($BACKUP_SIZE)"

        # Clean up old backups (retention)
        log "Cleaning up backups older than $RETENTION_DAYS days..."
        find "$BACKUP_DIR" -name "neta_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
        log "✓ Old backups cleaned up"

        return 0
    else
        log_error "Backup failed"
        return 1
    fi
}

# Function to upload to AWS S3
backup_s3() {
    log "Starting PostgreSQL backup to S3..."

    if [ -z "$AWS_S3_BUCKET" ]; then
        log_error "AWS_S3_BUCKET not configured"
        return 1
    fi

    # Check if aws-cli is installed
    if ! command -v aws &> /dev/null; then
        log_error "aws-cli is not installed"
        return 1
    fi

    # Generate backup filename
    BACKUP_FILE="/tmp/neta_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
    S3_KEY="backups/$(basename $BACKUP_FILE)"

    log "Dumping database..."
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h "$DATABASE_HOST" \
        -p "$DATABASE_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        | gzip > "$BACKUP_FILE"

    if [ $? -ne 0 ]; then
        log_error "Database dump failed"
        rm -f "$BACKUP_FILE"
        return 1
    fi

    log "Uploading to S3: s3://$AWS_S3_BUCKET/$S3_KEY"
    aws s3 cp "$BACKUP_FILE" "s3://$AWS_S3_BUCKET/$S3_KEY" \
        --region "$AWS_S3_REGION" \
        --sse AES256

    if [ $? -eq 0 ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log "✓ Backup uploaded to S3 ($BACKUP_SIZE)"

        # Clean up local file
        rm -f "$BACKUP_FILE"

        # Clean up old S3 backups (retention)
        log "Cleaning up S3 backups older than $RETENTION_DAYS days..."
        aws s3api list-objects-v2 \
            --bucket "$AWS_S3_BUCKET" \
            --prefix "backups/" \
            --region "$AWS_S3_REGION" \
            --query "Contents[?LastModified<'$(date -u -d "$RETENTION_DAYS days ago" +%Y-%m-%dT%H:%M:%S)'].Key" \
            --output text \
            | xargs -I {} aws s3api delete-object \
                --bucket "$AWS_S3_BUCKET" \
                --key {} \
                --region "$AWS_S3_REGION" 2>/dev/null || true

        return 0
    else
        log_error "S3 upload failed"
        rm -f "$BACKUP_FILE"
        return 1
    fi
}

# Function to upload to Google Cloud Storage
backup_gcs() {
    log "Starting PostgreSQL backup to GCS..."

    if [ -z "$GCS_BUCKET" ]; then
        log_error "GCS_BUCKET not configured"
        return 1
    fi

    # Check if gsutil is installed
    if ! command -v gsutil &> /dev/null; then
        log_error "gsutil is not installed"
        return 1
    fi

    # Generate backup filename
    BACKUP_FILE="/tmp/neta_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
    GCS_PATH="gs://$GCS_BUCKET/backups/$(basename $BACKUP_FILE)"

    log "Dumping database..."
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h "$DATABASE_HOST" \
        -p "$DATABASE_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        | gzip > "$BACKUP_FILE"

    if [ $? -ne 0 ]; then
        log_error "Database dump failed"
        rm -f "$BACKUP_FILE"
        return 1
    fi

    log "Uploading to GCS: $GCS_PATH"
    gsutil -h "Content-Type:application/gzip" cp "$BACKUP_FILE" "$GCS_PATH"

    if [ $? -eq 0 ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log "✓ Backup uploaded to GCS ($BACKUP_SIZE)"

        # Clean up local file
        rm -f "$BACKUP_FILE"

        return 0
    else
        log_error "GCS upload failed"
        rm -f "$BACKUP_FILE"
        return 1
    fi
}

# Main function
main() {
    log "Starting NETA AI database backup (location: $BACKUP_LOCATION)..."

    case "$BACKUP_LOCATION" in
        local)
            backup_local
            ;;
        s3)
            backup_s3
            ;;
        gcs)
            backup_gcs
            ;;
        *)
            log_error "Unknown backup location: $BACKUP_LOCATION"
            log "Supported locations: local, s3, gcs"
            return 1
            ;;
    esac

    if [ $? -eq 0 ]; then
        log "✓ Backup completed successfully"
        return 0
    else
        log_error "Backup failed"
        return 1
    fi
}

# Execute main function
main "$@"
