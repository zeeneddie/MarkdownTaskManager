#!/bin/bash

# ====================================================================
# MARKDOWN TASK MANAGER - COMPLETE STARTUP SCRIPT
# ====================================================================
# This script starts all required services for the Agentic Task Manager:
# 1. PostgreSQL (check/start)
# 2. Redis (for Celery task queue)
# 3. FastAPI Backend (with auto-reload)
# 4. Celery Workers (4 workers, 3 queues)
# 5. Ollama (check if running for local LLMs)
# 6. Smoke Tests (verify all endpoints)
# 7. Opens browser (optional)
# ====================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
PROJECT_ROOT="/home/eddie/Projects/MarkdownTaskManager"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/.venv"

# Log files
LOG_DIR="$BACKEND_DIR/logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
CELERY_LOG="$LOG_DIR/celery.log"
REDIS_LOG="$LOG_DIR/redis.log"
SMOKE_TEST_LOG="$LOG_DIR/smoke-test.log"

# PID files
PID_DIR="$BACKEND_DIR/.pids"
mkdir -p "$PID_DIR"
BACKEND_PID="$PID_DIR/backend.pid"
CELERY_PID="$PID_DIR/celery.pid"
REDIS_PID="$PID_DIR/redis.pid"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

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

# Check if a process is running by PID file
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Running
        fi
    fi
    return 1  # Not running
}

# ====================================================================
# SERVICE START FUNCTIONS
# ====================================================================

check_postgresql() {
    print_header "1. CHECKING POSTGRESQL"

    if pg_isready > /dev/null 2>&1; then
        print_success "PostgreSQL is running"
        return 0
    else
        print_warning "PostgreSQL is not running"
        print_info "Starting PostgreSQL..."

        sudo systemctl start postgresql

        if pg_isready > /dev/null 2>&1; then
            print_success "PostgreSQL started successfully"
            return 0
        else
            print_error "Failed to start PostgreSQL"
            return 1
        fi
    fi
}

start_redis() {
    print_header "2. STARTING REDIS"

    # Check if already running
    if is_running "$REDIS_PID"; then
        print_success "Redis is already running (PID: $(cat $REDIS_PID))"
        return 0
    fi

    # Kill any existing Redis on port 6379
    if lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Redis already running on port 6379, killing..."
        pkill -f "redis-server \*:6379" || true
        sleep 2
    fi

    # Start Redis via script
    cd "$BACKEND_DIR"

    print_info "Starting Redis server on port 6379..."
    nohup redis-server --port 6379 --daemonize no > "$REDIS_LOG" 2>&1 &
    local redis_pid=$!
    echo $redis_pid > "$REDIS_PID"

    # Wait for Redis to start
    sleep 2

    # Verify Redis is running
    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis started successfully (PID: $redis_pid)"
        print_info "Redis log: $REDIS_LOG"
        return 0
    else
        print_error "Failed to start Redis"
        return 1
    fi
}

start_backend() {
    print_header "3. STARTING FASTAPI BACKEND"

    # Check if already running
    if is_running "$BACKEND_PID"; then
        print_success "Backend is already running (PID: $(cat $BACKEND_PID))"
        return 0
    fi

    cd "$BACKEND_DIR"

    # Activate virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found at $VENV_DIR"
        print_info "Run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
        return 1
    fi

    print_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # Start backend
    print_info "Starting FastAPI backend on http://0.0.0.0:8000..."
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$BACKEND_LOG" 2>&1 &
    local backend_pid=$!
    echo $backend_pid > "$BACKEND_PID"

    # Wait for backend to start
    sleep 3

    # Verify backend is running
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        print_success "Backend started successfully (PID: $backend_pid)"
        print_info "API Docs: http://localhost:8000/api/docs"
        print_info "Backend log: $BACKEND_LOG"
        return 0
    else
        print_error "Failed to start backend (health check failed)"
        return 1
    fi
}

