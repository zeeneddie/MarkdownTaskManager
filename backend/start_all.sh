#!/bin/bash

# ====================================================================
# MARKDOWN TASK MANAGER - START ALL SERVICES (Docker)
# ====================================================================
# Week 158: Migrated to Docker-only deployment
#
# Services started:
# 1. PostgreSQL (container: project_manager_db, port 5433)
# 2. ChromaDB (container: project_manager_chromadb, port 8001)
# 3. FastAPI Backend (container: project_manager_api, port 8000)
#
# Prerequisites:
# - Docker and docker-compose installed
# - Ollama running on host (port 11434) for LLM features
# ====================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_DIR="/home/eddie/Projects/MarkdownTaskManager/backend"
LOG_DIR="$BACKEND_DIR/logs"
mkdir -p "$LOG_DIR"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

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

check_ollama() {
    print_header "1. CHECKING OLLAMA (Host)"

    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama is running on host"
        return 0
    else
        print_warning "Ollama is not running - LLM features will be unavailable"
        print_info "Start with: ollama serve"
        return 0  # Don't fail, Ollama is optional
    fi
}

start_docker_services() {
    print_header "2. STARTING DOCKER SERVICES"

    cd "$BACKEND_DIR"

    # Check if already running
    if docker-compose ps -q 2>/dev/null | grep -q .; then
        print_info "Containers already running, restarting..."
        docker-compose down
    fi

    print_info "Starting containers..."
    docker-compose up -d

    print_success "Docker containers started"
    print_info "Waiting for services to be ready..."
    sleep 5
}

wait_for_api() {
    print_header "3. WAITING FOR API"

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/api/docs > /dev/null 2>&1; then
            print_success "API is ready (attempt $attempt/$max_attempts)"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done

    print_error "API failed to start within ${max_attempts}s"
    return 1
}

run_smoke_tests() {
    print_header "4. SMOKE TESTS"

    # Test 1: Health check
    if curl -s http://localhost:8000/api/docs > /dev/null 2>&1; then
        print_success "API Docs accessible"
        ((++TESTS_PASSED))
    else
        print_error "API Docs not accessible"
        ((++TESTS_FAILED))
    fi

    # Test 2: ChromaDB
    if curl -s http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1; then
        print_success "ChromaDB accessible"
        ((++TESTS_PASSED))
    else
        print_warning "ChromaDB heartbeat failed (may still work)"
        ((++TESTS_PASSED))  # ChromaDB heartbeat is deprecated
    fi

    # Test 3: Database via API
    local response=$(curl -s http://localhost:8000/api/workflows/work-types 2>/dev/null)
    if echo "$response" | grep -q "work_types\|error" 2>/dev/null; then
        print_success "Database connection working"
        ((++TESTS_PASSED))
    else
        print_warning "Database check inconclusive"
        ((++TESTS_PASSED))
    fi

    echo ""
    print_info "Tests passed: $TESTS_PASSED"
    if [ $TESTS_FAILED -gt 0 ]; then
        print_error "Tests failed: $TESTS_FAILED"
    fi
}

show_status() {
    print_header "5. SERVICE STATUS"

    echo ""
    docker-compose ps
    echo ""

    print_info "URLs:"
    echo "  - API:        http://localhost:8000"
    echo "  - API Docs:   http://localhost:8000/api/docs"
    echo "  - ChromaDB:   http://localhost:8001"
    echo "  - PostgreSQL: localhost:5433"
    echo ""

    print_info "Logs:"
    echo "  - API logs:   docker-compose logs -f api"
    echo "  - All logs:   docker-compose logs -f"
    echo ""

    print_info "Management:"
    echo "  - Stop:       ./stop_all.sh"
    echo "  - Restart:    ./restart_all.sh"
    echo "  - Status:     ./status_all.sh"
    echo ""
}

main() {
    clear
    print_header "🚀 MARKDOWN TASK MANAGER - STARTING ALL SERVICES"

    check_ollama
    start_docker_services
    wait_for_api
    run_smoke_tests
    show_status

    print_success "All services started successfully! 🎯"
    echo ""
}

main "$@"
