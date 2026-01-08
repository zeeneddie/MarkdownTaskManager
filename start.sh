#!/bin/bash
#
# MarQed AI Agent Platform - Startup Script
# Usage: ./start.sh [--no-browser]
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
VENV_DIR="$BACKEND_DIR/.venv"
LOG_DIR="/tmp/marqed"
UVICORN_LOG="$LOG_DIR/uvicorn.log"
UVICORN_PID="$LOG_DIR/uvicorn.pid"

# Parse arguments
OPEN_BROWSER=true
for arg in "$@"; do
    case $arg in
        --no-browser)
            OPEN_BROWSER=false
            shift
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MarQed AI Agent Platform - Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create log directory
mkdir -p "$LOG_DIR"

# Function to check if port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local max_attempts=$2
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    return 1
}

# Step 1: Start Docker containers (PostgreSQL + ChromaDB)
echo -e "${YELLOW}[1/4]${NC} Starting Docker containers..."
cd "$BACKEND_DIR"

if ! docker-compose ps db | grep -q "Up"; then
    docker-compose up -d db chromadb
    echo -e "      Waiting for PostgreSQL to be healthy..."
    sleep 5

    # Wait for DB to be healthy
    for i in {1..30}; do
        if docker-compose ps db | grep -q "healthy"; then
            break
        fi
        sleep 1
    done
fi

if docker-compose ps db | grep -q "healthy"; then
    echo -e "      ${GREEN}PostgreSQL: healthy${NC}"
else
    echo -e "      ${YELLOW}PostgreSQL: starting...${NC}"
fi

if docker-compose ps chromadb | grep -q "Up"; then
    echo -e "      ${GREEN}ChromaDB: running${NC}"
else
    echo -e "      ${YELLOW}ChromaDB: starting...${NC}"
fi

# Step 2: Check/Activate Python virtual environment
echo -e "${YELLOW}[2/4]${NC} Checking Python environment..."
if [ ! -d "$VENV_DIR" ]; then
    echo -e "      ${RED}Virtual environment not found at $VENV_DIR${NC}"
    echo -e "      Run: cd backend && python -m venv .venv && pip install -r requirements.txt"
    exit 1
fi
echo -e "      ${GREEN}Virtual environment: OK${NC}"

# Step 3: Start uvicorn API server
echo -e "${YELLOW}[3/4]${NC} Starting API server..."

# Kill existing uvicorn if running on port 8000
if check_port 8000; then
    echo -e "      Stopping existing API server..."
    pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true
    sleep 2
fi

# Start uvicorn in background
cd "$BACKEND_DIR"
source "$VENV_DIR/bin/activate"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$UVICORN_LOG" 2>&1 &
echo $! > "$UVICORN_PID"

# Wait for API to be ready
echo -e "      Waiting for API to be ready..."
if wait_for_service "http://localhost:8000/api/health" 15; then
    echo -e "      ${GREEN}API server: running on http://localhost:8000${NC}"
else
    echo -e "      ${RED}API server failed to start. Check logs: $UVICORN_LOG${NC}"
    exit 1
fi

# Step 4: Verify health endpoint
echo -e "${YELLOW}[4/4]${NC} Verifying services..."
HEALTH=$(curl -s http://localhost:8000/api/health 2>/dev/null)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "      ${GREEN}Health check: passed${NC}"
else
    echo -e "      ${RED}Health check: failed${NC}"
    echo -e "      Response: $HEALTH"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All services started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  ${BLUE}Hub Portal:${NC}     http://localhost:8000/"
echo -e "  ${BLUE}API Docs:${NC}       http://localhost:8000/docs"
echo -e "  ${BLUE}Health API:${NC}     http://localhost:8000/api/health"
echo -e "  ${BLUE}PostgreSQL:${NC}     localhost:5433"
echo -e "  ${BLUE}ChromaDB:${NC}       localhost:8001"
echo ""
echo -e "  ${YELLOW}Logs:${NC}           $UVICORN_LOG"
echo -e "  ${YELLOW}Stop:${NC}           ./stop.sh or pkill -f uvicorn"
echo ""

# Open browser if requested
if [ "$OPEN_BROWSER" = true ]; then
    echo -e "Opening Hub Portal in browser..."
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:8000/" &
    elif command -v open &> /dev/null; then
        open "http://localhost:8000/" &
    fi
fi
