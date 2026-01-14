# Analysis Contract
# Core interface that decouples Brown Paper from Migration
#
# This is THE key contract that breaks the tight coupling between workflows.
# Brown Paper creates this contract, Migration consumes it.
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 (Week 145-146)

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import uuid
import json

from .stability_contract import StabilityInfo


class AnalysisSourceType(Enum):
    """Source of the analysis contract."""
    BROWN_PAPER = "brown_paper"      # From Brown Paper workflow
    GREEN_PAPER = "green_paper"      # From Green Paper (BMAD) workflow
    MANUAL_IMPORT = "manual_import"  # Handmatige JSON/YAML import
    EXTERNAL_TOOL = "external_tool"  # Third-party analysis tool


@dataclass
class ProjectInfo:
    """Basic project information."""
    name: str
    path: str
    description: str = ""
    repository_url: str = ""
    primary_language: str = ""
    framework: str = ""
    lines_of_code: int = 0
    total_files: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "description": self.description,
            "repository_url": self.repository_url,
            "primary_language": self.primary_language,
            "framework": self.framework,
            "lines_of_code": self.lines_of_code,
            "total_files": self.total_files,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectInfo":
        return cls(
            name=data.get("name", ""),
            path=data.get("path", ""),
            description=data.get("description", ""),
            repository_url=data.get("repository_url", ""),
            primary_language=data.get("primary_language", ""),
            framework=data.get("framework", ""),
            lines_of_code=data.get("lines_of_code", 0),
            total_files=data.get("total_files", 0),
        )


@dataclass
class DomainSummary:
    """Summary of a business domain."""
    name: str
    description: str = ""
    entities: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    modules: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"  # low, medium, high
    estimated_fp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "entities": self.entities,
            "use_cases": self.use_cases,
            "modules": self.modules,
            "estimated_complexity": self.estimated_complexity,
            "estimated_fp": self.estimated_fp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainSummary":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            entities=data.get("entities", []),
            use_cases=data.get("use_cases", []),
            modules=data.get("modules", []),
            estimated_complexity=data.get("estimated_complexity", "medium"),
            estimated_fp=data.get("estimated_fp", 0.0),
        )


@dataclass
class ModuleSummary:
    """Summary of a code module."""
    name: str
    path: str
    module_type: str = ""  # controller, service, model, util, etc.
    complexity: str = "medium"
    lines_of_code: int = 0
    classes: int = 0
    functions: int = 0
    dependencies: List[str] = field(default_factory=list)
    domain: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "module_type": self.module_type,
            "complexity": self.complexity,
            "lines_of_code": self.lines_of_code,
            "classes": self.classes,
            "functions": self.functions,
            "dependencies": self.dependencies,
            "domain": self.domain,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModuleSummary":
        return cls(
            name=data.get("name", ""),
            path=data.get("path", ""),
            module_type=data.get("module_type", ""),
            complexity=data.get("complexity", "medium"),
            lines_of_code=data.get("lines_of_code", 0),
            classes=data.get("classes", 0),
            functions=data.get("functions", 0),
            dependencies=data.get("dependencies", []),
            domain=data.get("domain", ""),
        )


