#!/bin/bash

# ====================================================================
# MARKDOWN TASK MANAGER - STOP ALL SERVICES
# ====================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directories
BACKEND_DIR="/home/eddie/Projects/MarkdownTaskManager/backend"
PID_DIR="$BACKEND_DIR/.pids"

BACKEND_PID="$PID_DIR/backend.pid"
CELERY_PID="$PID_DIR/celery.pid"
REDIS_PID="$PID_DIR/redis.pid"

print_header() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

stop_service() {
    local service_name=$1
    local pid_file=$2

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_info "Stopping $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            sleep 1

            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null || true
            fi

            rm -f "$pid_file"
            print_success "$service_name stopped"
        else
            print_info "$service_name was not running"
            rm -f "$pid_file"
        fi
    else
        print_info "$service_name was not running (no PID file)"
    fi
}

main() {
    clear
    print_header "🛑 MARKDOWN TASK MANAGER - STOPPING ALL SERVICES"

    print_info "Stopping services..."
    echo ""

    stop_service "Celery Workers" "$CELERY_PID"
    stop_service "FastAPI Backend" "$BACKEND_PID"
    stop_service "Redis" "$REDIS_PID"

    echo ""
    print_success "All services stopped successfully! 🎯"
    echo ""
    print_info "PostgreSQL not stopped (runs system-wide)"
    print_info "Ollama not stopped (runs system-wide)"
    echo ""
}

main
