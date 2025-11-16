# Project Manager API Backend

FastAPI-based backend for the Markdown Task Manager project with PostgreSQL database.

## Features

- **Hierarchical Project Structure**: Epic → Feature → Story → Task
- **Sprint Management**: Plan and track sprints with velocity metrics
- **Authentication**: JWT-based authentication system
- **Automatic Aggregation**: Story points automatically aggregate up the hierarchy
- **RESTful API**: Full CRUD operations for all entities
- **Markdown Export**: Maintain markdown representation for compatibility
- **Async Operations**: Full async/await support for high performance
- **Database Migrations**: Alembic for schema version control
- **Comprehensive Testing**: pytest-based test suite

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic 2.5
- **Authentication**: python-jose (JWT)
- **Migrations**: Alembic 1.12
- **Testing**: pytest with pytest-asyncio

## Project Structure

```
backend/
├── alembic/                 # Database migrations
│   ├── versions/           # Migration files
│   └── env.py             # Alembic environment
├── app/
│   ├── api/               # API endpoints
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── epics.py      # Epic endpoints
│   │   ├── features.py   # Feature endpoints
│   │   ├── stories.py    # Story endpoints
│   │   ├── tasks.py      # Task endpoints
│   │   └── sprints.py    # Sprint endpoints
│   ├── crud/             # Database operations
│   │   ├── item.py       # Item CRUD operations
│   │   ├── sprint.py     # Sprint CRUD operations
│   │   └── user.py       # User CRUD operations
│   ├── models/           # SQLAlchemy models
│   │   ├── item.py       # Item model (Epic/Feature/Story/Task)
│   │   ├── sprint.py     # Sprint model
│   │   └── user.py       # User model
│   ├── schemas/          # Pydantic schemas
│   │   ├── auth.py       # Auth schemas
│   │   ├── epic.py       # Epic schemas
│   │   ├── feature.py    # Feature schemas
│   │   ├── story.py      # Story schemas
│   │   ├── task.py       # Task schemas
│   │   ├── sprint.py     # Sprint schemas
│   │   └── user.py       # User schemas
│   ├── utils/            # Utility functions
│   │   ├── auth.py       # Auth utilities (JWT, password hashing)
│   │   └── markdown.py   # Markdown generation utilities
│   ├── config.py         # Configuration management
│   ├── database.py       # Database connection setup
│   └── main.py          # FastAPI application
├── tests/                # Test suite
│   ├── conftest.py      # Test fixtures
│   ├── test_auth.py     # Auth tests
│   ├── test_epics.py    # Epic tests
│   └── test_sprints.py  # Sprint tests
├── .env.example         # Environment variables example
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile          # Docker image definition
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Quick Start

### Option 1: Docker (Recommended)

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Access API**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs
   - ReDoc: http://localhost:8000/api/redoc

### Option 2: Local Development

1. **Install PostgreSQL**:
   ```bash
   # Install PostgreSQL 15+
   sudo apt-get install postgresql-15
   ```

2. **Create database**:
   ```bash
   sudo -u postgres psql
   CREATE DATABASE project_manager;
   CREATE USER user WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE project_manager TO user;
   \q
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit DATABASE_URL in .env
   ```

5. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start server**:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (form data)
- `POST /api/auth/token` - Login (JSON)
- `GET /api/auth/me` - Get current user

### Epics

- `GET /api/epics/` - List all epics
- `POST /api/epics/` - Create epic
- `GET /api/epics/{epic_id}` - Get epic
- `PUT /api/epics/{epic_id}` - Update epic
- `DELETE /api/epics/{epic_id}` - Delete epic
- `GET /api/epics/{epic_id}/hierarchy` - Get epic with descendants

### Features

- `GET /api/features/?epic_id={epic_id}` - List features
- `POST /api/features/` - Create feature
- `GET /api/features/{feature_id}` - Get feature
- `PUT /api/features/{feature_id}` - Update feature
- `DELETE /api/features/{feature_id}` - Delete feature
- `POST /api/features/{feature_id}/move?new_epic_id={id}` - Move feature

### Stories

- `GET /api/stories/?feature_id={id}&sprint={name}` - List stories
- `POST /api/stories/` - Create story
- `GET /api/stories/{story_id}` - Get story
- `PUT /api/stories/{story_id}` - Update story
- `DELETE /api/stories/{story_id}` - Delete story
- `POST /api/stories/{story_id}/move?new_feature_id={id}` - Move story
- `POST /api/stories/{story_id}/assign-sprint?sprint_name={name}` - Assign to sprint
- `POST /api/stories/{story_id}/unassign-sprint` - Unassign from sprint

### Tasks

- `GET /api/tasks/?story_id={story_id}` - List tasks
- `POST /api/tasks/` - Create task
- `GET /api/tasks/{task_id}` - Get task
- `PUT /api/tasks/{task_id}` - Update task
- `DELETE /api/tasks/{task_id}` - Delete task
- `POST /api/tasks/{task_id}/move?new_story_id={id}` - Move task

### Sprints

- `GET /api/sprints/?status={status}` - List sprints
- `GET /api/sprints/active` - Get active sprint
- `POST /api/sprints/` - Create sprint
- `GET /api/sprints/{sprint_id}` - Get sprint
- `PUT /api/sprints/{sprint_id}` - Update sprint
- `DELETE /api/sprints/{sprint_id}` - Delete sprint
- `GET /api/sprints/{sprint_id}/with-stories` - Get sprint with stories
- `GET /api/sprints/{sprint_id}/velocity` - Get sprint velocity metrics
- `POST /api/sprints/{sprint_id}/start` - Start sprint
- `POST /api/sprints/{sprint_id}/complete` - Complete sprint

## Database Migrations

### Create new migration:
```bash
alembic revision --autogenerate -m "Description"
```

### Apply migrations:
```bash
alembic upgrade head
```

### Rollback migration:
```bash
alembic downgrade -1
```

### View migration history:
```bash
alembic history
```

## Testing

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_epics.py -v
```

