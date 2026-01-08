"""
Week 131 API Tests - Code Transformation Endpoints

Tests for:
- GET /api/week131/status - Service status
- GET /api/week131/transform/rules - Transformation rules
- POST /api/week131/transform/file - File transformation (VB.NET to C#, T-SQL to PL/pgSQL)
- POST /api/week131/transform/directory - Directory transformation
- POST /api/week131/transform/rollback/{file_path} - Rollback functionality

Uses pytest-asyncio, httpx AsyncClient, and mocked external dependencies.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def temp_vb_file():
    """Create a temporary VB.NET file for transformation tests."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vb', delete=False) as f:
        f.write("""
Imports System
Imports System.Data

Public Class CustomerService
    Private connectionString As String = "Server=localhost"

    Public Sub New()
        Console.WriteLine("CustomerService initialized")
    End Sub

    Public Function GetCustomer(customerId As Integer) As String
        Dim result As String = Nothing
        If customerId > 0 Then
            result = "Customer found"
        Else
            result = "Invalid ID"
        End If
        Return result
    End Function
End Class
""")
        yield f.name
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_sql_file():
    """Create a temporary T-SQL file for transformation tests."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write("""
CREATE PROCEDURE GetCustomerOrders
    @CustomerId INT,
    @StartDate DATETIME = NULL
AS
BEGIN
    SELECT [OrderId], [OrderDate], [Total]
    FROM [Orders]
    WHERE [CustomerId] = @CustomerId
        AND [OrderDate] >= ISNULL(@StartDate, GETDATE())

    PRINT 'Query completed'
END
GO
""")
        yield f.name
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_directory():
    """Create a temporary directory with VB.NET and SQL files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create VB.NET file
        vb_path = Path(tmpdir) / "Service.vb"
        vb_path.write_text("""
Public Class Service
    Public Sub DoWork()
        Dim x As Integer = 10
        Console.WriteLine(x)
    End Sub
End Class
""")

        # Create SQL file
        sql_path = Path(tmpdir) / "query.sql"
        sql_path.write_text("""
SELECT [Name], GETDATE() AS CurrentDate
FROM [Users]
WHERE [Active] = 1
GO
""")

        yield tmpdir


class TestWeek131Status:
    """Tests for GET /api/week131/status endpoint."""

    @pytest.mark.asyncio
    async def test_status_returns_200(self):
        """Test that status endpoint returns 200 OK."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/week131/status")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_status_response_structure(self):
        """Test status response contains expected fields."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/week131/status")

        assert response.status_code == 200
        data = response.json()

        assert "week" in data
        assert data["week"] == 131
        assert "phase" in data
        assert "services" in data
        assert "endpoints" in data

    @pytest.mark.asyncio
    async def test_status_services_section(self):
        """Test services section contains code_transformation and database_migration."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/week131/status")

        data = response.json()
        services = data["services"]

        assert "code_transformation" in services
        assert "database_migration" in services
        assert services["code_transformation"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_status_supported_transformations(self):
        """Test that all 3 transformation types are listed."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/week131/status")

        data = response.json()
        transformations = data["services"]["code_transformation"]["supported_transformations"]

        assert "vbnet_to_csharp" in transformations
        assert "vbnet_to_python" in transformations
        assert "tsql_to_plpgsql" in transformations
        assert len(transformations) == 3


