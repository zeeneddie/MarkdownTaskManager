#!/bin/bash
# ============================================
# MarQed AI Platform - Stop Script
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_header() { echo -e "\n${BLUE}════════════════════════════════════════${NC}"; echo -e "${BLUE}  $1${NC}"; echo -e "${BLUE}════════════════════════════════════════${NC}\n"; }
log_step() { echo -e "${YELLOW}[$1]${NC} $2"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }

log_header "Stopping MarQed AI Platform"

# 1. Stop API server
log_step "1/2" "Stopping API server..."
if [ -f "$BACKEND_DIR/.pids/uvicorn.pid" ]; then
    PID=$(cat "$BACKEND_DIR/.pids/uvicorn.pid")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID" 2>/dev/null || true
        log_success "API server stopped (PID: $PID)"
    fi
    rm -f "$BACKEND_DIR/.pids/uvicorn.pid"
fi

# Also kill any remaining uvicorn processes
pkill -f "uvicorn app.main:app" 2>/dev/null || true

# 2. Stop Docker containers (optional)
if [[ "$1" == "--all" ]]; then
    log_step "2/2" "Stopping Docker containers..."
    cd "$BACKEND_DIR"
    docker-compose down
    log_success "Docker containers stopped"
else
    log_step "2/2" "Keeping Docker containers running"
    echo "  Use '--all' to also stop database containers"
fi

log_success "Platform stopped"
echo ""
