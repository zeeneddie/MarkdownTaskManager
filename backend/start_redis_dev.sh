#!/bin/bash
#
# Start Redis for Development (no auth)
#
# This starts Redis without authentication for local development.
# For production, use systemd service with proper authentication.
#

echo "Starting Redis for development (no auth, port 6379)..."
echo "Note: This is for LOCAL DEVELOPMENT only!"
echo ""

# Kill any existing Redis process on port 6379
if lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "Redis is already running on port 6379"
    echo "PID: $(lsof -Pi :6379 -sTCP:LISTEN -t)"
    echo ""
    read -p "Kill existing Redis and start fresh? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill $(lsof -Pi :6379 -sTCP:LISTEN -t) 2>/dev/null
        sleep 1
    else
        echo "Using existing Redis instance"
        redis-cli ping && echo "✓ Redis is responding" || echo "✗ Redis not responding"
        exit 0
    fi
fi

# Start Redis without config (defaults, no auth)
redis-server --port 6379 --daemonize yes --loglevel notice

# Wait a bit for Redis to start
sleep 1

# Test connection
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis started successfully on port 6379"
    echo "✓ No authentication required"
    echo ""
    echo "To stop Redis: redis-cli shutdown"
    echo "To check status: redis-cli ping"
else
    echo "✗ Failed to start Redis"
    exit 1
fi
