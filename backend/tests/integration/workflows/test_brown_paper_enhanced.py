"""
Tests for Brown Paper Enhanced - Phase 20 (Week 128-129)

Tests the 6-phase deep analysis integration:
1. Code Understanding (DependencyGraph + CodeAnalysis + LayeredAnalysis)
2. Domain Extraction (Peter agent)
3. Hierarchical Extraction (HierarchicalStoryExtractionService)
4. Deep Extraction (DeepExtractionService + LLM Council)
5. Estimation (brown_paper_estimation_service enhanced)
6. Output (Consolidation)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.models.brown_paper_enhanced import (
    EnhancedAnalysisTier,
    EnhancedAnalysisPhase,
    EnhancedAnalysisRequest,
    EnhancedAnalysisOptions,
    EnhancedAnalysisResponse,
    EnhancedAnalysisSummary,
    Phase1Result,
    Phase2Result,
    Phase3Result,
    Phase4Result,
    Phase5Result,
    TIER_PHASES,
    TIER_CONFIDENCE_TARGETS,
    TIER_PROVIDERS,
)


class TestEnhancedAnalysisModels:
    """Test the enhanced analysis data models."""

    def test_tier_enum_values(self):
        """Test all tier enum values are defined."""
        assert EnhancedAnalysisTier.FREE.value == "FREE"
        assert EnhancedAnalysisTier.BASIC.value == "BASIC"
        assert EnhancedAnalysisTier.STANDARD.value == "STANDARD"
        assert EnhancedAnalysisTier.PROFESSIONAL.value == "PROFESSIONAL"
        assert EnhancedAnalysisTier.PREMIUM.value == "PREMIUM"

    def test_phase_enum_values(self):
        """Test all phase enum values are defined."""
        assert EnhancedAnalysisPhase.CODE_UNDERSTANDING.value == "code_understanding"
        assert EnhancedAnalysisPhase.DOMAIN_EXTRACTION.value == "domain_extraction"
        assert EnhancedAnalysisPhase.HIERARCHICAL_EXTRACTION.value == "hierarchical_extraction"
        assert EnhancedAnalysisPhase.DEEP_EXTRACTION.value == "deep_extraction"
        assert EnhancedAnalysisPhase.ESTIMATION.value == "estimation"
        assert EnhancedAnalysisPhase.OUTPUT.value == "output"

    def test_tier_phases_configuration(self):
        """Test tier to phases mapping."""
        assert TIER_PHASES[EnhancedAnalysisTier.FREE] == [1]
        assert TIER_PHASES[EnhancedAnalysisTier.BASIC] == [1, 2]
        assert TIER_PHASES[EnhancedAnalysisTier.STANDARD] == [1, 2, 3]
        assert TIER_PHASES[EnhancedAnalysisTier.PROFESSIONAL] == [1, 2, 3, 4, 5]
        assert TIER_PHASES[EnhancedAnalysisTier.PREMIUM] == [1, 2, 3, 4, 5, 6]

    def test_tier_confidence_targets(self):
        """Test confidence targets per tier."""
        assert TIER_CONFIDENCE_TARGETS[EnhancedAnalysisTier.FREE] == 0.60
        assert TIER_CONFIDENCE_TARGETS[EnhancedAnalysisTier.BASIC] == 0.70
        assert TIER_CONFIDENCE_TARGETS[EnhancedAnalysisTier.STANDARD] == 0.80
        assert TIER_CONFIDENCE_TARGETS[EnhancedAnalysisTier.PROFESSIONAL] == 0.90
        assert TIER_CONFIDENCE_TARGETS[EnhancedAnalysisTier.PREMIUM] == 0.95

    def test_tier_providers(self):
        """Test LLM providers per tier."""
        assert "ollama" in TIER_PROVIDERS[EnhancedAnalysisTier.FREE]
        assert "groq" in TIER_PROVIDERS[EnhancedAnalysisTier.BASIC]
        assert "gemini" in TIER_PROVIDERS[EnhancedAnalysisTier.STANDARD]
        assert "openai" in TIER_PROVIDERS[EnhancedAnalysisTier.PROFESSIONAL]
        assert "anthropic" in TIER_PROVIDERS[EnhancedAnalysisTier.PREMIUM]

    def test_enhanced_analysis_request_defaults(self):
        """Test request defaults."""
        request = EnhancedAnalysisRequest()
        assert request.tier == EnhancedAnalysisTier.STANDARD
        assert request.include_phases == [1, 2, 3, 4, 5, 6]
        assert request.options.skip_vbscript is False
        assert request.options.include_cira is True

    def test_phase1_result_structure(self):
        """Test Phase 1 result structure."""
        result = Phase1Result(
            dependency_graph={"nodes": [], "edges": []},
            code_analysis={"complexity_profile": {}},
            layered_analysis={"vbscript_files": 5},
            duration_ms=1000,
            success=True
        )
        assert result.dependency_graph is not None
        assert result.code_analysis is not None
        assert result.success is True

    def test_phase2_result_cafcr_mapping(self):
        """Test Phase 2 CAFCR mapping structure."""
        result = Phase2Result(
            domains=[{"name": "UserService", "type": "service"}],
            cafcr_mapping={
                "Customer": ["UIComponents"],
                "Application": ["UserService"],
                "Functional": [],
                "Conceptual": ["UserModel"],
                "Realization": ["UserRepository"]
            },
            business_rules_count=15
        )
        assert len(result.cafcr_mapping) == 5
        assert "Application" in result.cafcr_mapping

    def test_phase3_result_with_cira(self):
        """Test Phase 3 with CiRA causal relations."""
        result = Phase3Result(
            extraction_result={
                "epics": [{"id": "E1", "title": "User Management"}],
                "features": [{"id": "F1", "epic_id": "E1"}],
                "stories": [],
                "tasks": []
            },
            causal_relations=[
                {"from": "S1", "to": "S2", "type": "enables"}
            ]
        )
        assert len(result.causal_relations) == 1
        assert result.causal_relations[0]["type"] == "enables"

    def test_phase4_result_conflicts(self):
        """Test Phase 4 conflict detection."""
        result = Phase4Result(
            deep_extraction_result={"validated_stories": []},
            conflicts=[
                {"id": "C1", "severity": "high", "description": "Conflicting requirements"},
                {"id": "C2", "severity": "low", "description": "Minor naming issue"}
            ],
            consensus_confidence=0.85,
            human_review_needed=1
        )
        assert len(result.conflicts) == 2
        assert result.human_review_needed == 1
        assert result.consensus_confidence == 0.85

    def test_phase5_result_estimation(self):
        """Test Phase 5 estimation with complexity multiplier."""
        result = Phase5Result(
            estimation_result={
                "total_fp": 450,
                "total_sp": 320,
                "estimated_hours": 1200
            },
            risk_assessment={
                "circular_dependencies": 3,
                "risk_level": "medium"
            },
            complexity_multiplier=1.3
        )
        assert result.complexity_multiplier == 1.3
        assert result.risk_assessment["risk_level"] == "medium"

    def test_enhanced_analysis_response_complete(self):
        """Test complete enhanced analysis response."""
        response = EnhancedAnalysisResponse(
            session_id="test-123",
            status="completed",
            tier=EnhancedAnalysisTier.STANDARD,
            phases_completed=[1, 2, 3],
            confidence=0.82,
            summary=EnhancedAnalysisSummary(
                epics=5,
                features=23,
                stories=89,
                tasks=234,
                total_fp=450,
                total_sp=320,
                estimated_hours=1200,
                confidence=0.82
            ),
            dependency_graph_url="/api/brown-paper/bmad/test-123/dependency-graph",
            hierarchy_url="/api/brown-paper/bmad/test-123/hierarchy",
            metrics_url="/api/brown-paper/bmad/test-123/metrics",
            conflicts_url="/api/brown-paper/bmad/test-123/conflicts"
        )
        assert response.status == "completed"
        assert response.summary.epics == 5
        assert "/dependency-graph" in response.dependency_graph_url


class TestBrownPaperServiceEnhanced:
    """Test the enhanced methods in BrownPaperService."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_services(self):
        """Create mock services for integration."""
        with patch('app.services.brown_paper_service.DependencyGraphService') as dep_mock, \
             patch('app.services.brown_paper_service.CodeAnalysisAggregatorService') as code_mock, \
             patch('app.services.brown_paper_service.LayeredAnalysisService') as layer_mock, \
             patch('app.services.brown_paper_service.HierarchicalStoryExtractionService') as hier_mock, \
             patch('app.services.brown_paper_service.DeepExtractionService') as deep_mock, \
             patch('app.services.brown_paper_service.get_brown_paper_estimation_service') as est_mock:

            # Configure dependency graph mock
            dep_instance = MagicMock()
            dep_instance.analyze_dependencies = AsyncMock(return_value=MagicMock(
                to_dict=lambda: {"nodes": [], "edges": [], "metrics": {}}
            ))
            dep_mock.return_value = dep_instance

            # Configure code analysis mock
            code_instance = MagicMock()
            code_instance.aggregate_analysis = AsyncMock(return_value=MagicMock(
                to_dict=lambda: {"complexity_profile": {"low": 50, "medium": 30, "high": 15, "very_high": 5}}
            ))
            code_mock.return_value = code_instance

            # Configure layered analysis mock
            layer_instance = MagicMock()
            layer_instance.analyze = AsyncMock(return_value={
                "vbscript_files": 23,
                "stored_procedures": 45,
                "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
            })
            layer_mock.return_value = layer_instance

            # Configure hierarchical extraction mock
            hier_instance = MagicMock()
            hier_instance.extract_stories = AsyncMock(return_value=MagicMock(
                to_dict=lambda: {
                    "epics": [{"id": "E1"}],
                    "features": [{"id": "F1"}],
                    "stories": [{"id": "S1"}],
                    "tasks": [{"id": "T1"}]
                },
                causal_relations=[]
            ))
            hier_mock.return_value = hier_instance

            # Configure deep extraction mock
            deep_instance = MagicMock()
            deep_instance.extract_with_council = AsyncMock(return_value={
                "stories": [],
                "conflicts": [],
                "confidence": 0.85
            })
            deep_mock.return_value = deep_instance

            # Configure estimation mock
            est_instance = MagicMock()
            est_instance.estimate_from_analysis = AsyncMock(return_value={
                "total_fp": 450,
                "total_sp": 320,
                "estimated_hours": 1200
            })
            est_mock.return_value = est_instance

            yield {
                "dependency": dep_mock,
                "code_analysis": code_mock,
                "layered": layer_mock,
                "hierarchical": hier_mock,
                "deep": deep_mock,
                "estimation": est_mock
            }

    @pytest.mark.asyncio
    async def test_phase1_code_understanding(self, mock_services, mock_db_session):
        """Test Phase 1 runs all three services."""
        from app.services.brown_paper_service import BrownPaperService

        service = BrownPaperService()
        options = EnhancedAnalysisOptions()

        result = await service._phase1_code_understanding("/test/path", options)

        assert result.success is True
        assert result.dependency_graph is not None
        assert result.code_analysis is not None
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_phase1_skips_vbscript_when_option_set(self, mock_services, mock_db_session):
        """Test Phase 1 skips VBScript analysis when option is set."""
        from app.services.brown_paper_service import BrownPaperService

        service = BrownPaperService()
        options = EnhancedAnalysisOptions(skip_vbscript=True)

        result = await service._phase1_code_understanding("/test/path", options)

        # LayeredAnalysis should not be called
        assert result.layered_analysis is None

    @pytest.mark.asyncio
    async def test_tier_affects_phases_run(self, mock_services, mock_db_session):
        """Test that tier correctly limits phases run."""
        # FREE tier should only run phase 1
        free_phases = TIER_PHASES[EnhancedAnalysisTier.FREE]
        assert free_phases == [1]

        # STANDARD tier should run phases 1-3
        standard_phases = TIER_PHASES[EnhancedAnalysisTier.STANDARD]
        assert 3 in standard_phases
        assert 4 not in standard_phases

    def test_cafcr_mapping(self):
        """Test CAFCR category mapping logic."""
        from app.services.brown_paper_service import BrownPaperService

        service = BrownPaperService()
        domains = [
            {"name": "UserUI", "type": "ui"},
            {"name": "UserService", "type": "service"},
            {"name": "UserModel", "type": "model"},
            {"name": "UserRepository", "type": "repository"},
            {"name": "PaymentProcessor", "type": "feature"}
        ]

        cafcr = service._map_to_cafcr(domains, {})

        assert "UserUI" in cafcr["Customer"]
        assert "UserService" in cafcr["Application"]
        assert "UserModel" in cafcr["Conceptual"]
        assert "UserRepository" in cafcr["Realization"]
        assert "PaymentProcessor" in cafcr["Functional"]

    def test_module_boundaries_extraction(self):
        """Test module boundary extraction from dependency graph."""
        from app.services.brown_paper_service import BrownPaperService

        service = BrownPaperService()
        dep_graph = {
            "nodes": [
                {"id": "user.service"},
                {"id": "user.repository"},
                {"id": "payment.service"},
                {"id": "payment.gateway"}
            ],
            "edges": []
        }

        boundaries = service._extract_module_boundaries(dep_graph)

        assert "user" in boundaries
        assert "payment" in boundaries
        assert len(boundaries["user"]) == 2
        assert len(boundaries["payment"]) == 2

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        from app.services.brown_paper_service import BrownPaperService

        service = BrownPaperService()

        # Test with all phases completed
        response = EnhancedAnalysisResponse(
            session_id="test",
            status="completed",
            tier=EnhancedAnalysisTier.STANDARD,
            phases_completed=[1, 2, 3, 4, 5, 6],
            phase4_result=Phase4Result(consensus_confidence=0.90)
        )

        confidence = service._calculate_confidence(response, target=0.80)

        # Should be close to target with high consensus
        assert 0.7 <= confidence <= 1.0

    def test_confidence_reduces_with_errors(self):
        """Test confidence is reduced when errors occur."""
        from app.services.brown_paper_service import BrownPaperService

        service = BrownPaperService()

        response = EnhancedAnalysisResponse(
            session_id="test",
            status="partial",
            tier=EnhancedAnalysisTier.STANDARD,
            phases_completed=[1, 2],
            errors=["Error 1", "Error 2", "Error 3"]
        )

        confidence = service._calculate_confidence(response, target=0.80)

        # Should be reduced due to errors
        assert confidence < 0.80


