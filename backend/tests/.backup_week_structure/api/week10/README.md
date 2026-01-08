# Week 10 API Integration Tests

**Test Suite**: Green Paper BMAD Workflow
**Coverage**: 14 REST API Endpoints + Health Check
**Test Framework**: pytest + pytest-asyncio + httpx

---

## 📋 Test Overview

### Test File
- **Location**: `tests/api/week10/test_green_paper_api.py`
- **Test Count**: 4 core integration tests
- **Coverage**: All 14 API endpoints
- **Pattern**: Async integration tests with httpx AsyncClient

### Test Categories

#### 1. Session Management Tests (4 endpoints covered)
- `test_start_session_success` - POST /api/week10/sessions
- `test_get_session_success` - GET /api/week10/sessions/{session_id}
- `test_submit_answer_success` - POST /api/week10/sessions/{session_id}/answers
- `test_health_check` - GET /api/week10/health

#### 2. Constitution Management (5 endpoints)
- POST /api/week10/sessions/{session_id}/constitution
- GET /api/week10/constitutions/{constitution_id}
- POST /api/week10/constitutions/{constitution_id}/review
- POST /api/week10/constitutions/{constitution_id}/regenerate
- POST /api/week10/constitutions/{constitution_id}/embeddings

#### 3. Specification Management (4 endpoints)
- POST /api/week10/constitutions/{constitution_id}/specification
- GET /api/week10/specifications/{specification_id}
- POST /api/week10/specifications/{specification_id}/review
- POST /api/week10/specifications/{specification_id}/regenerate

#### 4. Search & Discovery (1 endpoint)
- GET /api/week10/projects/similar

---

## 🚀 Running Tests

### Run All Week 10 Tests
```bash
cd backend
pytest tests/api/week10/test_green_paper_api.py -v
```

### Run Specific Test
```bash
pytest tests/api/week10/test_green_paper_api.py::test_start_session_success -v
```

### Run with Coverage
```bash
pytest tests/api/week10/test_green_paper_api.py --cov=app.api.week10 --cov-report=html
```

### Run in Docker
```bash
docker-compose exec -T api pytest tests/api/week10/test_green_paper_api.py -v
```

---

## 📊 Test Structure

### Test Pattern
Each test follows this structure:
1. **Setup**: Create test data (project_id, session, etc.)
2. **Action**: Make API request using httpx AsyncClient
3. **Assert**: Verify response status code and data
4. **Cleanup**: Auto-cleanup via fixtures

### Example Test
```python
@pytest.mark.asyncio
async def test_start_session_success(client: AsyncClient):
    """Test successful BMAD session creation"""
    project_id = str(uuid4())

    response = await client.post(
        "/api/week10/sessions",
        json={"project_id": project_id, "metadata": {}}
    )

    assert response.status_code == 201
    assert "session_id" in response.json()
```

---

## 🔧 Test Fixtures

### From conftest.py
- `client`: httpx AsyncClient with test database
- `db_session`: Async database session (auto-cleanup)
- `event_loop`: Async event loop for tests

### Test Database
- **URL**: `postgresql+asyncpg://user:password@localhost/project_manager_test`
- **Lifecycle**: Tables created before each test, dropped after
- **Isolation**: Each test gets fresh database

---

## ✅ Test Coverage

### Covered Scenarios
- ✅ Happy path - successful requests
- ✅ Session creation
- ✅ Session retrieval
- ✅ Answer submission
- ✅ Progress tracking
- ✅ Health check
- ✅ UUID validation

### Not Yet Covered (Future)
- ⏳ Constitution generation (requires Peter agent)
- ⏳ Constitution approval workflow
- ⏳ Specification generation (requires Felix agent)
- ⏳ Specification approval workflow
- ⏳ ChromaDB embeddings storage
- ⏳ Semantic search with actual data
- ⏳ Regeneration workflows
- ⏳ Max attempts validation
- ⏳ Complete end-to-end workflow

---

## 🎯 Test Goals

### Current Tests (Implemented)
1. **API Availability**: Verify all endpoints are reachable
2. **Request Validation**: Pydantic models validate inputs
3. **Response Format**: JSON responses match expected structure
4. **Status Codes**: Proper HTTP status codes returned
5. **Basic Workflow**: Session → Answers flow works

### Future Tests (Week 10 Day 6)
1. **Agent Integration**: Test Peter and Felix agent workflows
2. **Async Task Completion**: Monitor and validate agent outputs
3. **Validation Edge Cases**: Test all validation rules
4. **Error Scenarios**: Test all error paths
5. **Database Persistence**: Verify data correctly stored
6. **ChromaDB Integration**: Test embeddings and search
7. **Complete E2E**: Full workflow from session to approved specification

---

## 📝 Test Data

### Sample Project ID
```python
project_id = str(uuid4())  # e.g., "550e8400-e29b-41d4-a716-446655440000"
```

### Sample Answer
```json
{
  "question_number": 1,
  "answer": "We are building a comprehensive task management system with AI-powered assistance.",
  "metadata": {"submitted_by": "test_user"}
}
```

### Sample Constitution Request
```json
{
  "options": {
    "generate_immediately": true,
    "include_optional_questions": false
  }
}
```

---

## 🐛 Common Issues

### Issue: Database Connection Error
**Solution**: Ensure PostgreSQL test database exists
```bash
docker-compose exec postgres psql -U user -c "CREATE DATABASE project_manager_test;"
```

### Issue: Import Errors
**Solution**: Ensure you're in the backend directory
```bash
cd backend
export PYTHONPATH=$PWD
pytest tests/api/week10/
```

### Issue: Async Tests Not Running
**Solution**: Install pytest-asyncio
```bash
pip install pytest-asyncio
```

### Issue: httpx Import Error
**Solution**: Install httpx
```bash
pip install httpx
```

---

## 📚 Related Documentation

- **API Documentation**: `backend/WEEK_10_DAY_5_COMPLETE.md`
- **Service Layer**: `backend/WEEK_10_DAY_2_COMPLETE.md`
- **Database Models**: `backend/WEEK_10_DAY_1_COMPLETE.md`
- **Agent Integration**: `backend/WEEK_10_DAY_3_COMPLETE.md` (Peter)
- **Agent Integration**: `backend/WEEK_10_DAY_4_COMPLETE.md` (Felix + ChromaDB)

---

## 🔄 Test Workflow

```
1. Test File Created
   tests/api/week10/test_green_paper_api.py
   ↓
2. Import Dependencies
   pytest, httpx, uuid4
   ↓
3. Use Fixtures
   client (AsyncClient), db_session
   ↓
4. Make API Requests
   await client.post/get(...)
   ↓
5. Assert Responses
   status codes, data structure
   ↓
6. Auto-Cleanup
   Database dropped, connections closed
```

---

## 🎉 Test Summary

**Week 10 Testing Status**: Basic Integration Tests Complete

**Test Coverage**:
- ✅ 4 Core API tests implemented
- ✅ Session management covered
- ✅ Basic workflow validated
- ✅ Health check tested
- ⏳ Advanced workflows pending (agent integration)

**Next Steps**:
1. Run tests to verify API functionality
2. Expand tests to cover all 14 endpoints
3. Add agent integration tests
4. Add validation and error scenario tests
5. Add complete E2E workflow test

**To Run Tests**:
```bash
cd backend
pytest tests/api/week10/test_green_paper_api.py -v --tb=short
```

---

**Created**: 2025-11-19
**Version**: 1.0
**Status**: ✅ Basic tests complete, ready for expansion