## Configuration

Environment variables (see `.env.example`):

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key (generate with `openssl rand -hex 32`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT expiration (default: 30)
- `ALLOWED_ORIGINS` - CORS allowed origins

## Development

### Using Makefile:

```bash
make help          # Show available commands
make install       # Install dependencies
make dev           # Run development server
make test          # Run tests
make lint          # Run linting
make format        # Format code
make clean         # Clean cache files
make docker-build  # Build Docker images
make docker-up     # Start Docker containers
make docker-down   # Stop Docker containers
make migrate       # Run migrations
```

## Deployment

### Production Checklist:

1. ✅ Change `SECRET_KEY` to secure random value
2. ✅ Set `ENVIRONMENT=production` in .env
3. ✅ Update `ALLOWED_ORIGINS` with production URLs
4. ✅ Use strong PostgreSQL password
5. ✅ Run migrations: `alembic upgrade head`
6. ✅ Set up SSL/TLS for HTTPS
7. ✅ Configure firewall rules
8. ✅ Set up monitoring and logging
9. ✅ Configure backup strategy
10. ✅ Use reverse proxy (nginx/traefik)

### Docker Production:

```bash
# Build production image
docker build -t project-manager-api:latest .

# Run with production config
docker run -d \
  --name project-manager-api \
  -p 8000:8000 \
  --env-file .env.production \
  project-manager-api:latest
```

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Features in Detail

### Story Point Aggregation

Story points automatically aggregate from stories up through features and epics:

```
Epic (sp_total: 18, sp_completed: 5)
  └── Feature (sp_total: 13, sp_completed: 3)
      ├── Story 1 (sp: 5, status: COMPLETED)
      ├── Story 2 (sp: 3, status: IN_PROGRESS)
      └── Story 3 (sp: 5, status: BACKLOG)
```

### Sprint Velocity Tracking

Get detailed sprint metrics:
- Total/completed story points
- Stories count by status
- Days elapsed/remaining
- Velocity (SP per day)
- Predicted completion
- On-track status

### Markdown Export

All items maintain a `markdown_full` field with their markdown representation, enabling export back to .md files if needed.

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [repository URL]
- Email: support@example.com
