#!/bin/bash
#
# MarQed AI Agent Platform - Stop Script
# Usage: ./stop.sh [--all]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Parse arguments
STOP_ALL=false
for arg in "$@"; do
    case $arg in
        --all)
            STOP_ALL=true
            shift
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MarQed AI Agent Platform - Shutdown${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Stop uvicorn
echo -e "${YELLOW}[1/2]${NC} Stopping API server..."
if pgrep -f "uvicorn app.main:app" >/dev/null 2>&1; then
    pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true
    echo -e "      ${GREEN}API server: stopped${NC}"
else
    echo -e "      ${YELLOW}API server: not running${NC}"
fi

# Stop Docker containers (only if --all flag)
if [ "$STOP_ALL" = true ]; then
    echo -e "${YELLOW}[2/2]${NC} Stopping Docker containers..."
    cd "$BACKEND_DIR"
    docker-compose down
    echo -e "      ${GREEN}Docker containers: stopped${NC}"
else
    echo -e "${YELLOW}[2/2]${NC} Docker containers: ${YELLOW}kept running${NC} (use --all to stop)"
fi

echo ""
echo -e "${GREEN}Shutdown complete.${NC}"
echo ""
