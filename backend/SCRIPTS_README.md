# Management Scripts - Multi-Stack AI Agent Platform

Deze scripts beheren alle services voor het Agentic Task Management System.

## 📋 Beschikbare Scripts

### 1. `start_all.sh` - Start alle services
```bash
./start_all.sh
```

**Wat het doet:**
1. ✅ Check/start PostgreSQL
2. ✅ Start Redis (port 6379)
3. ✅ Start FastAPI Backend (port 8000)
4. ✅ Start Celery Workers (4 workers, 3 queues)
5. ✅ Check Ollama (local LLMs)
6. ✅ **Run 10 smoke tests** (API endpoints, workflows, agents)
7. ✅ Open browser (optioneel)

**Features:**
- Automatische service detection (skips al draaiende services)
- PID file management
- Logging naar `logs/` directory
- Volledige smoke test suite
- Color-coded output
- Health checks voor alle endpoints

**Output:**
- Backend log: `logs/backend.log`
- Celery log: `logs/celery.log`
- Redis log: `logs/redis.log`
- Smoke test log: `logs/smoke-test.log`

---

### 2. `stop_all.sh` - Stop alle services
```bash
./stop_all.sh
```

**Wat het doet:**
- Stop Celery workers (graceful + force kill fallback)
- Stop FastAPI backend
- Stop Redis
- Cleanup PID files

**Wat NIET gestopt wordt:**
- PostgreSQL (system-wide service)
- Ollama (system-wide service)

---

### 3. `status_all.sh` - Check system status
```bash
./status_all.sh
```

**Wat het toont:**
1. **Core Services Status:**
   - PostgreSQL (running/stopped)
   - Redis (PID + memory usage)
   - FastAPI Backend (PID + memory usage)
   - Celery Workers (PID + memory usage)

2. **API Endpoints Status:**
   - Health check (healthy/unhealthy)
   - Work types (9/9 available)
   - Agents (10/10 ready)
   - API Documentation (accessible/unavailable)

3. **Ollama Status:**
   - Service status
   - Installed models lijst

4. **Recent Log Activity:**
   - Log file sizes
   - Line counts
   - Last modified timestamps

5. **System Resources:**
   - Total memory gebruikt
   - Disk usage
   - Backend uptime

**Quick Links:**
- API Docs: http://localhost:8000/api/docs
- Project Viewer: http://localhost:8000/
- Sprint Planning: http://localhost:8000/sprint-planning.html

---

### 4. `restart_all.sh` - Restart alle services
```bash
./restart_all.sh
```

**Wat het doet:**
1. Stop alle services (via `stop_all.sh`)
2. Wacht 2 seconden
3. Start alle services (via `start_all.sh`)

Handig voor:
- Na configuratie wijzigingen
- Na code updates
- Troubleshooting

---

## 🧪 Smoke Tests

Het `start_all.sh` script voert 10 smoke tests uit:

| # | Test | Beschrijving | Success Criteria |
|---|------|--------------|------------------|
| 1 | Health Check | `/api/health` endpoint | Status "healthy" |
| 2 | Work Types | `/api/workflows/work-types` | 9 work types |
| 3 | Agents | `/api/workflows/agents` | 10 agents |
| 4 | Statistics | `/api/workflows/statistics` | Valid response |
| 5 | NEW_FEATURE Workflow | OAuth2 test | Work type classified |
| 6 | BUG Workflow | Session bug test | Work type classified |
| 7 | Redis Connection | PING command | PONG response |
| 8 | Celery Workers | Process check | Workers running |
| 9 | OpenAPI Docs | `/openapi.json` | Valid schema |
| 10 | TypeScript Executor | File check | `execute-workflow.ts` exists |

**Test Results:**
- Logs naar `logs/smoke-test.log`
- Summary in console output
- Pass/fail count totaal

---

## 📁 Directory Structuur