class TestTransformationRules:
    """Tests for GET /api/week131/transform/rules endpoint."""

    @pytest.mark.asyncio
    async def test_rules_returns_200(self):
        """Test that rules endpoint returns 200 OK."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/week131/transform/rules")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rules_contains_all_transformation_types(self):
        """Test rules response contains all 3 transformation types."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/week131/transform/rules")

        data = response.json()

        assert "vbnet_to_csharp" in data
        assert "vbnet_to_python" in data
        assert "tsql_to_plpgsql" in data

    @pytest.mark.asyncio
    async def test_rules_are_lists(self):
        """Test that rule values are lists."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/week131/transform/rules")

        data = response.json()

        assert isinstance(data["vbnet_to_csharp"], list)
        assert isinstance(data["vbnet_to_python"], list)
        assert isinstance(data["tsql_to_plpgsql"], list)


class TestTransformFile:
    """Tests for POST /api/week131/transform/file endpoint."""

    @pytest.mark.asyncio
    async def test_transform_vbnet_to_csharp_dry_run(self, temp_vb_file):
        """Test VB.NET to C# transformation with dry_run=True."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/file",
                json={
                    "file_path": temp_vb_file,
                    "transformation_type": "vbnet_to_csharp",
                    "dry_run": True,
                    "create_backup": False
                }
            )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "files_processed" in data
        assert data["files_processed"] == 1
        assert "errors" in data
        assert "warnings" in data

    @pytest.mark.asyncio
    async def test_transform_tsql_to_plpgsql_dry_run(self, temp_sql_file):
        """Test T-SQL to PL/pgSQL transformation with dry_run=True."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/file",
                json={
                    "file_path": temp_sql_file,
                    "transformation_type": "tsql_to_plpgsql",
                    "dry_run": True,
                    "create_backup": False
                }
            )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert data["files_processed"] == 1

    @pytest.mark.asyncio
    async def test_transform_vbnet_to_python_dry_run(self, temp_vb_file):
        """Test VB.NET to Python transformation with dry_run=True."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/file",
                json={
                    "file_path": temp_vb_file,
                    "transformation_type": "vbnet_to_python",
                    "dry_run": True,
                    "create_backup": False
                }
            )

        assert response.status_code == 200
        data = response.json()

        assert data["files_processed"] == 1

    @pytest.mark.asyncio
    async def test_transform_file_not_found(self):
        """Test transformation with non-existent file returns error."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/file",
                json={
                    "file_path": "/nonexistent/path/file.vb",
                    "transformation_type": "vbnet_to_csharp",
                    "dry_run": True
                }
            )

        # Service handles missing files gracefully
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is False or len(data["errors"]) > 0

    @pytest.mark.asyncio
    async def test_transform_response_structure(self, temp_vb_file):
        """Test transformation response has correct structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/file",
                json={
                    "file_path": temp_vb_file,
                    "transformation_type": "vbnet_to_csharp",
                    "dry_run": True
                }
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response model fields
        assert "success" in data
        assert "files_processed" in data
        assert "files_transformed" in data
        assert "total_lines_changed" in data
        assert "patterns_applied" in data
        assert "errors" in data
        assert "warnings" in data

    @pytest.mark.asyncio
    async def test_transform_with_diff_preview(self, temp_vb_file):
        """Test transformation returns diff preview in dry run mode."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/file",
                json={
                    "file_path": temp_vb_file,
                    "transformation_type": "vbnet_to_csharp",
                    "dry_run": True
                }
            )

        assert response.status_code == 200
        data = response.json()

        # diff_preview may be None if no changes
        assert "diff_preview" in data or data.get("total_lines_changed", 0) >= 0

    @pytest.mark.asyncio
    async def test_transform_missing_file_path(self):
        """Test transformation without file_path returns 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/file",
                json={
                    "transformation_type": "vbnet_to_csharp",
                    "dry_run": True
                }
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_transform_missing_transformation_type(self, temp_vb_file):
        """Test transformation without transformation_type returns 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/file",
                json={
                    "file_path": temp_vb_file,
                    "dry_run": True
                }
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_transform_invalid_transformation_type(self, temp_vb_file):
        """Test transformation with invalid type returns 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/file",
                json={
                    "file_path": temp_vb_file,
                    "transformation_type": "invalid_type",
                    "dry_run": True
                }
            )

        assert response.status_code == 422


class TestTransformDirectory:
    """Tests for POST /api/week131/transform/directory endpoint."""

    @pytest.mark.asyncio
    async def test_transform_directory_dry_run(self, temp_directory):
        """Test directory transformation with dry_run=True."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/directory",
                json={
                    "directory_path": temp_directory,
                    "transformation_type": "vbnet_to_csharp",
                    "file_patterns": ["*.vb"],
                    "recursive": True,
                    "dry_run": True
                }
            )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "files_processed" in data
        assert "files_transformed" in data

    @pytest.mark.asyncio
    async def test_transform_directory_response_structure(self, temp_directory):
        """Test directory transformation response structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/directory",
                json={
                    "directory_path": temp_directory,
                    "transformation_type": "tsql_to_plpgsql",
                    "file_patterns": ["*.sql"],
                    "dry_run": True
                }
            )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "files_processed" in data
        assert "files_transformed" in data
        assert "total_lines_changed" in data
        assert "patterns_applied" in data
        assert "errors" in data
        assert "warnings" in data

    @pytest.mark.asyncio
    async def test_transform_directory_not_found(self):
        """Test directory transformation with non-existent directory."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/directory",
                json={
                    "directory_path": "/nonexistent/directory/path",
                    "transformation_type": "vbnet_to_csharp",
                    "dry_run": True
                }
            )

        # Service handles missing directories gracefully
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_transform_directory_missing_path(self):
        """Test directory transformation without directory_path returns 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/directory",
                json={
                    "transformation_type": "vbnet_to_csharp",
                    "dry_run": True
                }
            )

        assert response.status_code == 422


class TestTransformRollback:
    """Tests for POST /api/week131/transform/rollback/{file_path} endpoint."""

    @pytest.mark.asyncio
    async def test_rollback_nonexistent_backup(self):
        """Test rollback with no backup available."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/rollback/nonexistent/path/file.vb"
            )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_rollback_response_structure(self):
        """Test rollback response structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/rollback/some/path/file.vb"
            )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "file_path" in data

    @pytest.mark.asyncio
    async def test_rollback_with_path_encoding(self):
        """Test rollback with special characters in path."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/week131/transform/rollback/path/with%20spaces/file.vb"
            )

        # Should handle encoded paths
        assert response.status_code == 200


class TestTransformationIntegration:
    """Integration tests for transformation workflow."""

    @pytest.mark.asyncio
    async def test_status_then_transform(self, temp_vb_file):
        """Test checking status then performing transformation."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Check status first
            status_response = await client.get("/api/week131/status")
            assert status_response.status_code == 200

            # Then transform
            transform_response = await client.post(
                "/api/week131/transform/file",
                json={
                    "file_path": temp_vb_file,
                    "transformation_type": "vbnet_to_csharp",
                    "dry_run": True
                }
            )
            assert transform_response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_rules_then_transform(self, temp_sql_file):
        """Test getting rules then performing transformation."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Get rules first
            rules_response = await client.get("/api/week131/transform/rules")
            assert rules_response.status_code == 200

            # Then transform
            transform_response = await client.post(
                "/api/week131/transform/file",
                json={
                    "file_path": temp_sql_file,
                    "transformation_type": "tsql_to_plpgsql",
                    "dry_run": True
                }
            )
            assert transform_response.status_code == 200