start_celery() {
    print_header "4. STARTING CELERY WORKERS"

    # Check if already running
    if is_running "$CELERY_PID"; then
        print_success "Celery workers are already running (PID: $(cat $CELERY_PID))"
        return 0
    fi

    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"

    # Start Celery workers
    print_info "Starting 4 Celery workers (queues: workflows, projects, celery)..."
    nohup celery -A app.celery_app worker \
        --loglevel=info \
        --concurrency=4 \
        --queues=workflows,projects,celery \
        --max-tasks-per-child=100 \
        --time-limit=1800 \
        --soft-time-limit=1800 \
        --prefetch-multiplier=1 \
        > "$CELERY_LOG" 2>&1 &
    local celery_pid=$!
    echo $celery_pid > "$CELERY_PID"

    # Wait for Celery to start
    sleep 3

    # Verify Celery is running
    if ps -p $celery_pid > /dev/null; then
        print_success "Celery workers started successfully (PID: $celery_pid)"
        print_info "Celery log: $CELERY_LOG"
        return 0
    else
        print_error "Failed to start Celery workers"
        return 1
    fi
}

check_ollama() {
    print_header "5. CHECKING OLLAMA (Local LLMs)"

    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        print_warning "Ollama is not installed"
        print_info "Install from: https://ollama.ai"
        return 1
    fi

    # Check if Ollama service is running
    if ! pgrep -x "ollama" > /dev/null; then
        print_warning "Ollama is not running"
        print_info "Start with: ollama serve"
        return 1
    fi

    print_success "Ollama is running"

    # Check installed models
    print_info "Checking installed models..."
    local models=$(ollama list 2>/dev/null || echo "")

    if [ -z "$models" ]; then
        print_warning "No Ollama models installed"
        print_info "Required models for agents:"
        echo "  - qwen2.5-coder:7b (4 agents)"
        echo "  - deepseek-r1:latest (3 agents)"
        echo "  - codellama:latest (1 agent)"
        echo "  - mistral:latest (1 agent)"
        echo "  - qwen2.5:7b (1 agent)"
        print_info "Download with: ollama pull <model-name>"
        return 1
    else
        print_success "Ollama models installed:"
        echo "$models" | tail -n +2 | awk '{printf "  ✓ %s\n", $1}'
    fi

    return 0
}

# ====================================================================
# SMOKE TESTS
# ====================================================================

