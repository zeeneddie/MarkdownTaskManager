#!/bin/bash

# ====================================================================
# MARKDOWN TASK MANAGER - STATUS CHECK
# ====================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directories
BACKEND_DIR="/home/eddie/Projects/MarkdownTaskManager/backend"
PID_DIR="$BACKEND_DIR/.pids"
LOG_DIR="$BACKEND_DIR/logs"

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

is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

check_service() {
    local service_name=$1
    local pid_file=$2
    local extra_check=$3

    printf "  %-20s " "$service_name:"

    if is_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        local mem=$(ps -p "$pid" -o rss= 2>/dev/null | awk '{printf "%.0f MB", $1/1024}')
        echo -e "${GREEN}✅ RUNNING${NC} (PID: $pid, MEM: $mem)"
    else
        if [ -n "$extra_check" ] && eval "$extra_check" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  RUNNING (no PID file)${NC}"
        else
            echo -e "${RED}❌ STOPPED${NC}"
        fi
    fi
}

show_api_status() {
    echo ""
    echo "API Endpoints Status:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Health check
    local health=$(curl -s http://localhost:8000/api/health 2>/dev/null || echo "")
    if echo "$health" | grep -q "healthy"; then
        echo -e "  Health:              ${GREEN}✅ HEALTHY${NC}"
    else
        echo -e "  Health:              ${RED}❌ UNHEALTHY${NC}"
    fi

    # Work types
    local work_types=$(curl -s http://localhost:8000/api/workflows/work-types 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
    if [ "$work_types" -eq 9 ]; then
        echo -e "  Work Types:          ${GREEN}✅ $work_types/9${NC}"
    else
        echo -e "  Work Types:          ${RED}❌ $work_types/9${NC}"
    fi

    # Agents
    local agents=$(curl -s http://localhost:8000/api/workflows/agents 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
    if [ "$agents" -eq 10 ]; then
        echo -e "  Agents:              ${GREEN}✅ $agents/10${NC}"
    else
        echo -e "  Agents:              ${RED}❌ $agents/10${NC}"
    fi

    # API Docs
    local docs=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs 2>/dev/null)
    if [ "$docs" -eq 200 ]; then
        echo -e "  API Documentation:   ${GREEN}✅ ACCESSIBLE${NC}"
    else
        echo -e "  API Documentation:   ${RED}❌ UNAVAILABLE${NC}"
    fi
}

show_ollama_status() {
    echo ""
    echo "Ollama Status:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if pgrep -x "ollama" > /dev/null; then
        echo -e "  Ollama Service:      ${GREEN}✅ RUNNING${NC}"

        # List models
        local models=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
        if [ "$models" -gt 0 ]; then
            echo -e "  Models Installed:    ${GREEN}✅ $models models${NC}"
            ollama list 2>/dev/null | tail -n +2 | awk '{printf "    • %s (%s)\n", $1, $2}'
        else
            echo -e "  Models Installed:    ${YELLOW}⚠️  0 models${NC}"
        fi
    else
        echo -e "  Ollama Service:      ${RED}❌ NOT RUNNING${NC}"
    fi
}

show_logs_info() {
    echo ""
    echo "Recent Log Activity:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ -d "$LOG_DIR" ]; then
        for log in backend celery redis smoke-test; do
            local log_file="$LOG_DIR/${log}.log"
            if [ -f "$log_file" ]; then
                local lines=$(wc -l < "$log_file" 2>/dev/null || echo "0")
                local size=$(du -h "$log_file" 2>/dev/null | cut -f1 || echo "0")
                local modified=$(stat -c %y "$log_file" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1 || echo "unknown")
                printf "  %-20s %6s (%s lines, updated: %s)\n" "$log:" "$size" "$lines" "$modified"
            fi
        done
    else
        echo "  No log directory found"
    fi
}

show_quick_stats() {
    echo ""
    echo "System Resources:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Total memory used by our services
    local total_mem=0
    for pid_file in "$BACKEND_PID" "$CELERY_PID" "$REDIS_PID"; do
        if is_running "$pid_file"; then
            local pid=$(cat "$pid_file")
            local mem=$(ps -p "$pid" -o rss= 2>/dev/null | awk '{print $1}')
            total_mem=$((total_mem + mem))
        fi
    done
    echo "  Total Memory Used:   $(echo $total_mem | awk '{printf "%.0f MB", $1/1024}')"

    # Disk usage
    local disk=$(df -h "$BACKEND_DIR" | tail -1 | awk '{print $5 " used (" $4 " free)"}')
    echo "  Disk Usage:          $disk"

    # Uptime of backend
    if is_running "$BACKEND_PID"; then
        local pid=$(cat "$BACKEND_PID")
        local uptime=$(ps -p "$pid" -o etime= 2>/dev/null | xargs || echo "unknown")
        echo "  Backend Uptime:      $uptime"
    fi
}

main() {
    clear
    print_header "📊 MARKDOWN TASK MANAGER - SYSTEM STATUS"

    echo "Core Services:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    check_service "PostgreSQL" "" "pg_isready"
    check_service "Redis" "$REDIS_PID" "redis-cli ping"
    check_service "FastAPI Backend" "$BACKEND_PID"
    check_service "Celery Workers" "$CELERY_PID"

    show_api_status
    show_ollama_status
    show_logs_info
    show_quick_stats

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Quick Links:"
    echo "  📚 API Docs:         http://localhost:8000/api/docs"
    echo "  📊 Project Viewer:   http://localhost:8000/"
    echo "  🗓️  Sprint Planning:  http://localhost:8000/sprint-planning.html"
    echo ""
    echo "Commands:"
    echo "  Start:   ./start_all.sh"
    echo "  Stop:    ./stop_all.sh"
    echo "  Restart: ./restart_all.sh"
    echo ""
}

main
