#!/usr/bin/env bash
#
# MarQed.ai Client Portal - Complete Test Suite Runner
#
# Usage:
#   ./scripts/test-all.sh              # Run all tests
#   ./scripts/test-all.sh --backend    # Run only backend tests
#   ./scripts/test-all.sh --frontend   # Run only frontend tests
#   ./scripts/test-all.sh --unit       # Run only unit tests
#   ./scripts/test-all.sh --integration # Run only integration tests
#   ./scripts/test-all.sh --e2e        # Run only e2e tests
#   ./scripts/test-all.sh --coverage   # Run with coverage reports
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
RUN_BACKEND=false
RUN_FRONTEND=false
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_E2E=false
WITH_COVERAGE=false

if [[ $# -eq 0 ]]; then
    # Default: run all
    RUN_BACKEND=true
    RUN_FRONTEND=true
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend)
            RUN_BACKEND=true
            shift
            ;;
        --frontend)
            RUN_FRONTEND=true
            shift
            ;;
        --unit)
            RUN_UNIT=true
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            shift
            ;;
        --e2e)
            RUN_E2E=true
            shift
            ;;
        --coverage)
            WITH_COVERAGE=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Results tracking
BACKEND_RESULT=0
FRONTEND_UNIT_RESULT=0
FRONTEND_STORYBOOK_RESULT=0
FRONTEND_E2E_RESULT=0

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  MarQed.ai Portal - Test Suite Runner  ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Backend Tests
run_backend_tests() {
    echo -e "${YELLOW}Running Backend Tests...${NC}"
    cd "$PROJECT_DIR/backend"

    local pytest_args=""

    if $RUN_UNIT && ! $RUN_INTEGRATION; then
        pytest_args="tests/unit"
    elif $RUN_INTEGRATION && ! $RUN_UNIT; then
        pytest_args="tests/integration"
    fi

    if $WITH_COVERAGE; then
        pytest_args="$pytest_args --cov=app --cov-report=html --cov-report=term-missing"
    fi

    if python -m pytest $pytest_args; then
        echo -e "${GREEN}Backend tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Backend tests failed!${NC}"
        return 1
    fi
}

# Frontend Unit Tests
run_frontend_unit_tests() {
    echo -e "${YELLOW}Running Frontend Unit Tests...${NC}"
    cd "$PROJECT_DIR/frontend"

    local vitest_args=""
    if $WITH_COVERAGE; then
        vitest_args="--coverage"
    fi

    if npm run test:unit -- $vitest_args; then
        echo -e "${GREEN}Frontend unit tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Frontend unit tests failed!${NC}"
        return 1
    fi
}

# Frontend Storybook Tests
run_storybook_tests() {
    echo -e "${YELLOW}Running Storybook Tests...${NC}"
    cd "$PROJECT_DIR/frontend"

    # Start Storybook in background if not running
    if ! curl -s http://localhost:6006 > /dev/null 2>&1; then
        echo "Starting Storybook..."
        npm run storybook &
        STORYBOOK_PID=$!
        sleep 10
    fi

    if npm run test:storybook; then
        echo -e "${GREEN}Storybook tests passed!${NC}"
        [[ -n "$STORYBOOK_PID" ]] && kill $STORYBOOK_PID 2>/dev/null || true
        return 0
    else
        echo -e "${RED}Storybook tests failed!${NC}"
        [[ -n "$STORYBOOK_PID" ]] && kill $STORYBOOK_PID 2>/dev/null || true
        return 1
    fi
}

# Frontend E2E Tests
run_e2e_tests() {
    echo -e "${YELLOW}Running E2E Tests...${NC}"
    cd "$PROJECT_DIR/frontend"

    if npm run test:e2e; then
        echo -e "${GREEN}E2E tests passed!${NC}"
        return 0
    else
        echo -e "${RED}E2E tests failed!${NC}"
        return 1
    fi
}

# Execute tests based on flags
if $RUN_BACKEND; then
    run_backend_tests || BACKEND_RESULT=1
    echo ""
fi

if $RUN_FRONTEND; then
    if $RUN_UNIT || [[ $RUN_UNIT == false && $RUN_INTEGRATION == false && $RUN_E2E == false ]]; then
        run_frontend_unit_tests || FRONTEND_UNIT_RESULT=1
        echo ""
    fi

    if ! $RUN_UNIT && ! $RUN_INTEGRATION && ! $RUN_E2E; then
        # Run Storybook tests only for full test run
        run_storybook_tests || FRONTEND_STORYBOOK_RESULT=1
        echo ""
    fi

    if $RUN_E2E || [[ $RUN_UNIT == false && $RUN_INTEGRATION == false && $RUN_E2E == false ]]; then
        run_e2e_tests || FRONTEND_E2E_RESULT=1
        echo ""
    fi
fi

# Summary
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}           Test Results Summary          ${NC}"
echo -e "${BLUE}=========================================${NC}"

print_result() {
    if [[ $2 -eq 0 ]]; then
        echo -e "${GREEN}[PASS]${NC} $1"
    else
        echo -e "${RED}[FAIL]${NC} $1"
    fi
}

if $RUN_BACKEND; then
    print_result "Backend Tests" $BACKEND_RESULT
fi

if $RUN_FRONTEND; then
    print_result "Frontend Unit Tests" $FRONTEND_UNIT_RESULT
    if [[ -z "$RUN_UNIT" || ! $RUN_UNIT ]]; then
        print_result "Storybook Tests" $FRONTEND_STORYBOOK_RESULT
    fi
    if [[ -z "$RUN_E2E" || ! $RUN_E2E ]] && [[ -z "$RUN_UNIT" || ! $RUN_UNIT ]]; then
        print_result "E2E Tests" $FRONTEND_E2E_RESULT
    fi
fi

# Exit with failure if any test failed
TOTAL_RESULT=$((BACKEND_RESULT + FRONTEND_UNIT_RESULT + FRONTEND_STORYBOOK_RESULT + FRONTEND_E2E_RESULT))
if [[ $TOTAL_RESULT -gt 0 ]]; then
    echo ""
    echo -e "${RED}Some tests failed. Please check the output above.${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