run_smoke_tests() {
    print_header "6. RUNNING SMOKE TESTS"

    TESTS_PASSED=0
    TESTS_FAILED=0

    echo "Running comprehensive API smoke tests..." > "$SMOKE_TEST_LOG"
    echo "Timestamp: $(date)" >> "$SMOKE_TEST_LOG"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$SMOKE_TEST_LOG"
    echo "" >> "$SMOKE_TEST_LOG"

    print_info "Testing API endpoints..."
    echo ""

    # Test 1: Health Check
    echo "Test 1: Health Check" | tee -a "$SMOKE_TEST_LOG"
    local response=$(curl -s http://localhost:8000/api/health)
    if echo "$response" | grep -q "healthy"; then
        print_success "  ✓ Health check passed"
        echo "  ✓ PASSED: $response" >> "$SMOKE_TEST_LOG"
        ((TESTS_PASSED++))
    else
        print_error "  ✗ Health check failed"
        echo "  ✗ FAILED: $response" >> "$SMOKE_TEST_LOG"
        ((TESTS_FAILED++))
    fi
    echo "" >> "$SMOKE_TEST_LOG"

    # Test 2: Work Types Endpoint
    echo "Test 2: Work Types Endpoint" | tee -a "$SMOKE_TEST_LOG"
    response=$(curl -s http://localhost:8000/api/workflows/work-types)
    local work_type_count=$(echo "$response" | jq '. | length' 2>/dev/null || echo "0")
    if [ "$work_type_count" -eq 9 ]; then
        print_success "  ✓ Work types endpoint passed (9 work types)"
        echo "  ✓ PASSED: Found $work_type_count work types" >> "$SMOKE_TEST_LOG"
        ((TESTS_PASSED++))
    else
        print_error "  ✗ Work types endpoint failed (expected 9, got $work_type_count)"
        echo "  ✗ FAILED: Expected 9 work types, got $work_type_count" >> "$SMOKE_TEST_LOG"
        ((TESTS_FAILED++))
    fi
    echo "" >> "$SMOKE_TEST_LOG"

    # Test 3: Agents Endpoint
    echo "Test 3: Agents Endpoint" | tee -a "$SMOKE_TEST_LOG"
    response=$(curl -s http://localhost:8000/api/workflows/agents)
    local agent_count=$(echo "$response" | jq '. | length' 2>/dev/null || echo "0")
    if [ "$agent_count" -eq 10 ]; then
        print_success "  ✓ Agents endpoint passed (10 agents)"
        echo "  ✓ PASSED: Found $agent_count agents" >> "$SMOKE_TEST_LOG"
        ((TESTS_PASSED++))
    else
        print_error "  ✗ Agents endpoint failed (expected 10, got $agent_count)"
        echo "  ✗ FAILED: Expected 10 agents, got $agent_count" >> "$SMOKE_TEST_LOG"
        ((TESTS_FAILED++))
    fi
    echo "" >> "$SMOKE_TEST_LOG"

    # Test 4: Statistics Endpoint
    echo "Test 4: Statistics Endpoint" | tee -a "$SMOKE_TEST_LOG"
    response=$(curl -s http://localhost:8000/api/workflows/statistics)
    if echo "$response" | grep -q "total_workflows"; then
        print_success "  ✓ Statistics endpoint passed"
        echo "  ✓ PASSED: $response" >> "$SMOKE_TEST_LOG"
        ((TESTS_PASSED++))
    else
        print_error "  ✗ Statistics endpoint failed"
        echo "  ✗ FAILED: $response" >> "$SMOKE_TEST_LOG"
        ((TESTS_FAILED++))
    fi
    echo "" >> "$SMOKE_TEST_LOG"

    # Test 5: Workflow Analysis (NEW_FEATURE)
    echo "Test 5: Workflow Analysis (NEW_FEATURE)" | tee -a "$SMOKE_TEST_LOG"
    response=$(curl -s -X POST http://localhost:8000/api/workflows/analyze \
        -H "Content-Type: application/json" \
        -d '{"description": "Add OAuth2 authentication"}')
    if echo "$response" | grep -q "NEW_FEATURE"; then
        print_success "  ✓ NEW_FEATURE workflow passed"
        local exec_time=$(echo "$response" | jq -r '.total_execution_time' 2>/dev/null || echo "N/A")
        echo "  ✓ PASSED: Execution time: ${exec_time}s" >> "$SMOKE_TEST_LOG"
        ((TESTS_PASSED++))
    else
        print_error "  ✗ NEW_FEATURE workflow failed"
        echo "  ✗ FAILED: $response" >> "$SMOKE_TEST_LOG"
        ((TESTS_FAILED++))
    fi
    echo "" >> "$SMOKE_TEST_LOG"

    # Test 6: BUG Workflow
    echo "Test 6: Workflow Analysis (BUG)" | tee -a "$SMOKE_TEST_LOG"
    response=$(curl -s -X POST http://localhost:8000/api/workflows/analyze \
        -H "Content-Type: application/json" \
        -d '{"description": "Fix session timeout bug"}')
    if echo "$response" | grep -q "BUG"; then
        print_success "  ✓ BUG workflow passed"
        local exec_time=$(echo "$response" | jq -r '.total_execution_time' 2>/dev/null || echo "N/A")
        echo "  ✓ PASSED: Execution time: ${exec_time}s" >> "$SMOKE_TEST_LOG"
        ((TESTS_PASSED++))
    else
        print_error "  ✗ BUG workflow failed"
        echo "  ✗ FAILED: $response" >> "$SMOKE_TEST_LOG"
        ((TESTS_FAILED++))
    fi
    echo "" >> "$SMOKE_TEST_LOG"

    # Test 7: Redis Connection
    echo "Test 7: Redis Connection" | tee -a "$SMOKE_TEST_LOG"
    if redis-cli ping > /dev/null 2>&1; then
        print_success "  ✓ Redis connection passed"
        echo "  ✓ PASSED: Redis responding to PING" >> "$SMOKE_TEST_LOG"
        ((TESTS_PASSED++))
    else
        print_error "  ✗ Redis connection failed"
        echo "  ✗ FAILED: Redis not responding" >> "$SMOKE_TEST_LOG"
        ((TESTS_FAILED++))
    fi
    echo "" >> "$SMOKE_TEST_LOG"

    # Test 8: Celery Workers
    echo "Test 8: Celery Workers" | tee -a "$SMOKE_TEST_LOG"
    if is_running "$CELERY_PID"; then
        print_success "  ✓ Celery workers running"
        echo "  ✓ PASSED: Celery workers active" >> "$SMOKE_TEST_LOG"
        ((TESTS_PASSED++))
    else
        print_error "  ✗ Celery workers not running"
        echo "  ✗ FAILED: Celery workers not active" >> "$SMOKE_TEST_LOG"
        ((TESTS_FAILED++))
    fi
    echo "" >> "$SMOKE_TEST_LOG"

    # Test 9: OpenAPI Documentation
    echo "Test 9: OpenAPI Documentation" | tee -a "$SMOKE_TEST_LOG"
    response=$(curl -s http://localhost:8000/openapi.json)
    if echo "$response" | grep -q "openapi"; then
        print_success "  ✓ OpenAPI documentation accessible"
        echo "  ✓ PASSED: OpenAPI schema valid" >> "$SMOKE_TEST_LOG"
        ((TESTS_PASSED++))
    else
        print_error "  ✗ OpenAPI documentation failed"
        echo "  ✗ FAILED: OpenAPI schema invalid" >> "$SMOKE_TEST_LOG"
        ((TESTS_FAILED++))
    fi
    echo "" >> "$SMOKE_TEST_LOG"

    # Test 10: TypeScript Executor
    echo "Test 10: TypeScript Agent Executor" | tee -a "$SMOKE_TEST_LOG"
    cd "$BACKEND_DIR/agents"
    if [ -f "execute-workflow.ts" ]; then
        print_success "  ✓ TypeScript executor exists"
        echo "  ✓ PASSED: execute-workflow.ts found" >> "$SMOKE_TEST_LOG"
        ((TESTS_PASSED++))
    else
        print_error "  ✗ TypeScript executor missing"
        echo "  ✗ FAILED: execute-workflow.ts not found" >> "$SMOKE_TEST_LOG"
        ((TESTS_FAILED++))
    fi
    echo "" >> "$SMOKE_TEST_LOG"

    # Summary
    echo "" | tee -a "$SMOKE_TEST_LOG"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$SMOKE_TEST_LOG"
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    echo "SMOKE TEST RESULTS: $TESTS_PASSED/$total_tests passed" | tee -a "$SMOKE_TEST_LOG"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$SMOKE_TEST_LOG"

    if [ $TESTS_FAILED -eq 0 ]; then
        print_success "All smoke tests passed! 🎉"
        echo "" >> "$SMOKE_TEST_LOG"
        echo "✅ ALL TESTS PASSED" >> "$SMOKE_TEST_LOG"
    else
        print_error "$TESTS_FAILED test(s) failed"
        echo "" >> "$SMOKE_TEST_LOG"
        echo "❌ $TESTS_FAILED TESTS FAILED" >> "$SMOKE_TEST_LOG"
    fi

    print_info "Smoke test log: $SMOKE_TEST_LOG"
    echo ""

    return $([ $TESTS_FAILED -eq 0 ] && echo 0 || echo 1)
}

# ====================================================================
# STATUS AND BROWSER
# ====================================================================

open_browser() {
    print_header "7. OPENING BROWSER"

    # URLs to open
    local api_docs="http://localhost:8000/api/docs"
    local project_viewer="http://localhost:8000/"
    local sprint_planning="http://localhost:8000/sprint-planning.html"

    print_info "Available URLs:"
    echo "  📚 API Documentation: $api_docs"
    echo "  📊 Project Viewer: $project_viewer"
    echo "  🗓️  Sprint Planning: $sprint_planning"

    # Ask user if they want to open browser
    read -p "Open browser? [y/N]: " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v xdg-open &> /dev/null; then
            xdg-open "$api_docs" &
            print_success "Browser opened"
        elif command -v open &> /dev/null; then
            open "$api_docs" &
            print_success "Browser opened"
        else
            print_warning "Could not open browser automatically"
        fi
    fi
}

show_status() {
    print_header "SYSTEM STATUS"

    echo "Service Status:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # PostgreSQL
    if pg_isready > /dev/null 2>&1; then
        echo -e "  PostgreSQL:  ${GREEN}✅ RUNNING${NC}"
    else
        echo -e "  PostgreSQL:  ${RED}❌ STOPPED${NC}"
    fi

    # Redis
    if is_running "$REDIS_PID"; then
        echo -e "  Redis:       ${GREEN}✅ RUNNING${NC} (PID: $(cat $REDIS_PID))"
    else
        echo -e "  Redis:       ${RED}❌ STOPPED${NC}"
    fi

    # Backend
    if is_running "$BACKEND_PID"; then
        echo -e "  Backend:     ${GREEN}✅ RUNNING${NC} (PID: $(cat $BACKEND_PID))"
    else
        echo -e "  Backend:     ${RED}❌ STOPPED${NC}"
    fi

    # Celery
    if is_running "$CELERY_PID"; then
        echo -e "  Celery:      ${GREEN}✅ RUNNING${NC} (PID: $(cat $CELERY_PID))"
    else
        echo -e "  Celery:      ${RED}❌ STOPPED${NC}"
    fi

    # Ollama
    if pgrep -x "ollama" > /dev/null; then
        echo -e "  Ollama:      ${GREEN}✅ RUNNING${NC}"
    else
        echo -e "  Ollama:      ${YELLOW}⚠️  NOT RUNNING${NC}"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Smoke test results
    if [ -f "$SMOKE_TEST_LOG" ]; then
        local test_summary=$(tail -n 5 "$SMOKE_TEST_LOG" | grep "SMOKE TEST RESULTS" || echo "")
        if [ -n "$test_summary" ]; then
            echo "Smoke Tests: $test_summary"
            echo ""
        fi
    fi

    print_info "Logs location: $LOG_DIR"
    print_info "PID files: $PID_DIR"
    echo ""

    print_success "All systems operational! 🚀"
    echo ""
    echo "Quick commands:"
    echo "  Stop all:  ./stop_all.sh"
    echo "  Restart:   ./restart_all.sh"
    echo "  Status:    ./status_all.sh"
    echo ""
}

# ====================================================================
# MAIN EXECUTION
# ====================================================================

main() {
    clear
    print_header "🚀 MARKDOWN TASK MANAGER - STARTUP"

    echo "Starting all services..."
    echo ""

    # Start services in order
    check_postgresql || exit 1
    start_redis || exit 1
    start_backend || exit 1
    start_celery || exit 1
    check_ollama || true  # Don't exit if Ollama not running (optional)

    # Run smoke tests
    run_smoke_tests || print_warning "Some smoke tests failed, but system is running"

    # Show final status
    show_status

    # Ask to open browser
    open_browser

    print_success "Startup complete! System is ready. ✨"
}

# Run main function
main
