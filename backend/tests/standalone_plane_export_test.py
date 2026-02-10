#!/usr/bin/env python3
"""
Standalone test for Plane Export module.

Tests:
1. Pydantic models - JSON round-trip serialization
2. Priority mapper - All edge cases
3. Assembler - Full M8 tree to PlaneExportPackage
4. CRUD dependencies - blocked_by chain correctness
5. Serializers - JSON + ADR-002 markdown output
6. Backward compatibility - M8 dataclass fields have defaults

Usage:
    cd backend
    .venv/bin/python3 tests/standalone_plane_export_test.py
"""

import json
import os
import shutil
import sys
import tempfile
from dataclasses import field
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# Test Helpers
# =============================================================================

def _make_test_generation_result():
    """Create a realistic M8 StoryGenerationResult for testing."""
    from app.services.business_driven_story_generator_service import (
        AcceptanceCriterion,
        GeneratedEpic,
        GeneratedFeature,
        GeneratedStory,
        SourceReference,
        StoryGenerationResult,
    )

    stories_crud = [
        GeneratedStory(
            id="STORY-001-001-001",
            title="Migreer Patient aanmaken functionaliteit",
            description="Migreer de legacy functionaliteit voor het aanmaken van een nieuwe Patient.",
            feature_id="FEAT-001-001",
            story_points=5,
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="AC-STORY-001-001-001-01",
                    description="Alle velden uit legacy form zijn beschikbaar in nieuwe UI",
                    test_type="functional",
                ),
                AcceptanceCriterion(
                    id="AC-STORY-001-001-001-02",
                    description="Validatie regels zijn behouden",
                    test_type="validation",
                    source_hint="Patient.cs:ValidateAge()",
                ),
            ],
            source_references=[
                SourceReference(
                    file_path="src/Models/Patient.cs",
                    line_start=10,
                    line_end=45,
                    element_type="class",
                ),
            ],
            complexity="medium",
            story_type="crud",
            legacy_functionality="Legacy: src/Models/Patient.cs",
            target_implementation="Modern: PatientService.create()",
        ),
        GeneratedStory(
            id="STORY-001-001-002",
            title="Migreer Patient ophalen/tonen",
            description="Migreer de legacy functionaliteit voor het ophalen en tonen van Patient gegevens.",
            feature_id="FEAT-001-001",
            story_points=3,
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="AC-STORY-001-001-002-01",
                    description="Alle legacy velden worden correct getoond",
                    test_type="functional",
                ),
            ],
            source_references=[
                SourceReference(
                    file_path="src/Models/Patient.cs",
                    line_start=10,
                    line_end=45,
                    element_type="class",
                ),
            ],
            complexity="medium",
            story_type="crud",
            blocked_by=["STORY-001-001-001"],
        ),
        GeneratedStory(
            id="STORY-001-001-003",
            title="Migreer Patient wijzigen",
            description="Migreer de legacy functionaliteit voor het wijzigen van Patient gegevens.",
            feature_id="FEAT-001-001",
            story_points=5,
            acceptance_criteria=[],
            source_references=[],
            complexity="medium",
            story_type="crud",
            blocked_by=["STORY-001-001-001"],
        ),
        GeneratedStory(
            id="STORY-001-001-004",
            title="Migreer Patient verwijderen",
            description="Migreer de legacy functionaliteit voor het verwijderen van Patient records.",
            feature_id="FEAT-001-001",
            story_points=3,
            acceptance_criteria=[],
            source_references=[],
            complexity="medium",
            story_type="crud",
            blocked_by=["STORY-001-001-002"],
        ),
    ]

    feature_crud = GeneratedFeature(
        id="FEAT-001-001",
        title="Patient Data Beheer",
        description="CRUD operaties voor patient entiteiten",
        epic_id="EPIC-001",
        stories=stories_crud,
        source_modules=["src/Models/Patient.cs"],
        estimated_story_points=16,
        complexity="medium",
    )

    story_business = GeneratedStory(
        id="STORY-001-002-001",
        title="Implementeer BSN validatie",
        description="Implementeer de BSN validatie business rule.",
        feature_id="FEAT-001-002",
        story_points=5,
        acceptance_criteria=[
            AcceptanceCriterion(
                id="AC-STORY-001-002-001-01",
                description="BSN 11-proef validatie werkt correct",
                test_type="validation",
            ),
        ],
        source_references=[
            SourceReference(
                file_path="src/Validation/BsnValidator.cs",
                line_start=1,
                element_type="class",
            ),
        ],
        complexity="high",
        story_type="business_rule",
        business_value="Wettelijke verplichting - BSN moet geldig zijn",
    )

    feature_business = GeneratedFeature(
        id="FEAT-001-002",
        title="BSN Validatie",
        description="Business rule voor BSN controle",
        epic_id="EPIC-001",
        stories=[story_business],
        source_modules=["src/Validation/BsnValidator.cs"],
        estimated_story_points=5,
        complexity="high",
    )

    epic = GeneratedEpic(
        id="EPIC-001",
        title="Patiëntbeheer Migratie",
        description="Migratie van alle patiëntbeheer gerelateerde functionaliteit.",
        domain_name="Patiëntbeheer",
        features=[feature_crud, feature_business],
        source_modules=["src/Models/Patient.cs", "src/Validation/BsnValidator.cs"],
        estimated_story_points=21,
        estimated_weeks=2,
        complexity="medium",
        metadata={
            "domain_confidence": 0.92,
            "entity_count": 3,
            "use_case_count": 5,
            "source_file_count": 8,
        },
    )

    return StoryGenerationResult(
        epics=[epic],
        total_stories=5,
        total_story_points=21,
        total_features=2,
        generation_time_ms=150,
        metadata={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "domains_processed": 1,
            "velocity_used": 20,
        },
    )


