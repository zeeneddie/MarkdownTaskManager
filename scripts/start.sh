#!/bin/bash
# ============================================
# MarQed AI Platform - Start Script
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_header() { echo -e "\n${BLUE}════════════════════════════════════════${NC}"; echo -e "${BLUE}  $1${NC}"; echo -e "${BLUE}════════════════════════════════════════${NC}\n"; }
log_step() { echo -e "${YELLOW}[$1]${NC} $2"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}" >&2; }

log_header "Starting MarQed AI Platform"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker first."
    exit 1
fi

# 1. Start databases
log_step "1/5" "Starting database containers..."
cd "$BACKEND_DIR"
docker-compose up -d db chromadb

# 2. Wait for PostgreSQL
log_step "2/5" "Waiting for PostgreSQL to be ready..."
until docker-compose exec -T db pg_isready -U user > /dev/null 2>&1; do
    sleep 1
    echo -n "."
done
echo ""
log_success "PostgreSQL is ready"

# 3. Activate virtual environment
log_step "3/5" "Activating Python environment..."
if [ ! -d "$BACKEND_DIR/.venv" ]; then
    log_error "Virtual environment not found. Run 'make setup' first."
    exit 1
fi
source "$BACKEND_DIR/.venv/bin/activate"

# 4. Run migrations (if needed)
log_step "4/5" "Checking database migrations..."
cd "$BACKEND_DIR"
CURRENT=$(alembic current 2>/dev/null | grep -oE '[a-f0-9]+' | head -1 || echo "none")
HEAD=$(alembic heads 2>/dev/null | grep -oE '[a-f0-9]+' | head -1 || echo "none")
if [ "$CURRENT" != "$HEAD" ]; then
    echo "Running pending migrations..."
    alembic upgrade head
else
    echo "Database is up to date"
fi

# 5. Start API server
log_step "5/5" "Starting API server..."

# Kill existing uvicorn processes
pkill -f "uvicorn app.main:app" 2>/dev/null || true

# Start uvicorn in background
cd "$BACKEND_DIR"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$BACKEND_DIR/logs/uvicorn.log" 2>&1 &
UVICORN_PID=$!
echo "$UVICORN_PID" > "$BACKEND_DIR/.pids/uvicorn.pid"

# Wait for API to be ready
echo -n "Waiting for API..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        echo ""
        log_success "API is ready"
        break
    fi
    echo -n "."
    sleep 1
done

# Open browser (optional)
if [[ "$1" != "--no-browser" ]]; then
    sleep 1
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000 2>/dev/null &
    elif command -v open &> /dev/null; then
        open http://localhost:8000 2>/dev/null &
    fi
fi

log_header "Platform Started Successfully"

echo ""
echo -e "${GREEN}Services:${NC}"
echo "  Hub Portal:   http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  ReDoc:        http://localhost:8000/redoc"
echo "  PostgreSQL:   localhost:5433"
echo "  ChromaDB:     localhost:8001"
echo ""
echo -e "${YELLOW}Logs:${NC} tail -f $BACKEND_DIR/logs/uvicorn.log"
echo -e "${YELLOW}Stop:${NC} make stop (or ./scripts/stop.sh)"
echo ""
