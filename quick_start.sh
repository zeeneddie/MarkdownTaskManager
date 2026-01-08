#!/bin/bash
# ====================================================================
# MARKDOWN TASK MANAGER - QUICK START
# ====================================================================
# Snel het hele systeem opstarten in 1 commando.
# Gebruik: ./quick_start.sh
#
# Dit script:
# 1. Start Docker containers (PostgreSQL + ChromaDB)
# 2. Installeert Python dependencies
# 3. Draait database migrations
# 4. Start de FastAPI backend
# 5. Opent de browser met API docs
# ====================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Directories
PROJECT_ROOT="/home/eddie/Projects/MarkdownTaskManager"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/.venv"

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       MARKDOWN TASK MANAGER - QUICK START                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ====================================================================
# 1. DOCKER
# ====================================================================
echo -e "${BLUE}[1/5] Starting Docker containers...${NC}"
cd "$BACKEND_DIR"

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running! Start it with: sudo systemctl start docker${NC}"
    exit 1
fi

docker-compose up -d db chromadb

# Wait for PostgreSQL
echo -n "Waiting for PostgreSQL"
for i in {1..30}; do
    if docker-compose exec -T db pg_isready -U user > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

echo -e "${GREEN}✅ Docker containers running${NC}"

# ====================================================================
# 2. PYTHON ENVIRONMENT
# ====================================================================
echo -e "${BLUE}[2/5] Setting up Python environment...${NC}"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✅ Python environment ready${NC}"

# ====================================================================
# 3. DATABASE MIGRATIONS
# ====================================================================
echo -e "${BLUE}[3/5] Running database migrations...${NC}"

export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5433/project_manager"
alembic upgrade head > /dev/null 2>&1

echo -e "${GREEN}✅ Database migrations complete${NC}"

# ====================================================================
# 4. START BACKEND
# ====================================================================
echo -e "${BLUE}[4/5] Starting FastAPI backend...${NC}"

# Kill existing process on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Stopping existing backend..."
    kill $(lsof -Pi :8000 -sTCP:LISTEN -t) 2>/dev/null || true
    sleep 2
fi

# Set environment
export CHROMA_HOST="localhost"
export CHROMA_PORT="8001"
export SECRET_KEY="dev-secret-key"
export ENVIRONMENT="development"

# Start backend
mkdir -p "$BACKEND_DIR/logs"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$BACKEND_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!

# Wait for startup
echo -n "Waiting for backend"
for i in {1..20}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend running (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}❌ Backend failed to start. Check logs: $BACKEND_DIR/logs/backend.log${NC}"
    exit 1
fi

# ====================================================================
# 5. DONE
# ====================================================================
echo -e "${BLUE}[5/5] Quick start complete!${NC}"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗"
echo -e "║                    SYSTEM READY!                                ║"
echo -e "╠════════════════════════════════════════════════════════════════╣"
echo -e "║  Hub Portal:      ${NC}http://localhost:8000${GREEN}                        ║"
echo -e "║  API Docs:        ${NC}http://localhost:8000/api/docs${GREEN}               ║"
echo -e "║  OpenAPI:         ${NC}http://localhost:8000/openapi.json${GREEN}           ║"
echo -e "╠════════════════════════════════════════════════════════════════╣"
echo -e "║  PostgreSQL:      ${NC}localhost:5433${GREEN}                              ║"
echo -e "║  ChromaDB:        ${NC}localhost:8001${GREEN}                              ║"
echo -e "╠════════════════════════════════════════════════════════════════╣"
echo -e "║  Backend log:     ${NC}$BACKEND_DIR/logs/backend.log${GREEN}               ║"
echo -e "╠════════════════════════════════════════════════════════════════╣"
echo -e "║  Stop services:   ${NC}./test_script.sh stop${GREEN}                       ║"
echo -e "║  Run tests:       ${NC}./test_script.sh${GREEN}                            ║"
echo -e "║  Status check:    ${NC}./test_script.sh status${GREEN}                     ║"
echo -e "╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Ask to open browser
read -p "Open browser? [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:8000" &
    elif command -v open &> /dev/null; then
        open "http://localhost:8000" &
    fi
fi

echo -e "${GREEN}Done! 🚀${NC}"
