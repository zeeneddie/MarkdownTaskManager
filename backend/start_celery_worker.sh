#!/bin/bash
#
# Start Celery Worker for Markdown Task Manager
#
# Usage:
#   ./start_celery_worker.sh
#
# This script starts a Celery worker that processes async workflow tasks.
#

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Markdown Task Manager - Celery Worker${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Check if Redis is running
echo -e "${YELLOW}Checking Redis connection...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${RED}✗ Redis is not running or requires authentication${NC}"
    echo -e "${YELLOW}  Starting Redis...${NC}"

    # Try to start Redis (if you have sudo access)
    # sudo systemctl start redis-server

    echo -e "${YELLOW}  Please start Redis manually:${NC}"
    echo -e "${YELLOW}    sudo systemctl start redis-server${NC}"
    echo ""
    echo -e "${YELLOW}  For development without auth:${NC}"
    echo -e "${YELLOW}    Edit /etc/redis/redis.conf${NC}"
    echo -e "${YELLOW}    Comment out: # requirepass <password>${NC}"
    echo -e "${YELLOW}    Restart: sudo systemctl restart redis-server${NC}"
    echo ""
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}✗ Virtual environment not found at .venv/${NC}"
    echo -e "${YELLOW}  Please create it first: uv venv${NC}"
    exit 1
fi

# Check if Celery is installed
echo -e "${YELLOW}Checking Celery installation...${NC}"
if python -c "import celery" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Celery is installed${NC}"
else
    echo -e "${RED}✗ Celery is not installed${NC}"
    echo -e "${YELLOW}  Installing Celery...${NC}"
    uv pip install celery redis
fi

echo ""
echo -e "${GREEN}Starting Celery worker...${NC}"
echo -e "${YELLOW}Worker configuration:${NC}"
echo -e "  App: app.celery_app"
echo -e "  Concurrency: 4 (autoscale)"
echo -e "  Queues: workflows, projects, celery"
echo -e "  Log level: INFO"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the worker${NC}"
echo ""

# Start Celery worker with recommended settings
celery -A app.celery_app worker \
    --loglevel=INFO \
    --concurrency=4 \
    --max-tasks-per-child=1000 \
    --time-limit=1800 \
    --soft-time-limit=1800 \
    --queues=workflows,projects,celery \
    --pool=prefork \
    --events \
    --beat

# Note: --beat is included for periodic tasks (if configured in beat_schedule)
# For production, run beat separately: celery -A app.celery_app beat