```
backend/
├── start_all.sh           # ⭐ Master startup script (met smoke tests)
├── stop_all.sh            # Stop alle services
├── status_all.sh          # Check system status
├── restart_all.sh         # Restart alle services
├── start_celery_worker.sh # Legacy (individueel)
├── start_redis_dev.sh     # Legacy (individueel)
├── SCRIPTS_README.md      # Deze file
├── .pids/                 # PID files
│   ├── backend.pid
│   ├── celery.pid
│   └── redis.pid
└── logs/                  # Log files
    ├── backend.log        # FastAPI logs
    ├── celery.log         # Celery worker logs
    ├── redis.log          # Redis server logs
    └── smoke-test.log     # Smoke test results
```

---

## 🚀 Quick Start

### Eerste keer opstarten:
```bash
cd /home/eddie/Projects/MarkdownTaskManager/backend

# Check of virtual environment bestaat
ls .venv/

# Als niet bestaat:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start alle services
./start_all.sh
```

### Dagelijks gebruik:
```bash
# Start
./start_all.sh

# Check status
./status_all.sh

# Restart
./restart_all.sh

# Stop
./stop_all.sh
```

---

## 🔧 Troubleshooting

### Script kan niet worden uitgevoerd
```bash
chmod +x *.sh
```

### PostgreSQL start niet
```bash
sudo systemctl start postgresql
pg_isready
```

### Redis port al in gebruik
```bash
# Kill bestaande Redis
pkill redis-server
# Of
lsof -ti:6379 | xargs kill -9
```

### Backend start niet (port 8000 bezet)
```bash
# Check wat er draait op port 8000
lsof -i:8000
# Kill het proces
kill -9 <PID>
```

### Celery workers reageren niet
```bash
# Stop forcefully
pkill -9 -f celery
rm .pids/celery.pid
# Herstart
./start_all.sh
```

### Logs bekijken (real-time)
```bash
# Backend
tail -f logs/backend.log

# Celery
tail -f logs/celery.log

# Redis
tail -f logs/redis.log

# Smoke tests
cat logs/smoke-test.log
```

### Alle processes killen (nuclear option)
```bash
pkill -f uvicorn
pkill -f celery
pkill redis-server
rm -rf .pids/*.pid
```

---

## 📊 Service Dependencies

```
PostgreSQL (system)
    ↓
FastAPI Backend (port 8000)
    ↓
├─→ Redis (port 6379)
│   └─→ Celery Workers (4x)
│       └─→ TypeScript Agent Executor
│           └─→ Ollama (local LLMs)
└─→ Database Models
```

**Startup volgorde:**
1. PostgreSQL (check/start)
2. Redis
3. FastAPI Backend
4. Celery Workers
5. Ollama (check only)

**Shutdown volgorde:**
1. Celery Workers
2. FastAPI Backend
3. Redis
4. PostgreSQL (remains running)

---

## 🎯 Production Checklist

Voor productie deployment:

1. **Redis:**
   - [ ] Enable authentication (`requirepass`)
   - [ ] Update Redis URL in `.env`
   - [ ] Configure persistence (RDB/AOF)

2. **Backend:**
   - [ ] Set `DEBUG=false`
   - [ ] Use production ASGI server (gunicorn + uvicorn)
   - [ ] Enable HTTPS
   - [ ] Configure CORS properly

3. **Celery:**
   - [ ] Use systemd service files
   - [ ] Configure Flower monitoring
   - [ ] Set up log rotation

4. **Ollama:**
   - [ ] Ensure all models downloaded
   - [ ] Configure GPU if available
   - [ ] Set resource limits

Zie `PRODUCTION_CHECKLIST.md` voor volledige lijst.

---

## 🔗 Related Documentation

- **HERSTART_PROJECT.md** - Complete project recovery guide
- **fasenplan.md** - 40-week development roadmap
- **DAY4_COMPLETE.md** - Week 5 Day 4 achievements
- **CELERY_REDIS_COMPLETE.md** - Celery/Redis setup details
- **LLM_CONFIGURATION.md** - Ollama model mapping

---

## 📞 Support

Als scripts niet werken:
1. Check logs in `logs/` directory
2. Run `./status_all.sh` voor diagnostics
3. Check `HERSTART_PROJECT.md` voor troubleshooting
4. Contact: Eddie (project owner)

---

**Version:** 1.0
**Last Updated:** 2025-11-13
**Author:** Eddie / Claude Code

---

**🚀 Veel succes met Fase 2!**
