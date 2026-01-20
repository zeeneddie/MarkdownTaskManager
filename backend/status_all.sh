#!/bin/bash

# ====================================================================
# MARKDOWN TASK MANAGER - STATUS ALL SERVICES (Docker)
# ====================================================================
# Week 158: Migrated to Docker-only deployment
# ====================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_DIR="/home/eddie/Projects/MarkdownTaskManager/backend"

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

main() {
    clear
    print_header "📊 MARKDOWN TASK MANAGER - SERVICE STATUS"

    cd "$BACKEND_DIR"

    # Docker containers
    print_info "Docker Containers:"
    echo ""
    docker-compose ps
    echo ""

    # Service health checks
    print_header "Health Checks"

    # API
    if curl -s http://localhost:8000/api/docs > /dev/null 2>&1; then
        print_success "API (8000): Running"
    else
        print_error "API (8000): Not responding"
    fi

    # ChromaDB
    if curl -s http://localhost:8001/api/v1 > /dev/null 2>&1; then
        print_success "ChromaDB (8001): Running"
    else
        print_warning "ChromaDB (8001): Not responding (may still work)"
    fi

    # PostgreSQL (container)
    if docker-compose exec -T db pg_isready -U user > /dev/null 2>&1; then
        print_success "PostgreSQL (5433): Running"
    else
        print_error "PostgreSQL (5433): Not responding"
    fi

    # Ollama (host)
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama (11434): Running"
    else
        print_warning "Ollama (11434): Not running (LLM features unavailable)"
    fi

    echo ""
    print_info "URLs:"
    echo "  - API:        http://localhost:8000"
    echo "  - API Docs:   http://localhost:8000/api/docs"
    echo "  - ChromaDB:   http://localhost:8001"
    echo "  - PostgreSQL: localhost:5433"
    echo ""
}

main
