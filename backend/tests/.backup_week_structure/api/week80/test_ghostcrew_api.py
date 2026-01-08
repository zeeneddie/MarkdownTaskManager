"""
Integration tests for GhostCrew API - Week 80-82

Tests for all GhostCrew API endpoints:
- Security scanning endpoints
- Scan management endpoints
- Shadow Graph endpoints
- Security knowledge endpoints
- Dashboard endpoint
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from httpx import AsyncClient
from datetime import datetime


class TestGhostCrewScanningEndpoints:
    """Tests for GhostCrew scanning endpoints."""

    @pytest.mark.asyncio
    async def test_security_assist_endpoint(self, test_client):
        """POST /api/ghostcrew/assist should provide security assistance."""
        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.assist = AsyncMock(return_value={
                "response": "To prevent SQL injection, use parameterized queries.",
                "knowledge_refs": ["CWE-89", "A03:2021"]
            })
            mock_service.return_value = mock_instance

            response = await test_client.post("/api/ghostcrew/assist", json={
                "query": "How do I prevent SQL injection?",
                "include_knowledge": True
            })

            assert response.status_code == 200
            data = response.json()
            assert "response" in data

    @pytest.mark.asyncio
    async def test_security_scan_endpoint(self, test_client):
        """POST /api/ghostcrew/scan should start autonomous scan."""
        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.scan_autonomous = AsyncMock(return_value={
                "scan_id": str(uuid4()),
                "status": "completed",
                "findings_count": 5,
                "files_scanned": 100
            })
            mock_service.return_value = mock_instance

            response = await test_client.post("/api/ghostcrew/scan", json={
                "repo_path": "/tmp/test-repo",
                "scan_type": "quick"
            })

            assert response.status_code == 200
            data = response.json()
            assert "scan_id" in data or "status" in data

    @pytest.mark.asyncio
    async def test_run_crew_endpoint(self, test_client):
        """POST /api/ghostcrew/crew/{project_id} should run security crew."""
        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.run_crew = AsyncMock(return_value={
                "status": "completed",
                "agents_run": ["SecurityAgent", "AuditAgent", "ComplianceAgent"],
                "total_findings": 12
            })
            mock_service.return_value = mock_instance

            response = await test_client.post("/api/ghostcrew/crew/1", json={
                "project_id": 1
            })

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_scan_with_workflow_context(self, test_client):
        """Scan should accept workflow context."""
        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.scan_autonomous = AsyncMock(return_value={
                "scan_id": str(uuid4()),
                "workflow_type": "QUALITY_AUDIT",
                "workflow_session_id": str(uuid4())
            })
            mock_service.return_value = mock_instance

            response = await test_client.post("/api/ghostcrew/scan", json={
                "repo_path": "/tmp/test",
                "scan_type": "full",
                "workflow_type": "QUALITY_AUDIT",
                "workflow_session_id": str(uuid4())
            })

            assert response.status_code == 200


class TestScanManagementEndpoints:
    """Tests for scan management endpoints."""

    @pytest.mark.asyncio
    async def test_get_scan_endpoint(self, test_client):
        """GET /api/ghostcrew/scans/{scan_id} should return scan details."""
        scan_id = uuid4()

        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_scan = MagicMock()
            mock_scan.to_dict.return_value = {
                "id": str(scan_id),
                "status": "completed",
                "findings_count": 5
            }
            mock_instance = MagicMock()
            mock_instance.get_scan = AsyncMock(return_value=mock_scan)
            mock_service.return_value = mock_instance

            response = await test_client.get(f"/api/ghostcrew/scans/{scan_id}")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_scan_not_found(self, test_client):
        """GET /api/ghostcrew/scans/{scan_id} should return 404 for unknown scan."""
        scan_id = uuid4()

        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_scan = AsyncMock(return_value=None)
            mock_service.return_value = mock_instance

            response = await test_client.get(f"/api/ghostcrew/scans/{scan_id}")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_scan_findings_endpoint(self, test_client):
        """GET /api/ghostcrew/scans/{scan_id}/findings should return findings."""
        scan_id = uuid4()

        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_findings = [
                MagicMock(to_dict=lambda: {"id": str(uuid4()), "severity": "high"}),
                MagicMock(to_dict=lambda: {"id": str(uuid4()), "severity": "medium"})
            ]
            mock_instance = MagicMock()
            mock_instance.get_scan_findings = AsyncMock(return_value=mock_findings)
            mock_service.return_value = mock_instance

            response = await test_client.get(f"/api/ghostcrew/scans/{scan_id}/findings")

            assert response.status_code == 200
            assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_scan_findings_with_severity_filter(self, test_client):
        """Should filter findings by severity."""
        scan_id = uuid4()

        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_scan_findings = AsyncMock(return_value=[])
            mock_service.return_value = mock_instance

            response = await test_client.get(
                f"/api/ghostcrew/scans/{scan_id}/findings?severity=critical"
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_project_scans_endpoint(self, test_client):
        """GET /api/ghostcrew/projects/{project_id}/scans should return scans."""
        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_scans = [
                MagicMock(to_dict=lambda: {"id": str(uuid4()), "status": "completed"})
            ]
            mock_instance = MagicMock()
            mock_instance.get_project_scans = AsyncMock(return_value=mock_scans)
            mock_service.return_value = mock_instance

            response = await test_client.get("/api/ghostcrew/projects/1/scans")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_mark_false_positive_endpoint(self, test_client):
        """POST /api/ghostcrew/findings/{finding_id}/false-positive should mark FP."""
        finding_id = uuid4()

        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.mark_finding_false_positive = AsyncMock(return_value={
                "status": "success",
                "pattern_updated": True
            })
            mock_service.return_value = mock_instance

            response = await test_client.post(
                f"/api/ghostcrew/findings/{finding_id}/false-positive",
                json={"reason": "Test code", "marked_by": "user"}
            )

            assert response.status_code == 200


class TestShadowGraphEndpoints:
    """Tests for Shadow Graph (pattern learning) endpoints."""

    @pytest.mark.asyncio
    async def test_get_patterns_endpoint(self, test_client):
        """GET /api/ghostcrew/shadow-graph/patterns should return patterns."""
        with patch('app.api.ghostcrew.get_shadow_graph_service') as mock_service:
            mock_patterns = [
                MagicMock(to_dict=lambda: {
                    "vulnerability_type": "sql_injection",
                    "accuracy": 0.9
                })
            ]
            mock_instance = MagicMock()
            mock_instance.get_patterns = AsyncMock(return_value=mock_patterns)
            mock_service.return_value = mock_instance

            response = await test_client.get("/api/ghostcrew/shadow-graph/patterns")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_patterns_with_filters(self, test_client):
        """Should filter patterns by language and accuracy."""
        with patch('app.api.ghostcrew.get_shadow_graph_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_patterns = AsyncMock(return_value=[])
            mock_service.return_value = mock_instance

            response = await test_client.get(
                "/api/ghostcrew/shadow-graph/patterns?language=python&min_accuracy=0.8"
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_learning_stats_endpoint(self, test_client):
        """GET /api/ghostcrew/shadow-graph/stats should return stats."""
        with patch('app.api.ghostcrew.get_shadow_graph_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_learning_stats = AsyncMock(return_value={
                "total_patterns": 50,
                "avg_accuracy": 0.85,
                "true_positives": 200,
                "false_positives": 35
            })
            mock_service.return_value = mock_instance

            response = await test_client.get("/api/ghostcrew/shadow-graph/stats")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_top_patterns_endpoint(self, test_client):
        """GET /api/ghostcrew/shadow-graph/top-patterns should return top patterns."""
        with patch('app.api.ghostcrew.get_shadow_graph_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_top_patterns = AsyncMock(return_value=[
                {"vulnerability_type": "sql_injection", "match_count": 100}
            ])
            mock_service.return_value = mock_instance

            response = await test_client.get("/api/ghostcrew/shadow-graph/top-patterns")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_confirm_vulnerability_endpoint(self, test_client):
        """POST /api/ghostcrew/shadow-graph/confirm/{finding_id} should confirm."""
        finding_id = uuid4()

        with patch('app.api.ghostcrew.get_shadow_graph_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.confirm_vulnerability = AsyncMock(return_value={
                "status": "confirmed",
                "pattern_accuracy_improved": True
            })
            mock_service.return_value = mock_instance

            response = await test_client.post(
                f"/api/ghostcrew/shadow-graph/confirm/{finding_id}?confirmed_by=security_team"
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_recommendations_endpoint(self, test_client):
        """GET /api/ghostcrew/shadow-graph/recommendations/{vuln} should return recs."""
        with patch('app.api.ghostcrew.get_shadow_graph_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_recommendations = AsyncMock(return_value={
                "vulnerability": "sql_injection",
                "recommendations": ["Use parameterized queries"]
            })
            mock_service.return_value = mock_instance

            response = await test_client.get(
                "/api/ghostcrew/shadow-graph/recommendations/sql_injection"
            )

            assert response.status_code == 200


class TestSecurityKnowledgeEndpoints:
    """Tests for security knowledge (RAG) endpoints."""

    @pytest.mark.asyncio
    async def test_initialize_knowledge_endpoint(self, test_client):
        """POST /api/ghostcrew/knowledge/initialize should init KB."""
        with patch('app.api.ghostcrew.get_security_rag_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.initialize_knowledge_base = AsyncMock(return_value={
                "status": "initialized",
                "owasp_loaded": 10,
                "cwe_loaded": 25
            })
            mock_service.return_value = mock_instance

            response = await test_client.post("/api/ghostcrew/knowledge/initialize")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_owasp_guidance_endpoint(self, test_client):
        """GET /api/ghostcrew/knowledge/owasp/{category} should return guidance."""
        with patch('app.api.ghostcrew.get_security_rag_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_owasp_guidance = AsyncMock(return_value={
                "category": "A01",
                "name": "Broken Access Control",
                "description": "...",
                "prevention": ["..."]
            })
            mock_service.return_value = mock_instance

            response = await test_client.get("/api/ghostcrew/knowledge/owasp/A01")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_owasp_not_found(self, test_client):
        """Should return 404 for unknown OWASP category."""
        with patch('app.api.ghostcrew.get_security_rag_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_owasp_guidance = AsyncMock(return_value=None)
            mock_service.return_value = mock_instance

            response = await test_client.get("/api/ghostcrew/knowledge/owasp/A99")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_cwe_guidance_endpoint(self, test_client):
        """GET /api/ghostcrew/knowledge/cwe/{cwe_id} should return guidance."""
        with patch('app.api.ghostcrew.get_security_rag_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_cwe_guidance = AsyncMock(return_value={
                "cwe_id": "CWE-79",
                "name": "Cross-site Scripting",
                "description": "...",
                "mitigation": "..."
            })
            mock_service.return_value = mock_instance

            response = await test_client.get("/api/ghostcrew/knowledge/cwe/CWE-79")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_remediation_endpoint(self, test_client):
        """POST /api/ghostcrew/knowledge/remediation should return guidance."""
        with patch('app.api.ghostcrew.get_security_rag_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_remediation = AsyncMock(return_value={
                "vulnerability_type": "sql_injection",
                "steps": ["Use parameterized queries", "Validate input"]
            })
            mock_service.return_value = mock_instance

            response = await test_client.post("/api/ghostcrew/knowledge/remediation", json={
                "vulnerability_type": "sql_injection",
                "language": "python"
            })

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_knowledge_endpoint(self, test_client):
        """GET /api/ghostcrew/knowledge/search should search KB."""
        with patch('app.api.ghostcrew.get_security_rag_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.search_knowledge = AsyncMock(return_value=[
                {"title": "SQL Injection", "type": "cwe"}
            ])
            mock_service.return_value = mock_instance

            response = await test_client.get(
                "/api/ghostcrew/knowledge/search?query=sql+injection"
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_security_checklist_endpoint(self, test_client):
        """GET /api/ghostcrew/knowledge/checklist should return checklist."""
        with patch('app.api.ghostcrew.get_security_rag_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_security_checklist = AsyncMock(return_value={
                "language": "python",
                "checklist": [
                    {"item": "Use parameterized queries", "category": "injection"}
                ]
            })
            mock_service.return_value = mock_instance

            response = await test_client.get(
                "/api/ghostcrew/knowledge/checklist?language=python"
            )

            assert response.status_code == 200


class TestDashboardEndpoint:
    """Tests for dashboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, test_client):
        """GET /api/ghostcrew/dashboard should return dashboard data."""
        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_gc, \
             patch('app.api.ghostcrew.get_shadow_graph_service') as mock_sg:

            mock_gc_instance = MagicMock()
            mock_gc_instance.get_project_scans = AsyncMock(return_value=[])
            mock_gc.return_value = mock_gc_instance

            mock_sg_instance = MagicMock()
            mock_sg_instance.get_learning_stats = AsyncMock(return_value={
                "total_patterns": 50
            })
            mock_sg_instance.get_top_patterns = AsyncMock(return_value=[])
            mock_sg.return_value = mock_sg_instance

            response = await test_client.get("/api/ghostcrew/dashboard")

            assert response.status_code == 200
            data = response.json()
            assert "learning_stats" in data or "recent_scans" in data

    @pytest.mark.asyncio
    async def test_get_dashboard_with_project(self, test_client):
        """Dashboard should filter by project_id."""
        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_gc, \
             patch('app.api.ghostcrew.get_shadow_graph_service') as mock_sg:

            mock_gc_instance = MagicMock()
            mock_gc_instance.get_project_scans = AsyncMock(return_value=[])
            mock_gc.return_value = mock_gc_instance

            mock_sg_instance = MagicMock()
            mock_sg_instance.get_learning_stats = AsyncMock(return_value={})
            mock_sg_instance.get_top_patterns = AsyncMock(return_value=[])
            mock_sg.return_value = mock_sg_instance

            response = await test_client.get("/api/ghostcrew/dashboard?project_id=1")

            assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_assist_server_error(self, test_client):
        """Should handle server errors gracefully."""
        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.assist = AsyncMock(side_effect=Exception("Service error"))
            mock_service.return_value = mock_instance

            response = await test_client.post("/api/ghostcrew/assist", json={
                "query": "test"
            })

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_scan_invalid_path(self, test_client):
        """Should handle invalid scan path."""
        with patch('app.api.ghostcrew.get_ghostcrew_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.scan_autonomous = AsyncMock(
                side_effect=FileNotFoundError("Path not found")
            )
            mock_service.return_value = mock_instance

            response = await test_client.post("/api/ghostcrew/scan", json={
                "repo_path": "/nonexistent/path",
                "scan_type": "quick"
            })

            assert response.status_code == 500
