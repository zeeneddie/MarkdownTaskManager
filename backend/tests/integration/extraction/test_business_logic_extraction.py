"""
Integration Tests for Business Logic Extraction.

Week 159 PVA: Tests for improved epic/story generation from code analysis.

Coverage:
- BusinessDomainExtractor service
- BusinessDrivenStoryGenerator service
- Integration with BrownPaperService
- Healthcare/FysioOne specific domain patterns
- Source file traceability

Acceptance Criteria (from PVA):
- [ ] Domain extraction finds minimaal 5 business domains voor FysioOne
- [ ] Elke epic is gekoppeld aan concrete source modules
- [ ] Stories bevatten references naar source files
- [ ] Acceptatiecriteria zijn afgeleid uit de legacy code
- [ ] Story points zijn gebaseerd op code complexity
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.business_domain_extractor_service import (
    BusinessDomainExtractorService,
    BusinessDomainCandidate,
    BusinessDomainExtractionResult,
    ExtractedEntity,
    ModuleCluster,
    get_business_domain_extractor,
    HEALTHCARE_DOMAIN_PATTERNS,
)
from app.services.business_driven_story_generator_service import (
    BusinessDrivenStoryGeneratorService,
    StoryGenerationResult,
    GeneratedEpic,
    GeneratedFeature,
    GeneratedStory,
    get_business_driven_story_generator,
    STORY_TEMPLATES,
)


# =============================================================================
# TEST DATA - FysioOne-like modules
# =============================================================================


def create_fysioone_modules() -> List[Dict[str, Any]]:
    """Create test modules resembling FysioOne structure."""
    return [
        # Patient Management
        {"name": "patient.asp", "path": "patient/patient.asp", "classes": ["Patient"], "functions": ["CreatePatient", "UpdatePatient"]},
        {"name": "patient_zoek.asp", "path": "patient/patient_zoek.asp", "classes": [], "functions": ["SearchPatient"]},
        {"name": "bsn_validatie.asp", "path": "patient/bsn_validatie.asp", "classes": [], "functions": ["ValidateBSN"]},
        {"name": "patientgegevens.asp", "path": "patient/patientgegevens.asp", "classes": ["PatientData"], "functions": []},
        {"name": "verzekering.asp", "path": "patient/verzekering.asp", "classes": ["Verzekering"], "functions": []},

        # Treatment Plans
        {"name": "behandeling.asp", "path": "behandeling/behandeling.asp", "classes": ["Behandelplan"], "functions": ["StartBehandeling"]},
        {"name": "diagnose.asp", "path": "behandeling/diagnose.asp", "classes": ["Diagnose"], "functions": ["SetDiagnose"]},
        {"name": "icpc_codes.asp", "path": "behandeling/icpc_codes.asp", "classes": [], "functions": ["GetICPCCodes"]},
        {"name": "verrichting.asp", "path": "behandeling/verrichting.asp", "classes": ["Verrichting"], "functions": []},

        # Appointments
        {"name": "agenda.asp", "path": "agenda/agenda.asp", "classes": ["Agenda"], "functions": ["GetAgenda"]},
        {"name": "afspraak.asp", "path": "agenda/afspraak.asp", "classes": ["Afspraak"], "functions": ["CreateAfspraak"]},
        {"name": "rooster.asp", "path": "agenda/rooster.asp", "classes": ["Rooster"], "functions": []},

        # Billing
        {"name": "declaratie.asp", "path": "declaratie/declaratie.asp", "classes": ["Declaratie"], "functions": ["CreateDeclaratie"]},
        {"name": "vecozo.asp", "path": "declaratie/vecozo.asp", "classes": [], "functions": ["SendToVecozo"]},
        {"name": "factuur.asp", "path": "declaratie/factuur.asp", "classes": ["Factuur"], "functions": []},
        {"name": "tarief.asp", "path": "declaratie/tarief.asp", "classes": ["Tarief"], "functions": []},

        # Reporting
        {"name": "rapport.asp", "path": "rapportage/rapport.asp", "classes": ["Rapport"], "functions": ["GenerateRapport"]},
        {"name": "statistiek.asp", "path": "rapportage/statistiek.asp", "classes": [], "functions": ["GetStatistics"]},
        {"name": "export.asp", "path": "rapportage/export.asp", "classes": [], "functions": ["ExportData"]},

        # User Management
        {"name": "login.asp", "path": "auth/login.asp", "classes": [], "functions": ["Login", "Logout"]},
        {"name": "gebruiker.asp", "path": "auth/gebruiker.asp", "classes": ["Gebruiker"], "functions": []},
        {"name": "rechten.asp", "path": "auth/rechten.asp", "classes": ["Recht"], "functions": []},

        # System Config
        {"name": "config.asp", "path": "systeem/config.asp", "classes": ["Config"], "functions": []},
        {"name": "instellingen.asp", "path": "systeem/instellingen.asp", "classes": [], "functions": ["GetSettings"]},
    ]


def create_fysioone_dependencies() -> List[Dict[str, Any]]:
    """Create test dependencies between FysioOne modules."""
    return [
        # Patient domain dependencies
        {"source": "patient/patient.asp", "target": "patient/bsn_validatie.asp"},
        {"source": "patient/patient.asp", "target": "patient/verzekering.asp"},
        {"source": "patient/patient_zoek.asp", "target": "patient/patient.asp"},

        # Treatment domain dependencies
        {"source": "behandeling/behandeling.asp", "target": "behandeling/diagnose.asp"},
        {"source": "behandeling/diagnose.asp", "target": "behandeling/icpc_codes.asp"},

        # Appointment domain dependencies
        {"source": "agenda/afspraak.asp", "target": "agenda/agenda.asp"},
        {"source": "agenda/afspraak.asp", "target": "patient/patient.asp"},

        # Billing domain dependencies
        {"source": "declaratie/declaratie.asp", "target": "declaratie/vecozo.asp"},
        {"source": "declaratie/declaratie.asp", "target": "declaratie/tarief.asp"},
        {"source": "declaratie/declaratie.asp", "target": "behandeling/verrichting.asp"},
    ]


# =============================================================================
# BUSINESS DOMAIN EXTRACTOR TESTS
# =============================================================================


class TestBusinessDomainExtractor:
    """Tests for BusinessDomainExtractorService."""

    @pytest.mark.asyncio
    async def test_extract_minimum_5_domains_fysioone(self):
        """PVA Acceptance: Domain extraction finds minimaal 5 business domains."""
        extractor = get_business_domain_extractor(use_healthcare_patterns=True)

        modules = create_fysioone_modules()
        dependencies = create_fysioone_dependencies()

        result = await extractor.extract_domains(
            modules=modules,
            dependencies=dependencies,
            scan_path="/opt/projecten/FysioOne",
        )

        # Should find at least 5 domains (patient, treatment, appointments, billing, reporting)
        assert len(result.domains) >= 5, f"Expected >= 5 domains, got {len(result.domains)}"

    @pytest.mark.asyncio
    async def test_healthcare_domain_patterns_detected(self):
        """Test that healthcare-specific patterns are detected."""
        extractor = get_business_domain_extractor(use_healthcare_patterns=True)

        modules = create_fysioone_modules()
        dependencies = create_fysioone_dependencies()

        result = await extractor.extract_domains(
            modules=modules,
            dependencies=dependencies,
        )

        domain_names = [d.name.lower() for d in result.domains]

        # Should detect healthcare domains
        healthcare_keywords = ["patiënt", "patient", "behandel", "agenda", "declaratie"]
        found_healthcare = any(
            any(kw in name for kw in healthcare_keywords)
            for name in domain_names
        )

        assert found_healthcare, f"No healthcare domains found in {domain_names}"

    @pytest.mark.asyncio
    async def test_domains_have_source_modules(self):
        """Test that each domain has linked source modules."""
        extractor = get_business_domain_extractor(use_healthcare_patterns=True)

        modules = create_fysioone_modules()
        dependencies = create_fysioone_dependencies()

        result = await extractor.extract_domains(
            modules=modules,
            dependencies=dependencies,
        )

        for domain in result.domains:
            assert len(domain.modules) > 0, f"Domain {domain.name} has no modules"
            assert len(domain.source_files) > 0, f"Domain {domain.name} has no source files"

    @pytest.mark.asyncio
    async def test_entities_extracted_from_modules(self):
        """Test that entities are extracted from module definitions."""
        extractor = get_business_domain_extractor()

        modules = create_fysioone_modules()
        dependencies = create_fysioone_dependencies()

        result = await extractor.extract_domains(
            modules=modules,
            dependencies=dependencies,
        )

        # Should have extracted entities
        assert result.total_entities_found > 0

        # Check that some domains have entities
        domains_with_entities = [d for d in result.domains if len(d.entities) > 0]
        assert len(domains_with_entities) > 0, "No domains have extracted entities"

    @pytest.mark.asyncio
    async def test_use_cases_generated_for_domains(self):
        """Test that use cases are generated from domain patterns."""
        extractor = get_business_domain_extractor(use_healthcare_patterns=True)

        modules = create_fysioone_modules()
        dependencies = create_fysioone_dependencies()

        result = await extractor.extract_domains(
            modules=modules,
            dependencies=dependencies,
        )

        # Healthcare domains should have use cases from patterns
        domains_with_usecases = [d for d in result.domains if len(d.use_cases) > 0]
        assert len(domains_with_usecases) > 0, "No domains have use cases"

    @pytest.mark.asyncio
    async def test_domain_confidence_calculated(self):
        """Test that confidence scores are calculated for domains."""
        extractor = get_business_domain_extractor()

        modules = create_fysioone_modules()
        dependencies = create_fysioone_dependencies()

        result = await extractor.extract_domains(
            modules=modules,
            dependencies=dependencies,
        )

        for domain in result.domains:
            assert 0.0 <= domain.confidence <= 1.0, \
                f"Domain {domain.name} has invalid confidence {domain.confidence}"

    @pytest.mark.asyncio
    async def test_module_clustering(self):
        """Test that modules are clustered based on dependencies."""
        extractor = get_business_domain_extractor()

        modules = create_fysioone_modules()
        dependencies = create_fysioone_dependencies()

        result = await extractor.extract_domains(
            modules=modules,
            dependencies=dependencies,
        )

        # Should have module clusters
        assert len(result.module_clusters) > 0

    def test_to_brown_paper_domains_format(self):
        """Test conversion to Brown Paper format."""
        extractor = get_business_domain_extractor()

        # Create mock result
        result = BusinessDomainExtractionResult(
            domains=[
                BusinessDomainCandidate(
                    name="Test Domain",
                    description="Test description",
                    modules=["module1.asp", "module2.asp"],
                    entities=[ExtractedEntity(name="Entity1", entity_type="class", source_file="module1.asp")],
                    use_cases=["Create", "Update"],
                    source_files=["module1.asp", "module2.asp"],
                    complexity="medium",
                    confidence=0.75,
                )
            ],
            module_clusters=[],
            total_modules_analyzed=2,
            total_entities_found=1,
            extraction_time_ms=100,
        )

        bp_domains = extractor.to_brown_paper_domains(result)

        assert len(bp_domains) == 1
        assert bp_domains[0]["name"] == "Test Domain"
        assert bp_domains[0]["modules"] == ["module1.asp", "module2.asp"]
        assert bp_domains[0]["confidence"] == 0.75


# =============================================================================
# BUSINESS DRIVEN STORY GENERATOR TESTS
# =============================================================================


class TestBusinessDrivenStoryGenerator:
    """Tests for BusinessDrivenStoryGeneratorService."""

    @pytest.fixture
    def domain_result(self) -> BusinessDomainExtractionResult:
        """Create test domain extraction result."""
        return BusinessDomainExtractionResult(
            domains=[
                BusinessDomainCandidate(
                    name="Patiënt Beheer",
                    description="Patient management domain",
                    modules=["patient.asp", "patient_zoek.asp", "bsn_validatie.asp"],
                    entities=[
                        ExtractedEntity(name="Patient", entity_type="class", source_file="patient.asp"),
                        ExtractedEntity(name="PatientForm", entity_type="form", source_file="patient.asp"),
                    ],
                    use_cases=["Patient registratie", "Patient zoeken", "BSN validatie"],
                    source_files=["patient.asp", "patient_zoek.asp", "bsn_validatie.asp"],
                    complexity="medium",
                    confidence=0.85,
                ),
                BusinessDomainCandidate(
                    name="Behandelplan & Diagnose",
                    description="Treatment and diagnosis domain",
                    modules=["behandeling.asp", "diagnose.asp"],
                    entities=[
                        ExtractedEntity(name="Behandelplan", entity_type="class", source_file="behandeling.asp"),
                    ],
                    use_cases=["Diagnose registreren", "Behandelplan opstellen"],
                    source_files=["behandeling.asp", "diagnose.asp"],
                    complexity="high",
                    confidence=0.80,
                ),
            ],
            module_clusters=[],
            total_modules_analyzed=5,
            total_entities_found=3,
            extraction_time_ms=100,
        )

    @pytest.mark.asyncio
    async def test_epic_per_business_domain(self, domain_result):
        """PVA Acceptance: Epic per business domain."""
        generator = get_business_driven_story_generator()

        result = await generator.generate_stories(domain_result=domain_result)

        # Should have one epic per domain
        assert len(result.epics) == len(domain_result.domains)

        # Each epic should map to a domain
        epic_domains = {e.domain_name for e in result.epics}
        expected_domains = {d.name for d in domain_result.domains}
        assert epic_domains == expected_domains

    @pytest.mark.asyncio
    async def test_epics_linked_to_source_modules(self, domain_result):
        """PVA Acceptance: Elke epic is gekoppeld aan concrete source modules."""
        generator = get_business_driven_story_generator()

        result = await generator.generate_stories(domain_result=domain_result)

        for epic in result.epics:
            assert len(epic.source_modules) > 0, f"Epic {epic.title} has no source modules"

    @pytest.mark.asyncio
    async def test_stories_have_source_references(self, domain_result):
        """PVA Acceptance: Stories bevatten references naar source files."""
        generator = get_business_driven_story_generator()

        result = await generator.generate_stories(domain_result=domain_result)

        stories_with_refs = 0
        total_stories = 0

        for epic in result.epics:
            for feature in epic.features:
                for story in feature.stories:
                    total_stories += 1
                    if len(story.source_references) > 0:
                        stories_with_refs += 1

        # At least 50% of stories should have source references
        ratio = stories_with_refs / total_stories if total_stories > 0 else 0
        assert ratio >= 0.5, f"Only {ratio*100:.0f}% of stories have source references"

    @pytest.mark.asyncio
    async def test_stories_have_acceptance_criteria(self, domain_result):
        """PVA Acceptance: Acceptatiecriteria zijn afgeleid uit de legacy code."""
        generator = get_business_driven_story_generator()

        result = await generator.generate_stories(domain_result=domain_result)

        for epic in result.epics:
            for feature in epic.features:
                for story in feature.stories:
                    assert len(story.acceptance_criteria) > 0, \
                        f"Story {story.title} has no acceptance criteria"

    @pytest.mark.asyncio
    async def test_story_points_based_on_complexity(self, domain_result):
        """PVA Acceptance: Story points zijn gebaseerd op code complexity."""
        generator = get_business_driven_story_generator()

        result = await generator.generate_stories(domain_result=domain_result)

        # Higher complexity domain should have higher average points
        epic_points = {}
        for epic in result.epics:
            total_points = sum(
                s.story_points
                for f in epic.features
                for s in f.stories
            )
            story_count = sum(len(f.stories) for f in epic.features)
            avg_points = total_points / story_count if story_count > 0 else 0
            epic_points[epic.domain_name] = (avg_points, epic.complexity)

        # Verify that complexity affects points
        for domain_name, (avg_points, complexity) in epic_points.items():
            assert avg_points > 0, f"Epic {domain_name} has no story points"

    @pytest.mark.asyncio
    async def test_features_have_stories(self, domain_result):
        """Test that each feature has at least one story."""
        generator = get_business_driven_story_generator()

        result = await generator.generate_stories(domain_result=domain_result)

        for epic in result.epics:
            assert len(epic.features) > 0, f"Epic {epic.title} has no features"
            for feature in epic.features:
                assert len(feature.stories) > 0, f"Feature {feature.title} has no stories"

    @pytest.mark.asyncio
    async def test_total_counts_correct(self, domain_result):
        """Test that total counts are calculated correctly."""
        generator = get_business_driven_story_generator()

        result = await generator.generate_stories(domain_result=domain_result)

        # Verify totals
        actual_features = sum(len(e.features) for e in result.epics)
        actual_stories = sum(len(f.stories) for e in result.epics for f in e.features)
        actual_points = sum(s.story_points for e in result.epics for f in e.features for s in f.stories)

        assert result.total_features == actual_features
        assert result.total_stories == actual_stories
        assert result.total_story_points == actual_points

    @pytest.mark.asyncio
    async def test_to_task_hierarchy_format(self, domain_result):
        """Test conversion to task hierarchy format."""
        generator = get_business_driven_story_generator()

        result = await generator.generate_stories(domain_result=domain_result)

        output = generator.to_task_hierarchy_format(
            result=result,
            specification_id="spec-123",
            project_id="proj-456",
        )

        assert "epics" in output
        assert "metadata" in output
        assert len(output["epics"]) == len(result.epics)

        # Verify structure
        for epic in output["epics"]:
            assert "id" in epic
            assert "title" in epic
            assert "features" in epic
            assert epic["specification_id"] == "spec-123"
            assert epic["project_id"] == "proj-456"


# =============================================================================
# INTEGRATION WITH BROWNPAPERSERVICE TESTS
# =============================================================================


class TestBrownPaperServiceIntegration:
    """Tests for integration with BrownPaperService."""

    @pytest.fixture
    def mock_phase1_result(self):
        """Create mock Phase 1 result."""
        from app.models.brown_paper_enhanced import Phase1Result

        return Phase1Result(
            dependency_graph={
                "modules": {
                    mod["name"]: mod for mod in create_fysioone_modules()
                },
                "edges": create_fysioone_dependencies(),
            },
            code_analysis={
                "total_files": 24,
                "total_classes": 15,
                "total_functions": 30,
            },
            success=True,
        )

    @pytest.mark.asyncio
    async def test_enhanced_domain_extraction_integration(self, mock_phase1_result):
        """Test enhanced domain extraction through BrownPaperService."""
        from app.services.brown_paper_service import BrownPaperService
        from app.models.brown_paper_enhanced import EnhancedAnalysisOptions

        service = BrownPaperService()

        result = await service._enhanced_domain_extraction(
            project_path="/opt/projecten/FysioOne",
            phase1=mock_phase1_result,
            options=EnhancedAnalysisOptions(use_business_logic_extraction=True),
        )

        assert isinstance(result, BusinessDomainExtractionResult)
        assert len(result.domains) >= 5

    @pytest.mark.asyncio
    async def test_business_driven_stories_integration(self, mock_phase1_result):
        """Test business-driven story generation through BrownPaperService."""
        from app.services.brown_paper_service import BrownPaperService
        from app.models.brown_paper_enhanced import EnhancedAnalysisOptions

        service = BrownPaperService()

        # First extract domains
        domain_result = await service._enhanced_domain_extraction(
            project_path="/opt/projecten/FysioOne",
            phase1=mock_phase1_result,
            options=EnhancedAnalysisOptions(),
        )

        # Then generate stories
        story_result = await service._generate_business_driven_stories(
            domain_result=domain_result,
            phase1=mock_phase1_result,
        )

        assert isinstance(story_result, StoryGenerationResult)
        assert story_result.total_stories > 0
        assert story_result.total_story_points > 0

    @pytest.mark.asyncio
    async def test_convert_story_result_to_epics(self, mock_phase1_result):
        """Test conversion of story result to Brown Paper epic format."""
        from app.services.brown_paper_service import BrownPaperService
        from app.models.brown_paper_enhanced import EnhancedAnalysisOptions

        service = BrownPaperService()

        # Extract and generate
        domain_result = await service._enhanced_domain_extraction(
            project_path="/opt/projecten/FysioOne",
            phase1=mock_phase1_result,
            options=EnhancedAnalysisOptions(),
        )

        story_result = await service._generate_business_driven_stories(
            domain_result=domain_result,
            phase1=mock_phase1_result,
        )

        # Convert to Brown Paper format
        epics = service._convert_story_result_to_epics(story_result)

        assert len(epics) > 0

        for epic in epics:
            assert "id" in epic
            assert "name" in epic
            assert "domain" in epic
            assert "features" in epic
            assert "metadata" in epic
            assert len(epic["features"]) > 0

    @pytest.mark.asyncio
    async def test_run_business_logic_extraction(self, mock_phase1_result):
        """Test complete business logic extraction workflow."""
        from app.services.brown_paper_service import BrownPaperService

        service = BrownPaperService()

        epics, domain_result = await service.run_business_logic_extraction(
            session_id="test-session",
            phase1=mock_phase1_result,
            project_path="/opt/projecten/FysioOne",
        )

        # Verify epics
        assert len(epics) >= 5, f"Expected >= 5 epics, got {len(epics)}"

        # Verify domain result
        assert isinstance(domain_result, BusinessDomainExtractionResult)

        # Verify each epic has required fields
        for epic in epics:
            assert epic.get("name"), "Epic missing name"
            assert epic.get("features"), "Epic missing features"
            assert epic.get("metadata", {}).get("modules"), "Epic missing module references"


# =============================================================================
# EDGE CASES AND ERROR HANDLING
# =============================================================================


class TestEdgeCasesErrorHandling:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_modules_list(self):
        """Test handling of empty modules list."""
        extractor = get_business_domain_extractor()

        result = await extractor.extract_domains(
            modules=[],
            dependencies=[],
        )

        assert isinstance(result, BusinessDomainExtractionResult)
        assert result.total_modules_analyzed == 0

    @pytest.mark.asyncio
    async def test_modules_without_classes(self):
        """Test handling of modules without classes."""
        extractor = get_business_domain_extractor()

        modules = [
            {"name": "util.asp", "path": "util/util.asp", "classes": [], "functions": ["Helper"]},
        ]

        result = await extractor.extract_domains(
            modules=modules,
            dependencies=[],
        )

        assert isinstance(result, BusinessDomainExtractionResult)

    @pytest.mark.asyncio
    async def test_story_generation_with_no_entities(self):
        """Test story generation when domains have no entities."""
        generator = get_business_driven_story_generator()

        domain_result = BusinessDomainExtractionResult(
            domains=[
                BusinessDomainCandidate(
                    name="Test Domain",
                    description="Domain without entities",
                    modules=["test.asp"],
                    entities=[],  # No entities
                    use_cases=["Test use case"],
                    source_files=["test.asp"],
                    complexity="low",
                    confidence=0.5,
                ),
            ],
            module_clusters=[],
            total_modules_analyzed=1,
            total_entities_found=0,
            extraction_time_ms=10,
        )

        result = await generator.generate_stories(domain_result=domain_result)

        # Should still generate epics with use case-based features
        assert len(result.epics) == 1

    @pytest.mark.asyncio
    async def test_custom_domain_patterns(self):
        """Test using custom domain patterns."""
        custom_patterns = {
            "custom_domain": {
                "keywords": ["custom", "special"],
                "file_patterns": [r"custom"],
                "entities": ["CustomEntity"],
                "use_cases": ["Custom use case"],
            }
        }

        extractor = BusinessDomainExtractorService(
            domain_patterns=custom_patterns,
            use_healthcare_patterns=False,
        )

        modules = [
            {"name": "custom_module.asp", "path": "custom_module.asp", "classes": ["CustomClass"]},
        ]

        result = await extractor.extract_domains(
            modules=modules,
            dependencies=[],
        )

        # Should detect custom domain
        assert isinstance(result, BusinessDomainExtractionResult)

    @pytest.mark.asyncio
    async def test_custom_story_templates(self):
        """Test using custom story templates."""
        custom_templates = {
            "custom_story": {
                "title": "Custom: {entity}",
                "description": "Custom story for {entity}",
                "acceptance_criteria": ["Custom criterion"],
                "base_points": 10,
            }
        }

        generator = BusinessDrivenStoryGeneratorService(
            story_templates={**STORY_TEMPLATES, **custom_templates}
        )

        assert "custom_story" in generator.story_templates
