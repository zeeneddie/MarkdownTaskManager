#!/bin/bash
#
# Test Runner Script for Markdown Task Manager
# Usage: ./run-tests.sh [command]
#
# Commands:
#   install    - Install test dependencies and browsers
#   test       - Run all tests (headless)
#   headed     - Run tests with browser visible
#   debug      - Run tests in debug mode
#   ui         - Run tests in interactive UI mode
#   drill-down - Run only drill-down tests
#   report     - Show HTML test report
#   clean      - Clean test results
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$PROJECT_ROOT/tests"

# Functions
print_header() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed!"
        echo "Install Node.js: https://nodejs.org/"
        exit 1
    fi
    print_success "Node.js found: $(node --version)"

    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed!"
        exit 1
    fi
    print_success "npm found: $(npm --version)"

    # Check PostgreSQL
    if ! command -v pg_isready &> /dev/null; then
        print_error "PostgreSQL is not installed!"
        exit 1
    fi

    if ! pg_isready &> /dev/null; then
        print_error "PostgreSQL is not running!"
        echo "Start PostgreSQL: sudo systemctl start postgresql"
        exit 1
    fi
    print_success "PostgreSQL is running"
}

install_dependencies() {
    print_header "Installing Test Dependencies"

    cd "$TESTS_DIR"

    print_info "Installing npm packages..."
    npm install

    print_info "Installing Playwright browsers..."
    npx playwright install

    print_success "Dependencies installed successfully!"
}

run_tests() {
    print_header "Running E2E Tests"

    check_prerequisites

    cd "$TESTS_DIR"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_error "Dependencies not installed!"
        print_info "Run: ./run-tests.sh install"
        exit 1
    fi

    print_info "Starting tests..."
    npm test

    print_success "Tests completed!"
    print_info "View report: ./run-tests.sh report"
}

run_tests_headed() {
    print_header "Running Tests (Headed Mode)"
    check_prerequisites
    cd "$TESTS_DIR"
    npm run test:headed
}

run_tests_debug() {
    print_header "Running Tests (Debug Mode)"
    check_prerequisites
    cd "$TESTS_DIR"
    npm run test:debug
}

run_tests_ui() {
    print_header "Running Tests (UI Mode)"
    check_prerequisites
    cd "$TESTS_DIR"
    npm run test:ui
}

run_drill_down_tests() {
    print_header "Running Drill-Down Tests Only"
    check_prerequisites
    cd "$TESTS_DIR"
    npm run test:drill-down
}

show_report() {
    print_header "Opening Test Report"
    cd "$TESTS_DIR"

    if [ ! -d "test-results/html" ]; then
        print_error "No test results found!"
        print_info "Run tests first: ./run-tests.sh test"
        exit 1
    fi

    npm run test:report
}

clean_results() {
    print_header "Cleaning Test Results"
    cd "$TESTS_DIR"

    rm -rf test-results/
    rm -rf playwright-report/
    rm -rf screenshots/*.png

    print_success "Test results cleaned!"
}

show_help() {
    cat << EOF
Test Runner Script for Markdown Task Manager

Usage: ./run-tests.sh [command]

Commands:
  install       Install test dependencies and Playwright browsers
  test          Run all tests in headless mode (default)
  headed        Run tests with browser window visible
  debug         Run tests in debug mode (step through)
  ui            Run tests in interactive UI mode
  drill-down    Run only drill-down navigation tests
  report        Show HTML test report in browser
  clean         Clean test results and screenshots
  help          Show this help message

Examples:
  ./run-tests.sh install          # First time setup
  ./run-tests.sh test             # Run all tests
  ./run-tests.sh headed           # See browser while testing
  ./run-tests.sh drill-down       # Test only drill-down feature
  ./run-tests.sh report           # View last test results

For more info, see: tests/README.md
EOF
}

# Main script
main() {
    local command="${1:-test}"

    case "$command" in
        install)
            install_dependencies
            ;;
        test)
            run_tests
            ;;
        headed)
            run_tests_headed
            ;;
        debug)
            run_tests_debug
            ;;
        ui)
            run_tests_ui
            ;;
        drill-down)
            run_drill_down_tests
            ;;
        report)
            show_report
            ;;
        clean)
            clean_results
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"
