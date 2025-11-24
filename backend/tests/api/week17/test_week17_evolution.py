"""
Week 17 Evolution & Validation Tests

Tests for Week 17 functionality:
- Agent Evolution API
- Experience Store
- Validation Pipeline
- Self-Navigating (Guidance)
- Self-Questioning (Learning Tasks)
- Self-Attributing (Outcome Analysis)

Run with: pytest tests/api/week17/test_week17_evolution.py -v
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from datetime import datetime


# Valid enum values for testing
AGENT_ROLES = {
    "felix": "Feature Architect",
    "marcus": "Maintenance Specialist",
    "quinn": "Quality Inspector",
    "betty": "Bug Hunter",
    "eliza": "Estimation Engine",
    "tessa": "Test Engineer",
    "miguel": "Migration Architect",
    "diana": "Documentation Writer",
    "peter": "Product Owner",
    "paul": "Project Lead"
}

WORK_TYPES = {
    "new_feature": "NEW_FEATURE",
    "maintenance": "MAINTENANCE",
    "bug": "BUG",
    "quality_audit": "QUALITY_AUDIT",
    "enhancement": "ENHANCEMENT",
    "migration": "MIGRATION",
    "quality_improvement": "QUALITY_IMPROVEMENT",
    "testing": "TESTING",
    "project_definition": "PROJECT_DEFINITION"
}


@pytest.fixture
async def client():
    """Create test client without database dependency"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

