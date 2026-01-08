#!/bin/bash
# ============================================
# MarQed AI Platform - CI/CD Common Functions
# ============================================

# Colors
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export PURPLE='\033[0;35m'
export CYAN='\033[0;36m'
export NC='\033[0m'

# Paths
export SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
export BACKEND_DIR="$PROJECT_ROOT/backend"
export FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Logging functions
log_header() {
    echo -e "\n${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}\n"
}

log_step() {
    echo -e "${YELLOW}[$1]${NC} $2"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" >&2
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
check_requirements() {
    local missing=()

    for tool in "$@"; do
        if ! command_exists "$tool"; then
            missing+=("$tool")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing[*]}"
        return 1
    fi
    return 0
}

# Get current version from VERSION file or git
get_version() {
    if [ -f "$PROJECT_ROOT/VERSION" ]; then
        cat "$PROJECT_ROOT/VERSION"
    else
        git -C "$PROJECT_ROOT" describe --tags --always 2>/dev/null || echo "dev"
    fi
}

# Get current git branch
get_branch() {
    git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"
}

# Get current git commit hash (short)
get_commit() {
    git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown"
}

# Check if working directory is clean
is_git_clean() {
    [ -z "$(git -C "$PROJECT_ROOT" status --porcelain)" ]
}

# Wait for service to be ready
wait_for_service() {
    local url="$1"
    local max_attempts="${2:-30}"
    local attempt=1

    echo -n "Waiting for $url"
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo ""
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    echo ""
    return 1
}

# Run command with timeout
run_with_timeout() {
    local timeout="$1"
    shift
    timeout "$timeout" "$@"
}

# Backup file before modifying
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        cp "$file" "${file}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
}

# Load environment variables from file
load_env() {
    local env_file="${1:-.env}"
    if [ -f "$env_file" ]; then
        set -a
        source "$env_file"
        set +a
    fi
}

# Print summary
print_summary() {
    local status="$1"
    local duration="$2"

    echo ""
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    if [ "$status" = "success" ]; then
        echo -e "${GREEN}  ✅ COMPLETED SUCCESSFULLY${NC}"
    else
        echo -e "${RED}  ❌ FAILED${NC}"
    fi
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo ""
    echo "  Version:  $(get_version)"
    echo "  Branch:   $(get_branch)"
    echo "  Commit:   $(get_commit)"
    [ -n "$duration" ] && echo "  Duration: ${duration}s"
    echo ""
}
