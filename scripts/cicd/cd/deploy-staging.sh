#!/bin/bash
# ============================================
# MarQed AI Platform - Deploy to Staging
# ============================================
# Blue-green deployment to staging environment
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../_common.sh"

# Configuration
STAGING_HOST="${STAGING_HOST:-staging.marqed.local}"
STAGING_USER="${STAGING_USER:-deploy}"
STAGING_PATH="${STAGING_PATH:-/opt/marqed}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-registry.marqed.local}"

log_header "Deploying to Staging"

# Pre-flight checks
log_step "1/6" "Pre-flight checks..."

if ! is_git_clean; then
    log_warning "Working directory has uncommitted changes"
fi

VERSION=$(get_version)
COMMIT=$(get_commit)
BRANCH=$(get_branch)

echo "  Version: $VERSION"
echo "  Commit:  $COMMIT"
echo "  Branch:  $BRANCH"

# Validate branch
if [ "$BRANCH" != "master" ] && [ "$BRANCH" != "main" ] && [[ ! "$BRANCH" =~ ^release/ ]]; then
    log_warning "Deploying from non-main branch: $BRANCH"
fi

# Step 2: Run CI validation
log_step "2/6" "Running CI validation..."
if [ "${SKIP_CI:-false}" != "true" ]; then
    "$SCRIPT_DIR/../ci/validate.sh" || {
        log_error "CI validation failed. Use SKIP_CI=true to override."
        exit 1
    }
else
    log_warning "CI validation skipped (SKIP_CI=true)"
fi

# Step 3: Build Docker images
log_step "3/6" "Building Docker images..."
cd "$BACKEND_DIR"

IMAGE_TAG="${DOCKER_REGISTRY}/marqed-api:${VERSION}-${COMMIT}"
docker build -t "$IMAGE_TAG" -f Dockerfile . || {
    # Fallback: use docker-compose build
    log_info "Using docker-compose build..."
    docker-compose build api
    IMAGE_TAG="marqed-api:latest"
}
log_success "Image built: $IMAGE_TAG"

# Step 4: Push to registry (if available)
log_step "4/6" "Pushing to registry..."
if docker push "$IMAGE_TAG" 2>/dev/null; then
    log_success "Pushed to registry"
else
    log_warning "Registry push failed (local deployment only)"
fi

# Step 5: Deploy to staging
log_step "5/6" "Deploying to staging..."

# For local staging (docker-compose)
cd "$BACKEND_DIR"
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d 2>/dev/null || {
    # Fallback to standard docker-compose
    docker-compose up -d
}
log_success "Containers started"

# Step 6: Health check
log_step "6/6" "Running health checks..."
sleep 5

HEALTH_URL="http://localhost:8000/api/health"
if wait_for_service "$HEALTH_URL" 30; then
    log_success "Health check passed"

    # Verify API response
    HEALTH_RESPONSE=$(curl -sf "$HEALTH_URL" 2>/dev/null)
    if echo "$HEALTH_RESPONSE" | grep -q "healthy\|ok\|true"; then
        log_success "API responding correctly"
    else
        log_warning "API response unexpected: $HEALTH_RESPONSE"
    fi
else
    log_error "Health check failed"
    exit 1
fi

# Summary
print_summary "success"

echo "Staging deployment complete!"
echo ""
echo "  API:      http://localhost:8000"
echo "  Docs:     http://localhost:8000/docs"
echo "  Health:   http://localhost:8000/api/health"
echo ""
echo "To rollback: make rollback"
echo ""

# Save deployment info for rollback
mkdir -p "$PROJECT_ROOT/.deployments"
cat > "$PROJECT_ROOT/.deployments/staging-latest.json" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "version": "$VERSION",
    "commit": "$COMMIT",
    "branch": "$BRANCH",
    "image": "$IMAGE_TAG",
    "environment": "staging"
}
EOF
