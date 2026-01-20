#!/bin/bash
# MarQed Backend Dev Restart Script
# Week 158: Quick restart voor development

echo "🔄 Stoppen bestaande processen..."
pkill -f "uvicorn app.main" 2>/dev/null
sleep 2

echo "🚀 Starten MarQed Backend op poort 8000..."
cd /home/eddie/Projects/MarkdownTaskManager/backend
source .venv/bin/activate

# Start met reload voor development
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/marqed-backend.log 2>&1 &

echo "⏳ Wachten op startup..."
sleep 10

# Check of het werkt
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend draait op http://localhost:8000"
    echo "📄 Logs: tail -f /tmp/marqed-backend.log"
else
    echo "❌ Backend niet gestart. Check logs:"
    tail -20 /tmp/marqed-backend.log
fi
