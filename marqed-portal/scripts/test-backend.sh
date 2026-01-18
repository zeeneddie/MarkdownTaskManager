#!/usr/bin/env bash
#
# MarQed.ai Client Portal - Backend Test Runner
#
# Usage:
#   ./scripts/test-backend.sh              # Run all backend tests
#   ./scripts/test-backend.sh unit         # Run only unit tests
#   ./scripts/test-backend.sh integration  # Run only integration tests
#   ./scripts/test-backend.sh --coverage   # Run with coverage
#   ./scripts/test-backend.sh --watch      # Run in watch mode
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")/backend"

cd "$BACKEND_DIR"

# Parse arguments
TEST_TYPE=""
WITH_COVERAGE=false
WATCH_MODE=false
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        unit)
            TEST_TYPE="tests/unit"
            shift
            ;;
        integration)
            TEST_TYPE="tests/integration"
            shift
            ;;
        tenant)
            TEST_TYPE="tests/test_tenant_isolation.py"
            shift
            ;;
        auth)
            TEST_TYPE="tests/test_auth.py"
            shift
            ;;
        --coverage|-c)
            WITH_COVERAGE=true
            shift
            ;;
        --watch|-w)
            WATCH_MODE=true
            shift
            ;;
        --verbose|-v)
            EXTRA_ARGS="$EXTRA_ARGS -v"
            shift
            ;;
        --failed|-f)
            EXTRA_ARGS="$EXTRA_ARGS --lf"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo ""
            echo "Usage: ./scripts/test-backend.sh [test_type] [options]"
            echo ""
            echo "Test types:"
            echo "  unit         Run unit tests only"
            echo "  integration  Run integration tests only"
            echo "  tenant       Run tenant isolation tests"
            echo "  auth         Run authentication tests"
            echo ""
            echo "Options:"
            echo "  --coverage, -c   Include coverage report"
            echo "  --watch, -w      Run in watch mode (ptw)"
            echo "  --verbose, -v    Verbose output"
            echo "  --failed, -f     Run only previously failed tests"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="python -m pytest"

if $WITH_COVERAGE; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=html --cov-report=term-missing"
fi

PYTEST_CMD="$PYTEST_CMD $EXTRA_ARGS $TEST_TYPE"

echo "Running: $PYTEST_CMD"
echo ""

if $WATCH_MODE; then
    # Watch mode using pytest-watch
    ptw -- $PYTEST_CMD
else
    eval $PYTEST_CMD
fi
