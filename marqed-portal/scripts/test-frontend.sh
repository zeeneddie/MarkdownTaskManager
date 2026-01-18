#!/usr/bin/env bash
#
# MarQed.ai Client Portal - Frontend Test Runner
#
# Usage:
#   ./scripts/test-frontend.sh              # Run all frontend tests
#   ./scripts/test-frontend.sh unit         # Run only unit tests
#   ./scripts/test-frontend.sh storybook    # Run only Storybook tests
#   ./scripts/test-frontend.sh e2e          # Run only E2E tests
#   ./scripts/test-frontend.sh --coverage   # Run with coverage
#   ./scripts/test-frontend.sh --watch      # Run in watch mode
#   ./scripts/test-frontend.sh --ui         # Run E2E with UI
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")/frontend"

cd "$FRONTEND_DIR"

# Parse arguments
TEST_TYPE="all"
WITH_COVERAGE=false
WATCH_MODE=false
UI_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        unit)
            TEST_TYPE="unit"
            shift
            ;;
        storybook|stories)
            TEST_TYPE="storybook"
            shift
            ;;
        e2e|playwright)
            TEST_TYPE="e2e"
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
        --ui|-u)
            UI_MODE=true
            shift
            ;;
        --headed)
            HEADED_MODE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo ""
            echo "Usage: ./scripts/test-frontend.sh [test_type] [options]"
            echo ""
            echo "Test types:"
            echo "  unit       Run Vitest unit tests"
            echo "  storybook  Run Storybook component tests"
            echo "  e2e        Run Playwright E2E tests"
            echo "  all        Run all tests (default)"
            echo ""
            echo "Options:"
            echo "  --coverage, -c   Include coverage report (unit tests)"
            echo "  --watch, -w      Run in watch mode (unit tests)"
            echo "  --ui, -u         Open Playwright UI (e2e tests)"
            echo "  --headed         Run E2E tests in headed mode"
            exit 1
            ;;
    esac
done

run_unit_tests() {
    echo "Running unit tests..."
    if $WATCH_MODE; then
        npm run test:unit:watch
    elif $WITH_COVERAGE; then
        npm run test:coverage
    else
        npm run test:unit
    fi
}

run_storybook_tests() {
    echo "Running Storybook tests..."
    # Check if Storybook is running
    if ! curl -s http://localhost:6006 > /dev/null 2>&1; then
        echo "Starting Storybook server..."
        npm run storybook &
        STORYBOOK_PID=$!
        sleep 15
        trap "kill $STORYBOOK_PID 2>/dev/null" EXIT
    fi
    npm run test:storybook
}

run_e2e_tests() {
    echo "Running E2E tests..."
    if $UI_MODE; then
        npm run test:e2e:ui
    elif [[ "$HEADED_MODE" == "true" ]]; then
        npm run test:e2e:headed
    else
        npm run test:e2e
    fi
}

case $TEST_TYPE in
    unit)
        run_unit_tests
        ;;
    storybook)
        run_storybook_tests
        ;;
    e2e)
        run_e2e_tests
        ;;
    all)
        echo "========================================="
        echo "Running all frontend tests"
        echo "========================================="
        echo ""
        run_unit_tests
        echo ""
        echo "========================================="
        run_storybook_tests
        echo ""
        echo "========================================="
        run_e2e_tests
        ;;
esac