# =============================================================================
# Test 1: Pydantic Models - JSON Round-trip
# =============================================================================

def test_models_json_roundtrip():
    """Test PlaneExportPackage JSON serialization and deserialization."""
    from app.services.plane_export.models import (
        ExportAcceptanceCriterion,
        ExportEpic,
        ExportFeature,
        ExportProjectSummary,
        ExportRelation,
        ExportSourceReference,
        ExportStory,
        PlanePriority,
        PlaneExportPackage,
        PlaneStatus,
        RelationType,
    )

    story = ExportStory(
        id="STORY-001",
        title="Test Story",
        description="A test story",
        feature_id="FEAT-001",
        story_points=5,
        complexity="medium",
        story_type="crud",
        priority=PlanePriority.high,
        status=PlaneStatus.backlog,
        acceptance_criteria=[
            ExportAcceptanceCriterion(
                id="AC-001",
                description="Test criterion",
                test_type="functional",
                source_hint="test.py:42",
            ),
        ],
        source_references=[
            ExportSourceReference(
                file_path="src/test.py",
                line_start=10,
                line_end=20,
                element_type="class",
            ),
        ],
        legacy_functionality="Legacy: old_module.py",
        blocked_by=["STORY-000"],
    )

    feature = ExportFeature(
        id="FEAT-001",
        title="Test Feature",
        description="A test feature",
        epic_id="EPIC-001",
        stories=[story],
        estimated_story_points=5,
    )

    epic = ExportEpic(
        id="EPIC-001",
        title="Test Epic",
        description="A test epic",
        domain_name="TestDomain",
        features=[feature],
        estimated_story_points=5,
        priority=PlanePriority.high,
    )

    package = PlaneExportPackage(
        session_id="test-session",
        project_summary=ExportProjectSummary(
            project_path="/test",
            project_name="TestProject",
            total_epics=1,
            total_features=1,
            total_stories=1,
            total_story_points=5,
        ),
        epics=[epic],
        relations=[
            ExportRelation(
                source_id="STORY-001",
                target_id="STORY-000",
                relation_type=RelationType.blocked_by,
                reason="CRUD dependency",
            ),
        ],
    )

    # Serialize to JSON
    json_str = package.model_dump_json(indent=2)
    assert json_str, "JSON serialization produced empty string"

    # Parse back
    parsed = json.loads(json_str)
    assert parsed["version"] == "1.0.0"
    assert parsed["source"] == "marqed"
    assert len(parsed["epics"]) == 1
    assert parsed["epics"][0]["priority"] == "high"
    assert len(parsed["epics"][0]["features"][0]["stories"][0]["acceptance_criteria"]) == 1
    assert parsed["epics"][0]["features"][0]["stories"][0]["legacy_functionality"] == "Legacy: old_module.py"
    assert parsed["relations"][0]["relation_type"] == "blocked_by"

    # Deserialize back to model
    roundtrip = PlaneExportPackage.model_validate_json(json_str)
    assert roundtrip.version == "1.0.0"
    assert roundtrip.epics[0].priority == PlanePriority.high
    assert len(roundtrip.epics[0].features[0].stories[0].acceptance_criteria) == 1

    print("  PASS: JSON round-trip serialization")
    return True


