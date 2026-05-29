#!/usr/bin/env bash
# setup-vps.sh — Complete VPS setup for NETA.AI production deployment
#
# Run as root or with sudo on a fresh Ubuntu 22.04 / 24.04 VPS.
# Usage: sudo bash scripts/setup-vps.sh app.netaai.in
#
# What this script does:
#   1. Installs Docker, nginx, certbot
#   2. Creates required directories
#   3. Configures nginx with your domain
#   4. Obtains SSL certificate
#   5. Starts production Docker stack
#   6. Copies frontend build to nginx web root

set -euo pipefail

DOMAIN="${1:-}"

if [[ -z "$DOMAIN" ]]; then
    echo "Usage: sudo bash scripts/setup-vps.sh your-domain.com"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log()  { echo -e "\n\033[1;32m[$(date +%H:%M:%S)] $*\033[0m"; }
warn() { echo -e "\n\033[1;33m[WARN] $*\033[0m"; }
err()  { echo -e "\n\033[1;31m[ERROR] $*\033[0m" >&2; exit 1; }

# ── 1. Install system packages ────────────────────────────────────────────────
log "Installing Docker, nginx, certbot..."

if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    log "Docker installed"
else
    log "Docker already installed: $(docker --version)"
fi

apt-get update -qq
apt-get install -y --no-install-recommends nginx certbot python3-certbot-nginx curl

# ── 2. Create required directories ───────────────────────────────────────────
log "Creating directories..."
mkdir -p /var/www/neta-frontend
mkdir -p /var/www/certbot
mkdir -p /etc/nginx/sites-available
chown -R www-data:www-data /var/www/neta-frontend

# ── 3. Configure nginx domain ─────────────────────────────────────────────────
log "Configuring nginx for domain: $DOMAIN"
bash "$SCRIPT_DIR/configure-domain.sh" "$DOMAIN"
cp "$PROJECT_ROOT/nginx/nginx.conf" /etc/nginx/nginx.conf

# ── 4. Obtain SSL certificate ─────────────────────────────────────────────────
log "Obtaining SSL certificate for $DOMAIN via certbot --nginx..."

# Start nginx with HTTP-only temporarily (cert paths don't exist yet, comment out ssl block)
# Use certbot's nginx plugin — it handles nginx config automatically
if [[ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
    # Stop nginx temporarily for standalone cert acquisition
    systemctl stop nginx 2>/dev/null || true
    certbot certonly --standalone \
        --non-interactive \
        --agree-tos \
        --email "admin@${DOMAIN}" \
        -d "$DOMAIN"
    log "SSL certificate obtained: /etc/letsencrypt/live/$DOMAIN/"
else
    log "SSL certificate already exists — skipping certbot"
fi

# ── 5. Start/reload nginx ─────────────────────────────────────────────────────
log "Starting nginx..."
nginx -t
systemctl enable nginx
systemctl start nginx || systemctl reload nginx
log "nginx running"

# ── 6. Start production Docker stack ─────────────────────────────────────────
log "Starting production Docker stack..."
cd "$PROJECT_ROOT"
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
log "Containers started"

# ── 7. Wait for API health ────────────────────────────────────────────────────
log "Waiting for API health check..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
        log "API is healthy"
        break
    fi
    echo "  Attempt $i/30..."
    sleep 5
done

# ── 8. Set up certbot auto-renewal ────────────────────────────────────────────
log "Configuring certbot auto-renewal..."
if ! crontab -l 2>/dev/null | grep -q certbot; then
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
    log "Certbot renewal cron added (daily at 3:00 AM)"
fi

# ── 9. Summary ────────────────────────────────────────────────────────────────
echo ""
echo "======================================================================"
echo "  NETA.AI VPS SETUP COMPLETE"
echo "======================================================================"
echo ""
echo "  Domain     : https://$DOMAIN"
echo "  API health : https://$DOMAIN/api/health"
echo "  API docs   : https://$DOMAIN/api/docs"
echo ""
echo "  REMAINING MANUAL STEPS:"
echo ""
echo "  1. Build and deploy frontend (run on your dev machine or CI):"
echo "     cd frontend && npm run build"
echo "     scp -r dist/* ubuntu@<server-ip>:/var/www/neta-frontend/"
echo ""
echo "  2. Set WhatsApp credentials in .env:"
echo "     WHATSAPP_API_TOKEN=<from Meta Developer Console>"
echo "     WHATSAPP_PHONE_ID=<from Meta Developer Console>"
echo "     docker compose restart api celery-worker"
echo ""
echo "  3. Register webhook in Meta Developer Console:"
echo "     URL:   https://$DOMAIN/api/v1/notifications/webhook"
echo "     Token: (value of WHATSAPP_WEBHOOK_VERIFY_TOKEN in .env)"
echo ""
echo "======================================================================"
