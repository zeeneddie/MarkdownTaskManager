# Periodic Maintenance Scheduling

## Overview

Automatic scheduling system for recurring maintenance scans using APScheduler. The scheduler runs within the FastAPI application and manages periodic execution of the Code-Maintenance-Agent workflow.

---

## Quick Start

The scheduler starts automatically when the FastAPI application launches:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Output:
```
✅ Database tables created successfully
✅ Maintenance scheduler started
📅 Scheduler API: http://localhost:8000/api/scheduler/status
```

---

## API Endpoints

### Schedule Daily Scan
```http
POST /api/scheduler/daily
Content-Type: application/json

{
  "hour": 2,
  "minute": 0,
  "scope": "full_codebase",
  "focusAreas": ["dependencies", "security"],
  "urgency": "medium"
}
```

**Response:**
```json
{
  "success": true,
  "jobId": "daily_scan_full_codebase",
  "message": "Daily scan scheduled at 02:00 UTC"
}
```

---

### Schedule Weekly Scan
```http
POST /api/scheduler/weekly
Content-Type: application/json

{
  "dayOfWeek": "mon",
  "hour": 2,
  "minute": 0,
  "scope": "full_codebase",
  "focusAreas": ["dependencies", "security", "code_quality"],
  "urgency": "medium"
}
```

**Response:**
```json
{
  "success": true,
  "jobId": "weekly_scan_full_codebase",
  "message": "Weekly scan scheduled on mon at 02:00 UTC"
}
```

---

### Schedule Interval Scan
```http
POST /api/scheduler/interval
Content-Type: application/json

{
  "hours": 24,
  "scope": "full_codebase",
  "focusAreas": ["dependencies", "security"],
  "urgency": "medium"
}
```

**Response:**
```json
{
  "success": true,
  "jobId": "interval_scan_full_codebase_24h",
  "message": "Interval scan scheduled every 24 hours"
}
```

---

### Get All Scheduled Jobs
```http
GET /api/scheduler/jobs
```

**Response:**
```json
[
  {
    "id": "daily_scan_full_codebase",
    "name": "Daily full_codebase scan",
    "nextRunTime": "2025-11-15T02:00:00+00:00",
    "trigger": "cron[hour='2', minute='0']"
  },
  {
    "id": "weekly_scan_full_codebase",
    "name": "Weekly full_codebase scan",
    "nextRunTime": "2025-11-18T02:00:00+00:00",
    "trigger": "cron[day_of_week='mon', hour='2', minute='0']"
  }
]
```

---

### Get Execution History
```http
GET /api/scheduler/history?limit=10&status=completed
```

**Response:**
```json
[
  {
    "jobId": "daily_scan_full_codebase",
    "startTime": "2025-11-14T02:00:00",
    "endTime": "2025-11-14T02:15:23",
    "durationSeconds": 923.5,
    "scope": "full_codebase",
    "focusAreas": ["dependencies", "security"],
    "urgency": "medium",
    "status": "completed",
    "findingsCount": 12,
    "tasksCount": 8
  }
]
```

---

### Remove Scheduled Job
```http
DELETE /api/scheduler/jobs/daily_scan_full_codebase
```

**Response:**
```json
{
  "success": true,
  "jobId": "daily_scan_full_codebase",
  "message": "Job daily_scan_full_codebase removed successfully"
}
```

---

### Get Scheduler Status
```http
GET /api/scheduler/status
```

**Response:**
```json
{
  "running": true,
  "scheduledJobs": 2,
  "executionRecords": 45,
  "completedScans": 42,
  "failedScans": 2,
  "timeoutScans": 1
}
```

---

## Configuration Options

### Scope
- `full_codebase`: Scan entire codebase
- `module`: Scan specific module (requires `modulePath`)
- `specific_files`: Scan specific files (requires `targetFiles`)

### Focus Areas
- `dependencies`: Package updates, vulnerabilities
- `code_quality`: Complexity, duplication, refactoring
- `security`: Security vulnerabilities, OWASP issues
- `performance`: Performance bottlenecks, N+1 queries
- `tests`: Test coverage improvements
- `documentation`: Documentation updates

### Urgency Levels
- `low`: Documentation, minor cleanup
- `medium`: Regular maintenance, improvements (default)
- `high`: Important refactoring, significant debt
- `critical`: Security vulnerabilities, production issues

---

## Example Usage Scenarios

### 1. Daily Dependency & Security Scan (2 AM UTC)
```bash
curl -X POST http://localhost:8000/api/scheduler/daily \
  -H "Content-Type: application/json" \
  -d '{
    "hour": 2,
    "minute": 0,
    "scope": "full_codebase",
    "focusAreas": ["dependencies", "security"],
    "urgency": "high"
  }'
```

### 2. Weekly Comprehensive Scan (Monday 3 AM UTC)
```bash
curl -X POST http://localhost:8000/api/scheduler/weekly \
  -H "Content-Type: application/json" \
  -d '{
    "dayOfWeek": "mon",
    "hour": 3,
    "minute": 0,
    "scope": "full_codebase",
    "focusAreas": ["dependencies", "security", "code_quality", "performance", "tests"],
    "urgency": "medium"
  }'
```

