#!/usr/bin/env bash
# configure-domain.sh — Apply production domain to nginx.conf and .env
# Usage:  bash scripts/configure-domain.sh app.netaai.in
# Run on the VPS after cloning the repo and before starting containers.

set -euo pipefail

DOMAIN="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ── Validation ────────────────────────────────────────────────────────────────
if [[ -z "$DOMAIN" ]]; then
    echo "ERROR: domain argument required."
    echo "Usage: bash scripts/configure-domain.sh app.netaai.in"
    exit 1
fi

# Basic domain sanity check (no http://, no trailing slash)
if [[ "$DOMAIN" == http* || "$DOMAIN" == *"/" ]]; then
    echo "ERROR: pass bare domain only, e.g.  app.netaai.in"
    exit 1
fi

NGINX_CONF="$PROJECT_ROOT/nginx/nginx.conf"
ENV_FILE="$PROJECT_ROOT/.env"

echo ""
echo "===================================================================="
echo "  NETA.AI — Domain Configuration"
echo "  Domain : $DOMAIN"
echo "  nginx  : $NGINX_CONF"
echo "  .env   : $ENV_FILE"
echo "===================================================================="

# ── 1. Patch nginx.conf ───────────────────────────────────────────────────────
if [[ ! -f "$NGINX_CONF" ]]; then
    echo "ERROR: $NGINX_CONF not found"
    exit 1
fi

PLACEHOLDER_COUNT=$(grep -c "REPLACE_WITH_YOUR_DOMAIN" "$NGINX_CONF" || true)
if [[ "$PLACEHOLDER_COUNT" -eq 0 ]]; then
    echo "[SKIP] nginx.conf: domain already configured (no placeholders found)"
else
    # Backup original
    cp "$NGINX_CONF" "${NGINX_CONF}.bak"
    sed -i "s/REPLACE_WITH_YOUR_DOMAIN/${DOMAIN}/g" "$NGINX_CONF"
    echo "[OK]   nginx.conf: replaced $PLACEHOLDER_COUNT placeholder(s) with '$DOMAIN'"
    echo "       Backup saved: ${NGINX_CONF}.bak"
fi

# ── 2. Patch ALLOWED_ORIGINS in .env ─────────────────────────────────────────
if [[ ! -f "$ENV_FILE" ]]; then
    echo "[WARN] .env not found — skipping ALLOWED_ORIGINS update"
else
    # Replace the ALLOWED_ORIGINS line with production-only domain
    if grep -q "^ALLOWED_ORIGINS=" "$ENV_FILE"; then
        sed -i "s|^ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=[\"https://${DOMAIN}\"]|" "$ENV_FILE"
        echo "[OK]   .env: ALLOWED_ORIGINS set to [\"https://${DOMAIN}\"]"
    else
        echo "ALLOWED_ORIGINS=[\"https://${DOMAIN}\"]" >> "$ENV_FILE"
        echo "[OK]   .env: ALLOWED_ORIGINS appended"
    fi
fi

# ── 3. Validate nginx config syntax ──────────────────────────────────────────
if command -v nginx &>/dev/null; then
    if nginx -t -c "$NGINX_CONF" 2>&1; then
        echo "[OK]   nginx -t: configuration syntax is valid"
    else
        echo "[WARN] nginx -t: syntax error — check output above"
    fi
else
    echo "[SKIP] nginx not installed locally — validate on server with: nginx -t"
fi

# ── 4. Next steps ─────────────────────────────────────────────────────────────
echo ""
echo "===================================================================="
echo "  NEXT STEPS"
echo "===================================================================="
echo ""
echo "  1. Obtain SSL certificate:"
echo "     sudo certbot certonly --standalone -d $DOMAIN"
echo ""
echo "  2. Copy nginx.conf to system nginx:"
echo "     sudo cp nginx/nginx.conf /etc/nginx/nginx.conf"
echo "     sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "  3. Build and deploy frontend:"
echo "     cd frontend"
echo "     VITE_API_URL=https://$DOMAIN npm run build"
echo "     sudo cp -r dist/* /var/www/neta-frontend/"
echo ""
echo "  4. Start production stack:"
echo "     docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
echo ""
echo "  5. Register WhatsApp webhook in Meta Developer Console:"
echo "     URL: https://$DOMAIN/api/v1/notifications/webhook"
echo "     Token: \$WHATSAPP_WEBHOOK_VERIFY_TOKEN (from .env)"
echo ""
echo "===================================================================="
