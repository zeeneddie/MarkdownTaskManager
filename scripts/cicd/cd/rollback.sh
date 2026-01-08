#!/bin/bash
# ============================================
# MarQed AI Platform - Rollback Deployment
# ============================================
# Rollback to previous deployment
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../_common.sh"

# Configuration
ENVIRONMENT="${1:-staging}"

log_header "Rollback: $ENVIRONMENT"

# Find backup file
BACKUP_DIR="$PROJECT_ROOT/.deployments/backups"
LATEST_FILE="$PROJECT_ROOT/.deployments/${ENVIRONMENT}-latest.json"

if [ ! -f "$LATEST_FILE" ]; then
    log_error "No deployment found for $ENVIRONMENT"
    exit 1
fi

# Get backup info from current deployment
BACKUP_FILE=$(jq -r '.backup // empty' "$LATEST_FILE" 2>/dev/null)
CURRENT_COMMIT=$(jq -r '.commit' "$LATEST_FILE" 2>/dev/null)

log_info "Current deployment: $CURRENT_COMMIT"

# Find previous backup
if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    # Find most recent backup
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/${ENVIRONMENT}-*.json 2>/dev/null | head -1)
fi

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    log_error "No backup found for rollback"
    log_info "Available backups:"
    ls -la "$BACKUP_DIR"/*.json 2>/dev/null || echo "  (none)"
    exit 1
fi

ROLLBACK_COMMIT=$(jq -r '.commit' "$BACKUP_FILE" 2>/dev/null)
ROLLBACK_VERSION=$(jq -r '.version' "$BACKUP_FILE" 2>/dev/null)

log_info "Rolling back to: $ROLLBACK_VERSION ($ROLLBACK_COMMIT)"

# Confirmation
if [ "${FORCE:-false}" != "true" ]; then
    echo ""
    read -p "Confirm rollback to $ROLLBACK_VERSION? [y/N]: " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        log_info "Rollback cancelled"
        exit 0
    fi
fi

# Step 1: Git checkout
log_step "1/4" "Checking out previous version..."
cd "$PROJECT_ROOT"

if git checkout "$ROLLBACK_COMMIT" 2>/dev/null; then
    log_success "Checked out $ROLLBACK_COMMIT"
else
    log_warning "Could not checkout commit, using current code"
fi

# Step 2: Database rollback (if applicable)
log_step "2/4" "Checking database state..."
cd "$BACKEND_DIR"

# Find corresponding SQL backup
DB_BACKUP=$(ls -t "$BACKUP_DIR"/db-*.sql 2>/dev/null | head -1)
if [ -n "$DB_BACKUP" ] && [ -f "$DB_BACKUP" ]; then
    echo "Database backup available: $DB_BACKUP"
    read -p "Restore database backup? [y/N]: " restore_db
    if [ "$restore_db" = "y" ] || [ "$restore_db" = "Y" ]; then
        log_info "Restoring database..."
        docker-compose exec -T db psql -U user -d project_manager < "$DB_BACKUP" && {
            log_success "Database restored"
        } || {
            log_warning "Database restore failed"
        }
    fi
else
    # Try alembic downgrade
    source .venv/bin/activate
    log_info "Running migration downgrade..."
    alembic downgrade -1 2>/dev/null || log_warning "Downgrade skipped"
fi

# Step 3: Restart services
log_step "3/4" "Restarting services..."
cd "$BACKEND_DIR"
docker-compose restart api 2>/dev/null || docker-compose up -d
log_success "Services restarted"

# Step 4: Health check
log_step "4/4" "Health check..."
sleep 5

if wait_for_service "http://localhost:8000/api/health" 30; then
    log_success "Rollback successful"
else
    log_error "Health check failed after rollback"
    exit 1
fi

# Update deployment file
cp "$BACKUP_FILE" "$LATEST_FILE"

print_summary "success"

echo "Rollback complete!"
echo ""
echo "  Rolled back to: $ROLLBACK_VERSION"
echo "  Commit: $ROLLBACK_COMMIT"
echo ""
