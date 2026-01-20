#!/bin/bash

# ====================================================================
# MARKDOWN TASK MANAGER - STOP ALL SERVICES (Docker)
# ====================================================================
# Week 158: Migrated to Docker-only deployment
# ====================================================================

set -e

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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

main() {
    clear
    print_header "🛑 MARKDOWN TASK MANAGER - STOPPING ALL SERVICES"

    cd "$BACKEND_DIR"

    print_info "Stopping Docker containers..."
    echo ""

    if docker-compose ps -q 2>/dev/null | grep -q .; then
        docker-compose down
        print_success "Docker containers stopped"
    else
        print_info "No containers were running"
    fi

    echo ""
    print_success "All services stopped successfully!"
    echo ""
    print_info "PostgreSQL (system-wide) not stopped"
    print_info "Ollama (system-wide) not stopped"
    echo ""
}

main
