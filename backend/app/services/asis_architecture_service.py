"""
AS-IS Architecture Service (Miguel Agent)

Week 69: Gestandaardiseerde Project Workflows - Phase 2
Analyzes existing codebase to understand current architecture patterns,
layers, components, and identify architectural issues.

This service provides the AS-IS (current state) analysis that serves as
the foundation for migration planning.

Author: Claude Code (Week 69)
Date: 2025-12-15
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class ArchitecturePattern(str, Enum):
    """Known architecture patterns"""
    MONOLITH = "monolith"
    LAYERED = "layered"
    MODULAR = "modular_monolith"
    CLEAN = "clean_architecture"
    HEXAGONAL = "hexagonal"
    MICROSERVICES = "microservices"
    EVENT_DRIVEN = "event_driven"
    SERVERLESS = "serverless"
    MVC = "mvc"
    MVP = "mvp"
    MVVM = "mvvm"
    CQRS = "cqrs"
    DDD = "ddd"
    UNKNOWN = "unknown"


class LayerType(str, Enum):
    """Standard architecture layers"""
    PRESENTATION = "presentation"
    API = "api"
    APPLICATION = "application"
    DOMAIN = "domain"
    INFRASTRUCTURE = "infrastructure"
    DATA = "data"
    SHARED = "shared"
    TESTS = "tests"
    UNKNOWN = "unknown"


@dataclass
class ArchitectureLayer:
    """Detected architecture layer"""
    name: str
    layer_type: LayerType
    directories: List[str] = field(default_factory=list)
    file_count: int = 0
    line_count: int = 0
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)


@dataclass
class ArchitectureComponent:
    """Detected component within the architecture"""
    name: str
    component_type: str  # controller, service, repository, model, etc.
    layer: Optional[str] = None
    file_path: str = ""
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    complexity_score: float = 0.0


@dataclass
class ArchitectureIssue:
    """Identified architecture issue"""
    issue_type: str  # circular_dependency, layer_violation, etc.
    severity: str  # critical, high, medium, low
    title: str
    description: str
    affected_files: List[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class ASISArchitecture:
    """Complete AS-IS architecture analysis result"""
    repo_path: str
    detected_pattern: ArchitecturePattern = ArchitecturePattern.UNKNOWN
    pattern_confidence: float = 0.0
    layers: List[ArchitectureLayer] = field(default_factory=list)
    components: List[ArchitectureComponent] = field(default_factory=list)
    issues: List[ArchitectureIssue] = field(default_factory=list)
    architecture_score: int = 0  # 0-100
    evidence: List[str] = field(default_factory=list)

    # Metrics
    total_files: int = 0
    total_lines: int = 0
    max_depth: int = 0
    avg_component_size: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_path": self.repo_path,
            "detected_pattern": self.detected_pattern.value,
            "pattern_confidence": self.pattern_confidence,
            "layers": [
                {
                    "name": l.name,
                    "layer_type": l.layer_type.value,
                    "directories": l.directories,
                    "file_count": l.file_count,
                    "line_count": l.line_count,
                    "confidence": l.confidence,
                    "evidence": l.evidence
                }
                for l in self.layers
            ],
            "components": [
                {
                    "name": c.name,
                    "component_type": c.component_type,
                    "layer": c.layer,
                    "file_path": c.file_path,
                    "dependencies": c.dependencies,
                    "dependents": c.dependents,
                    "complexity_score": c.complexity_score
                }
                for c in self.components
            ],
            "issues": [
                {
                    "issue_type": i.issue_type,
                    "severity": i.severity,
                    "title": i.title,
                    "description": i.description,
                    "affected_files": i.affected_files,
                    "recommendation": i.recommendation
                }
                for i in self.issues
            ],
            "architecture_score": self.architecture_score,
            "evidence": self.evidence,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "max_depth": self.max_depth,
            "avg_component_size": self.avg_component_size
        }


# Layer detection patterns by directory name
LAYER_PATTERNS = {
    LayerType.PRESENTATION: [
        r"(^|/)(views?|pages?|screens?|ui|frontend|web|wwwroot|public|static|templates?|layouts?)(/|$)",
        r"(^|/)(components?|widgets?)(/|$)",
        r"(^|/)Controllers?(/|$)",  # MVC
    ],
    LayerType.API: [
        r"(^|/)(api|apis|routes?|routing|endpoints?|rest|graphql)(/|$)",
        r"(^|/)Controllers?(/|$)",
    ],
    LayerType.APPLICATION: [
        r"(^|/)(application|app|services?|usecases?|use_cases?|commands?|queries?|handlers?)(/|$)",
        r"(^|/)(business|bll)(/|$)",
    ],
    LayerType.DOMAIN: [
        r"(^|/)(domain|core|entities?|models?|aggregates?|value_objects?)(/|$)",
        r"(^|/)(businesslogic|business_logic)(/|$)",
    ],
    LayerType.INFRASTRUCTURE: [
        r"(^|/)(infrastructure|infra|persistence|external|adapters?|ports?)(/|$)",
        r"(^|/)(repositories?|data_access|dal)(/|$)",
    ],
    LayerType.DATA: [
        r"(^|/)(data|db|database|migrations?|schemas?|sql)(/|$)",
        r"(^|/)(models?|entities?)(/|$)",
    ],
    LayerType.SHARED: [
        r"(^|/)(shared|common|utils?|utilities?|helpers?|lib|libs?)(/|$)",
        r"(^|/)(core|base|foundation)(/|$)",
    ],
    LayerType.TESTS: [
        r"(^|/)(tests?|testing|specs?|__tests__|test_)(/|$)",
        r"\.test\.(ts|js|py|cs|java)$",
        r"_test\.(py|go)$",
    ],
}

# Architecture pattern signatures
PATTERN_SIGNATURES = {
    ArchitecturePattern.CLEAN: {
        "required_layers": [LayerType.DOMAIN, LayerType.APPLICATION],
        "directory_hints": ["domain", "application", "infrastructure", "usecases", "entities"],
        "file_patterns": [r"use_?case", r"interactor", r"port", r"adapter"],
        "weight": 1.5
    },
    ArchitecturePattern.HEXAGONAL: {
        "required_layers": [LayerType.DOMAIN],
        "directory_hints": ["ports", "adapters", "domain", "application"],
        "file_patterns": [r"port\.py", r"adapter\.py", r"_port", r"_adapter"],
        "weight": 1.5
    },
    ArchitecturePattern.DDD: {
        "required_layers": [LayerType.DOMAIN],
        "directory_hints": ["domain", "aggregates", "entities", "value_objects", "repositories"],
        "file_patterns": [r"aggregate", r"value_object", r"domain_event", r"repository"],
        "weight": 1.4
    },
    ArchitecturePattern.LAYERED: {
        "required_layers": [LayerType.PRESENTATION, LayerType.APPLICATION, LayerType.DATA],
        "directory_hints": ["presentation", "business", "data", "dal", "bll", "ui"],
        "file_patterns": [],
        "weight": 1.0
    },
    ArchitecturePattern.MVC: {
        "required_layers": [LayerType.PRESENTATION],
        "directory_hints": ["models", "views", "controllers"],
        "file_patterns": [r"Controller\.", r"Model\.", r"View\."],
        "weight": 1.2
    },
    ArchitecturePattern.MVVM: {
        "required_layers": [LayerType.PRESENTATION],
        "directory_hints": ["models", "views", "viewmodels", "view_models"],
        "file_patterns": [r"ViewModel", r"View\.", r"Model\."],
        "weight": 1.2
    },
    ArchitecturePattern.CQRS: {
        "required_layers": [LayerType.APPLICATION],
        "directory_hints": ["commands", "queries", "handlers", "events"],
        "file_patterns": [r"Command", r"Query", r"Handler", r"Event"],
        "weight": 1.3
    },
    ArchitecturePattern.MICROSERVICES: {
        "required_layers": [],
        "directory_hints": ["services", "microservices", "api-gateway"],
        "file_patterns": [r"docker-compose", r"kubernetes", r"\.k8s\."],
        "weight": 1.5
    },
    ArchitecturePattern.MODULAR: {
        "required_layers": [],
        "directory_hints": ["modules", "features", "areas"],
        "file_patterns": [r"module\.ts", r"module\.py"],
        "weight": 1.1
    },
}

# Component type patterns
COMPONENT_PATTERNS = {
    "controller": [r"Controller\.(cs|java|ts|py)$", r"_controller\.py$", r"controllers/"],
    "service": [r"Service\.(cs|java|ts|py)$", r"_service\.py$", r"services/"],
    "repository": [r"Repository\.(cs|java|ts|py)$", r"_repository\.py$", r"repositories/"],
    "model": [r"Model\.(cs|java|ts|py)$", r"models/", r"entities/"],
    "viewmodel": [r"ViewModel\.(cs|ts)$", r"viewmodels/"],
    "handler": [r"Handler\.(cs|java|ts|py)$", r"_handler\.py$", r"handlers/"],
    "middleware": [r"Middleware\.(cs|ts|py)$", r"middlewares?/"],
    "validator": [r"Validator\.(cs|java|ts|py)$", r"validators/"],
    "mapper": [r"Mapper\.(cs|java|ts|py)$", r"mappers/"],
    "factory": [r"Factory\.(cs|java|ts|py)$", r"factories/"],
    "command": [r"Command\.(cs|java|ts|py)$", r"commands/"],
    "query": [r"Query\.(cs|java|ts|py)$", r"queries/"],
    "event": [r"Event\.(cs|java|ts|py)$", r"events/"],
    "dto": [r"Dto\.(cs|java|ts|py)$", r"dtos/", r"DTO\.(cs|java|ts|py)$"],
}

# Files/directories to ignore
IGNORE_PATTERNS = [
    r"node_modules",
    r"\.git",
    r"\.svn",
    r"__pycache__",
    r"\.pyc$",
    r"bin",
    r"obj",
    r"dist",
    r"build",
    r"\.vs",
    r"\.idea",
    r"coverage",
    r"\.next",
    r"\.nuxt",
    r"packages",
    r"vendor",
    r"target",
]


class ASISArchitectureService:
    """
    AS-IS Architecture Analysis Service (Miguel Agent)

    Analyzes existing codebases to determine:
    - Current architecture pattern (Clean, Hexagonal, Layered, MVC, etc.)
    - Detected layers and their organization
    - Components and their relationships
    - Architecture issues and technical debt
    - Overall architecture quality score
    """

    def __init__(self):
        self.ignore_regex = re.compile("|".join(f"({p})" for p in IGNORE_PATTERNS))

    def analyze(self, repo_path: str) -> ASISArchitecture:
        """
        Main entry point: Analyze a repository's architecture

        Args:
            repo_path: Path to the repository root

        Returns:
            ASISArchitecture object with complete analysis
        """
        result = ASISArchitecture(repo_path=repo_path)

        if not os.path.exists(repo_path):
            result.issues.append(ArchitectureIssue(
                issue_type="path_not_found",
                severity="critical",
                title="Repository path not found",
                description=f"The path {repo_path} does not exist",
                recommendation="Verify the repository path is correct"
            ))
            return result

        # Phase 1: Scan directory structure
        dir_structure = self._scan_directory_structure(repo_path)
        result.total_files = dir_structure["total_files"]
        result.total_lines = dir_structure["total_lines"]
        result.max_depth = dir_structure["max_depth"]

        # Phase 2: Detect layers
        result.layers = self._detect_layers(repo_path, dir_structure)

        # Phase 3: Detect architecture pattern
        result.detected_pattern, result.pattern_confidence, pattern_evidence = \
            self._detect_architecture_pattern(repo_path, result.layers, dir_structure)
        result.evidence.extend(pattern_evidence)

        # Phase 4: Detect components
        result.components = self._detect_components(repo_path, result.layers)
        if result.components:
            result.avg_component_size = sum(c.complexity_score for c in result.components) / len(result.components)

        # Phase 5: Analyze dependencies and detect issues
        result.issues.extend(self._analyze_architecture_issues(result))

        # Phase 6: Calculate architecture score
        result.architecture_score = self._calculate_architecture_score(result)

        return result

    def _scan_directory_structure(self, repo_path: str) -> Dict[str, Any]:
        """Scan the repository directory structure"""
        result = {
            "total_files": 0,
            "total_lines": 0,
            "max_depth": 0,
            "directories": [],
            "files_by_extension": defaultdict(int),
            "files_by_directory": defaultdict(list),
        }

        repo_root = Path(repo_path)

        for root, dirs, files in os.walk(repo_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not self.ignore_regex.search(d)]

            rel_path = Path(root).relative_to(repo_root)
            depth = len(rel_path.parts)
            result["max_depth"] = max(result["max_depth"], depth)

            if str(rel_path) != ".":
                result["directories"].append(str(rel_path))

            for file in files:
                if self.ignore_regex.search(file):
                    continue

                result["total_files"] += 1
                ext = Path(file).suffix.lower()
                result["files_by_extension"][ext] += 1

                file_path = os.path.join(root, file)
                rel_file_path = str(Path(file_path).relative_to(repo_root))

                # Get directory for this file
                file_dir = str(rel_path) if str(rel_path) != "." else "root"
                result["files_by_directory"][file_dir].append(rel_file_path)

                # Count lines for code files
                if ext in [".py", ".cs", ".java", ".js", ".ts", ".php", ".vb", ".go", ".rs", ".rb"]:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            result["total_lines"] += sum(1 for _ in f)
                    except Exception:
                        pass

        return result

    def _detect_layers(self, repo_path: str, dir_structure: Dict[str, Any]) -> List[ArchitectureLayer]:
        """Detect architecture layers from directory structure"""
        layers = []
        layer_scores = defaultdict(lambda: {"directories": [], "file_count": 0, "line_count": 0, "evidence": []})

        repo_root = Path(repo_path)

        # Analyze each directory
        for directory in dir_structure["directories"]:
            dir_path = str(directory).lower()

            for layer_type, patterns in LAYER_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, dir_path, re.IGNORECASE):
                        layer_scores[layer_type]["directories"].append(directory)
                        layer_scores[layer_type]["evidence"].append(f"Directory '{directory}' matches {layer_type.value} pattern")

                        # Count files in this directory
                        if directory in dir_structure["files_by_directory"]:
                            files = dir_structure["files_by_directory"][directory]
                            layer_scores[layer_type]["file_count"] += len(files)
                        break

        # Convert to ArchitectureLayer objects
        for layer_type, data in layer_scores.items():
            if data["directories"]:
                confidence = min(1.0, len(data["directories"]) * 0.3 + data["file_count"] * 0.01)
                layers.append(ArchitectureLayer(
                    name=layer_type.value,
                    layer_type=layer_type,
                    directories=data["directories"],
                    file_count=data["file_count"],
                    line_count=data["line_count"],
                    confidence=round(confidence, 2),
                    evidence=data["evidence"]
                ))

        # Sort by confidence
        layers.sort(key=lambda l: l.confidence, reverse=True)

        return layers

    def _detect_architecture_pattern(
        self,
        repo_path: str,
        layers: List[ArchitectureLayer],
        dir_structure: Dict[str, Any]
    ) -> Tuple[ArchitecturePattern, float, List[str]]:
        """Detect the overall architecture pattern"""
        pattern_scores = defaultdict(lambda: {"score": 0.0, "evidence": []})

        layer_types = {l.layer_type for l in layers}
        all_dirs = set(dir_structure["directories"])

        for pattern, signature in PATTERN_SIGNATURES.items():
            score = 0.0
            evidence = []

            # Check required layers
            required = set(signature.get("required_layers", []))
            if required:
                found_required = required.intersection(layer_types)
                layer_score = len(found_required) / len(required)
                score += layer_score * 0.4
                if found_required:
                    evidence.append(f"Found required layers: {[l.value for l in found_required]}")

            # Check directory hints
            hints = signature.get("directory_hints", [])
            if hints:
                found_hints = 0
                for hint in hints:
                    for d in all_dirs:
                        if hint.lower() in d.lower():
                            found_hints += 1
                            break
                hint_score = found_hints / len(hints) if hints else 0
                score += hint_score * 0.3
                if found_hints:
                    evidence.append(f"Found {found_hints}/{len(hints)} directory hints")

            # Check file patterns
            file_patterns = signature.get("file_patterns", [])
            if file_patterns:
                pattern_matches = 0
                for directory, files in dir_structure["files_by_directory"].items():
                    for file_path in files:
                        for fp in file_patterns:
                            if re.search(fp, file_path, re.IGNORECASE):
                                pattern_matches += 1
                                break

                if pattern_matches > 0:
                    pattern_score = min(1.0, pattern_matches / 10)
                    score += pattern_score * 0.3
                    evidence.append(f"Found {pattern_matches} file pattern matches")

            # Apply weight
            score *= signature.get("weight", 1.0)

            pattern_scores[pattern]["score"] = score
            pattern_scores[pattern]["evidence"] = evidence

        # Find best match
        best_pattern = ArchitecturePattern.MONOLITH
        best_score = 0.0
        best_evidence = []

        for pattern, data in pattern_scores.items():
            if data["score"] > best_score:
                best_score = data["score"]
                best_pattern = pattern
                best_evidence = data["evidence"]

        # If score is too low, default to monolith
        if best_score < 0.3:
            best_pattern = ArchitecturePattern.MONOLITH
            best_evidence = ["No clear architecture pattern detected - defaulting to monolith"]

        return best_pattern, round(min(1.0, best_score), 2), best_evidence

    def _detect_components(self, repo_path: str, layers: List[ArchitectureLayer]) -> List[ArchitectureComponent]:
        """Detect components within the architecture"""
        components = []
        repo_root = Path(repo_path)

        # Map directories to layers
        dir_to_layer = {}
        for layer in layers:
            for d in layer.directories:
                dir_to_layer[d] = layer.name

        # Scan files for component patterns
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not self.ignore_regex.search(d)]

            for file in files:
                if self.ignore_regex.search(file):
                    continue

                file_path = os.path.join(root, file)
                rel_path = str(Path(file_path).relative_to(repo_root))

                # Determine component type
                component_type = None
                for ctype, patterns in COMPONENT_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, rel_path, re.IGNORECASE):
                            component_type = ctype
                            break
                    if component_type:
                        break

                if component_type:
                    # Find layer for this component
                    layer = None
                    for d, l in dir_to_layer.items():
                        if rel_path.startswith(d):
                            layer = l
                            break

                    # Calculate simple complexity (file size proxy)
                    try:
                        size = os.path.getsize(file_path)
                        complexity = min(100, size / 100)  # Rough proxy
                    except Exception:
                        complexity = 0

                    component_name = Path(file).stem
                    components.append(ArchitectureComponent(
                        name=component_name,
                        component_type=component_type,
                        layer=layer,
                        file_path=rel_path,
                        complexity_score=complexity
                    ))

        return components

    def _analyze_architecture_issues(self, result: ASISArchitecture) -> List[ArchitectureIssue]:
        """Analyze architecture for common issues"""
        issues = []

        # Issue 1: No clear layer separation
        if len(result.layers) < 2:
            issues.append(ArchitectureIssue(
                issue_type="no_layer_separation",
                severity="high",
                title="No clear layer separation detected",
                description="The codebase doesn't show clear architectural layers. This can lead to tight coupling and difficulty in maintenance.",
                recommendation="Consider organizing code into distinct layers (presentation, application, domain, infrastructure)"
            ))

        # Issue 2: God components (very large files)
        large_components = [c for c in result.components if c.complexity_score > 80]
        if large_components:
            issues.append(ArchitectureIssue(
                issue_type="god_components",
                severity="medium",
                title=f"Large components detected ({len(large_components)} files)",
                description="Large files often indicate components that do too much. This violates the Single Responsibility Principle.",
                affected_files=[c.file_path for c in large_components[:5]],
                recommendation="Consider breaking down large components into smaller, focused units"
            ))

        # Issue 3: Missing test layer
        test_layer = next((l for l in result.layers if l.layer_type == LayerType.TESTS), None)
        if not test_layer:
            issues.append(ArchitectureIssue(
                issue_type="missing_tests",
                severity="medium",
                title="No test layer detected",
                description="No dedicated test directory or test files were found.",
                recommendation="Add unit tests and integration tests to ensure code quality"
            ))
        elif test_layer.file_count < result.total_files * 0.1:
            issues.append(ArchitectureIssue(
                issue_type="insufficient_tests",
                severity="low",
                title="Low test coverage suspected",
                description=f"Only {test_layer.file_count} test files for {result.total_files} total files",
                recommendation="Increase test coverage to at least 60% for critical paths"
            ))

        # Issue 4: Deep nesting
        if result.max_depth > 8:
            issues.append(ArchitectureIssue(
                issue_type="deep_nesting",
                severity="low",
                title=f"Deep directory nesting (depth: {result.max_depth})",
                description="Deep directory nesting can make navigation and understanding the codebase difficult.",
                recommendation="Consider flattening the directory structure where possible"
            ))

        # Issue 5: No domain layer (for non-CRUD apps)
        domain_layer = next((l for l in result.layers if l.layer_type == LayerType.DOMAIN), None)
        if not domain_layer and result.total_files > 50:
            issues.append(ArchitectureIssue(
                issue_type="missing_domain",
                severity="medium",
                title="No domain layer detected",
                description="For applications with significant business logic, a dedicated domain layer helps organize business rules.",
                recommendation="Consider extracting business logic into a dedicated domain layer"
            ))

        # Issue 6: Mixed concerns (presentation + data in same layer)
        presentation_dirs = set()
        data_dirs = set()
        for layer in result.layers:
            if layer.layer_type == LayerType.PRESENTATION:
                presentation_dirs.update(layer.directories)
            elif layer.layer_type == LayerType.DATA:
                data_dirs.update(layer.directories)

        overlap = presentation_dirs.intersection(data_dirs)
        if overlap:
            issues.append(ArchitectureIssue(
                issue_type="mixed_concerns",
                severity="high",
                title="Mixed architectural concerns",
                description="Presentation and data access code detected in same directories, indicating poor separation of concerns.",
                affected_files=list(overlap),
                recommendation="Separate presentation logic from data access logic into distinct layers"
            ))

        return issues

    def _calculate_architecture_score(self, result: ASISArchitecture) -> int:
        """Calculate overall architecture quality score (0-100)"""
        score = 70  # Base score

        # Bonus for clear pattern
        if result.pattern_confidence > 0.7:
            score += 10
        elif result.pattern_confidence > 0.4:
            score += 5

        # Bonus for layer organization
        score += min(15, len(result.layers) * 3)

        # Penalty for issues
        for issue in result.issues:
            if issue.severity == "critical":
                score -= 20
            elif issue.severity == "high":
                score -= 10
            elif issue.severity == "medium":
                score -= 5
            else:  # low
                score -= 2

        # Bonus for tests
        test_layer = next((l for l in result.layers if l.layer_type == LayerType.TESTS), None)
        if test_layer:
            test_ratio = test_layer.file_count / max(1, result.total_files)
            if test_ratio > 0.3:
                score += 10
            elif test_ratio > 0.1:
                score += 5

        return max(0, min(100, score))

    def get_architecture_summary(self, result: ASISArchitecture) -> str:
        """Generate a human-readable summary of the architecture analysis"""
        lines = [
            f"# AS-IS Architecture Analysis",
            f"",
            f"## Overview",
            f"- **Detected Pattern**: {result.detected_pattern.value} (confidence: {result.pattern_confidence:.0%})",
            f"- **Architecture Score**: {result.architecture_score}/100",
            f"- **Total Files**: {result.total_files:,}",
            f"- **Total Lines**: {result.total_lines:,}",
            f"- **Max Directory Depth**: {result.max_depth}",
            f"",
            f"## Detected Layers ({len(result.layers)})",
        ]

        for layer in result.layers:
            lines.append(f"- **{layer.name}**: {layer.file_count} files in {len(layer.directories)} directories")

        if result.issues:
            lines.extend([
                f"",
                f"## Architecture Issues ({len(result.issues)})",
            ])
            for issue in result.issues:
                lines.append(f"- [{issue.severity.upper()}] **{issue.title}**")
                lines.append(f"  - {issue.description}")

        if result.evidence:
            lines.extend([
                f"",
                f"## Evidence",
            ])
            for e in result.evidence:
                lines.append(f"- {e}")

        return "\n".join(lines)


# Singleton instance
_service_instance: Optional[ASISArchitectureService] = None


def get_asis_architecture_service() -> ASISArchitectureService:
    """Get or create the AS-IS Architecture Service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ASISArchitectureService()
    return _service_instance
