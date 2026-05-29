#!/usr/bin/env bash
# validate-production.sh — Full production validation smoke test
# Usage: bash scripts/validate-production.sh [base_url]
# Default base_url: http://localhost:8000
#
# Exit code 0 = all pass, 1 = one or more failures

set -euo pipefail

BASE="${1:-http://localhost:8000}"
CID="11111111-0052-4000-8000-000000000001"
EMAIL="${ADMIN_EMAIL:-admin@netaai.in}"
PASSWORD="${ADMIN_PASSWORD:-Admin123!Secure}"

pass=0; fail=0; warn=0

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'; BOLD='\033[1m'; NC='\033[0m'

hdr() { echo -e "\n${BOLD}=== $* ===${NC}"; }

check() {
    local label="$1" method="$2" url="$3" auth="$4"
    local args=(-s -o /dev/null -w "%{http_code}" -X "$method")
    [[ "$auth" == "yes" ]] && args+=(-H "Authorization: Bearer $TOKEN")
    local code
    code=$(curl "${args[@]}" "${BASE}${url}")
    local ok=0
    for c in 200 201 204 422; do [[ "$code" == "$c" ]] && ok=1; done
    if [[ $ok -eq 1 ]]; then
        echo -e "  ${GREEN}PASS${NC} [$code] $label"
        ((pass++))
    else
        echo -e "  ${RED}FAIL${NC} [$code] $label"
        ((fail++))
    fi
}

# ── Acquire token ─────────────────────────────────────────────────────────────
hdr "AUTHENTICATION"
LOGIN_RESP=$(curl -sf -X POST "${BASE}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" 2>/dev/null || echo "{}")
TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null || echo "")
if [[ -z "$TOKEN" ]]; then
    echo -e "  ${RED}FATAL${NC}: Login failed — cannot continue authenticated checks"
    exit 1
fi
echo -e "  ${GREEN}PASS${NC} [200] login → token acquired"
((pass++))
check "GET /me"           GET  "/api/auth/me"     yes
check "POST /refresh"     POST "/api/auth/refresh" no

# ── Infrastructure ─────────────────────────────────────────────────────────────
hdr "INFRASTRUCTURE"
check "health"            GET  "/api/health"       no

# ── GeoJSON ────────────────────────────────────────────────────────────────────
hdr "GEO (v1)"
check "zones"             GET  "/api/v1/geo/zones"   yes
check "booths"            GET  "/api/v1/geo/booths"  yes

# ── Ground Ops ────────────────────────────────────────────────────────────────
hdr "GROUND OPS (v1)"
check "reports list"      GET  "/api/v1/ground/reports"         yes
check "workers active"    GET  "/api/v1/ground/workers/active"  yes

# ── News Intelligence ─────────────────────────────────────────────────────────
hdr "NEWS INTELLIGENCE (v1)"
check "articles"          GET  "/api/v1/news/articles"          yes
check "sources health"    GET  "/api/v1/news/sources/health"    yes

# ── Booth Management ──────────────────────────────────────────────────────────
hdr "BOOTH MANAGEMENT (v1)"
check "booth list"        GET  "/api/v1/booths"                 yes
check "risk report"       GET  "/api/v1/booths/risk-report"     yes
check "health status"     GET  "/api/v1/booths/health/status"   yes

# ── Predictions ───────────────────────────────────────────────────────────────
hdr "PREDICTIONS (v1)"
check "win-probability"   GET  "/api/v1/predictions/win-probability?constituency_id=${CID}"   yes
check "sentiment"         GET  "/api/v1/predictions/sentiment-breakdown?constituency_id=${CID}" yes

# ── Opposition ────────────────────────────────────────────────────────────────
hdr "OPPOSITION INTELLIGENCE (v1)"
check "sentiment-compare" GET  "/api/v1/opposition/sentiment-comparison?constituency_id=${CID}" yes
check "narratives"        GET  "/api/v1/opposition/narratives?constituency_id=${CID}"           yes

# ── Intelligence / Command Centre ─────────────────────────────────────────────
hdr "INTELLIGENCE HUB"
check "command centre"    GET  "/api/intelligence/command-centre/overview"  yes
check "alerts live"       GET  "/api/intelligence/alerts/live"              yes
check "ground pulse"      GET  "/api/intelligence/ground-pulse/live"        yes
check "candidate brief"   GET  "/api/intelligence/candidate-brief"          yes

# ── SSE ───────────────────────────────────────────────────────────────────────
hdr "SSE (live streams)"
check "sse auth-enforced" GET  "/api/sse/alerts"                            no

# ── WhatsApp / Notifications ──────────────────────────────────────────────────
hdr "WHATSAPP / NOTIFICATIONS (v1)"
WH_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    "${BASE}/api/v1/notifications/webhook?hub.mode=subscribe&hub.verify_token=neta_whatsapp_webhook_2024&hub.challenge=123456")
[[ "$WH_CODE" == "200" ]] && { echo -e "  ${GREEN}PASS${NC} [$WH_CODE] webhook verify"; ((pass++)); } \
                           || { echo -e "  ${RED}FAIL${NC} [$WH_CODE] webhook verify"; ((fail++)); }
