# MarQed.ai Client Portal - Testing Guide

Dit document beschrijft de test setup voor het MarQed.ai Client Portal project.

## Test Types

### 1. Unit Tests
- **Doel**: Test individuele functies en componenten in isolatie
- **Tools**:
  - Backend: pytest
  - Frontend: Vitest + Testing Library
- **Locatie**:
  - Backend: `backend/tests/unit/`
  - Frontend: `frontend/src/**/*.test.tsx`

### 2. Story Tests (Component Tests)
- **Doel**: Visuele en interactie tests voor UI componenten
- **Tools**: Storybook + Test Runner
- **Locatie**: `frontend/src/**/*.stories.tsx`

### 3. Integration Tests
- **Doel**: Test interacties tussen componenten en systemen
- **Tools**:
  - Backend: pytest + httpx
  - Frontend: Vitest met MSW (Mock Service Worker)
- **Locatie**:
  - Backend: `backend/tests/integration/`

### 4. E2E Tests
- **Doel**: Test volledige user flows door de applicatie
- **Tools**: Playwright
- **Locatie**: `frontend/e2e/`

## Test Commando's

### Alle Tests Draaien

```bash
# Alle tests
./scripts/test-all.sh

# Met coverage rapporten
./scripts/test-all.sh --coverage
```

### Backend Tests

```bash
cd backend

# Alle backend tests
python -m pytest

# Alleen unit tests
python -m pytest tests/unit/

# Alleen integration tests
python -m pytest tests/integration/

# Met coverage
python -m pytest --cov=app --cov-report=html

# Specifieke test file
python -m pytest tests/test_tenant_isolation.py

# Verbose output
python -m pytest -v
```

Of via het script:
```bash
./scripts/test-backend.sh
./scripts/test-backend.sh unit
./scripts/test-backend.sh integration
./scripts/test-backend.sh --coverage
```

### Frontend Tests

```bash
cd frontend

# Unit tests
npm run test:unit
npm run test:unit:watch  # watch mode

# Met coverage
npm run test:coverage

# Storybook tests (start eerst Storybook)
npm run storybook
npm run test:storybook

# E2E tests met Playwright
npm run test:e2e
npm run test:e2e:ui      # interactive UI mode
npm run test:e2e:headed  # zichtbare browser
```

Of via het script:
```bash
./scripts/test-frontend.sh
./scripts/test-frontend.sh unit
./scripts/test-frontend.sh storybook
./scripts/test-frontend.sh e2e
./scripts/test-frontend.sh --watch
```

## Test Coverage Doelen

| Categorie | Doel |
|-----------|------|
| Statements | 80% |
| Branches | 80% |
| Functions | 80% |
| Lines | 80% |

## Test Database

Voor backend tests wordt een aparte test database gebruikt:
- Naam: `marqed_portal_test`
- URL: `postgresql+asyncpg://postgres:postgres@localhost:5432/marqed_portal_test`

Maak de database aan voordat je integration tests draait:
```sql
CREATE DATABASE marqed_portal_test;
```

## Mock Data

### Frontend (MSW Handlers)
API mocks zijn gedefinieerd in `frontend/src/test/mocks/handlers.ts`:
- `/api/auth/login` - Login simulatie
- `/api/auth/me` - Huidige gebruiker
- `/api/projects` - Project CRUD operaties
- `/api/health` - Health check

### Backend (Pytest Fixtures)
Fixtures zijn gedefinieerd in `backend/tests/conftest.py`:
- `test_tenant` - Test tenant organisatie
- `test_user` - Test gebruiker
- `test_tenant_user` - Koppeling tenant-user
- `auth_headers` - JWT auth headers

## CI/CD Integration

Tests kunnen in CI/CD pipelines draaien met:

```yaml
# Backend
- name: Run Backend Tests
  run: |
    cd marqed-portal/backend
    python -m pytest --cov=app --cov-report=xml

# Frontend Unit Tests
- name: Run Frontend Unit Tests
  run: |
    cd marqed-portal/frontend
    npm run test:coverage

# Frontend E2E Tests
- name: Run E2E Tests
  run: |
    cd marqed-portal/frontend
    npx playwright install --with-deps
    npm run test:e2e
```

## Troubleshooting

### Database Connection Errors
Zorg dat PostgreSQL draait en de test database bestaat:
```bash
pg_isready
createdb marqed_portal_test
```

### Playwright Browser Errors
Installeer browsers voor Playwright:
```bash
npx playwright install
```

### Storybook Test Timeout
Zorg dat Storybook draait op port 6006 voordat je tests draait:
```bash
npm run storybook &
sleep 10
npm run test:storybook
```

## Best Practices

1. **Schrijf tests voor elke nieuwe feature** - Coverage moet > 80% blijven
2. **Test tenant isolation** - Controleer altijd dat tenant A niet bij data van tenant B kan
3. **Gebruik meaningful test names** - `test_tenant_a_cannot_see_tenant_b_projects`
4. **Mock external services** - Gebruik MSW voor API mocking
5. **Test error cases** - Niet alleen happy path
6. **Run tests lokaal voor commit** - `./scripts/test-all.sh`