# =============================================================================
# Test 2: Priority Mapper
# =============================================================================

def test_priority_mapper():
    """Test priority inference from various signal combinations."""
    from app.services.plane_export.priority_mapper import PriorityMapper
    from app.services.plane_export.models import PlanePriority

    mapper = PriorityMapper()

    # Test 1: Peter priority takes precedence
    result = mapper.map_story_priority(
        story_priority="low",
        peter_priority="critical",
    )
    assert result == PlanePriority.urgent, f"Peter critical -> urgent, got {result}"
    print("  PASS: Peter priority takes precedence")

    # Test 2: Explicit non-default M8 priority
    result = mapper.map_story_priority(
        story_priority="high",
    )
    assert result == PlanePriority.high, f"M8 high -> high, got {result}"
    print("  PASS: Explicit M8 priority")

    # Test 3: Story type inference (data_migration = high)
    result = mapper.map_story_priority(
        story_type="data_migration",
    )
    assert result == PlanePriority.high, f"data_migration -> high, got {result}"
    print("  PASS: Story type data_migration -> high")

    # Test 4: High domain confidence boost
    result = mapper.map_story_priority(
        domain_confidence=0.92,
    )
    assert result == PlanePriority.high, f"confidence 0.92 -> high, got {result}"
    print("  PASS: High domain confidence -> high")

    # Test 5: Low domain confidence
    result = mapper.map_story_priority(
        domain_confidence=0.3,
    )
    assert result == PlanePriority.medium, f"confidence 0.3 -> medium (complexity default), got {result}"
    print("  PASS: Low domain confidence -> medium/low")

    # Test 6: very_high complexity boost
    result = mapper.map_story_priority(
        complexity="very_high",
    )
    assert result == PlanePriority.high, f"very_high complexity -> high, got {result}"
    print("  PASS: Very high complexity -> high")

    # Test 7: Default (all medium signals)
    result = mapper.map_story_priority()
    assert result == PlanePriority.medium, f"Default -> medium, got {result}"
    print("  PASS: Default -> medium")

    # Test 8: Epic priority from domain confidence + features
    result = mapper.map_epic_priority(
        domain_confidence=0.90,
        feature_priorities=[PlanePriority.medium, PlanePriority.high],
    )
    assert result == PlanePriority.high, f"Epic priority -> high, got {result}"
    print("  PASS: Epic priority combines signals")

    return True


# =============================================================================
# Test 3: Assembler
# =============================================================================

