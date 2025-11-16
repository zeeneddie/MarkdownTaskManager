#!/bin/bash

# ====================================================================
# MARKDOWN TASK MANAGER - RESTART ALL SERVICES
# ====================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
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

main() {
    clear
    print_header "🔄 MARKDOWN TASK MANAGER - RESTART ALL SERVICES"

    cd "$BACKEND_DIR"

    # Stop all services
    print_info "Stopping all services..."
    ./stop_all.sh

    echo ""
    print_info "Waiting 2 seconds..."
    sleep 2

    # Start all services
    print_info "Starting all services..."
    ./start_all.sh
}

main
