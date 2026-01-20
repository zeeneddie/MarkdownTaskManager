#!/bin/bash

# ============================================================================
# MARQED.AI PLATFORM - UNIFIED SERVICE MANAGER
# ============================================================================
# Central script for starting all MarQed services with unique ports.
#
# Port Assignments (Reserved):
#   8000 - ChromaDB (external, already running)
#   8001 - MarQed Backend API (FastAPI)
#   8002 - MarQed Portal Frontend (Next.js dev)
#   8003 - Agents Service (TypeScript executor)
#   6379 - Redis (Celery broker)
#   5432 - PostgreSQL (database)
#   11434 - Ollama (local LLMs)
#
# Usage:
#   ./marqed-services.sh start    # Start all services
#   ./marqed-services.sh stop     # Stop all services
#   ./marqed-services.sh restart  # Restart all services
#   ./marqed-services.sh status   # Show service status
#   ./marqed-services.sh logs     # Tail all logs
# ============================================================================

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

# Directories
PROJECT_ROOT="/home/eddie/Projects/MarkdownTaskManager"
BACKEND_DIR="$PROJECT_ROOT/backend"
AGENTS_DIR="$PROJECT_ROOT/agents"
PORTAL_DIR="$PROJECT_ROOT/marqed-portal/frontend"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

# Virtual environment
VENV_DIR="$BACKEND_DIR/.venv"

# Log directory
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# PID directory
PID_DIR="$PROJECT_ROOT/.pids"
mkdir -p "$PID_DIR"

# =============================================================================
# PORT ASSIGNMENTS (UNIQUE PER SERVICE)
# =============================================================================
# These ports are reserved for MarQed services. Do not change without updating
# all dependent configurations.
#
# NOTE: ChromaDB Docker uses 8000 (internal) mapped to 8001 (external)

PORT_CHROMADB=8001      # ChromaDB Docker container (mapped from 8000)
PORT_BACKEND=8003       # FastAPI backend
PORT_PORTAL=8004        # Next.js frontend (MarQed Portal)
PORT_AGENTS=8005        # TypeScript agent executor
PORT_REDIS=6379         # Redis (standard)
PORT_POSTGRES=5432      # PostgreSQL (standard)
PORT_OLLAMA=11434       # Ollama (standard)

# =============================================================================
# LOG FILES
# =============================================================================

LOG_BACKEND="$LOG_DIR/marqed-backend.log"
LOG_CELERY="$LOG_DIR/marqed-celery.log"
LOG_PORTAL="$LOG_DIR/marqed-portal.log"
LOG_AGENTS="$LOG_DIR/marqed-agents.log"
LOG_REDIS="$LOG_DIR/marqed-redis.log"

# =============================================================================
# PID FILES
# =============================================================================

PID_BACKEND="$PID_DIR/backend.pid"
PID_CELERY="$PID_DIR/celery.pid"
PID_PORTAL="$PID_DIR/portal.pid"
PID_AGENTS="$PID_DIR/agents.pid"
PID_REDIS="$PID_DIR/redis.pid"

# =============================================================================
# COLORS
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}============================================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}============================================================================${NC}"
    echo ""
}

print_section() {
    echo -e "${BLUE}[$1]${NC} $2"
}

print_success() {
    echo -e "  ${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "  ${RED}✗${NC} $1"
}

print_warning() {
    echo -e "  ${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
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

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port in use
    fi
    return 1  # Port free
}

kill_on_port() {
    local port=$1
    if check_port $port; then
        print_warning "Killing process on port $port..."
        fuser -k $port/tcp 2>/dev/null || true
        sleep 1
    fi
}

# =============================================================================
# SERVICE FUNCTIONS
# =============================================================================

check_prerequisites() {
    print_section "PREREQ" "Checking prerequisites..."

    local all_ok=true

    # PostgreSQL
    if pg_isready > /dev/null 2>&1; then
        print_success "PostgreSQL running on port $PORT_POSTGRES"
    else
        print_error "PostgreSQL not running"
        print_info "Start with: sudo systemctl start postgresql"
        all_ok=false
    fi

    # Python venv
    if [ -d "$VENV_DIR" ]; then
        print_success "Python venv exists"
    else
        print_error "Python venv not found at $VENV_DIR"
        print_info "Create with: python -m venv $VENV_DIR"
        all_ok=false
    fi

    # Node.js
    if command -v node &> /dev/null; then
        print_success "Node.js installed ($(node -v))"
    else
        print_warning "Node.js not installed (optional for portal)"
    fi

    # ChromaDB (Docker container)
    if curl -s http://localhost:$PORT_CHROMADB/api/v1/heartbeat > /dev/null 2>&1; then
        print_success "ChromaDB running on port $PORT_CHROMADB (Docker)"
    else
        print_warning "ChromaDB not responding on port $PORT_CHROMADB"
    fi

    if [ "$all_ok" = false ]; then
        print_error "Prerequisites not met. Fix issues above before starting."
        exit 1
    fi
}