def test_assembler():
    """Test PlaneExportAssembler with realistic M8 data."""
    from app.services.plane_export.assembler import PlaneExportAssembler
    from app.services.plane_export.models import PlanePriority, PlaneStatus

    generation_result = _make_test_generation_result()

    assembler = PlaneExportAssembler()
    package = assembler.assemble(
        generation_result=generation_result,
        estimation_result=None,
        peter_enrichments=None,
        project_context={"project_path": "/opt/projecten/test"},
        session_id="test-session-001",
        domain_data={
            "domains": [
                {"name": "Patiëntbeheer", "confidence": 0.92},
            ],
        },
    )

    # Verify package structure
    assert package.version == "1.0.0"
    assert package.session_id == "test-session-001"
    assert package.source == "marqed"
    assert len(package.epics) == 1
    print("  PASS: Package structure correct")

    epic = package.epics[0]
    assert epic.id == "EPIC-001"
    assert epic.domain_name == "Patiëntbeheer"
    assert len(epic.features) == 2
    # High domain confidence (0.92) should boost epic priority
    assert epic.priority in (PlanePriority.high, PlanePriority.urgent), f"Epic priority: {epic.priority}"
    print("  PASS: Epic assembled with priority from domain confidence")

    # Verify feature
    crud_feature = epic.features[0]
    assert crud_feature.id == "FEAT-001-001"
    assert len(crud_feature.stories) == 4
    print("  PASS: CRUD feature with 4 stories")

    # Verify story data preservation (NOT lost like _epic_to_dict)
    create_story = crud_feature.stories[0]
    assert create_story.id == "STORY-001-001-001"
    assert len(create_story.acceptance_criteria) == 2, "Acceptance criteria preserved"
    assert create_story.acceptance_criteria[0].description == "Alle velden uit legacy form zijn beschikbaar in nieuwe UI"
    assert create_story.acceptance_criteria[1].source_hint == "Patient.cs:ValidateAge()"
    print("  PASS: Acceptance criteria preserved (not lost)")

    assert len(create_story.source_references) == 1, "Source references preserved"
    assert create_story.source_references[0].line_start == 10
    assert create_story.source_references[0].line_end == 45
    print("  PASS: Source references with line numbers preserved")

    assert create_story.legacy_functionality == "Legacy: src/Models/Patient.cs"
    assert create_story.target_implementation == "Modern: PatientService.create()"
    print("  PASS: Legacy/target implementation preserved")

    # Verify blocked_by
    read_story = crud_feature.stories[1]
    assert "STORY-001-001-001" in read_story.blocked_by, "Read blocked by Create"
    print("  PASS: blocked_by dependencies preserved")

    # Verify business story
    business_feature = epic.features[1]
    business_story = business_feature.stories[0]
    assert business_story.business_value == "Wettelijke verplichting - BSN moet geldig zijn"
    assert business_story.story_type == "business_rule"
    print("  PASS: Business value preserved")

    # Verify relations
    assert len(package.relations) > 0, "Relations should contain blocked_by entries"
    print(f"  PASS: {len(package.relations)} relations assembled")

    # Verify project summary
    summary = package.project_summary
    assert summary.total_epics == 1
    assert summary.total_stories == 5
    assert summary.total_story_points == 21
    assert summary.project_name == "test"
    print("  PASS: Project summary correct")

    return True


# =============================================================================
# Test 4: CRUD Dependencies
# =============================================================================

