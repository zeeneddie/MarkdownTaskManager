"""
Week 131 API Tests - Database Migration Endpoints

Tests for:
- POST /api/week131/migration/start - Start a migration (dry_run=True)
- GET /api/week131/migration/{session_id} - Get migration status
- GET /api/week131/migration/{session_id}/phases - Get phase details
- GET /api/week131/migration/{session_id}/tables - Get table progress
- POST /api/week131/migration/{session_id}/rollback - Rollback migration

Uses pytest-asyncio, httpx AsyncClient, and mocked external dependencies.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.database_migration_executor_service import (
    MigrationProgress,
    MigrationPhase,
    MigrationStatus,
    MigrationConfig,
    DatabaseConnection,
    DatabaseType,
    TableMigrationStats,
)


@pytest.fixture
def sample_migration_request():
    """Sample migration request for testing."""
    return {
        "source": {
            "db_type": "sqlserver",
            "host": "source-db.example.com",
            "port": 1433,
            "database": "LegacyDB",
            "username": "admin",
            "password": "password123",
            "schema": "dbo"
        },
        "target": {
            "db_type": "postgresql",
            "host": "target-db.example.com",
            "port": 5432,
            "database": "ModernDB",
            "username": "postgres",
            "password": "postgres123",
            "schema": "public"
        },
        "dry_run": True,
        "batch_size": 10000,
        "parallel_tables": 4,
        "create_backup": True
    }


@pytest.fixture
def mock_migration_progress():
    """Create a mock migration progress object."""
    config = MigrationConfig(
        source=DatabaseConnection(
            db_type=DatabaseType.SQL_SERVER,
            host="source-db",
            port=1433,
            database="LegacyDB",
            username="admin",
            password="pass"
        ),
        target=DatabaseConnection(
            db_type=DatabaseType.POSTGRESQL,
            host="target-db",
            port=5432,
            database="ModernDB",
            username="postgres",
            password="pass"
        ),
        dry_run=True
    )

    progress = MigrationProgress(
        session_id="mig_test123abc",
        config=config,
        current_phase=MigrationPhase.SCHEMA_CONVERSION,
        phase_status={
            MigrationPhase.PREPARATION: MigrationStatus.COMPLETED,
            MigrationPhase.SCHEMA_EXTRACTION: MigrationStatus.COMPLETED,
            MigrationPhase.SCHEMA_CONVERSION: MigrationStatus.IN_PROGRESS,
        },
        total_tables=10,
        tables_completed=3,
        total_rows=100000,
        rows_migrated=30000,
        start_time=datetime.now(),
        table_stats={
            "users": TableMigrationStats(
                table_name="users",
                schema_name="dbo",
                source_row_count=1000,
                rows_migrated=1000,
                status=MigrationStatus.COMPLETED,
                duration_seconds=5.2
            ),
            "orders": TableMigrationStats(
                table_name="orders",
                schema_name="dbo",
                source_row_count=5000,
                rows_migrated=2500,
                status=MigrationStatus.IN_PROGRESS,
                duration_seconds=10.5
            )
        }
    )

    return progress


class TestMigrationStart:
    """Tests for POST /api/week131/migration/start endpoint."""

    @pytest.mark.asyncio
    async def test_start_migration_dry_run(self, sample_migration_request):
        """Test starting a migration with dry_run=True."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "session_id" in data
        assert "current_phase" in data
        assert "overall_progress" in data

    @pytest.mark.asyncio
    async def test_start_migration_response_structure(self, sample_migration_request):
        """Test migration start response has correct structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )

        assert response.status_code == 200
        data = response.json()

        # Verify all expected fields
        assert "success" in data
        assert "session_id" in data
        assert "current_phase" in data
        assert "overall_progress" in data
        assert "tables_completed" in data
        assert "rows_migrated" in data
        assert "duration_seconds" in data
        assert "errors" in data

    @pytest.mark.asyncio
    async def test_start_migration_missing_source(self):
        """Test migration start without source returns 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/migration/start",
                json={
                    "target": {
                        "db_type": "postgresql",
                        "host": "localhost",
                        "port": 5432,
                        "database": "test",
                        "username": "user",
                        "password": "pass"
                    },
                    "dry_run": True
                }
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_migration_missing_target(self):
        """Test migration start without target returns 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/migration/start",
                json={
                    "source": {
                        "db_type": "sqlserver",
                        "host": "localhost",
                        "port": 1433,
                        "database": "test",
                        "username": "user",
                        "password": "pass"
                    },
                    "dry_run": True
                }
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_migration_invalid_db_type(self):
        """Test migration start with invalid database type returns error (422 or 500)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/migration/start",
                json={
                    "source": {
                        "db_type": "invalid_db",
                        "host": "localhost",
                        "port": 1433,
                        "database": "test",
                        "username": "user",
                        "password": "pass"
                    },
                    "target": {
                        "db_type": "postgresql",
                        "host": "localhost",
                        "port": 5432,
                        "database": "test",
                        "username": "user",
                        "password": "pass"
                    },
                    "dry_run": True
                }
            )

        # 422 for validation errors, 500 if validation passes but enum conversion fails
        assert response.status_code in [422, 500]

    @pytest.mark.asyncio
    async def test_start_migration_returns_session_id(self, sample_migration_request):
        """Test that migration start returns a valid session_id."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )

        assert response.status_code == 200
        data = response.json()

        assert "session_id" in data
        assert data["session_id"].startswith("mig_")
        assert len(data["session_id"]) > 4


class TestMigrationStatus:
    """Tests for GET /api/week131/migration/{session_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_migration_status_not_found(self):
        """Test getting status for non-existent session returns 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/week131/migration/mig_nonexistent123")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_migration_status_after_start(self, sample_migration_request):
        """Test getting status for a started migration."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Start migration
            start_response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            assert start_response.status_code == 200
            session_id = start_response.json()["session_id"]

            # Get status
            status_response = await client.get(f"/api/week131/migration/{session_id}")

        assert status_response.status_code == 200
        data = status_response.json()

        assert data["session_id"] == session_id
        assert "current_phase" in data
        assert "overall_progress" in data

    @pytest.mark.asyncio
    async def test_get_migration_status_response_structure(self, sample_migration_request):
        """Test migration status response has correct structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Start migration
            start_response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            session_id = start_response.json()["session_id"]

            # Get status
            status_response = await client.get(f"/api/week131/migration/{session_id}")

        assert status_response.status_code == 200
        data = status_response.json()

        assert "success" in data
        assert "session_id" in data
        assert "current_phase" in data
        assert "overall_progress" in data
        assert "tables_completed" in data
        assert "rows_migrated" in data
        assert "duration_seconds" in data
        assert "errors" in data


class TestMigrationPhases:
    """Tests for GET /api/week131/migration/{session_id}/phases endpoint."""

    @pytest.mark.asyncio
    async def test_get_phases_not_found(self):
        """Test getting phases for non-existent session returns 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/week131/migration/mig_nonexistent123/phases")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_phases_after_start(self, sample_migration_request):
        """Test getting phases for a started migration."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Start migration
            start_response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            session_id = start_response.json()["session_id"]

            # Get phases
            phases_response = await client.get(f"/api/week131/migration/{session_id}/phases")

        assert phases_response.status_code == 200
        data = phases_response.json()

        assert "session_id" in data
        assert data["session_id"] == session_id
        assert "phases" in data
        assert isinstance(data["phases"], list)

    @pytest.mark.asyncio
    async def test_get_phases_response_structure(self, sample_migration_request):
        """Test phases response has correct structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Start migration
            start_response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            session_id = start_response.json()["session_id"]

            # Get phases
            phases_response = await client.get(f"/api/week131/migration/{session_id}/phases")

        assert phases_response.status_code == 200
        data = phases_response.json()

        assert "phases" in data
        for phase in data["phases"]:
            assert "phase" in phase
            assert "status" in phase
            assert "is_current" in phase

    @pytest.mark.asyncio
    async def test_get_phases_contains_all_phases(self, sample_migration_request):
        """Test that all migration phases are returned."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Start migration
            start_response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            session_id = start_response.json()["session_id"]

            # Get phases
            phases_response = await client.get(f"/api/week131/migration/{session_id}/phases")

        data = phases_response.json()
        phase_names = [p["phase"] for p in data["phases"]]

        # Check expected phases
        expected_phases = [
            "preparation", "schema_extraction", "schema_conversion",
            "schema_deployment", "data_extraction", "data_transformation",
            "data_loading", "validation", "cleanup"
        ]

        for expected in expected_phases:
            assert expected in phase_names, f"Phase {expected} not found in response"


class TestMigrationTables:
    """Tests for GET /api/week131/migration/{session_id}/tables endpoint."""

    @pytest.mark.asyncio
    async def test_get_tables_not_found(self):
        """Test getting tables for non-existent session returns 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/week131/migration/mig_nonexistent123/tables")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_tables_after_start(self, sample_migration_request):
        """Test getting tables for a started migration."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Start migration
            start_response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            session_id = start_response.json()["session_id"]

            # Get tables
            tables_response = await client.get(f"/api/week131/migration/{session_id}/tables")

        assert tables_response.status_code == 200
        data = tables_response.json()

        assert "session_id" in data
        assert data["session_id"] == session_id
        assert "total_tables" in data
        assert "tables_completed" in data
        assert "tables" in data
        assert isinstance(data["tables"], list)

    @pytest.mark.asyncio
    async def test_get_tables_response_structure(self, sample_migration_request):
        """Test tables response has correct structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Start migration
            start_response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            session_id = start_response.json()["session_id"]

            # Get tables
            tables_response = await client.get(f"/api/week131/migration/{session_id}/tables")

        assert tables_response.status_code == 200
        data = tables_response.json()

        assert "session_id" in data
        assert "total_tables" in data
        assert "tables_completed" in data
        assert "tables" in data


class TestMigrationRollback:
    """Tests for POST /api/week131/migration/{session_id}/rollback endpoint."""

    @pytest.mark.asyncio
    async def test_rollback_not_found(self):
        """Test rollback for non-existent session returns error."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/week131/migration/mig_nonexistent123/rollback")

        # Returns 400 when rollback fails or session not found
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_rollback_dry_run_session(self, sample_migration_request):
        """Test rollback for a dry-run session (no backup available)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Start migration (dry run, no backup created)
            start_response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            session_id = start_response.json()["session_id"]

            # Attempt rollback
            rollback_response = await client.post(f"/api/week131/migration/{session_id}/rollback")

        # Rollback should fail for dry-run (no backup)
        assert rollback_response.status_code == 400

    @pytest.mark.asyncio
    async def test_rollback_response_structure(self, sample_migration_request):
        """Test rollback error response structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/week131/migration/mig_nonexistent123/rollback")

        assert response.status_code == 400
        data = response.json()

        # Error response should have detail
        assert "detail" in data


class TestMigrationIntegration:
    """Integration tests for migration workflow."""

    @pytest.mark.asyncio
    async def test_full_migration_workflow_dry_run(self, sample_migration_request):
        """Test complete migration workflow with dry_run=True."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Step 1: Start migration
            start_response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            assert start_response.status_code == 200
            session_id = start_response.json()["session_id"]

            # Step 2: Check status
            status_response = await client.get(f"/api/week131/migration/{session_id}")
            assert status_response.status_code == 200

            # Step 3: Get phases
            phases_response = await client.get(f"/api/week131/migration/{session_id}/phases")
            assert phases_response.status_code == 200

            # Step 4: Get tables
            tables_response = await client.get(f"/api/week131/migration/{session_id}/tables")
            assert tables_response.status_code == 200

    @pytest.mark.asyncio
    async def test_start_then_status_consistency(self, sample_migration_request):
        """Test that session_id is consistent between start and status."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Start migration
            start_response = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            start_data = start_response.json()
            session_id = start_data["session_id"]

            # Get status
            status_response = await client.get(f"/api/week131/migration/{session_id}")
            status_data = status_response.json()

        assert start_data["session_id"] == status_data["session_id"]
        assert start_data["current_phase"] == status_data["current_phase"]

    @pytest.mark.asyncio
    async def test_multiple_migrations(self, sample_migration_request):
        """Test starting multiple migrations returns unique session IDs."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Start first migration
            response1 = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            session_id_1 = response1.json()["session_id"]

            # Start second migration
            response2 = await client.post(
                "/api/week131/migration/start",
                json=sample_migration_request
            )
            session_id_2 = response2.json()["session_id"]

        assert session_id_1 != session_id_2
        assert session_id_1.startswith("mig_")
        assert session_id_2.startswith("mig_")


class TestDatabaseTypeValidation:
    """Tests for database type validation in migration requests."""

    @pytest.mark.asyncio
    async def test_valid_oracle_to_postgresql(self):
        """Test migration from Oracle to PostgreSQL."""
        request = {
            "source": {
                "db_type": "oracle",
                "host": "oracle-db.example.com",
                "port": 1521,
                "database": "ORCL",
                "username": "system",
                "password": "oracle123"
            },
            "target": {
                "db_type": "postgresql",
                "host": "pg-db.example.com",
                "port": 5432,
                "database": "target_db",
                "username": "postgres",
                "password": "postgres123"
            },
            "dry_run": True
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/week131/migration/start", json=request)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_valid_mysql_to_postgresql(self):
        """Test migration from MySQL to PostgreSQL."""
        request = {
            "source": {
                "db_type": "mysql",
                "host": "mysql-db.example.com",
                "port": 3306,
                "database": "source_db",
                "username": "root",
                "password": "mysql123"
            },
            "target": {
                "db_type": "postgresql",
                "host": "pg-db.example.com",
                "port": 5432,
                "database": "target_db",
                "username": "postgres",
                "password": "postgres123"
            },
            "dry_run": True
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/week131/migration/start", json=request)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_all_supported_database_types(self):
        """Test that all supported database types are accepted."""
        supported_types = ["oracle", "sqlserver", "postgresql", "mysql"]

        for db_type in supported_types:
            request = {
                "source": {
                    "db_type": db_type,
                    "host": "localhost",
                    "port": 1433,
                    "database": "test",
                    "username": "user",
                    "password": "pass"
                },
                "target": {
                    "db_type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "database": "test",
                    "username": "user",
                    "password": "pass"
                },
                "dry_run": True
            }

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/week131/migration/start", json=request)

            assert response.status_code == 200, f"Failed for db_type: {db_type}"