@dataclass
class FeatureSummary:
    """Summary of a feature within an epic."""
    feature_id: str
    title: str
    description: str = ""
    estimated_sp: int = 0
    priority: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "title": self.title,
            "description": self.description,
            "estimated_sp": self.estimated_sp,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureSummary":
        return cls(
            feature_id=data.get("feature_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            estimated_sp=data.get("estimated_sp", 0),
            priority=data.get("priority", "medium"),
        )


@dataclass
class EpicSummary:
    """Summary of an epic."""
    epic_id: str
    title: str
    description: str = ""
    domain: str = ""
    estimated_fp: float = 0.0
    estimated_weeks: float = 0.0
    features: List[FeatureSummary] = field(default_factory=list)
    priority: str = "medium"
    complexity: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epic_id": self.epic_id,
            "title": self.title,
            "description": self.description,
            "domain": self.domain,
            "estimated_fp": self.estimated_fp,
            "estimated_weeks": self.estimated_weeks,
            "features": [f.to_dict() for f in self.features],
            "priority": self.priority,
            "complexity": self.complexity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpicSummary":
        features = [
            FeatureSummary.from_dict(f)
            for f in data.get("features", [])
        ]
        return cls(
            epic_id=data.get("epic_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            domain=data.get("domain", ""),
            estimated_fp=data.get("estimated_fp", 0.0),
            estimated_weeks=data.get("estimated_weeks", 0.0),
            features=features,
            priority=data.get("priority", "medium"),
            complexity=data.get("complexity", "medium"),
        )


@dataclass
class BusinessRuleSummary:
    """Summary of a business rule."""
    rule_id: str
    name: str
    description: str = ""
    source_file: str = ""
    line_number: int = 0
    domain: str = ""
    complexity: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "source_file": self.source_file,
            "line_number": self.line_number,
            "domain": self.domain,
            "complexity": self.complexity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessRuleSummary":
        return cls(
            rule_id=data.get("rule_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            source_file=data.get("source_file", ""),
            line_number=data.get("line_number", 0),
            domain=data.get("domain", ""),
            complexity=data.get("complexity", "low"),
        )


@dataclass
class AnalysisContract:
    """
    THE interface between Brown Paper and Migration.

    This contract breaks the tight coupling:
    - Brown Paper creates this contract after analysis
    - Migration consumes this contract (NOT brown_paper_session_id)
    - Quality can create contracts from standalone scans

    Key principle: analysis_id is the ONLY identifier needed for migration.
    """
    # === Identity ===
    analysis_id: str  # Unique ID (NOT brown_paper_session_id)
    source_type: AnalysisSourceType
    source_id: Optional[str] = None  # Original source ID (e.g., brown_paper_session_id)

    # === Project Info ===
    project: ProjectInfo = field(default_factory=lambda: ProjectInfo(name="", path=""))

    # === Analysis Results ===
    domains: List[DomainSummary] = field(default_factory=list)
    modules: List[ModuleSummary] = field(default_factory=list)
    stability: StabilityInfo = field(default_factory=StabilityInfo.empty)
    epics: List[EpicSummary] = field(default_factory=list)
    business_rules: List[BusinessRuleSummary] = field(default_factory=list)

    # === Metadata ===
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"

    # === Computed Properties ===
    @property
    def total_domains(self) -> int:
        return len(self.domains)

    @property
    def total_modules(self) -> int:
        return len(self.modules)

    @property
    def total_epics(self) -> int:
        return len(self.epics)

    @property
    def total_features(self) -> int:
        return sum(len(e.features) for e in self.epics)

    @property
    def total_fp(self) -> float:
        return sum(e.estimated_fp for e in self.epics)

    @property
    def total_weeks(self) -> float:
        return sum(e.estimated_weeks for e in self.epics)

    @property
    def has_stability_issues(self) -> bool:
        return self.stability.total_findings > 0

    @property
    def is_high_risk(self) -> bool:
        return self.stability.overall_risk in ("CRITICAL", "HIGH")

    # === Serialization ===
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "analysis_id": self.analysis_id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "project": self.project.to_dict(),
            "domains": [d.to_dict() for d in self.domains],
            "modules": [m.to_dict() for m in self.modules],
            "stability": self.stability.to_dict(),
            "epics": [e.to_dict() for e in self.epics],
            "business_rules": [b.to_dict() for b in self.business_rules],
            "created_at": self.created_at.isoformat(),
            "version": self.version,
            # Computed fields for easy access
            "summary": {
                "total_domains": self.total_domains,
                "total_modules": self.total_modules,
                "total_epics": self.total_epics,
                "total_features": self.total_features,
                "total_fp": self.total_fp,
                "total_weeks": self.total_weeks,
                "has_stability_issues": self.has_stability_issues,
                "is_high_risk": self.is_high_risk,
            },
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisContract":
        """Create from dictionary."""
        # Parse source type
        source_type_str = data.get("source_type", "brown_paper")
        try:
            source_type = AnalysisSourceType(source_type_str)
        except ValueError:
            source_type = AnalysisSourceType.BROWN_PAPER

        # Parse created_at
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        else:
            created_at = datetime.now(timezone.utc)

        return cls(
            analysis_id=data.get("analysis_id", str(uuid.uuid4())),
            source_type=source_type,
            source_id=data.get("source_id"),
            project=ProjectInfo.from_dict(data.get("project", {})),
            domains=[DomainSummary.from_dict(d) for d in data.get("domains", [])],
            modules=[ModuleSummary.from_dict(m) for m in data.get("modules", [])],
            stability=StabilityInfo.from_dict(data.get("stability", {})),
            epics=[EpicSummary.from_dict(e) for e in data.get("epics", [])],
            business_rules=[BusinessRuleSummary.from_dict(b) for b in data.get("business_rules", [])],
            created_at=created_at,
            version=data.get("version", "1.0"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "AnalysisContract":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def create_new(
        cls,
        source_type: AnalysisSourceType,
        project_name: str,
        project_path: str,
        source_id: Optional[str] = None,
    ) -> "AnalysisContract":
        """Factory method to create a new contract."""
        return cls(
            analysis_id=str(uuid.uuid4()),
            source_type=source_type,
            source_id=source_id,
            project=ProjectInfo(name=project_name, path=project_path),
        )

    # === Validation ===
    def validate_for_migration(self) -> tuple[bool, List[str]]:
        """
        Validate if this contract has sufficient data for migration.
        Returns (is_valid, list_of_issues).
        """
        issues = []

        if not self.analysis_id:
            issues.append("Missing analysis_id")

        if not self.project.name:
            issues.append("Missing project name")

        if not self.project.path:
            issues.append("Missing project path")

        if not self.domains:
            issues.append("No domains identified - analysis may be incomplete")

        if not self.epics:
            issues.append("No epics generated - estimation not possible")

        # Warning if high risk
        if self.is_high_risk:
            issues.append(f"Warning: High stability risk ({self.stability.overall_risk})")

        return len([i for i in issues if not i.startswith("Warning")]) == 0, issues
