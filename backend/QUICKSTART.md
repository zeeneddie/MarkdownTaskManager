# Quick Start Guide

Get the Project Manager API running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- OR Python 3.11+ and PostgreSQL 15+

## Option 1: Docker (Easiest)

### 1. Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit `.env` and set a secure SECRET_KEY:
```bash
# Generate a secure secret key
openssl rand -hex 32
```

### 2. Start Everything

```bash
docker-compose up -d
```

That's it! The API is now running at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### 3. Test the API

Open http://localhost:8000/api/docs in your browser and try the endpoints!

### 4. View Logs

```bash
docker-compose logs -f api
```

### 5. Stop Services

```bash
docker-compose down
```

## Option 2: Local Development

### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql-15

# macOS
brew install postgresql@15
```

### 2. Create Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE project_manager;
CREATE USER pm_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE project_manager TO pm_user;
\q
```

### 3. Install Python Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql+asyncpg://pm_user:secure_password_here@localhost:5432/project_manager
SECRET_KEY=your-secret-key-from-openssl-rand-hex-32
```

### 5. Run Migrations

```bash
alembic upgrade head
```

### 6. Start Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access at http://localhost:8000/api/docs

## First Steps

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "admin123",
    "full_name": "Admin User"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Save the `access_token` from the response.

### 3. Create Your First Epic

```bash
curl -X POST http://localhost:8000/api/epics/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "title": "My First Epic",
    "status": "PLANNED",
    "priority": "HIGH",
    "owner": "Admin User",
    "description": "This is my first epic"
  }'
```

### 4. Create a Feature

```bash
curl -X POST http://localhost:8000/api/features/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "title": "User Authentication",
    "parent_id": "EPIC-001",
    "status": "PLANNED",
    "priority": "HIGH"
  }'
```

### 5. Create a Sprint

```bash
curl -X POST http://localhost:8000/api/sprints/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "Sprint 1",
    "start_date": "2025-11-12T00:00:00",
    "end_date": "2025-11-26T00:00:00",
    "goal": "Complete user authentication",
    "status": "PLANNED"
  }'
```

### 6. Create a Story

```bash
curl -X POST http://localhost:8000/api/stories/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "title": "User can login",
    "parent_id": "FEAT-001",
    "status": "BACKLOG",
    "priority": "HIGH",
    "sp": 5,
    "sprint": "Sprint 1"
  }'
```

## Common Commands

### Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f api

# Rebuild images
docker-compose build

# Run migrations in container
docker-compose exec api alembic upgrade head

# Access database
docker-compose exec db psql -U user -d project_manager
```

### Development Commands

```bash
# Start dev server
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Format code
black app/ tests/

# Lint code
flake8 app/ tests/
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

**Docker:**
```yaml
# Edit docker-compose.yml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

**Local:**
```bash
uvicorn app.main:app --reload --port 8001
```

### Database Connection Error

Check your DATABASE_URL in `.env`:
```env
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL=postgresql+asyncpg://pm_user:password@localhost:5432/project_manager
```

### Migration Errors

Reset database and run migrations:
```bash
# Drop and recreate database
sudo -u postgres psql
DROP DATABASE project_manager;
CREATE DATABASE project_manager;
\q

# Run migrations
alembic upgrade head
```

### Token Expired Error

Login again to get a new token:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

## Next Steps

1. ✅ Explore the interactive API docs: http://localhost:8000/api/docs
2. ✅ Read the full README: [README.md](README.md)
3. ✅ Learn about frontend integration: [API_INTEGRATION.md](API_INTEGRATION.md)
4. ✅ Set up your IDE with the project structure
5. ✅ Start building features!

## Need Help?

- **API Documentation**: http://localhost:8000/api/docs
- **Backend README**: [README.md](README.md)
- **Integration Guide**: [API_INTEGRATION.md](API_INTEGRATION.md)
- **GitHub Issues**: [Create an issue](https://github.com/your-repo/issues)

## Useful Links

- FastAPI Documentation: https://fastapi.tiangolo.com
- SQLAlchemy Documentation: https://docs.sqlalchemy.org
- Alembic Documentation: https://alembic.sqlalchemy.org
- Pydantic Documentation: https://docs.pydantic.dev

Happy coding! 🚀
