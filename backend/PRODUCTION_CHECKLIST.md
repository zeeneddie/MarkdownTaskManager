# Production Deployment Checklist

**Last Updated:** 2025-11-13
**Status:** Development → Production Preparation

---

## 🔴 CRITICAL - Security

### Redis Authentication & Security
**Priority:** HIGH
**Status:** ⚠️ TODO

**Current Situation:**
- Redis is running without authentication in development
- Connection string: `redis://localhost:6379/0` (no password)

**Required for Production:**
1. **Enable Redis Authentication**
   ```bash
   # In /etc/redis/redis.conf:
   requirepass <strong-password-here>
   ```

2. **Update Connection String**
   ```python
   # In app/core/config.py:
   REDIS_URL: str = "redis://:password@localhost:6379/0"
   ```

3. **Use Environment Variables**
   ```bash
   # In .env:
   REDIS_PASSWORD=<strong-password>
   REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
   ```

4. **Network Security**
   - Bind Redis to `127.0.0.1` only (not 0.0.0.0)
   - Use firewall rules to restrict access
   - Consider TLS/SSL for Redis connections

5. **Celery Configuration**
   - Update broker URL with password
   - Update result backend URL with password
   - Test connection before deployment

**Testing:**
```bash
# Test Redis with auth
redis-cli -a <password> ping
# Should return: PONG

# Test Celery connection
celery -A app.celery_app inspect ping
```

**Related Files:**
- `backend/app/core/config.py` - Update REDIS_URL
- `backend/app/celery_app.py` - Uses settings.REDIS_URL
- `.env.production` - Set REDIS_PASSWORD

---

## 🔴 CRITICAL - Configuration

### Environment Variables
**Priority:** HIGH
**Status:** ⚠️ TODO

**Required .env Variables:**
```bash
# Application
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<generate-random-key>

# Database
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/project_manager
POSTGRES_PASSWORD=<strong-password>

# Redis
REDIS_URL=redis://:password@redis:6379/0
REDIS_PASSWORD=<strong-password>

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# API
API_V1_PREFIX=/api
CORS_ORIGINS=["https://yourdomain.com"]

# Logging
LOG_LEVEL=INFO
```

### Database Security
**Priority:** HIGH
- Change default database password
- Use SSL/TLS for database connections
- Set up database backup strategy
- Configure connection pooling limits

### API Security
**Priority:** HIGH
- Generate strong SECRET_KEY
- Configure CORS properly (no wildcards)
- Enable rate limiting
- Set up API key authentication
- Implement request validation

---

## 🟡 IMPORTANT - Infrastructure

### Docker Compose Production
**Priority:** MEDIUM
**Status:** ⚠️ TODO

Update `docker-compose.yml` for production:
```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "127.0.0.1:6379:6379"  # Bind to localhost only
    volumes:
      - redis_data:/data
    restart: unless-stopped

  celery_worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - REDIS_URL=${REDIS_URL}
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - redis
      - db
    restart: unless-stopped

volumes:
  redis_data:
```

### Monitoring & Logging
**Priority:** MEDIUM
- Set up application logging (structured logs)
- Configure Celery monitoring (Flower)
- Set up error tracking (Sentry)
- Configure metrics (Prometheus + Grafana)
- Set up uptime monitoring

### Backup Strategy
**Priority:** MEDIUM
- Automated PostgreSQL backups
- Redis persistence configuration (AOF + RDB)
- Backup rotation policy
- Disaster recovery plan

---

## 🟢 NICE TO HAVE - Performance

### Redis Optimization
- Configure maxmemory policy
- Enable persistence (AOF)
- Tune eviction policies
- Set up Redis replication (if needed)

### Celery Optimization
- Configure worker concurrency
- Set up task routing
- Configure result expiration
- Set up dead letter queues

### Database Optimization
- Create indexes for frequent queries
- Configure connection pooling
- Set up read replicas (if needed)
- Optimize slow queries

---

## 📋 Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Security scan completed
- [ ] Dependencies updated
- [ ] Documentation updated

### Infrastructure
- [ ] Redis authentication enabled
- [ ] Database password changed
- [ ] SSL/TLS certificates configured
- [ ] Firewall rules configured
- [ ] Backup strategy tested

### Configuration
- [ ] Environment variables set
- [ ] CORS origins configured
- [ ] Secrets rotated
- [ ] Logging configured
- [ ] Monitoring enabled

### Testing
- [ ] Load testing completed
- [ ] Security testing completed
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Rollback plan tested

---

## 🚀 Deployment Steps

### 1. Pre-Deployment (Day before)
- [ ] Code freeze
- [ ] Final tests
- [ ] Backup current production
- [ ] Prepare rollback plan

### 2. Deployment (Deployment day)
- [ ] Set maintenance mode
- [ ] Deploy new version
- [ ] Run database migrations
- [ ] Start services
- [ ] Health checks
- [ ] Smoke tests

### 3. Post-Deployment (After deployment)
- [ ] Monitor logs
- [ ] Check metrics
- [ ] Verify functionality
- [ ] Remove maintenance mode
- [ ] Notify stakeholders

---

## 📞 Emergency Contacts

**If something goes wrong:**
- Project Lead: Eddie
- DevOps: [TBD]
- On-call: [TBD]

**Rollback Command:**
```bash
# Rollback to previous version
docker-compose down
git checkout <previous-tag>
docker-compose up -d
```

---

## 📚 Related Documents

- [fasenplan.md](../fasenplan.md) - Week 13-16: Production preparation
- [HERSTART_PROJECT.md](../HERSTART_PROJECT.md) - System overview
- [LLM_CONFIGURATION.md](agents/LLM_CONFIGURATION.md) - Model setup

---

**Next Review:** Before Fase 4 (Week 13) - Production Preparation Sprint