def test_crud_dependencies():
    """Test automatic CRUD dependency chain setting."""
    from app.services.business_driven_story_generator_service import (
        AcceptanceCriterion,
        BusinessDrivenStoryGeneratorService,
        GeneratedStory,
        SourceReference,
    )

    service = BusinessDrivenStoryGeneratorService()

    # Create CRUD stories for an entity
    stories = [
        GeneratedStory(
            id="S-001",
            title="Migreer Factuur aanmaken functionaliteit",
            description="Create",
            feature_id="F-001",
            story_points=5,
            acceptance_criteria=[],
            source_references=[],
            complexity="medium",
            story_type="crud",
        ),
        GeneratedStory(
            id="S-002",
            title="Migreer Factuur ophalen/tonen",
            description="Read",
            feature_id="F-001",
            story_points=3,
            acceptance_criteria=[],
            source_references=[],
            complexity="medium",
            story_type="crud",
        ),
        GeneratedStory(
            id="S-003",
            title="Migreer Factuur wijzigen",
            description="Update",
            feature_id="F-001",
            story_points=5,
            acceptance_criteria=[],
            source_references=[],
            complexity="medium",
            story_type="crud",
        ),
        GeneratedStory(
            id="S-004",
            title="Migreer Factuur verwijderen",
            description="Delete",
            feature_id="F-001",
            story_points=3,
            acceptance_criteria=[],
            source_references=[],
            complexity="medium",
            story_type="crud",
        ),
        GeneratedStory(
            id="S-005",
            title="Implementeer BTW berekening",
            description="Business rule",
            feature_id="F-001",
            story_points=5,
            acceptance_criteria=[],
            source_references=[],
            complexity="medium",
            story_type="business_rule",
        ),
    ]

    # All blocked_by should be empty initially
    for s in stories:
        assert len(s.blocked_by) == 0, f"Story {s.id} should start with empty blocked_by"

    # Apply CRUD dependencies
    service._set_crud_dependencies(stories)

    # Verify dependencies
    create = stories[0]
    read = stories[1]
    update = stories[2]
    delete = stories[3]
    business = stories[4]

    assert len(create.blocked_by) == 0, "Create should have no dependencies"
    assert "S-001" in read.blocked_by, "Read should be blocked by Create"
    assert "S-001" in update.blocked_by, "Update should be blocked by Create"
    assert "S-002" in delete.blocked_by, "Delete should be blocked by Read"
    assert len(business.blocked_by) == 0, "Business rule should have no CRUD dependencies"

    print("  PASS: CRUD dependency chain: Create -> Read/Update, Read -> Delete")
    print(f"  PASS: Create blocked_by: {create.blocked_by}")
    print(f"  PASS: Read blocked_by: {read.blocked_by}")
    print(f"  PASS: Update blocked_by: {update.blocked_by}")
    print(f"  PASS: Delete blocked_by: {delete.blocked_by}")
    print(f"  PASS: Business blocked_by: {business.blocked_by}")

    return True


# =============================================================================
# Test 5: Serializers
# =============================================================================

def test_json_serializer():
    """Test JSON serializer output."""
    from app.services.plane_export.assembler import PlaneExportAssembler
    from app.services.plane_export.serializers import JsonExportSerializer

    generation_result = _make_test_generation_result()

    assembler = PlaneExportAssembler()
    package = assembler.assemble(
        generation_result=generation_result,
        project_context={"project_path": "/test"},
    )

    serializer = JsonExportSerializer()

    # Test serialization to string
    json_str = serializer.serialize(package)
    parsed = json.loads(json_str)
    assert "epics" in parsed
    assert "project_summary" in parsed
    assert "relations" in parsed
    print("  PASS: JSON string serialization")

    # Test write to file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name

    try:
        serializer.write(package, tmp_path)
        assert os.path.exists(tmp_path)
        with open(tmp_path, "r") as f:
            content = json.load(f)
        assert content["version"] == "1.0.0"
        assert len(content["epics"]) == 1
        print("  PASS: JSON file write")
    finally:
        os.unlink(tmp_path)

    return True


