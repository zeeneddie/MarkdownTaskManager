#!/bin/bash
# Test Runner with Detailed Logging
# Creates dated logs for tracking test progress over time

set -e

# Configuration
BACKEND_DIR="/home/eddie/Projects/MarkdownTaskManager/backend"
LOGS_DIR="${BACKEND_DIR}/tests/logs"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)

# Create log directories
mkdir -p "${LOGS_DIR}/detailed"
mkdir -p "${LOGS_DIR}/summaries"

# Log files
DETAILED_LOG="${LOGS_DIR}/detailed/${TIMESTAMP}_full.log"
SUMMARY_LOG="${LOGS_DIR}/summaries/${DATE}_summary.md"

echo "=============================================="
echo "  Test Runner with Logging"
echo "  Date: ${DATE}"
echo "  Time: $(date +%H:%M:%S)"
echo "=============================================="

# Check if database is running
echo ""
echo "Checking database status..."
cd "${BACKEND_DIR}"

if docker-compose ps db 2>/dev/null | grep -q "Up"; then
    echo "✅ Database is running"
else
    echo "🔄 Starting database..."
    docker-compose up -d db
    echo "⏳ Waiting for database to be ready..."
    sleep 5

    # Wait for PostgreSQL to be ready
    for i in {1..30}; do
        if pg_isready -h localhost -p 5433 -U user 2>/dev/null; then
            echo "✅ Database is ready"
            break
        fi
        echo "   Waiting... ($i/30)"
        sleep 1
    done
fi

# Activate virtual environment
source .venv/bin/activate

echo ""
echo "Running tests..."
echo "Detailed log: ${DETAILED_LOG}"
echo ""

# Run pytest and capture output
START_TIME=$(date +%s)

pytest tests/unit/ -v --tb=short 2>&1 | tee "${DETAILED_LOG}"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Parse results from log
PASSED=$(grep -c "PASSED" "${DETAILED_LOG}" 2>/dev/null || echo "0")
FAILED=$(grep -c "FAILED" "${DETAILED_LOG}" 2>/dev/null || echo "0")
ERRORS=$(grep -c "^ERROR" "${DETAILED_LOG}" 2>/dev/null || echo "0")
SKIPPED=$(grep -c "SKIPPED" "${DETAILED_LOG}" 2>/dev/null || echo "0")

TOTAL=$((PASSED + FAILED + ERRORS + SKIPPED))
if [ $TOTAL -gt 0 ]; then
    PASS_RATE=$(echo "scale=1; $PASSED * 100 / $TOTAL" | bc)
else
    PASS_RATE="0"
fi

# Extract summary line from pytest output
PYTEST_SUMMARY=$(tail -5 "${DETAILED_LOG}" | grep -E "passed|failed|error" | head -1)

# Get error categories
CONNECTION_ERRORS=$(grep -c "ConnectionRefusedError\|ConnectionError" "${DETAILED_LOG}" 2>/dev/null || echo "0")
ASYNC_ERRORS=$(grep -c "async\|AsyncClient" "${DETAILED_LOG}" 2>/dev/null || echo "0")

# Create/append to summary
{
    echo ""
    echo "---"
    echo ""
    echo "## Test Run: ${TIMESTAMP}"
    echo ""
    echo "### Results"
    echo ""
    echo "| Status | Count |"
    echo "|--------|-------|"
    echo "| ✅ Passed | ${PASSED} |"
    echo "| ❌ Failed | ${FAILED} |"
    echo "| 🔴 Errors | ${ERRORS} |"
    echo "| ⏭️ Skipped | ${SKIPPED} |"
    echo "| **Total** | **${TOTAL}** |"
    echo "| **Pass Rate** | **${PASS_RATE}%** |"
    echo ""
    echo "**Duration:** ${DURATION} seconds"
    echo ""
    echo "### Pytest Summary"
    echo "\`\`\`"
    echo "${PYTEST_SUMMARY}"
    echo "\`\`\`"
    echo ""
    echo "### Error Categories"
    echo ""
    echo "- Connection Errors: ${CONNECTION_ERRORS}"
    echo "- Async/Client Errors: ${ASYNC_ERRORS}"
    echo ""
    echo "### Failed Tests"
    echo ""
    echo "\`\`\`"
    grep "^FAILED\|^ERROR" "${DETAILED_LOG}" | head -50
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "${SUMMARY_LOG}"

# Create/update index
INDEX_FILE="${LOGS_DIR}/INDEX.md"
{
    echo "# Test Log Index"
    echo ""
    echo "Last updated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "## Latest Run"
    echo ""
    echo "| Metric | Value |"
    echo "|--------|-------|"
    echo "| Date | ${DATE} |"
    echo "| Passed | ${PASSED} |"
    echo "| Failed | ${FAILED} |"
    echo "| Errors | ${ERRORS} |"
    echo "| Pass Rate | ${PASS_RATE}% |"
    echo ""
    echo "## Summary Files"
    echo ""
    ls -la "${LOGS_DIR}/summaries/"*.md 2>/dev/null | awk '{print "- " $NF}' | sed 's|.*/||'
    echo ""
    echo "## Detailed Logs"
    echo ""
    ls -la "${LOGS_DIR}/detailed/"*.log 2>/dev/null | tail -10 | awk '{print "- " $NF}' | sed 's|.*/||'
} > "${INDEX_FILE}"

echo ""
echo "=============================================="
echo "  TEST RUN COMPLETE"
echo "=============================================="
echo ""
echo "| Status     | Count |"
echo "|------------|-------|"
echo "| ✅ Passed  | ${PASSED} |"
echo "| ❌ Failed  | ${FAILED} |"
echo "| 🔴 Errors  | ${ERRORS} |"
echo "| ⏭️ Skipped | ${SKIPPED} |"
echo "| Total      | ${TOTAL} |"
echo "| Pass Rate  | ${PASS_RATE}% |"
echo ""
echo "Duration: ${DURATION} seconds"
echo ""
echo "Logs saved to:"
echo "  - Detailed: ${DETAILED_LOG}"
echo "  - Summary:  ${SUMMARY_LOG}"
echo "  - Index:    ${INDEX_FILE}"
echo ""