### 3. Module-Specific Performance Check (Every 12 hours)
```bash
curl -X POST http://localhost:8000/api/scheduler/interval \
  -H "Content-Type: application/json" \
  -d '{
    "hours": 12,
    "scope": "module",
    "modulePath": "src/api",
    "focusAreas": ["performance", "code_quality"],
    "urgency": "medium"
  }'
```

---

## Execution Behavior

### Timeout
- Maximum execution time: 30 minutes
- Execution marked as `timeout` if exceeded
- History tracked with timeout status

### Error Handling
- Exceptions caught and logged
- Execution history tracks `failed` status
- Error messages stored in history

### Concurrent Execution
- Multiple scans can run simultaneously
- Each job has unique ID
- Independent execution tracking

---

## Monitoring

### View Scheduled Jobs
```bash
curl http://localhost:8000/api/scheduler/jobs
```

### View Recent Executions
```bash
curl 'http://localhost:8000/api/scheduler/history?limit=20'
```

### Filter by Status
```bash
# Only completed scans
curl 'http://localhost:8000/api/scheduler/history?status=completed'

# Only failed scans
curl 'http://localhost:8000/api/scheduler/history?status=failed'

# Only timeout scans
curl 'http://localhost:8000/api/scheduler/history?status=timeout'
```

### Check Scheduler Health
```bash
curl http://localhost:8000/api/scheduler/status
```

---

## Architecture

### Components

**1. SchedulerService** (`app/services/scheduler_service.py`)
- AsyncIOScheduler from APScheduler
- Memory job store (in-memory persistence)
- Execution history tracking
- Job management (add/remove/list)

**2. Scheduler API** (`app/api/scheduler.py`)
- REST endpoints for schedule management
- Pydantic models for validation
- OpenAPI/Swagger documentation

**3. FastAPI Integration** (`app/main.py`)
- Scheduler startup in `@app.on_event("startup")`
- Scheduler shutdown in `@app.on_event("shutdown")`
- Graceful lifecycle management

### Trigger Types

**Cron Trigger** (Daily/Weekly):
- `hour`, `minute`: Time of day
- `day_of_week`: Day for weekly scans
- Cron syntax support

**Interval Trigger** (Interval):
- `hours`: Fixed interval
- Repeats indefinitely
- Starts immediately

---

## Limitations

### Persistence
- Jobs stored in memory
- Lost on server restart
- Re-schedule required after restart

**Future Enhancement**: Persist to database or Redis

### Execution History
- Stored in memory (limited to last ~1000 executions)
- Lost on server restart

**Future Enhancement**: Store in database

### Timezone
- All times in UTC
- No timezone conversion

**Future Enhancement**: Support local timezone

---

## Troubleshooting

### Scheduler Not Starting
**Check**:
```bash
# Verify APScheduler installed
pip list | grep apscheduler

# Check startup logs
# Look for "✅ Maintenance scheduler started"
```

### Job Not Executing
**Check**:
```bash
# Verify job exists
curl http://localhost:8000/api/scheduler/jobs

# Check next_run_time
# If null, job may be paused or misconfigured
```

### Execution Failed
**Check**:
```bash
# View failure details
curl 'http://localhost:8000/api/scheduler/history?status=failed&limit=5'

# Check error field for details
```

---

## Best Practices

### 1. Stagger Schedules
Avoid scheduling multiple heavy scans at the same time:
```
Daily dependency scan: 02:00
Weekly comprehensive scan: 03:00 (Monday)
Performance check: 04:00
```

### 2. Use Appropriate Urgency
- `critical`: Only for security-critical scans
- `high`: Important but not emergency
- `medium`: Regular maintenance (default)
- `low`: Nice-to-have improvements

### 3. Monitor Execution History
Regularly check for:
- Failed executions
- Timeout executions
- Increasing execution times

### 4. Remove Unused Jobs
Clean up old schedules:
```bash
curl -X DELETE http://localhost:8000/api/scheduler/jobs/old_job_id
```

---

## Integration with MAINTENANCE Workflow

Periodic scans automatically trigger the full 6-stage Code-Maintenance-Agent workflow:

1. **Analysis** (Marcus): Scan for issues
2. **Prioritization** (Quinn): Risk × ROI scoring
3. **Planning** (Eliza): Task breakdown with actions
4. **Execution Strategy** (Marcus): Automated vs manual
5. **Test Strategy** (Tessa): Coverage planning
6. **Deployment Plan** (Marcus): Risk-based strategy

**Result**: Complete maintenance analysis with actionable tasks

---

## See Also

- [MAINTENANCE Work Type Documentation](./MAINTENANCE_WORK_TYPE.md)
- [Code-Maintenance-Agent Architecture](../WEEK_8_DAY_1_SUMMARY.md)
- [Action Breakdown System](../WEEK_8_DAY_5_ACTION_BREAKDOWN.md)

---

**Last Updated**: 2025-11-14
**Version**: 1.0.0
**Status**: ✅ Production Ready