start_redis() {
    print_section "REDIS" "Starting Redis on port $PORT_REDIS..."

    if is_running "$PID_REDIS"; then
        print_success "Redis already running (PID: $(cat $PID_REDIS))"
        return 0
    fi

    kill_on_port $PORT_REDIS

    nohup redis-server --port $PORT_REDIS --daemonize no > "$LOG_REDIS" 2>&1 &
    echo $! > "$PID_REDIS"
    sleep 2

    if redis-cli -p $PORT_REDIS ping > /dev/null 2>&1; then
        print_success "Redis started (PID: $(cat $PID_REDIS))"
    else
        print_error "Redis failed to start"
        return 1
    fi
}

start_backend() {
    print_section "BACKEND" "Starting FastAPI on port $PORT_BACKEND..."

    if is_running "$PID_BACKEND"; then
        print_success "Backend already running (PID: $(cat $PID_BACKEND))"
        return 0
    fi

    kill_on_port $PORT_BACKEND

    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"

    nohup uvicorn app.main:app \
        --host 0.0.0.0 \
        --port $PORT_BACKEND \
        --reload \
        > "$LOG_BACKEND" 2>&1 &
    echo $! > "$PID_BACKEND"

    # Wait longer for uvicorn with --reload to fully start
    sleep 10

    # Check if responding (try multiple times)
    local retries=3
    while [ $retries -gt 0 ]; do
        if curl -s http://localhost:$PORT_BACKEND/ > /dev/null 2>&1; then
            print_success "Backend started on port $PORT_BACKEND"
            print_info "API Docs: http://localhost:$PORT_BACKEND/docs"
            return 0
        fi
        retries=$((retries - 1))
        sleep 2
    done

    print_error "Backend failed to start"
    print_info "Check log: $LOG_BACKEND"
    return 1
}

start_celery() {
    print_section "CELERY" "Starting Celery workers..."

    if is_running "$PID_CELERY"; then
        print_success "Celery already running (PID: $(cat $PID_CELERY))"
        return 0
    fi

    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"

    nohup celery -A app.celery_app worker \
        --loglevel=info \
        --concurrency=4 \
        --queues=workflows,projects,celery \
        --max-tasks-per-child=100 \
        > "$LOG_CELERY" 2>&1 &
    echo $! > "$PID_CELERY"

    sleep 3

    if is_running "$PID_CELERY"; then
        print_success "Celery started (PID: $(cat $PID_CELERY))"
    else
        print_error "Celery failed to start"
        return 1
    fi
}

start_portal() {
    print_section "PORTAL" "Starting MarQed Portal on port $PORT_PORTAL..."

    if is_running "$PID_PORTAL"; then
        print_success "Portal already running (PID: $(cat $PID_PORTAL))"
        return 0
    fi

    if [ ! -d "$PORTAL_DIR" ]; then
        print_warning "Portal directory not found, skipping"
        return 0
    fi

    kill_on_port $PORT_PORTAL

    cd "$PORTAL_DIR"

    if [ ! -d "node_modules" ]; then
        print_info "Installing portal dependencies..."
        npm install
    fi

    # Vite uses --port flag (not -p like Next.js)
    nohup npm run dev -- --port $PORT_PORTAL > "$LOG_PORTAL" 2>&1 &
    echo $! > "$PID_PORTAL"

    # Vite starts fast but give it time to bind the port
    sleep 8

    # Check with retries
    local retries=5
    while [ $retries -gt 0 ]; do
        if check_port $PORT_PORTAL; then
            print_success "Portal started on port $PORT_PORTAL"
            print_info "Portal: http://localhost:$PORT_PORTAL"
            return 0
        fi
        retries=$((retries - 1))
        sleep 2
    done

    # Check if process is at least running
    if is_running "$PID_PORTAL"; then
        print_warning "Portal process running but port not yet listening"
        print_info "Check log: $LOG_PORTAL"
    else
        print_error "Portal failed to start"
        print_info "Check log: $LOG_PORTAL"
    fi
}

check_ollama() {
    print_section "OLLAMA" "Checking Ollama on port $PORT_OLLAMA..."

    if pgrep -x "ollama" > /dev/null; then
        print_success "Ollama running"
        local models=$(ollama list 2>/dev/null | wc -l)
        print_info "Models installed: $((models - 1))"
    else
        print_warning "Ollama not running"
        print_info "Start with: ollama serve"
    fi
}

# =============================================================================
# STOP FUNCTIONS
# =============================================================================

