#!/bin/bash
# ============================================
# MarQed AI Platform - CI Validation Pipeline
# ============================================
# Runs: lint, type check, security scan, tests
# Exit codes: 0 = success, 1 = failure
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../_common.sh"

# Configuration
FAIL_FAST="${FAIL_FAST:-false}"
SKIP_LINT="${SKIP_LINT:-false}"
SKIP_TESTS="${SKIP_TESTS:-false}"
SKIP_SECURITY="${SKIP_SECURITY:-false}"

# Track failures
FAILURES=()
START_TIME=$(date +%s)

log_header "CI Validation Pipeline"
echo "Version: $(get_version)"
echo "Branch:  $(get_branch)"
echo "Commit:  $(get_commit)"
echo ""

# Step 1: Lint
if [ "$SKIP_LINT" != "true" ]; then
    log_step "1/4" "Running linters..."
    cd "$BACKEND_DIR"
    source .venv/bin/activate

    # Ruff (fast Python linter)
    if command_exists ruff; then
        if ruff check app/ --output-format=concise 2>/dev/null; then
            log_success "Ruff: passed"
        else
            log_error "Ruff: failed"
            FAILURES+=("ruff")
            [ "$FAIL_FAST" = "true" ] && exit 1
        fi
    else
        log_warning "Ruff not installed, skipping"
    fi

    # MyPy (type checking)
    if command_exists mypy; then
        if mypy app/ --ignore-missing-imports --no-error-summary 2>/dev/null; then
            log_success "MyPy: passed"
        else
            log_warning "MyPy: warnings found (non-blocking)"
        fi
    fi
else
    log_step "1/4" "Linting skipped (SKIP_LINT=true)"
fi

# Step 2: Security Scan
if [ "$SKIP_SECURITY" != "true" ]; then
    log_step "2/4" "Running security scans..."
    cd "$BACKEND_DIR"
    source .venv/bin/activate

    # Bandit (Python security linter)
    if command_exists bandit; then
        if bandit -r app/ -ll -q 2>/dev/null; then
            log_success "Bandit: passed"
        else
            log_error "Bandit: security issues found"
            FAILURES+=("bandit")
            [ "$FAIL_FAST" = "true" ] && exit 1
        fi
    else
        log_warning "Bandit not installed, skipping"
    fi

    # Safety (dependency vulnerability check)
    if command_exists safety; then
        if safety check -r requirements.txt --short-report 2>/dev/null; then
            log_success "Safety: no vulnerabilities"
        else
            log_warning "Safety: vulnerabilities found (review required)"
        fi
    fi
else
    log_step "2/4" "Security scan skipped (SKIP_SECURITY=true)"
fi

# Step 3: Unit Tests
if [ "$SKIP_TESTS" != "true" ]; then
    log_step "3/4" "Running unit tests..."
    cd "$BACKEND_DIR"
    source .venv/bin/activate

    if python -m pytest tests/ -v --tb=short -q 2>/dev/null; then
        log_success "Tests: passed"
    else
        log_error "Tests: failed"
        FAILURES+=("tests")
        [ "$FAIL_FAST" = "true" ] && exit 1
    fi
else
    log_step "3/4" "Tests skipped (SKIP_TESTS=true)"
fi

# Step 4: Build Check
log_step "4/4" "Verifying build..."
cd "$BACKEND_DIR"

# Check if main app can be imported
if python -c "from app.main import app; print('App loaded')" 2>/dev/null; then
    log_success "Build: verified"
else
    log_error "Build: failed to load app"
    FAILURES+=("build")
fi

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Summary
if [ ${#FAILURES[@]} -eq 0 ]; then
    print_summary "success" "$DURATION"
    exit 0
else
    log_error "Failed checks: ${FAILURES[*]}"
    print_summary "failed" "$DURATION"
    exit 1
fi
