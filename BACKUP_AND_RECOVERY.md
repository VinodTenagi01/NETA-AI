# NETA.AI — Backup and Recovery Guide

---

## Backup Strategy

| Component | Method | Storage | Retention |
|---|---|---|---|
| PostgreSQL | pg_dump compressed | Local `backups/` dir | 30 days |
| Redis | Append-only file (AOF) | Docker volume (automatic) | Continuous |
| Application code | Git repository | Source control | Permanent |
| Frontend build | `frontend/dist/` | Local + VPS `/var/www/neta-frontend/` | Per-deploy |

---

## Windows — Backup Database

```powershell
# Standard backup (saves to D:\NETA.AI\backups\)
.\scripts\backup-db.ps1

# Custom location, keep 60 days
.\scripts\backup-db.ps1 -BackupDir D:\Backups\NETA -Keep 60
```

Backups are named: `neta_backup_YYYYMMDD_HHMMSS.sql.gz`

---

## VPS — Backup Database

```bash
# Manual backup
docker exec neta_postgres sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U $POSTGRES_USER -d $POSTGRES_DB | gzip' \
  > /opt/neta-ai/backups/neta_backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Or run the included backup script
cd /opt/neta-ai
bash scripts/backup.sh local
```

### Automated daily backup (VPS cron)
```bash
sudo crontab -e
# Add this line:
0 2 * * * cd /opt/neta-ai && bash scripts/backup.sh local >> /var/log/neta-backup.log 2>&1
```

---

## Restore Database

### From .sql.gz backup file

```bash
# Stop the API to prevent writes during restore
docker compose stop api celery-worker celery-beat

# Restore (this will REPLACE existing data)
gunzip -c backups/neta_backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i neta_postgres psql -U netaai_app -d netaai_prod

# Restart services
docker compose start api celery-worker celery-beat
```

### Windows (PowerShell)
```powershell
$backupFile = "D:\NETA.AI\backups\neta_backup_20260528_235959.sql.gz"

# Stop API
docker compose stop api celery-worker celery-beat

# Restore
& cmd /c "type `"$backupFile`" | gzip -d | docker exec -i neta_postgres psql -U netaai_app -d netaai_prod"

# Restart
docker compose start api celery-worker celery-beat
```

---

## Docker Volume Safety

**NEVER run these commands — they destroy data:**
```bash
# DANGEROUS — DO NOT USE
docker compose down -v          # removes all volumes including postgres_data
docker volume rm netaai_postgres_data
docker volume prune
```

**Safe stop (preserves all data):**
```bash
docker compose stop             # stops containers, volumes intact
docker compose down             # removes containers only, volumes intact
docker compose down --volumes   # DANGEROUS: removes volumes
```

---

## WSL2 / Docker Desktop Recovery (Windows)

If Docker Desktop fails to start after reboot:

```powershell
# Step 1: Quick check
.\scripts\recovery-check.ps1

# Step 2: Auto-recover
.\scripts\recovery-check.ps1 -AutoRecover

# Step 3: If engine still won't start, force WSL VM restart
# Run PowerShell as Administrator:
wsl --shutdown
Start-Sleep -Seconds 5
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
# Wait 30s then:
.\scripts\stack-start.ps1
```

### Critical files to NEVER delete
| File/Directory | Contents |
|---|---|
| `docker_data.vhdx` | All Docker volumes including Postgres data |
| `ext4.vhdx` | Docker engine filesystem |
| `D:\NETA.AI\` | Application code and configs |
| `D:\NETA.AI\backups\` | Local database backups |

---

## Disaster Recovery — Full Rebuild

If the Docker volume is lost (worst case):

```bash
# 1. Start fresh stack
docker compose up -d

# 2. Wait for postgres to be healthy
docker compose ps

# 3. Restore latest backup
gunzip -c backups/neta_backup_latest.sql.gz | \
  docker exec -i neta_postgres psql -U netaai_app -d netaai_prod

# 4. Verify
curl http://localhost:8000/api/health
```

---

## Verify Backup Integrity

```bash
# Check the backup is a valid gzip SQL file
gunzip -t backups/neta_backup_YYYYMMDD.sql.gz && echo "Backup OK"

# Count records (quick sanity check)
gunzip -c backups/neta_backup_YYYYMMDD.sql.gz | grep -c "^INSERT INTO booths"
```