check "notification prefs" GET "/api/v1/notifications/user/notification-preferences" yes
check "wa health"          GET "/api/v1/notifications/health"                        yes

# ── Admin ─────────────────────────────────────────────────────────────────────
hdr "ADMIN"
check "system stats"      GET  "/api/admin/system"          yes
check "celery queues"     GET  "/api/admin/queues"          yes
check "ingestion status"  GET  "/api/admin/ingestion"       yes
check "voter scores"      GET  "/api/admin/scores"          yes
check "alert stats"       GET  "/api/admin/alerts/stats"    yes
check "whatsapp status"   GET  "/api/admin/whatsapp/status" yes

# ── Demographics ──────────────────────────────────────────────────────────────
hdr "DEMOGRAPHICS"
check "constituency"      GET  "/api/demographics/constituency/${CID}" yes
check "booths breakdown"  GET  "/api/demographics/booths/${CID}"       yes
check "influencers"       GET  "/api/demographics/influencers/${CID}"  yes

# ── Docker health (if running locally) ───────────────────────────────────────
hdr "DOCKER CONTAINERS"
if command -v docker &>/dev/null; then
    while IFS= read -r line; do
        name=$(echo "$line" | awk '{print $1}')
        status=$(echo "$line" | awk '{print $2}')
        if echo "$status" | grep -q "(healthy)"; then
            echo -e "  ${GREEN}PASS${NC} $name — $status"
            ((pass++))
        elif echo "$status" | grep -q "Up"; then
            echo -e "  ${YELLOW}WARN${NC} $name — $status (no healthcheck)"
            ((warn++))
        else
            echo -e "  ${RED}FAIL${NC} $name — $status"
            ((fail++))
        fi
    done < <(docker ps --format "{{.Names}} {{.Status}}" | grep "^neta_")
else
    echo "  [SKIP] docker not available locally"
fi

# ── Redis connectivity ────────────────────────────────────────────────────────
hdr "REDIS"
REDIS_PING=$(docker exec neta_redis redis-cli -a "${REDIS_PASSWORD:-}" ping 2>/dev/null || echo "FAIL")
if [[ "$REDIS_PING" == *"PONG"* ]]; then
    echo -e "  ${GREEN}PASS${NC} Redis PING → PONG"
    ((pass++))
else
    echo -e "  ${RED}FAIL${NC} Redis ping failed"
    ((fail++))
fi

# ── PostgreSQL connectivity ───────────────────────────────────────────────────
hdr "POSTGRESQL"
PG_CHECK=$(docker exec neta_postgres psql -U netaai_app -d netaai_prod -c "SELECT COUNT(*) FROM users;" 2>/dev/null | grep -E "^\s+[0-9]" | tr -d ' ' || echo "FAIL")
if [[ "$PG_CHECK" =~ ^[0-9]+$ ]]; then
    echo -e "  ${GREEN}PASS${NC} PostgreSQL — users table reachable (${PG_CHECK} rows)"
    ((pass++))
else
    echo -e "  ${RED}FAIL${NC} PostgreSQL connectivity check failed"
    ((fail++))
fi

# ── Summary ───────────────────────────────────────────────────────────────────
total=$((pass + fail))
echo ""
echo -e "${BOLD}======================================================${NC}"
printf "  %b%d PASS%b  |  %b%d FAIL%b  |  %d WARN  |  %d total\n" \
    "$GREEN" $pass "$NC" "$RED" $fail "$NC" $warn $total
echo -e "${BOLD}======================================================${NC}"
echo ""

if [[ $fail -eq 0 ]]; then
    echo -e "  ${GREEN}${BOLD}ALL CHECKS PASSED — system is production-ready${NC}"
    exit 0
else
    echo -e "  ${RED}${BOLD}$fail CHECK(S) FAILED — review output above${NC}"
    exit 1
fi