def test_adr002_markdown_serializer():
    """Test ADR-002 markdown directory structure output."""
    from app.services.plane_export.assembler import PlaneExportAssembler
    from app.services.plane_export.serializers import Adr002MarkdownSerializer

    generation_result = _make_test_generation_result()

    assembler = PlaneExportAssembler()
    package = assembler.assemble(
        generation_result=generation_result,
        project_context={"project_path": "/test"},
    )

    serializer = Adr002MarkdownSerializer()

    tmp_dir = tempfile.mkdtemp()
    try:
        output_dir = os.path.join(tmp_dir, "plane-export")
        serializer.write(package, output_dir)

        # Verify directory structure
        assert os.path.exists(os.path.join(output_dir, "project.md"))
        print("  PASS: project.md exists")

        assert os.path.isdir(os.path.join(output_dir, "epics"))
        print("  PASS: epics/ directory exists")

        # Find epic directory
        epics_dir = os.path.join(output_dir, "epics")
        epic_dirs = os.listdir(epics_dir)
        assert len(epic_dirs) == 1, f"Expected 1 epic dir, got {epic_dirs}"
        epic_dir = os.path.join(epics_dir, epic_dirs[0])
        print(f"  PASS: Epic directory: {epic_dirs[0]}")

        assert os.path.exists(os.path.join(epic_dir, "epic.md"))
        print("  PASS: epic.md exists")

        # Verify feature directories
        features_dir = os.path.join(epic_dir, "features")
        assert os.path.isdir(features_dir)
        feature_dirs = os.listdir(features_dir)
        assert len(feature_dirs) == 2, f"Expected 2 feature dirs, got {feature_dirs}"
        print(f"  PASS: {len(feature_dirs)} feature directories")

        # Verify story directories in CRUD feature
        for fd in feature_dirs:
            stories_dir = os.path.join(features_dir, fd, "stories")
            if os.path.isdir(stories_dir):
                story_dirs = os.listdir(stories_dir)
                for sd in story_dirs:
                    story_md = os.path.join(stories_dir, sd, "story.md")
                    assert os.path.exists(story_md), f"Missing story.md in {sd}"

        print("  PASS: All story.md files exist")

        # Verify story content preserves rich data
        # Find a story.md with acceptance criteria
        found_rich_story = False
        for fd in feature_dirs:
            stories_dir = os.path.join(features_dir, fd, "stories")
            if os.path.isdir(stories_dir):
                for sd in os.listdir(stories_dir):
                    story_md = os.path.join(stories_dir, sd, "story.md")
                    with open(story_md, "r") as f:
                        content = f.read()
                    if "Acceptance Criteria" in content and "Alle velden uit legacy form" in content:
                        assert "Source References" in content
                        assert "Patient.cs" in content
                        print("  PASS: Story markdown contains acceptance criteria + source refs")
                        found_rich_story = True
                        break
            if found_rich_story:
                break
        assert found_rich_story, "Should find at least one story with rich acceptance criteria"

        # Verify project.md content
        with open(os.path.join(output_dir, "project.md"), "r") as f:
            project_content = f.read()
        assert "Story Points" in project_content
        assert "EPIC-001" in project_content
        print("  PASS: project.md has summary content")

    finally:
        shutil.rmtree(tmp_dir)

    return True


# =============================================================================
# Test 6: Backward Compatibility
# =============================================================================

def test_backward_compatibility():
    """Test that new dataclass fields have defaults and don't break existing code."""
    from app.services.business_driven_story_generator_service import (
        AcceptanceCriterion,
        GeneratedEpic,
        GeneratedFeature,
        GeneratedStory,
        SourceReference,
    )

    # Create story WITHOUT new fields (simulating old code)
    story = GeneratedStory(
        id="S-001",
        title="Test",
        description="Test story",
        feature_id="F-001",
        story_points=5,
        acceptance_criteria=[],
        source_references=[],
        complexity="medium",
        story_type="crud",
    )
    assert story.priority == "medium", "Default priority should be medium"
    assert story.status == "backlog", "Default status should be backlog"
    assert story.blocked_by == [], "Default blocked_by should be empty list"
    assert story.business_value is None, "Default business_value should be None"
    print("  PASS: GeneratedStory backward compatible (new fields have defaults)")

    # Create feature WITHOUT new fields
    feature = GeneratedFeature(
        id="F-001",
        title="Test",
        description="Test feature",
        epic_id="E-001",
        stories=[story],
        source_modules=["test.py"],
        estimated_story_points=5,
        complexity="medium",
    )
    assert feature.priority == "medium"
    assert feature.status == "backlog"
    print("  PASS: GeneratedFeature backward compatible")

    # Create epic WITHOUT new fields
    epic = GeneratedEpic(
        id="E-001",
        title="Test",
        description="Test epic",
        domain_name="Test",
        features=[feature],
        source_modules=["test.py"],
        estimated_story_points=5,
        estimated_weeks=1,
        complexity="medium",
    )
    assert epic.priority == "medium"
    assert epic.status == "backlog"
    print("  PASS: GeneratedEpic backward compatible")

    return True


# =============================================================================
# Test 7: Assembler with M9 estimation data
# =============================================================================