class TestEnhancedAnalysisAPI:
    """Test the enhanced analysis API endpoints."""

    @pytest.fixture
    def mock_service(self):
        """Create mock BrownPaperService."""
        with patch('app.api.brown_paper.get_brown_paper_service') as mock:
            service_instance = MagicMock()
            service_instance.get_session = MagicMock(return_value=MagicMock(
                enhanced_analysis={
                    "phase1_result": {"dependency_graph": {"nodes": []}},
                    "phase3_result": {"extraction_result": {"epics": [], "stories": []}},
                    "phase4_result": {"conflicts": [], "consensus_confidence": 0.85},
                    "phase5_result": {"estimation_result": {"total_fp": 100}}
                }
            ))
            service_instance.run_enhanced_analysis = AsyncMock(return_value=EnhancedAnalysisResponse(
                session_id="test-123",
                status="completed",
                tier=EnhancedAnalysisTier.STANDARD,
                phases_completed=[1, 2, 3],
                confidence=0.82
            ))
            mock.return_value = service_instance
            yield mock

    def test_enhanced_analysis_request_model(self):
        """Test request model validation."""
        from app.api.brown_paper import EnhancedAnalysisRequestModel

        request = EnhancedAnalysisRequestModel(
            tier="STANDARD",
            include_phases=[1, 2, 3],
            skip_vbscript=False,
            include_cira=True
        )

        assert request.tier == "STANDARD"
        assert request.include_cira is True

    def test_enhanced_analysis_response_model(self):
        """Test response model structure."""
        from app.api.brown_paper import EnhancedAnalysisResponseModel

        response = EnhancedAnalysisResponseModel(
            session_id="test-123",
            status="completed",
            tier="STANDARD",
            phases_completed=[1, 2, 3],
            confidence=0.82,
            total_duration_ms=5000
        )

        assert response.session_id == "test-123"
        assert len(response.phases_completed) == 3


# Integration test with real service calls (requires running services)
class TestEnhancedAnalysisIntegration:
    """Integration tests that require actual services."""

    @pytest.mark.skip(reason="Requires running services")
    @pytest.mark.asyncio
    async def test_full_enhanced_analysis_workflow(self):
        """Test complete 6-phase workflow end-to-end."""
        pass  # Implementation requires actual services

    @pytest.mark.skip(reason="Requires running services")
    @pytest.mark.asyncio
    async def test_tier_premium_includes_human_review(self):
        """Test PREMIUM tier triggers human review for high conflicts."""
        pass  # Implementation requires actual services
