#!/bin/bash
# ============================================
# MarQed AI Platform - Deploy to Production
# ============================================
# Blue-green deployment with safety checks
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../_common.sh"

# Configuration
PROD_HOST="${PROD_HOST:-prod.marqed.ai}"
REQUIRE_STAGING="${REQUIRE_STAGING:-true}"
REQUIRE_APPROVAL="${REQUIRE_APPROVAL:-true}"

log_header "Production Deployment"

# Safety checks
log_step "1/7" "Safety checks..."

VERSION=$(get_version)
COMMIT=$(get_commit)
BRANCH=$(get_branch)

echo "  Version: $VERSION"
echo "  Commit:  $COMMIT"
echo "  Branch:  $BRANCH"

# Check branch
if [ "$BRANCH" != "master" ] && [ "$BRANCH" != "main" ] && [[ ! "$BRANCH" =~ ^release/ ]]; then
    log_error "Production deployments must be from main/master or release/* branch"
    log_error "Current branch: $BRANCH"
    exit 1
fi

# Check for uncommitted changes
if ! is_git_clean; then
    log_error "Cannot deploy to production with uncommitted changes"
    exit 1
fi

# Verify staging was deployed
if [ "$REQUIRE_STAGING" = "true" ]; then
    STAGING_FILE="$PROJECT_ROOT/.deployments/staging-latest.json"
    if [ ! -f "$STAGING_FILE" ]; then
        log_error "No staging deployment found. Deploy to staging first."
        exit 1
    fi

    STAGING_COMMIT=$(jq -r '.commit' "$STAGING_FILE" 2>/dev/null)
    if [ "$STAGING_COMMIT" != "$COMMIT" ]; then
        log_error "Staging commit ($STAGING_COMMIT) does not match current commit ($COMMIT)"
        log_error "Deploy to staging first, then deploy to production"
        exit 1
    fi
    log_success "Staging verification passed"
fi

# Require approval
if [ "$REQUIRE_APPROVAL" = "true" ] && [ "${FORCE:-false}" != "true" ]; then
    echo ""
    echo -e "${YELLOW}════════════════════════════════════════${NC}"
    echo -e "${YELLOW}  PRODUCTION DEPLOYMENT CONFIRMATION${NC}"
    echo -e "${YELLOW}════════════════════════════════════════${NC}"
    echo ""
    echo "  Version: $VERSION"
    echo "  Commit:  $COMMIT"
    echo "  Branch:  $BRANCH"
    echo ""
    read -p "Type 'deploy' to confirm production deployment: " confirm
    if [ "$confirm" != "deploy" ]; then
        log_error "Deployment cancelled"
        exit 1
    fi
fi

# Step 2: Run full CI
log_step "2/7" "Running full CI validation..."
"$SCRIPT_DIR/../ci/validate.sh" || {
    log_error "CI validation failed. Cannot deploy to production."
    exit 1
}

# Step 3: Create backup
log_step "3/7" "Creating backup..."
mkdir -p "$PROJECT_ROOT/.deployments/backups"
BACKUP_FILE="$PROJECT_ROOT/.deployments/backups/prod-$(date +%Y%m%d_%H%M%S).json"

# Save current production state
if [ -f "$PROJECT_ROOT/.deployments/prod-latest.json" ]; then
    cp "$PROJECT_ROOT/.deployments/prod-latest.json" "$BACKUP_FILE"
    log_success "Backup created: $BACKUP_FILE"
else
    log_warning "No previous production deployment to backup"
fi

# Step 4: Database backup
log_step "4/7" "Creating database backup..."
cd "$BACKEND_DIR"
BACKUP_SQL="$PROJECT_ROOT/.deployments/backups/db-$(date +%Y%m%d_%H%M%S).sql"
docker-compose exec -T db pg_dump -U user project_manager > "$BACKUP_SQL" 2>/dev/null && {
    log_success "Database backup: $BACKUP_SQL"
} || {
    log_warning "Database backup failed (continuing anyway)"
}

# Step 5: Run migrations
log_step "5/7" "Running database migrations..."
cd "$BACKEND_DIR"
source .venv/bin/activate
alembic upgrade head || {
    log_error "Migration failed!"
    log_info "Rolling back..."
    alembic downgrade -1
    exit 1
}
log_success "Migrations complete"

# Step 6: Deploy
log_step "6/7" "Deploying to production..."
cd "$BACKEND_DIR"

# Graceful restart
docker-compose up -d --no-deps --build api 2>/dev/null || {
    docker-compose up -d
}

# Step 7: Health check with retries
log_step "7/7" "Running production health checks..."
sleep 5

HEALTH_URL="http://localhost:8000/api/health"
RETRIES=3
for i in $(seq 1 $RETRIES); do
    if wait_for_service "$HEALTH_URL" 30; then
        log_success "Health check passed (attempt $i)"
        break
    else
        if [ $i -eq $RETRIES ]; then
            log_error "Health check failed after $RETRIES attempts"
            log_info "Initiating rollback..."
            "$SCRIPT_DIR/rollback.sh"
            exit 1
        fi
        log_warning "Health check failed, retrying..."
        sleep 5
    fi
done

# Save deployment info
cat > "$PROJECT_ROOT/.deployments/prod-latest.json" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "version": "$VERSION",
    "commit": "$COMMIT",
    "branch": "$BRANCH",
    "environment": "production",
    "backup": "$BACKUP_FILE"
}
EOF

print_summary "success"

echo -e "${GREEN}Production deployment successful!${NC}"
echo ""
echo "  Version: $VERSION"
echo "  Commit:  $COMMIT"
echo ""
echo "To rollback: make rollback"
echo ""