class TestEvolutionHealth:
    """Test Evolution service health endpoint"""

    @pytest.mark.asyncio
    async def test_evolution_health(self, client: AsyncClient):
        """Test evolution service health check"""
        response = await client.get("/api/evolution/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "timestamp" in data

        # Check service statuses
        services = data["services"]
        assert "experience_store" in services
        assert "evolution_service" in services
        assert "validation_pipeline" in services


# ============================================================================
# EXPERIENCE MANAGEMENT TESTS
# ============================================================================

class TestExperienceManagement:
    """Test Experience CRUD operations"""

    @pytest.mark.asyncio
    async def test_add_experience(self, client: AsyncClient):
        """Test adding a new experience"""
        experience_data = {
            "agent_id": "felix-001",
            "agent_role": AGENT_ROLES["felix"],
            "work_type": WORK_TYPES["new_feature"],
            "task_description": "Design user authentication system",
            "approach": "Implemented OAuth2 with JWT tokens",
            "outcome": "success",
            "lessons_learned": [
                "JWT expiration should be configurable",
                "Refresh tokens improve UX"
            ],
            "key_decisions": [
                {"decision": "Use OAuth2", "reason": "Industry standard"},
                {"decision": "JWT for sessions", "reason": "Stateless"}
            ],
            "duration": 7200,
            "quality_score": 0.85,
            "metadata": {"complexity": "high"}
        }

        response = await client.post("/api/evolution/experiences", json=experience_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["agent_id"] == "felix-001"
        assert data["agent_role"] == AGENT_ROLES["felix"]
        assert data["work_type"] == WORK_TYPES["new_feature"]
        assert data["outcome"] == "success"
        assert data["quality_score"] == 0.85
        assert len(data["lessons_learned"]) == 2

    @pytest.mark.asyncio
    async def test_search_similar_experiences(self, client: AsyncClient):
        """Test searching for similar experiences"""
        # First add an experience
        experience_data = {
            "agent_id": "felix-002",
            "agent_role": AGENT_ROLES["felix"],
            "work_type": WORK_TYPES["new_feature"],
            "task_description": "Build REST API for user management",
            "approach": "FastAPI with Pydantic models",
            "outcome": "success",
            "lessons_learned": ["Schema validation is crucial"],
            "key_decisions": [],
            "duration": 3600,
            "quality_score": 0.9,
            "metadata": {}
        }
        await client.post("/api/evolution/experiences", json=experience_data)

        # Search for similar
        response = await client.post(
            "/api/evolution/experiences/search",
            params={
                "task_description": "Create API for user management",
                "agent_role": AGENT_ROLES["felix"],
                "limit": 5
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "experiences" in data
        assert "query" in data
        assert "count" in data
        assert data["query"] == "Create API for user management"


# ============================================================================
# PATTERN MANAGEMENT TESTS
# ============================================================================

class TestPatternManagement:
    """Test Successful Pattern CRUD operations"""

    @pytest.mark.asyncio
    async def test_add_pattern(self, client: AsyncClient):
        """Test adding a successful pattern"""
        pattern_data = {
            "pattern_name": "API-First Design",
            "agent_role": AGENT_ROLES["felix"],
            "work_types": [WORK_TYPES["new_feature"], WORK_TYPES["enhancement"]],
            "context_keywords": ["api", "rest", "design"],
            "description": "Design API contracts before implementation",
            "steps": [
                "Define OpenAPI spec",
                "Review with stakeholders",
                "Generate client SDKs",
                "Implement server"
            ],
            "success_criteria": [
                "API spec approved",
                "No breaking changes needed"
            ],
            "times_used": 5,
            "success_rate": 0.95,
            "metadata": {}
        }

        response = await client.post("/api/evolution/patterns", json=pattern_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["pattern_name"] == "API-First Design"
        assert data["success_rate"] == 0.95
        assert len(data["steps"]) == 4

    @pytest.mark.asyncio
    async def test_search_applicable_patterns(self, client: AsyncClient):
        """Test searching for applicable patterns"""
        response = await client.post(
            "/api/evolution/patterns/search",
            params={
                "context": "Building new REST API",
                "work_type": WORK_TYPES["new_feature"],
                "limit": 3
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "patterns" in data
        assert "count" in data


# ============================================================================
# FAILURE ANALYSIS TESTS
# ============================================================================

class TestFailureAnalysis:
    """Test Failure Analysis CRUD operations"""

    @pytest.mark.asyncio
    async def test_add_failure_analysis(self, client: AsyncClient):
        """Test adding a failure analysis"""
        failure_data = {
            "agent_id": "betty-001",
            "agent_role": AGENT_ROLES["betty"],
            "work_type": WORK_TYPES["bug"],
            "task_description": "Fix null pointer exception in user service",
            "failure_point": "User lookup returns null for inactive users",
            "root_cause": "Missing null check after database query",
            "attempted_fixes": [
                "Added try-catch (didn't solve root cause)",
                "Added null check before access"
            ],
            "resolution": "Added explicit null check with proper error handling",
            "preventive_measures": [
                "Add null safety to all DB queries",
                "Add unit tests for edge cases"
            ],
            "severity": "high",
            "metadata": {}
        }

        response = await client.post("/api/evolution/failures", json=failure_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["agent_role"] == AGENT_ROLES["betty"]
        assert data["severity"] == "high"
        assert data["resolution"] is not None

    @pytest.mark.asyncio
    async def test_search_similar_failures(self, client: AsyncClient):
        """Test searching for similar failures"""
        response = await client.post(
            "/api/evolution/failures/search",
            params={
                "root_cause": "null pointer",
                "agent_role": AGENT_ROLES["betty"],
                "limit": 5
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "failures" in data
        assert "count" in data


# ============================================================================
# GUIDANCE TESTS (SELF-NAVIGATING)
# ============================================================================

class TestGuidance:
    """Test Self-Navigating guidance endpoints"""

    @pytest.mark.asyncio
    async def test_get_guidance(self, client: AsyncClient):
        """Test getting guidance for a task"""
        guidance_request = {
            "agent_id": "felix-001",
            "agent_role": AGENT_ROLES["felix"],
            "work_type": WORK_TYPES["new_feature"],
            "task_description": "Implement user registration with email verification",
            "constraints": ["Must use existing email service", "24h timeout"],
            "goals": ["Secure registration", "Good UX"],
            "available_resources": ["email_service", "user_database"]
        }

        response = await client.post("/api/evolution/guidance", json=guidance_request)
        assert response.status_code == 200

        data = response.json()
        assert "confidence" in data
        assert "recommended_approach" in data
        assert "relevant_patterns" in data
        assert "warnings" in data
        assert "estimated_duration" in data
        assert "success_probability" in data

        # Confidence should be a float between 0 and 1
        assert 0 <= data["confidence"] <= 1
        assert 0 <= data["success_probability"] <= 1


# ============================================================================
# LEARNING TASKS TESTS (SELF-QUESTIONING)
# ============================================================================

class TestLearningTasks:
    """Test Self-Questioning learning task generation"""

    @pytest.mark.asyncio
    async def test_generate_learning_tasks(self, client: AsyncClient):
        """Test generating learning tasks for an agent"""
        request_data = {
            "agent_id": "quinn-001",
            "agent_role": AGENT_ROLES["quinn"],
            "max_tasks": 5
        }

        response = await client.post("/api/evolution/learning-tasks", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Should return some learning tasks (may be 0 if no gaps identified)
        for task in data:
            assert "task_id" in task
            assert "task_type" in task
            assert "description" in task
            assert "priority" in task


# ============================================================================
# OUTCOME ANALYSIS TESTS (SELF-ATTRIBUTING)
# ============================================================================

class TestOutcomeAnalysis:
    """Test Self-Attributing outcome analysis"""

    @pytest.mark.asyncio
    async def test_analyze_outcome(self, client: AsyncClient):
        """Test analyzing task outcome"""
        analysis_request = {
            "agent_id": "marcus-001",
            "agent_role": AGENT_ROLES["marcus"],
            "task_id": "task-123",
            "steps_taken": [
                {"step": "Analyzed codebase", "duration": 300, "success": True},
                {"step": "Identified tech debt", "duration": 600, "success": True},
                {"step": "Created refactoring plan", "duration": 400, "success": True},
                {"step": "Executed refactoring", "duration": 1800, "success": True}
            ],
            "outcome": "success",
            "quality_score": 0.88,
            "duration": 3100
        }

        response = await client.post("/api/evolution/analyze-outcome", json=analysis_request)
        assert response.status_code == 200

        data = response.json()
        assert "task_id" in data
        assert "critical_steps" in data
        assert "success_factors" in data
        assert "improvement_areas" in data
        assert "overall_score" in data
        assert "recommendations" in data

        assert data["task_id"] == "task-123"
        assert 0 <= data["overall_score"] <= 1


# ============================================================================
# PERFORMANCE METRICS TESTS
# ============================================================================

class TestPerformanceMetrics:
    """Test Performance Metrics endpoints"""

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, client: AsyncClient):
        """Test getting performance metrics for an agent"""
        response = await client.get(
            "/api/evolution/metrics/felix-001",
            params={"agent_role": AGENT_ROLES["felix"], "days": 30}
        )
        assert response.status_code == 200

        data = response.json()
        assert "agent_id" in data
        assert "agent_role" in data
        assert "period_days" in data
        assert "total_tasks" in data
        assert "success_rate" in data
        assert "average_quality" in data
        assert "improvement_trend" in data
        assert "top_strengths" in data
        assert "improvement_areas" in data

        # Validate ranges
        assert 0 <= data["success_rate"] <= 1
        assert 0 <= data["average_quality"] <= 1

    @pytest.mark.asyncio
    async def test_adapt_evolution_config(self, client: AsyncClient):
        """Test adapting evolution config based on performance"""
        response = await client.post(
            "/api/evolution/config/adapt",
            params={"agent_id": "felix-001", "agent_role": AGENT_ROLES["felix"]}
        )
        assert response.status_code == 200

        data = response.json()
        assert "agent_id" in data
        assert "adapted_config" in data

        config = data["adapted_config"]
        assert "learning_rate" in config
        assert "experience_weight" in config
        assert "exploration_rate" in config

        # Validate config ranges
        assert 0 < config["learning_rate"] <= 1
        assert 0 < config["experience_weight"] <= 1
        assert 0 <= config["exploration_rate"] <= 1


# ============================================================================
# ESTIMATION ACCURACY TESTS
# ============================================================================

class TestEstimationAccuracy:
    """Test Estimation Accuracy tracking"""

    @pytest.mark.asyncio
    async def test_add_estimation_accuracy(self, client: AsyncClient):
        """Test recording estimation accuracy"""
        response = await client.post(
            "/api/evolution/estimation-accuracy",
            params={
                "agent_id": "eliza-001",
                "agent_role": AGENT_ROLES["eliza"],
                "work_type": WORK_TYPES["new_feature"],
                "task_id": "task-456",
                "estimated_hours": 8.0,
                "actual_hours": 10.0,
                "estimation_method": "function_points"
            }
        )
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert "accuracy_ratio" in data
        # Accuracy ratio = actual/estimated = 10/8 = 1.25
        assert data["accuracy_ratio"] == 1.25

    @pytest.mark.asyncio
    async def test_get_estimation_stats(self, client: AsyncClient):
        """Test getting estimation statistics"""
        response = await client.get(
            "/api/evolution/estimation-stats/eliza-001",
            params={"days": 90}
        )
        assert response.status_code == 200

        data = response.json()
        # Stats should contain aggregated metrics
        assert isinstance(data, dict)


# ============================================================================
# QUALITY METRICS TESTS
# ============================================================================

class TestQualityMetrics:
    """Test Quality Metrics tracking"""

    @pytest.mark.asyncio
    async def test_add_quality_metrics(self, client: AsyncClient):
        """Test recording quality metrics"""
        response = await client.post(
            "/api/evolution/quality-metrics",
            params={
                "agent_id": "quinn-001",
                "agent_role": AGENT_ROLES["quinn"],
                "work_type": WORK_TYPES["quality_audit"],
                "task_id": "task-789",
                "code_quality_score": 0.85,
                "test_coverage": 0.82,
                "security_score": 0.90,
                "documentation_score": 0.75,
                "maintainability_score": 0.80,
                "issues_found": 12,
                "issues_fixed": 10
            }
        )
        assert response.status_code == 201

        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_quality_trend(self, client: AsyncClient):
        """Test getting quality metrics trend"""
        response = await client.get(
            "/api/evolution/quality-trend/quinn-001",
            params={"days": 90}
        )
        assert response.status_code == 200

        data = response.json()
        # Trend should contain historical metrics
        assert isinstance(data, dict)


# ============================================================================
# VALIDATION PIPELINE TESTS
# ============================================================================

class TestValidationPipeline:
    """Test Validation Pipeline endpoints"""

    @pytest.mark.asyncio
    async def test_quick_lint_python(self, client: AsyncClient):
        """Test quick lint for Python code"""
        python_code = '''
def hello_world():
    print("Hello, World!")
    return True
'''
        response = await client.post(
            "/api/evolution/api/validation/lint",
            params={"code": python_code, "language": "python"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "phase" in data
        assert "passed" in data
        assert "errors" in data
        assert "warnings" in data
        assert data["phase"] == "linting"

    @pytest.mark.asyncio
    async def test_quick_lint_typescript(self, client: AsyncClient):
        """Test quick lint for TypeScript code"""
        ts_code = '''
function helloWorld(): string {
    return "Hello, World!";
}
'''
        response = await client.post(
            "/api/evolution/api/validation/lint",
            params={"code": ts_code, "language": "typescript"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "phase" in data
        assert data["phase"] == "linting"

    @pytest.mark.asyncio
    async def test_run_validation_pipeline(self, client: AsyncClient):
        """Test running full validation pipeline"""
        python_code = '''
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def test_add():
    assert add(2, 3) == 5
'''
        validation_request = {
            "code": python_code,
            "language": "python",
            "phases": ["linting", "type_check", "style"],
            "max_iterations": 1,
            "stop_on_first_failure": False
        }

        response = await client.post("/api/evolution/api/validation/run", json=validation_request)
        assert response.status_code == 200

        data = response.json()
        assert "overall_passed" in data
        assert "phases_run" in data
        assert "phase_results" in data
        assert "total_errors" in data
        assert "total_warnings" in data
        assert "total_duration" in data

        # Check phase results structure
        for result in data["phase_results"]:
            assert "phase" in result
            assert "passed" in result
            assert "errors" in result
            assert "duration" in result

    @pytest.mark.asyncio
    async def test_iterate_until_valid(self, client: AsyncClient):
        """Test iterate until valid endpoint"""
        # Code with minor style issues
        python_code = '''
def greet(name):
    return f"Hello, {name}!"
'''
        iterate_request = {
            "code": python_code,
            "language": "python",
            "max_iterations": 3
        }

        response = await client.post("/api/evolution/api/validation/iterate", json=iterate_request)
        assert response.status_code == 200

        data = response.json()
        assert "final_code" in data
        assert "is_valid" in data
        assert "iterations_used" in data
        assert "validation_result" in data

        # Should complete within max iterations
        assert data["iterations_used"] <= 3


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling for Evolution API"""

    @pytest.mark.asyncio
    async def test_invalid_agent_role(self, client: AsyncClient):
        """Test error handling for invalid agent role"""
        experience_data = {
            "agent_id": "test-001",
            "agent_role": "invalid_role",  # Invalid
            "work_type": WORK_TYPES["new_feature"],
            "task_description": "Test task",
            "approach": "Test approach",
            "outcome": "success",
            "lessons_learned": [],
            "key_decisions": [],
            "duration": 100,
            "quality_score": 0.5,
            "metadata": {}
        }

        response = await client.post("/api/evolution/experiences", json=experience_data)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_work_type(self, client: AsyncClient):
        """Test error handling for invalid work type"""
        experience_data = {
            "agent_id": "test-001",
            "agent_role": AGENT_ROLES["felix"],
            "work_type": "invalid_work",  # Invalid
            "task_description": "Test task",
            "approach": "Test approach",
            "outcome": "success",
            "lessons_learned": [],
            "key_decisions": [],
            "duration": 100,
            "quality_score": 0.5,
            "metadata": {}
        }

        response = await client.post("/api/evolution/experiences", json=experience_data)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_quality_score(self, client: AsyncClient):
        """Test error handling for out of range quality score"""
        experience_data = {
            "agent_id": "test-001",
            "agent_role": AGENT_ROLES["felix"],
            "work_type": WORK_TYPES["new_feature"],
            "task_description": "Test task",
            "approach": "Test approach",
            "outcome": "success",
            "lessons_learned": [],
            "key_decisions": [],
            "duration": 100,
            "quality_score": 1.5,  # Out of range
            "metadata": {}
        }

        response = await client.post("/api/evolution/experiences", json=experience_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_invalid_language_validation(self, client: AsyncClient):
        """Test error handling for invalid language in validation"""
        response = await client.post(
            "/api/evolution/api/validation/lint",
            params={"code": "print('test')", "language": "cobol"}  # Invalid
        )
        assert response.status_code == 400


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEvolutionIntegration:
    """Integration tests for Evolution workflow"""

    @pytest.mark.asyncio
    async def test_full_evolution_cycle(self, client: AsyncClient):
        """Test full evolution cycle: guidance -> task -> outcome -> learning"""
        # 1. Get guidance for a task
        guidance_response = await client.post(
            "/api/evolution/guidance",
            json={
                "agent_id": "felix-integration",
                "agent_role": AGENT_ROLES["felix"],
                "work_type": WORK_TYPES["new_feature"],
                "task_description": "Build notification system",
                "constraints": [],
                "goals": ["Real-time notifications"],
                "available_resources": []
            }
        )
        assert guidance_response.status_code == 200
        guidance = guidance_response.json()

        # 2. Record the experience
        experience_response = await client.post(
            "/api/evolution/experiences",
            json={
                "agent_id": "felix-integration",
                "agent_role": AGENT_ROLES["felix"],
                "work_type": WORK_TYPES["new_feature"],
                "task_description": "Build notification system",
                "approach": guidance["recommended_approach"],
                "outcome": "success",
                "lessons_learned": ["WebSocket is good for real-time"],
                "key_decisions": [],
                "duration": 5400,
                "quality_score": 0.9,
                "metadata": {}
            }
        )
        assert experience_response.status_code == 201
        experience = experience_response.json()

        # 3. Analyze the outcome
        analysis_response = await client.post(
            "/api/evolution/analyze-outcome",
            json={
                "agent_id": "felix-integration",
                "agent_role": AGENT_ROLES["felix"],
                "task_id": experience["id"],
                "steps_taken": [
                    {"step": "Designed WebSocket handler", "duration": 1800, "success": True},
                    {"step": "Implemented pub/sub", "duration": 2400, "success": True},
                    {"step": "Added error handling", "duration": 1200, "success": True}
                ],
                "outcome": "success",
                "quality_score": 0.9,
                "duration": 5400
            }
        )
        assert analysis_response.status_code == 200

        # 4. Generate learning tasks
        learning_response = await client.post(
            "/api/evolution/learning-tasks",
            json={
                "agent_id": "felix-integration",
                "agent_role": AGENT_ROLES["felix"],
                "max_tasks": 3
            }
        )
        assert learning_response.status_code == 200

        # 5. Get updated metrics
        metrics_response = await client.get(
            "/api/evolution/metrics/felix-integration",
            params={"agent_role": AGENT_ROLES["felix"], "days": 30}
        )
        assert metrics_response.status_code == 200

    @pytest.mark.asyncio
    async def test_validation_with_guidance(self, client: AsyncClient):
        """Test validation pipeline with evolution guidance"""
        # Get guidance for code quality task
        guidance_response = await client.post(
            "/api/evolution/guidance",
            json={
                "agent_id": "quinn-integration",
                "agent_role": AGENT_ROLES["quinn"],
                "work_type": WORK_TYPES["quality_audit"],
                "task_description": "Review and validate new module",
                "constraints": [],
                "goals": ["High code quality", "Full test coverage"],
                "available_resources": []
            }
        )
        assert guidance_response.status_code == 200

        # Run validation on sample code
        validation_response = await client.post(
            "/api/evolution/api/validation/run",
            json={
                "code": '''
def calculate_score(items: list) -> float:
    """Calculate average score from items."""
    if not items:
        return 0.0
    return sum(items) / len(items)
''',
                "language": "python",
                "phases": ["linting", "type_check"],
                "max_iterations": 1,
                "stop_on_first_failure": False
            }
        )
        assert validation_response.status_code == 200

        validation_result = validation_response.json()

        # Record quality metrics from validation
        quality_response = await client.post(
            "/api/evolution/quality-metrics",
            params={
                "agent_id": "quinn-integration",
                "agent_role": AGENT_ROLES["quinn"],
                "work_type": WORK_TYPES["quality_audit"],
                "task_id": "validation-test",
                "code_quality_score": 0.95 if validation_result["overall_passed"] else 0.70,
                "test_coverage": 0.0,
                "security_score": 0.9,
                "documentation_score": 0.8,
                "maintainability_score": 0.85,
                "issues_found": validation_result["total_errors"],
                "issues_fixed": 0
            }
        )
        assert quality_response.status_code == 201