stop_service() {
    local name=$1
    local pid_file=$2

    if is_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        print_info "Stopping $name (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        rm -f "$pid_file"
        print_success "$name stopped"
    else
        print_info "$name not running"
    fi
}

stop_all() {
    print_header "STOPPING ALL MARQED SERVICES"

    stop_service "Portal" "$PID_PORTAL"
    stop_service "Celery" "$PID_CELERY"
    stop_service "Backend" "$PID_BACKEND"
    stop_service "Redis" "$PID_REDIS"

    print_success "All services stopped"
}

# =============================================================================
# STATUS FUNCTION
# =============================================================================

show_status() {
    print_header "MARQED SERVICE STATUS"

    echo "Port Assignments:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # ChromaDB (Docker container - use curl to check)
    if curl -s http://localhost:$PORT_CHROMADB/api/v1/heartbeat > /dev/null 2>&1; then
        echo -e "  ChromaDB ($PORT_CHROMADB):    ${GREEN}● RUNNING${NC} (Docker)"
    else
        echo -e "  ChromaDB ($PORT_CHROMADB):    ${YELLOW}○ NOT RUNNING${NC}"
    fi

    # Backend
    if is_running "$PID_BACKEND"; then
        echo -e "  Backend ($PORT_BACKEND):     ${GREEN}● RUNNING${NC} (PID: $(cat $PID_BACKEND))"
    else
        echo -e "  Backend ($PORT_BACKEND):     ${RED}○ STOPPED${NC}"
    fi

    # Portal
    if is_running "$PID_PORTAL"; then
        echo -e "  Portal ($PORT_PORTAL):      ${GREEN}● RUNNING${NC} (PID: $(cat $PID_PORTAL))"
    else
        echo -e "  Portal ($PORT_PORTAL):      ${YELLOW}○ STOPPED${NC}"
    fi

    # Redis
    if is_running "$PID_REDIS"; then
        echo -e "  Redis ($PORT_REDIS):       ${GREEN}● RUNNING${NC} (PID: $(cat $PID_REDIS))"
    else
        echo -e "  Redis ($PORT_REDIS):       ${RED}○ STOPPED${NC}"
    fi

    # PostgreSQL
    if pg_isready > /dev/null 2>&1; then
        echo -e "  PostgreSQL ($PORT_POSTGRES):   ${GREEN}● RUNNING${NC}"
    else
        echo -e "  PostgreSQL ($PORT_POSTGRES):   ${RED}○ STOPPED${NC}"
    fi

    # Ollama
    if pgrep -x "ollama" > /dev/null; then
        echo -e "  Ollama ($PORT_OLLAMA):    ${GREEN}● RUNNING${NC}"
    else
        echo -e "  Ollama ($PORT_OLLAMA):    ${YELLOW}○ NOT RUNNING${NC}"
    fi

    # Celery
    if is_running "$PID_CELERY"; then
        echo -e "  Celery Workers:       ${GREEN}● RUNNING${NC} (PID: $(cat $PID_CELERY))"
    else
        echo -e "  Celery Workers:       ${RED}○ STOPPED${NC}"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Quick URLs:"
    echo "  Backend API:  http://localhost:$PORT_BACKEND"
    echo "  API Docs:     http://localhost:$PORT_BACKEND/docs"
    echo "  Portal:       http://localhost:$PORT_PORTAL"
    echo ""
    echo "Log files: $LOG_DIR/"
}

# =============================================================================
# LOGS FUNCTION
# =============================================================================

tail_logs() {
    print_header "TAILING ALL LOGS (Ctrl+C to exit)"

    tail -f "$LOG_DIR"/*.log 2>/dev/null || print_error "No log files found"
}

# =============================================================================
# START ALL
# =============================================================================

start_all() {
    print_header "STARTING MARQED PLATFORM SERVICES"

    echo "Port Configuration:"
    echo "  ChromaDB:   $PORT_CHROMADB (external)"
    echo "  Backend:    $PORT_BACKEND"
    echo "  Portal:     $PORT_PORTAL"
    echo "  Redis:      $PORT_REDIS"
    echo "  PostgreSQL: $PORT_POSTGRES"
    echo "  Ollama:     $PORT_OLLAMA"
    echo ""

    check_prerequisites
    start_redis
    start_backend
    start_celery
    start_portal
    check_ollama

    echo ""
    print_success "All MarQed services started!"
    echo ""
    show_status
}

# =============================================================================
# MAIN
# =============================================================================

case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 2
        start_all
        ;;
    status)
        show_status
        ;;
    logs)
        tail_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all MarQed services"
        echo "  stop    - Stop all MarQed services"
        echo "  restart - Restart all MarQed services"
        echo "  status  - Show service status"
        echo "  logs    - Tail all log files"
        exit 1
        ;;
esac
