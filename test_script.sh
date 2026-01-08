#!/bin/bash
# ====================================================================
# MARKDOWN TASK MANAGER - COMPLETE TEST SCRIPT
# ====================================================================
# Dit script start alles van nul en draait alle tests:
# 1. Docker containers (PostgreSQL + ChromaDB)
# 2. Database migrations
# 3. Backend API
# 4. Backend Python tests (pytest)
# 5. E2E Playwright tests
# 6. Agent TypeScript tests (optional)
#
# Usage:
#   ./test_script.sh              - Full test run (start services + all tests)
#   ./test_script.sh quick        - Quick start (only backend + pytest)
#   ./test_script.sh backend      - Only backend pytest tests
#   ./test_script.sh e2e          - Only E2E Playwright tests
#   ./test_script.sh agents       - Only agent tests
#   ./test_script.sh status       - Show service status
#   ./test_script.sh stop         - Stop all services
#   ./test_script.sh clean        - Clean and restart fresh
# ====================================================================

set -e  # Exit on error (can be overridden per command)

# ====================================================================
# CONFIGURATION
# ====================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directories
PROJECT_ROOT="/home/eddie/Projects/MarkdownTaskManager"
BACKEND_DIR="$PROJECT_ROOT/backend"
TESTS_DIR="$PROJECT_ROOT/tests"
AGENTS_DIR="$PROJECT_ROOT/agents"
VENV_DIR="$BACKEND_DIR/.venv"

# Log directory
LOG_DIR="$BACKEND_DIR/logs"
mkdir -p "$LOG_DIR"

# PID files
PID_DIR="$BACKEND_DIR/.pids"
mkdir -p "$PID_DIR"
BACKEND_PID="$PID_DIR/backend.pid"

# Database config
export POSTGRES_USER="${POSTGRES_USER:-user}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-password}"
export POSTGRES_DB="${POSTGRES_DB:-project_manager}"
export TEST_DB="${TEST_DB:-project_manager_test}"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# ====================================================================
# HELPER FUNCTIONS
# ====================================================================