def test_assembler_with_estimation():
    """Test assembler enriches package with M9 estimation data."""
    from app.services.plane_export.assembler import PlaneExportAssembler
    from dataclasses import dataclass

    # Minimal mock of EstimationResult (just the fields assembler uses)
    @dataclass
    class MockEstimationResult:
        project_path: str = "/test"
        estimated_weeks_low: int = 8
        estimated_weeks_high: int = 16
        estimated_weeks_likely: int = 12
        unadjusted_fp: float = 150.0
        adjusted_fp: float = 180.0
        total_effort_person_days: float = 60.0
        recommended_team_size: int = 3
        confidence_level: float = 0.82
        risk_factors: list = None
        recommendations: list = None

        def __post_init__(self):
            if self.risk_factors is None:
                self.risk_factors = [{"factor": "Legacy complexity", "impact": "high"}]
            if self.recommendations is None:
                self.recommendations = ["Start with core domain", "Parallel development recommended"]

    generation_result = _make_test_generation_result()
    estimation_result = MockEstimationResult()

    assembler = PlaneExportAssembler()
    package = assembler.assemble(
        generation_result=generation_result,
        estimation_result=estimation_result,
        project_context={"project_path": "/test"},
    )

    summary = package.project_summary
    assert summary.estimated_weeks_likely == 12, f"Expected 12, got {summary.estimated_weeks_likely}"
    assert summary.adjusted_fp == 180.0
    assert summary.recommended_team_size == 3
    assert summary.estimation_confidence == 0.82
    assert len(summary.risk_factors) == 1
    assert len(summary.recommendations) == 2
    print("  PASS: M9 estimation data enriches project summary")

    # Verify stage versions include estimation
    assert "m9_estimation" in package.stage_versions
    print("  PASS: Stage versions track M9")

    return True


# =============================================================================
# Test 8: Assembler with Peter enrichments
# =============================================================================

def test_assembler_with_peter():
    """Test assembler uses Peter enrichments for priority."""
    from app.services.plane_export.assembler import PlaneExportAssembler
    from app.services.plane_export.models import PlanePriority

    generation_result = _make_test_generation_result()

    peter_enrichments = {
        "success": True,
        "story_enrichments": {
            "STORY-001-002-001": {
                "priority": "critical",
                "business_context": "Wettelijke verplichting",
            },
        },
    }

    assembler = PlaneExportAssembler()
    package = assembler.assemble(
        generation_result=generation_result,
        peter_enrichments=peter_enrichments,
        project_context={"project_path": "/test"},
    )

    # Find the BSN story
    bsn_story = None
    for epic in package.epics:
        for feature in epic.features:
            for story in feature.stories:
                if story.id == "STORY-001-002-001":
                    bsn_story = story
                    break

    assert bsn_story is not None, "BSN story should exist"
    assert bsn_story.priority == PlanePriority.urgent, f"Peter critical -> urgent, got {bsn_story.priority}"
    print("  PASS: Peter priority 'critical' maps to Plane 'urgent'")

    # Verify stage versions include Peter
    assert "peter_enrichment" in package.stage_versions
    print("  PASS: Stage versions track Peter")

    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all tests."""
    print("=" * 60)
    print("Plane Export Module - Test Suite")
    print("=" * 60)

    tests = [
        ("Models: JSON round-trip", test_models_json_roundtrip),
        ("Priority Mapper: edge cases", test_priority_mapper),
        ("Assembler: M8 tree -> package", test_assembler),
        ("CRUD Dependencies: blocked_by chain", test_crud_dependencies),
        ("JSON Serializer: output", test_json_serializer),
        ("ADR-002 Markdown: directory structure", test_adr002_markdown_serializer),
        ("Backward Compatibility: M8 defaults", test_backward_compatibility),
        ("Assembler + M9 Estimation", test_assembler_with_estimation),
        ("Assembler + Peter Enrichments", test_assembler_with_peter),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"\n--- {name} ---")
        try:
            result = test_fn()
            if result:
                passed += 1
                print(f"  RESULT: PASSED")
            else:
                failed += 1
                print(f"  RESULT: FAILED")
        except Exception as e:
            failed += 1
            print(f"  RESULT: ERROR - {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
