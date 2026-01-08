#!/bin/bash
# ============================================
# MarQed AI Platform - Health Check
# ============================================
# Comprehensive health check for all services
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../_common.sh"

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
CHROMADB_URL="${CHROMADB_URL:-http://localhost:8001}"

log_header "Health Check"

FAILURES=0

# Check API
log_step "1/4" "Checking API..."
if curl -sf "${API_URL}/api/health" > /dev/null 2>&1; then
    log_success "API: healthy"

    # Get API details
    HEALTH=$(curl -sf "${API_URL}/api/health" 2>/dev/null)
    echo "  Response: $(echo "$HEALTH" | head -c 100)"
else
    log_error "API: not responding"
    ((FAILURES++))
fi

# Check Database
log_step "2/4" "Checking PostgreSQL..."
cd "$BACKEND_DIR"
if docker-compose exec -T db pg_isready -U user > /dev/null 2>&1; then
    log_success "PostgreSQL: ready"

    # Get connection count
    CONN_COUNT=$(docker-compose exec -T db psql -U user -d project_manager -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ')
    [ -n "$CONN_COUNT" ] && echo "  Active connections: $CONN_COUNT"
else
    log_error "PostgreSQL: not ready"
    ((FAILURES++))
fi

# Check ChromaDB
log_step "3/4" "Checking ChromaDB..."
if curl -sf "${CHROMADB_URL}/api/v1/heartbeat" > /dev/null 2>&1; then
    log_success "ChromaDB: healthy"
else
    log_warning "ChromaDB: not responding (optional service)"
fi

# Check Docker containers
log_step "4/4" "Checking containers..."
cd "$BACKEND_DIR"
echo ""
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || {
    docker-compose ps
}

# Summary
echo ""
if [ $FAILURES -eq 0 ]; then
    log_success "All critical services healthy"
    exit 0
else
    log_error "$FAILURES service(s) unhealthy"
    exit 1
fi