print_header() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_subheader() {
    echo ""
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed!"
        return 1
    fi
    return 0
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

wait_for_port() {
    local port=$1
    local max_wait=${2:-30}
    local count=0

    while ! nc -z localhost "$port" 2>/dev/null; do
        count=$((count + 1))
        if [ $count -ge $max_wait ]; then
            return 1
        fi
        sleep 1
    done
    return 0
}

# ====================================================================
# PREREQUISITES CHECK
# ====================================================================

check_prerequisites() {
    print_header "CHECKING PREREQUISITES"

    local missing=0

    # Required tools
    for cmd in docker docker-compose python3 pip node npm curl nc; do
        if check_command "$cmd"; then
            print_success "$cmd found"
        else
            print_error "$cmd is missing"
            missing=$((missing + 1))
        fi
    done

    # Python virtual environment
    if [ -d "$VENV_DIR" ]; then
        print_success "Python venv found: $VENV_DIR"
    else
        print_warning "Python venv not found - will create"
    fi

    # Docker running
    if docker info > /dev/null 2>&1; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running!"
        print_info "Start with: sudo systemctl start docker"
        missing=$((missing + 1))
    fi

    if [ $missing -gt 0 ]; then
        print_error "$missing prerequisites missing. Please install them first."
        exit 1
    fi

    print_success "All prerequisites met!"
}

# ====================================================================
# DOCKER SERVICES
# ====================================================================

start_docker_services() {
    print_header "STARTING DOCKER SERVICES"

    cd "$BACKEND_DIR"

    # Check if containers are already running
    if docker-compose ps | grep -q "Up"; then
        print_info "Some containers already running..."
    fi

    print_info "Starting PostgreSQL and ChromaDB containers..."
    docker-compose up -d db chromadb

    # Wait for PostgreSQL to be healthy
    print_info "Waiting for PostgreSQL to be ready..."
    local count=0
    local max_wait=60

    while ! docker-compose exec -T db pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; do
        count=$((count + 1))
        if [ $count -ge $max_wait ]; then
            print_error "PostgreSQL failed to start within $max_wait seconds"
            docker-compose logs db
            exit 1
        fi
        echo -n "."
        sleep 1
    done
    echo ""
    print_success "PostgreSQL is ready (port 5433)"

    # Wait for ChromaDB
    print_info "Waiting for ChromaDB to be ready..."
    if wait_for_port 8001 30; then
        print_success "ChromaDB is ready (port 8001)"
    else
        print_warning "ChromaDB may not be fully ready, but continuing..."
    fi

    # Create test database if it doesn't exist
    print_info "Creating test database if needed..."
    docker-compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1 FROM pg_database WHERE datname='$TEST_DB'" | grep -q 1 || \
        docker-compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE DATABASE $TEST_DB;" 2>/dev/null || true
    print_success "Test database ready"
}

stop_docker_services() {
    print_header "STOPPING DOCKER SERVICES"

    cd "$BACKEND_DIR"
    docker-compose down
    print_success "Docker services stopped"
}

# ====================================================================
# PYTHON ENVIRONMENT
# ====================================================================

setup_python_env() {
    print_header "SETTING UP PYTHON ENVIRONMENT"

    cd "$BACKEND_DIR"

    # Create venv if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    fi

    # Activate venv
    print_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # Install/update dependencies
    print_info "Installing Python dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt

    # Install test dependencies
    pip install --quiet pytest pytest-asyncio pytest-cov httpx

    print_success "Python environment ready"
}

# ====================================================================
# DATABASE MIGRATIONS
# ====================================================================

run_migrations() {
    print_header "RUNNING DATABASE MIGRATIONS"

    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"

    # Set database URL for main db
    export DATABASE_URL="postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5433/$POSTGRES_DB"

    print_info "Running Alembic migrations on main database..."
    alembic upgrade head
    print_success "Main database migrations complete"

    # Run migrations on test database
    print_info "Running Alembic migrations on test database..."
    export DATABASE_URL="postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5433/$TEST_DB"
    alembic upgrade head
    print_success "Test database migrations complete"

    # Reset DATABASE_URL to main
    export DATABASE_URL="postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5433/$POSTGRES_DB"
}

# ====================================================================
# BACKEND API
# ====================================================================

start_backend() {
    print_header "STARTING BACKEND API"

    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"

    # Check if already running
    if is_running "$BACKEND_PID"; then
        print_info "Backend already running (PID: $(cat $BACKEND_PID))"
        return 0
    fi

    # Kill any existing process on port 8000
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port 8000 in use, killing existing process..."
        kill $(lsof -Pi :8000 -sTCP:LISTEN -t) 2>/dev/null || true
        sleep 2
    fi

    # Set environment
    export DATABASE_URL="postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5433/$POSTGRES_DB"
    export CHROMA_HOST="localhost"
    export CHROMA_PORT="8001"
    export SECRET_KEY="test-secret-key-for-testing-only"
    export ENVIRONMENT="test"

    print_info "Starting FastAPI backend..."
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
    local backend_pid=$!
    echo $backend_pid > "$BACKEND_PID"

    # Wait for backend to be ready
    print_info "Waiting for backend to be ready..."
    if wait_for_port 8000 30; then
        print_success "Backend started (PID: $backend_pid)"
        print_info "API: http://localhost:8000"
        print_info "Docs: http://localhost:8000/api/docs"
    else
        print_error "Backend failed to start"
        cat "$LOG_DIR/backend.log" | tail -20
        exit 1
    fi
}

stop_backend() {
    if is_running "$BACKEND_PID"; then
        print_info "Stopping backend (PID: $(cat $BACKEND_PID))..."
        kill $(cat "$BACKEND_PID") 2>/dev/null || true
        rm -f "$BACKEND_PID"
        print_success "Backend stopped"
    fi
}

# ====================================================================
# TESTS
# ====================================================================

run_backend_tests() {
    print_header "RUNNING BACKEND PYTHON TESTS"

    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"

    # Set test database URL
    export DATABASE_URL="postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5433/$TEST_DB"
    export CHROMA_HOST="localhost"
    export CHROMA_PORT="8001"
    export SECRET_KEY="test-secret-key-for-testing-only"
    export ENVIRONMENT="test"

    print_info "Running pytest..."

    # Run tests with coverage
    local test_result=0
    pytest tests/ \
        -v \
        --tb=short \
        --cov=app \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        -x \
        2>&1 | tee "$LOG_DIR/pytest.log" || test_result=$?

    if [ $test_result -eq 0 ]; then
        print_success "All backend tests passed!"
        print_info "Coverage report: $BACKEND_DIR/htmlcov/index.html"
    else
        print_error "Some backend tests failed (exit code: $test_result)"
    fi

    return $test_result
}

run_e2e_tests() {
    print_header "RUNNING E2E PLAYWRIGHT TESTS"

    # Check if backend is running
    if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        print_error "Backend is not running! Start it first."
        return 1
    fi

    cd "$TESTS_DIR"

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_info "Installing E2E test dependencies..."
        npm install
        npx playwright install chromium
    fi

    print_info "Running Playwright E2E tests..."

    local test_result=0
    npm test 2>&1 | tee "$LOG_DIR/e2e.log" || test_result=$?

    if [ $test_result -eq 0 ]; then
        print_success "All E2E tests passed!"
    else
        print_error "Some E2E tests failed (exit code: $test_result)"
    fi

    return $test_result
}

run_agent_tests() {
    print_header "RUNNING AGENT TESTS"

    if [ ! -d "$AGENTS_DIR" ]; then
        print_warning "Agents directory not found, skipping..."
        return 0
    fi

    cd "$AGENTS_DIR"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_info "Installing agent dependencies..."
        npm install
    fi

    # Check if Jest is configured
    if [ ! -f "jest.config.js" ] && [ ! -f "jest.config.ts" ]; then
        print_warning "No Jest config found, skipping agent tests..."
        return 0
    fi

    print_info "Running Jest agent tests..."

    local test_result=0
    npm test 2>&1 | tee "$LOG_DIR/agents.log" || test_result=$?

    if [ $test_result -eq 0 ]; then
        print_success "All agent tests passed!"
    else
        print_error "Some agent tests failed (exit code: $test_result)"
    fi

    return $test_result
}

# ====================================================================
# STATUS
# ====================================================================

show_status() {
    print_header "SERVICE STATUS"

    echo "Service Status:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Docker
    if docker info > /dev/null 2>&1; then
        echo -e "  Docker:      ${GREEN}✅ RUNNING${NC}"
    else
        echo -e "  Docker:      ${RED}❌ STOPPED${NC}"
    fi

    # PostgreSQL container
    cd "$BACKEND_DIR"
    if docker-compose ps 2>/dev/null | grep -q "db.*Up"; then
        echo -e "  PostgreSQL:  ${GREEN}✅ RUNNING${NC} (port 5433)"
    else
        echo -e "  PostgreSQL:  ${RED}❌ STOPPED${NC}"
    fi

    # ChromaDB container
    if docker-compose ps 2>/dev/null | grep -q "chromadb.*Up"; then
        echo -e "  ChromaDB:    ${GREEN}✅ RUNNING${NC} (port 8001)"
    else
        echo -e "  ChromaDB:    ${RED}❌ STOPPED${NC}"
    fi

    # Backend
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "  Backend:     ${GREEN}✅ RUNNING${NC} (port 8000)"
    else
        echo -e "  Backend:     ${RED}❌ STOPPED${NC}"
    fi

    # Ollama
    if pgrep -x "ollama" > /dev/null; then
        echo -e "  Ollama:      ${GREEN}✅ RUNNING${NC}"
    else
        echo -e "  Ollama:      ${YELLOW}⚠️  NOT RUNNING${NC} (optional for LLM tests)"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ====================================================================
# CLEANUP
# ====================================================================

clean_all() {
    print_header "CLEANING UP"

    # Stop backend
    stop_backend

    # Stop docker
    cd "$BACKEND_DIR"
    docker-compose down -v

    # Clean Python cache
    find "$BACKEND_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find "$BACKEND_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
    rm -rf "$BACKEND_DIR/.pytest_cache" "$BACKEND_DIR/htmlcov" 2>/dev/null || true

    # Clean logs
    rm -rf "$LOG_DIR"/* 2>/dev/null || true

    # Clean E2E test results
    rm -rf "$TESTS_DIR/test-results" "$TESTS_DIR/playwright-report" 2>/dev/null || true

    print_success "Cleanup complete"
}

# ====================================================================
# MAIN COMMANDS
# ====================================================================

run_full_tests() {
    print_header "🚀 FULL TEST RUN"

    local start_time=$(date +%s)
    local backend_result=0
    local e2e_result=0
    local agent_result=0

    # Prerequisites
    check_prerequisites

    # Start services
    start_docker_services
    setup_python_env
    run_migrations
    start_backend

    # Run all tests
    print_subheader "Running Backend Tests..."
    run_backend_tests || backend_result=$?

    print_subheader "Running E2E Tests..."
    run_e2e_tests || e2e_result=$?

    # Optional: Agent tests
    # print_subheader "Running Agent Tests..."
    # run_agent_tests || agent_result=$?

    # Summary
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    print_header "TEST SUMMARY"

    echo "Results:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ $backend_result -eq 0 ]; then
        echo -e "  Backend Tests:   ${GREEN}✅ PASSED${NC}"
    else
        echo -e "  Backend Tests:   ${RED}❌ FAILED${NC}"
    fi

    if [ $e2e_result -eq 0 ]; then
        echo -e "  E2E Tests:       ${GREEN}✅ PASSED${NC}"
    else
        echo -e "  E2E Tests:       ${RED}❌ FAILED${NC}"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Duration: ${duration}s"
    echo ""

    # Logs
    print_info "Logs directory: $LOG_DIR"
    print_info "Coverage report: $BACKEND_DIR/htmlcov/index.html"

    # Final status
    if [ $backend_result -eq 0 ] && [ $e2e_result -eq 0 ]; then
        print_success "All tests passed! 🎉"
        return 0
    else
        print_error "Some tests failed!"
        return 1
    fi
}

run_quick_start() {
    print_header "⚡ QUICK START (Backend + Pytest)"

    check_prerequisites
    start_docker_services
    setup_python_env
    run_migrations
    start_backend
    run_backend_tests
}

# ====================================================================
# ENTRY POINT
# ====================================================================

show_help() {
    cat << EOF
MARKDOWN TASK MANAGER - TEST SCRIPT

Usage: ./test_script.sh [command]

Commands:
  (no args)     Full test run: start all services, run all tests
  quick         Quick start: services + backend pytest only
  backend       Run only backend pytest tests (assumes services running)
  e2e           Run only E2E Playwright tests (assumes services running)
  agents        Run only agent TypeScript tests
  start         Start all services without running tests
  stop          Stop all services
  status        Show service status
  clean         Stop services and clean all caches/logs
  help          Show this help message

Examples:
  ./test_script.sh                # Full test run from scratch
  ./test_script.sh quick          # Quick backend tests only
  ./test_script.sh start          # Just start services
  ./test_script.sh backend        # Run pytest (services must be running)
  ./test_script.sh e2e            # Run Playwright (services must be running)
  ./test_script.sh status         # Check what's running
  ./test_script.sh stop           # Stop everything
  ./test_script.sh clean          # Full cleanup and reset

Ports:
  PostgreSQL:   5433 (Docker container)
  ChromaDB:     8001 (Docker container)
  Backend API:  8000 (FastAPI)

Logs:
  Backend:      $LOG_DIR/backend.log
  Pytest:       $LOG_DIR/pytest.log
  E2E:          $LOG_DIR/e2e.log

EOF
}

main() {
    local command="${1:-}"

    case "$command" in
        "")
            run_full_tests
            ;;
        quick)
            run_quick_start
            ;;
        backend)
            run_backend_tests
            ;;
        e2e)
            run_e2e_tests
            ;;
        agents)
            run_agent_tests
            ;;
        start)
            check_prerequisites
            start_docker_services
            setup_python_env
            run_migrations
            start_backend
            show_status
            ;;
        stop)
            stop_backend
            stop_docker_services
            ;;
        status)
            show_status
            ;;
        clean)
            clean_all
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run
main "$@"
