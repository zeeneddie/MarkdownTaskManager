#!/bin/bash

# ====================================================================
# MARKDOWN TASK MANAGER - RESTART ALL SERVICES (Docker)
# ====================================================================
# Week 158: Migrated to Docker-only deployment
# ====================================================================

set -e

BACKEND_DIR="/home/eddie/Projects/MarkdownTaskManager/backend"

# Colors
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

main() {
    clear
    print_header "🔄 MARKDOWN TASK MANAGER - RESTARTING ALL SERVICES"

    cd "$BACKEND_DIR"

    # Use docker-compose restart for faster restart
    echo "Restarting Docker containers..."
    docker-compose restart

    echo ""
    echo "Waiting for services to be ready..."
    sleep 5

    # Run status check
    ./status_all.sh
}

main
