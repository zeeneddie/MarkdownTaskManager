#!/bin/bash
# ============================================
# MarQed AI Platform - Test Reorganization
# ============================================
# Moves tests from week-based to service-based
# ============================================

set -e

BACKEND_DIR="/home/eddie/Projects/MarkdownTaskManager/backend"
TESTS_DIR="$BACKEND_DIR/tests"
BACKUP_DIR="$TESTS_DIR/.backup_week_structure"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[REORG]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Create new service-based directories
log "Creating service-based test directories..."

mkdir -p "$TESTS_DIR/unit/agents"
mkdir -p "$TESTS_DIR/unit/workflows"
mkdir -p "$TESTS_DIR/unit/extraction"
mkdir -p "$TESTS_DIR/unit/migration"
mkdir -p "$TESTS_DIR/unit/analysis"
mkdir -p "$TESTS_DIR/unit/quality"
mkdir -p "$TESTS_DIR/unit/observability"
mkdir -p "$TESTS_DIR/unit/council"
mkdir -p "$TESTS_DIR/unit/portal"
mkdir -p "$TESTS_DIR/unit/estimation"
mkdir -p "$TESTS_DIR/unit/integration"
mkdir -p "$TESTS_DIR/unit/data"
mkdir -p "$TESTS_DIR/unit/security"
mkdir -p "$TESTS_DIR/unit/evolution"
mkdir -p "$TESTS_DIR/unit/core"
mkdir -p "$TESTS_DIR/unit/providers"

mkdir -p "$TESTS_DIR/integration/api"
mkdir -p "$TESTS_DIR/integration/workflows"
mkdir -p "$TESTS_DIR/integration/database"

mkdir -p "$TESTS_DIR/e2e"

success "Created 20 service-based directories"

# Backup current structure
log "Creating backup of current structure..."
mkdir -p "$BACKUP_DIR"
cp -r "$TESTS_DIR/api" "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$TESTS_DIR/services" "$BACKUP_DIR/" 2>/dev/null || true
success "Backup created at $BACKUP_DIR"

echo ""
log "Directory structure created. Ready for file migration."
echo ""
echo "New structure:"
find "$TESTS_DIR/unit" -type d | sed 's|'"$TESTS_DIR"'|tests|'
echo ""
