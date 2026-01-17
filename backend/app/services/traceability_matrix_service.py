"""
Traceability Matrix Service - Week 85

Maps code elements to user stories for:
- Code coverage analysis (which code implements which story)
- Orphan detection (code without story connection)
- Gap analysis (stories without implementation)
- Impact analysis (what stories are affected by code changes)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4
import re
import logging

logger = logging.getLogger(__name__)


class LinkType(str, Enum):
    """Type of traceability link."""
    IMPLEMENTS = "implements"  # Code implements story
    TESTS = "tests"  # Test covers story
    DOCUMENTS = "documents"  # Documentation for story
    REFERENCES = "references"  # Code references story
    PARTIAL = "partial"  # Partial implementation
    # Week 125: CiRA causal link types
    CAUSES = "causes"  # Story A causes/enables Story B
    DEPENDS_ON = "depends_on"  # Story A depends on Story B
    BLOCKS = "blocks"  # Story A blocks Story B until completed


class LinkConfidence(str, Enum):
    """Confidence level of the link."""
    HIGH = "high"  # Explicit reference (story ID in code)
    MEDIUM = "medium"  # Semantic match
    LOW = "low"  # Inferred from context
    MANUAL = "manual"  # Human-verified


class CodeElementType(str, Enum):
    """Type of code element."""
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    MODULE = "module"
    TEST = "test"
    DOCUMENTATION = "documentation"


@dataclass
class CodeElement:
    """Represents a code element (file, class, function, etc.)."""
    id: str
    element_type: CodeElementType
    path: str
    name: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    language: Optional[str] = None
    complexity: Optional[int] = None
    loc: Optional[int] = None
    last_modified: Optional[datetime] = None
    git_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StoryReference:
    """Reference to a user story."""
    story_id: str
    title: Optional[str] = None
    story_type: Optional[str] = None  # epic, feature, story, task
    acceptance_criteria: List[str] = field(default_factory=list)
    priority: Optional[str] = None
    status: Optional[str] = None


@dataclass
class TraceabilityLink:
    """A link between code and story."""
    id: str
    code_element: CodeElement
    story: StoryReference
    link_type: LinkType
    confidence: LinkConfidence
    created_at: datetime
    created_by: str  # "auto" or user id
    evidence: List[str] = field(default_factory=list)  # Why this link exists
    verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class OrphanCodeResult:
    """Code without story connection."""
    element: CodeElement
    suggested_stories: List[Tuple[StoryReference, float]] = field(default_factory=list)
    reason: str = ""


@dataclass
class UnimplementedStoryResult:
    """Story without code implementation."""
    story: StoryReference
    expected_elements: List[str] = field(default_factory=list)
    coverage_percentage: float = 0.0
    blocking_reason: Optional[str] = None


@dataclass
class ImpactAnalysisResult:
    """Impact of code changes on stories."""
    changed_files: List[str]
    affected_stories: List[StoryReference]
    affected_links: List[TraceabilityLink]
    risk_level: str  # low, medium, high
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CoverageMetrics:
    """Traceability coverage metrics."""
    total_code_elements: int
    linked_code_elements: int
    orphan_code_elements: int
    total_stories: int
    implemented_stories: int
    unimplemented_stories: int
    partially_implemented_stories: int
    code_coverage_percentage: float
    story_coverage_percentage: float
    high_confidence_links: int
    medium_confidence_links: int
    low_confidence_links: int
    manual_links: int
    verified_links: int
    unverified_links: int
    # Week 125: Causal link metrics
    causal_links: int = 0
    dependency_links: int = 0
    blocking_links: int = 0


@dataclass
class CausalStoryLink:
    """
    Week 125: Represents a causal dependency between stories.

    Created from CiRA analysis of story descriptions and acceptance criteria.
    """
    id: str
    cause_story_id: str
    effect_story_id: str
    link_type: LinkType  # CAUSES, DEPENDS_ON, or BLOCKS
    confidence: float
    evidence: str  # The causal sentence that created this link
    created_at: datetime
    created_by: str = "cira"
    cira_session_id: Optional[str] = None


@dataclass
class TraceabilityMatrixResult:
    """Complete traceability matrix."""
    matrix_id: str
    project_id: int
    created_at: datetime
    links: List[TraceabilityLink]
    orphan_code: List[OrphanCodeResult]
    unimplemented_stories: List[UnimplementedStoryResult]
    metrics: CoverageMetrics
    extraction_session_id: Optional[str] = None
    # Week 125: Causal story links from CiRA
    causal_links: List[CausalStoryLink] = field(default_factory=list)
    cira_session_id: Optional[str] = None
    suggested_sprint_order: List[str] = field(default_factory=list)


class TraceabilityMatrixService:
    """
    Service for creating and managing code-to-story traceability.

    Capabilities:
    - Auto-detect story references in code (comments, docstrings, commit messages)
    - Semantic matching between code and story descriptions
    - Orphan code detection
    - Gap analysis for unimplemented stories
    - Impact analysis for code changes
    """

    # Patterns for detecting story references in code
    STORY_PATTERNS = [
        r'(?:story|user-story|us|feature|epic|task)[:\s#-]*([A-Z]+-\d+)',  # PROJ-123
        r'(?:implements|closes|fixes|refs?)[:\s#]*([A-Z]+-\d+)',  # implements PROJ-123
        r'\[([A-Z]+-\d+)\]',  # [PROJ-123]
        r'#(\d{3,6})',  # #12345 (GitHub-style)
        r'(?:story_id|storyId|STORY_ID)[:\s="\']*([A-Za-z0-9-]+)',  # story_id: abc-123
    ]

    def __init__(self, db=None):
        self.db = db
        self._links: Dict[str, TraceabilityLink] = {}
        self._code_elements: Dict[str, CodeElement] = {}
        self._stories: Dict[str, StoryReference] = {}

    async def build_matrix(
        self,
        project_id: int,
        code_elements: List[Dict[str, Any]],
        stories: List[Dict[str, Any]],
        existing_links: Optional[List[Dict[str, Any]]] = None,
        auto_detect: bool = True,
        semantic_match: bool = True,
        semantic_threshold: float = 0.7,
    ) -> TraceabilityMatrixResult:
        """
        Build a complete traceability matrix.

        Args:
            project_id: Project ID
            code_elements: List of code elements from extraction
            stories: List of user stories
            existing_links: Pre-existing manual links
            auto_detect: Auto-detect story references in code
            semantic_match: Use semantic matching for linking
            semantic_threshold: Minimum similarity for semantic matching

        Returns:
            TraceabilityMatrixResult with all links and metrics
        """
        matrix_id = str(uuid4())
        created_at = datetime.now(timezone.utc)

        # Convert to internal representations
        self._code_elements = {
            elem.get("id", str(uuid4())): self._to_code_element(elem)
            for elem in code_elements
        }
        self._stories = {
            story.get("id", str(uuid4())): self._to_story_reference(story)
            for story in stories
        }

        # Load existing links
        if existing_links:
            for link_data in existing_links:
                link = self._to_traceability_link(link_data)
                if link:
                    self._links[link.id] = link

        # Auto-detect story references
        if auto_detect:
            await self._auto_detect_references()

        # Semantic matching
        if semantic_match and len(self._stories) > 0:
            await self._semantic_match(threshold=semantic_threshold)

        # Find orphan code
        orphan_code = self._find_orphan_code()

        # Find unimplemented stories
        unimplemented = self._find_unimplemented_stories()

        # Calculate metrics
        metrics = self._calculate_metrics()

        return TraceabilityMatrixResult(
            matrix_id=matrix_id,
            project_id=project_id,
            created_at=created_at,
            links=list(self._links.values()),
            orphan_code=orphan_code,
            unimplemented_stories=unimplemented,
            metrics=metrics,
        )

    async def analyze_impact(
        self,
        changed_files: List[str],
        change_type: str = "modification",
    ) -> ImpactAnalysisResult:
        """
        Analyze the impact of code changes on user stories.

        Args:
            changed_files: List of changed file paths
            change_type: Type of change (modification, deletion, addition)

        Returns:
            ImpactAnalysisResult with affected stories
        """
        affected_links = []
        affected_story_ids = set()

        for file_path in changed_files:
            # Find links involving this file
            for link in self._links.values():
                if link.code_element.path == file_path:
                    affected_links.append(link)
                    affected_story_ids.add(link.story.story_id)

        affected_stories = [
            self._stories[sid]
            for sid in affected_story_ids
            if sid in self._stories
        ]

        # Determine risk level
        risk_level = self._calculate_risk_level(
            affected_links,
            affected_stories,
            change_type
        )

        # Generate recommendations
        recommendations = self._generate_impact_recommendations(
            affected_links,
            affected_stories,
            change_type,
        )

        return ImpactAnalysisResult(
            changed_files=changed_files,
            affected_stories=affected_stories,
            affected_links=affected_links,
            risk_level=risk_level,
            recommendations=recommendations,
        )

    async def add_manual_link(
        self,
        code_element_id: str,
        story_id: str,
        link_type: LinkType,
        user_id: str,
        notes: Optional[str] = None,
    ) -> TraceabilityLink:
        """Add a manual traceability link."""
        if code_element_id not in self._code_elements:
            raise ValueError(f"Code element {code_element_id} not found")
        if story_id not in self._stories:
            raise ValueError(f"Story {story_id} not found")

        link = TraceabilityLink(
            id=str(uuid4()),
            code_element=self._code_elements[code_element_id],
            story=self._stories[story_id],
            link_type=link_type,
            confidence=LinkConfidence.MANUAL,
            created_at=datetime.now(timezone.utc),
            created_by=user_id,
            evidence=["Manually linked by user"],
            verified=True,
            verified_at=datetime.now(timezone.utc),
            verified_by=user_id,
            notes=notes,
        )

        self._links[link.id] = link
        return link

    async def verify_link(
        self,
        link_id: str,
        user_id: str,
        is_valid: bool,
        notes: Optional[str] = None,
    ) -> Optional[TraceabilityLink]:
        """Verify or reject a traceability link."""
        if link_id not in self._links:
            return None

        link = self._links[link_id]

        if is_valid:
            link.verified = True
            link.verified_at = datetime.now(timezone.utc)
            link.verified_by = user_id
            if notes:
                link.notes = notes
        else:
            # Remove invalid link
            del self._links[link_id]
            return None

        return link

    async def suggest_links(
        self,
        code_element_id: str,
        max_suggestions: int = 5,
    ) -> List[Tuple[StoryReference, float, List[str]]]:
        """
        Suggest possible story links for a code element.

        Returns:
            List of (story, confidence_score, reasons) tuples
        """
        if code_element_id not in self._code_elements:
            return []

        element = self._code_elements[code_element_id]
        suggestions = []

        for story_id, story in self._stories.items():
            # Check if already linked
            if self._is_linked(code_element_id, story_id):
                continue

            score, reasons = self._calculate_match_score(element, story)
            if score > 0.3:
                suggestions.append((story, score, reasons))

        # Sort by score descending
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:max_suggestions]

    async def get_story_coverage(
        self,
        story_id: str,
    ) -> Dict[str, Any]:
        """Get coverage details for a specific story."""
        if story_id not in self._stories:
            return {"error": "Story not found"}

        story = self._stories[story_id]
        story_links = [
            link for link in self._links.values()
            if link.story.story_id == story_id
        ]

        # Group by element type
        by_type: Dict[str, List[TraceabilityLink]] = {}
        for link in story_links:
            elem_type = link.code_element.element_type.value
            if elem_type not in by_type:
                by_type[elem_type] = []
            by_type[elem_type].append(link)

        # Check acceptance criteria coverage
        ac_coverage = self._check_acceptance_criteria_coverage(
            story, story_links
        )

        return {
            "story_id": story_id,
            "story_title": story.title,
            "total_links": len(story_links),
            "by_element_type": {k: len(v) for k, v in by_type.items()},
            "has_tests": any(
                link.code_element.element_type == CodeElementType.TEST
                for link in story_links
            ),
            "has_documentation": any(
                link.code_element.element_type == CodeElementType.DOCUMENTATION
                for link in story_links
            ),
            "acceptance_criteria_coverage": ac_coverage,
            "verified_links": sum(1 for link in story_links if link.verified),
            "confidence_breakdown": {
                "high": sum(1 for l in story_links if l.confidence == LinkConfidence.HIGH),
                "medium": sum(1 for l in story_links if l.confidence == LinkConfidence.MEDIUM),
                "low": sum(1 for l in story_links if l.confidence == LinkConfidence.LOW),
                "manual": sum(1 for l in story_links if l.confidence == LinkConfidence.MANUAL),
            },
        }

    # ==================== Private Methods ====================

    def _to_code_element(self, data: Dict[str, Any]) -> CodeElement:
        """Convert dict to CodeElement."""
        return CodeElement(
            id=data.get("id", str(uuid4())),
            element_type=CodeElementType(data.get("type", "file")),
            path=data.get("path", ""),
            name=data.get("name", ""),
            start_line=data.get("start_line"),
            end_line=data.get("end_line"),
            language=data.get("language"),
            complexity=data.get("complexity"),
            loc=data.get("loc"),
            last_modified=data.get("last_modified"),
            git_hash=data.get("git_hash"),
            metadata=data.get("metadata", {}),
        )

    def _to_story_reference(self, data: Dict[str, Any]) -> StoryReference:
        """Convert dict to StoryReference."""
        return StoryReference(
            story_id=data.get("id", str(uuid4())),
            title=data.get("title"),
            story_type=data.get("type"),
            acceptance_criteria=data.get("acceptance_criteria", []),
            priority=data.get("priority"),
            status=data.get("status"),
        )

    def _to_traceability_link(self, data: Dict[str, Any]) -> Optional[TraceabilityLink]:
        """Convert dict to TraceabilityLink."""
        try:
            return TraceabilityLink(
                id=data.get("id", str(uuid4())),
                code_element=self._to_code_element(data.get("code_element", {})),
                story=self._to_story_reference(data.get("story", {})),
                link_type=LinkType(data.get("link_type", "implements")),
                confidence=LinkConfidence(data.get("confidence", "low")),
                created_at=data.get("created_at", datetime.now(timezone.utc)),
                created_by=data.get("created_by", "auto"),
                evidence=data.get("evidence", []),
                verified=data.get("verified", False),
            )
        except Exception as e:
            logger.warning(f"Failed to convert link data: {e}")
            return None

    async def _auto_detect_references(self):
        """Auto-detect story references in code elements."""
        for elem_id, element in self._code_elements.items():
            # Get text content to search
            search_text = self._get_searchable_text(element)

            for pattern in self.STORY_PATTERNS:
                matches = re.findall(pattern, search_text, re.IGNORECASE)
                for match in matches:
                    # Try to find matching story
                    story = self._find_story_by_reference(match)
                    if story and not self._is_linked(elem_id, story.story_id):
                        link = TraceabilityLink(
                            id=str(uuid4()),
                            code_element=element,
                            story=story,
                            link_type=LinkType.IMPLEMENTS,
                            confidence=LinkConfidence.HIGH,
                            created_at=datetime.now(timezone.utc),
                            created_by="auto",
                            evidence=[f"Found reference '{match}' in code"],
                        )
                        self._links[link.id] = link

    async def _semantic_match(self, threshold: float = 0.7):
        """Match code to stories using semantic similarity."""
        for elem_id, element in self._code_elements.items():
            # Skip if already linked with high confidence
            if self._has_high_confidence_link(elem_id):
                continue

            best_match = None
            best_score = 0.0
            best_reasons: List[str] = []

            for story_id, story in self._stories.items():
                if self._is_linked(elem_id, story_id):
                    continue

                score, reasons = self._calculate_match_score(element, story)
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = story
                    best_reasons = reasons

            if best_match:
                confidence = (
                    LinkConfidence.MEDIUM if best_score >= 0.8
                    else LinkConfidence.LOW
                )
                link = TraceabilityLink(
                    id=str(uuid4()),
                    code_element=element,
                    story=best_match,
                    link_type=LinkType.IMPLEMENTS,
                    confidence=confidence,
                    created_at=datetime.now(timezone.utc),
                    created_by="auto",
                    evidence=best_reasons,
                )
                self._links[link.id] = link

    def _calculate_match_score(
        self,
        element: CodeElement,
        story: StoryReference,
    ) -> Tuple[float, List[str]]:
        """Calculate semantic match score between code and story."""
        score = 0.0
        reasons = []

        # Name matching
        elem_name = element.name.lower()
        story_title = (story.title or "").lower()

        # Extract keywords from story
        story_keywords = self._extract_keywords(story_title)
        elem_keywords = self._extract_keywords(elem_name)

        # Keyword overlap
        overlap = story_keywords.intersection(elem_keywords)
        if overlap:
            keyword_score = len(overlap) / max(len(story_keywords), 1)
            score += keyword_score * 0.5
            reasons.append(f"Keyword match: {', '.join(overlap)}")

        # Path matching (domain terms in path)
        path_lower = element.path.lower()
        for keyword in story_keywords:
            if keyword in path_lower:
                score += 0.1
                reasons.append(f"Story keyword '{keyword}' in path")
                break

        # Type correlation (test files for stories, etc.)
        if element.element_type == CodeElementType.TEST:
            if "test" in story_title or "verify" in story_title:
                score += 0.2
                reasons.append("Test file for testing story")

        # Acceptance criteria matching
        for ac in story.acceptance_criteria:
            ac_keywords = self._extract_keywords(ac.lower())
            ac_overlap = ac_keywords.intersection(elem_keywords)
            if ac_overlap:
                score += 0.15
                reasons.append(f"AC keyword match: {', '.join(ac_overlap)}")
                break

        return min(score, 1.0), reasons

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text."""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'under', 'again', 'further', 'then', 'once',
            'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either',
            'neither', 'not', 'only', 'own', 'same', 'than', 'too', 'very',
            'can', 'just', 'should', 'now', 'i', 'me', 'my', 'we', 'our',
            'you', 'your', 'he', 'she', 'it', 'they', 'them', 'this', 'that',
        }

        # Tokenize
        words = re.findall(r'[a-zA-Z]+', text.lower())

        # Filter
        keywords = {
            word for word in words
            if len(word) > 2 and word not in stop_words
        }

        return keywords

    def _get_searchable_text(self, element: CodeElement) -> str:
        """Get text content to search for story references."""
        parts = [element.name, element.path]
        if element.metadata:
            if "docstring" in element.metadata:
                parts.append(element.metadata["docstring"])
            if "comments" in element.metadata:
                parts.extend(element.metadata["comments"])
        return " ".join(parts)

    def _find_story_by_reference(self, reference: str) -> Optional[StoryReference]:
        """Find a story by its reference string."""
        reference = reference.upper()
        for story in self._stories.values():
            if story.story_id.upper() == reference:
                return story
            # Also check if reference is in story ID
            if reference in story.story_id.upper():
                return story
        return None

    def _is_linked(self, code_element_id: str, story_id: str) -> bool:
        """Check if code element is linked to story."""
        for link in self._links.values():
            if (link.code_element.id == code_element_id and
                link.story.story_id == story_id):
                return True
        return False

    def _has_high_confidence_link(self, code_element_id: str) -> bool:
        """Check if code element has a high confidence link."""
        for link in self._links.values():
            if (link.code_element.id == code_element_id and
                link.confidence in [LinkConfidence.HIGH, LinkConfidence.MANUAL]):
                return True
        return False

    def _find_orphan_code(self) -> List[OrphanCodeResult]:
        """Find code elements without story links."""
        linked_elements = {link.code_element.id for link in self._links.values()}
        orphans = []

        for elem_id, element in self._code_elements.items():
            if elem_id not in linked_elements:
                # Try to suggest stories
                suggestions = []
                for story_id, story in self._stories.items():
                    score, _ = self._calculate_match_score(element, story)
                    if score > 0.2:
                        suggestions.append((story, score))
                suggestions.sort(key=lambda x: x[1], reverse=True)

                orphans.append(OrphanCodeResult(
                    element=element,
                    suggested_stories=suggestions[:3],
                    reason=self._determine_orphan_reason(element),
                ))

        return orphans

    def _determine_orphan_reason(self, element: CodeElement) -> str:
        """Determine why code might be orphan."""
        name_lower = element.name.lower()
        path_lower = element.path.lower()

        if "test" in name_lower or "test" in path_lower:
            return "Test file - may need linking to tested story"
        if "util" in name_lower or "helper" in name_lower:
            return "Utility code - may be cross-cutting concern"
        if "config" in name_lower or "settings" in name_lower:
            return "Configuration - may be infrastructure code"
        if "__init__" in name_lower:
            return "Package initialization - typically no direct story"

        return "No story reference found"

    def _find_unimplemented_stories(self) -> List[UnimplementedStoryResult]:
        """Find stories without code implementation."""
        linked_stories = {link.story.story_id for link in self._links.values()}
        unimplemented = []

        for story_id, story in self._stories.items():
            story_links = [
                link for link in self._links.values()
                if link.story.story_id == story_id
            ]

            if not story_links:
                unimplemented.append(UnimplementedStoryResult(
                    story=story,
                    expected_elements=self._predict_expected_elements(story),
                    coverage_percentage=0.0,
                ))
            elif self._is_partially_implemented(story, story_links):
                coverage = self._calculate_story_coverage(story, story_links)
                unimplemented.append(UnimplementedStoryResult(
                    story=story,
                    expected_elements=self._predict_expected_elements(story),
                    coverage_percentage=coverage,
                    blocking_reason="Partial implementation",
                ))

        return unimplemented

    def _predict_expected_elements(self, story: StoryReference) -> List[str]:
        """Predict what code elements a story should have."""
        elements = []
        title_lower = (story.title or "").lower()

        # API stories should have routes
        if "api" in title_lower or "endpoint" in title_lower:
            elements.append("API route handler")
            elements.append("Request/response models")

        # Data stories should have models
        if "data" in title_lower or "store" in title_lower or "save" in title_lower:
            elements.append("Database model")
            elements.append("Repository/service")

        # UI stories should have components
        if "ui" in title_lower or "page" in title_lower or "form" in title_lower:
            elements.append("Frontend component")

        # All stories should have tests
        elements.append("Unit tests")

        return elements

    def _is_partially_implemented(
        self,
        story: StoryReference,
        links: List[TraceabilityLink],
    ) -> bool:
        """Check if story is only partially implemented."""
        if not links:
            return False

        # Check if any links are partial
        if any(link.link_type == LinkType.PARTIAL for link in links):
            return True

        # Check if missing tests
        has_impl = any(
            link.link_type == LinkType.IMPLEMENTS for link in links
        )
        has_tests = any(
            link.link_type == LinkType.TESTS for link in links
        )

        if has_impl and not has_tests:
            return True

        return False

    def _calculate_story_coverage(
        self,
        story: StoryReference,
        links: List[TraceabilityLink],
    ) -> float:
        """Calculate coverage percentage for a story."""
        if not story.acceptance_criteria:
            # Simple heuristic based on link count and types
            has_impl = any(l.link_type == LinkType.IMPLEMENTS for l in links)
            has_tests = any(l.link_type == LinkType.TESTS for l in links)
            has_docs = any(l.link_type == LinkType.DOCUMENTS for l in links)

            score = 0.0
            if has_impl:
                score += 0.6
            if has_tests:
                score += 0.3
            if has_docs:
                score += 0.1
            return score

        # Check acceptance criteria coverage
        covered = self._check_acceptance_criteria_coverage(story, links)
        return covered.get("coverage_percentage", 0.0)

    def _check_acceptance_criteria_coverage(
        self,
        story: StoryReference,
        links: List[TraceabilityLink],
    ) -> Dict[str, Any]:
        """Check how many acceptance criteria are covered by code."""
        if not story.acceptance_criteria:
            return {"coverage_percentage": 100.0, "details": []}

        ac_status = []
        covered_count = 0

        for ac in story.acceptance_criteria:
            ac_keywords = self._extract_keywords(ac.lower())

            # Check if any link covers this AC
            is_covered = False
            covering_link = None

            for link in links:
                elem_keywords = self._extract_keywords(
                    link.code_element.name.lower()
                )
                if ac_keywords.intersection(elem_keywords):
                    is_covered = True
                    covering_link = link.code_element.name
                    break

            ac_status.append({
                "acceptance_criterion": ac,
                "covered": is_covered,
                "covered_by": covering_link,
            })

            if is_covered:
                covered_count += 1

        coverage_pct = (covered_count / len(story.acceptance_criteria)) * 100

        return {
            "coverage_percentage": coverage_pct,
            "total_criteria": len(story.acceptance_criteria),
            "covered_criteria": covered_count,
            "details": ac_status,
        }

    def _calculate_risk_level(
        self,
        affected_links: List[TraceabilityLink],
        affected_stories: List[StoryReference],
        change_type: str,
    ) -> str:
        """Calculate risk level of code changes."""
        # High risk factors
        high_risk = (
            len(affected_stories) > 3 or
            change_type == "deletion" or
            any(s.priority == "high" for s in affected_stories) or
            any(l.confidence == LinkConfidence.HIGH for l in affected_links)
        )

        # Medium risk factors
        medium_risk = (
            len(affected_stories) > 1 or
            any(s.priority == "medium" for s in affected_stories)
        )

        if high_risk:
            return "high"
        elif medium_risk:
            return "medium"
        return "low"

    def _generate_impact_recommendations(
        self,
        affected_links: List[TraceabilityLink],
        affected_stories: List[StoryReference],
        change_type: str,
    ) -> List[str]:
        """Generate recommendations for handling impact."""
        recommendations = []

        if not affected_stories:
            recommendations.append(
                "No stories affected. Consider if this code should be linked to stories."
            )
            return recommendations

        if change_type == "deletion":
            recommendations.append(
                f"Deleting code affects {len(affected_stories)} stories. "
                "Verify removal is intentional."
            )
            for story in affected_stories:
                recommendations.append(
                    f"Review story '{story.title}' for impact"
                )

        # Check for missing tests
        has_test_links = any(
            link.link_type == LinkType.TESTS for link in affected_links
        )
        if not has_test_links:
            recommendations.append(
                "Consider updating tests for affected functionality"
            )

        # High confidence links need careful review
        high_confidence = [
            l for l in affected_links
            if l.confidence == LinkConfidence.HIGH
        ]
        if high_confidence:
            recommendations.append(
                f"{len(high_confidence)} high-confidence links affected. "
                "Extra review recommended."
            )

        return recommendations

    def _calculate_metrics(self) -> CoverageMetrics:
        """Calculate coverage metrics."""
        total_elements = len(self._code_elements)
        linked_elements = len({
            link.code_element.id for link in self._links.values()
        })

        total_stories = len(self._stories)
        linked_stories = len({
            link.story.story_id for link in self._links.values()
        })

        # Partially implemented stories (have links but incomplete)
        partial_stories = 0
        for story_id in self._stories:
            story_links = [
                l for l in self._links.values()
                if l.story.story_id == story_id
            ]
            if story_links and self._is_partially_implemented(
                self._stories[story_id], story_links
            ):
                partial_stories += 1

        return CoverageMetrics(
            total_code_elements=total_elements,
            linked_code_elements=linked_elements,
            orphan_code_elements=total_elements - linked_elements,
            total_stories=total_stories,
            implemented_stories=linked_stories - partial_stories,
            unimplemented_stories=total_stories - linked_stories,
            partially_implemented_stories=partial_stories,
            code_coverage_percentage=(
                (linked_elements / total_elements * 100)
                if total_elements > 0 else 0.0
            ),
            story_coverage_percentage=(
                (linked_stories / total_stories * 100)
                if total_stories > 0 else 0.0
            ),
            high_confidence_links=sum(
                1 for l in self._links.values()
                if l.confidence == LinkConfidence.HIGH
            ),
            medium_confidence_links=sum(
                1 for l in self._links.values()
                if l.confidence == LinkConfidence.MEDIUM
            ),
            low_confidence_links=sum(
                1 for l in self._links.values()
                if l.confidence == LinkConfidence.LOW
            ),
            manual_links=sum(
                1 for l in self._links.values()
                if l.confidence == LinkConfidence.MANUAL
            ),
            verified_links=sum(
                1 for l in self._links.values() if l.verified
            ),
            unverified_links=sum(
                1 for l in self._links.values() if not l.verified
            ),
        )

    # =========================================================================
    # WEEK 125: CiRA CAUSAL LINK INTEGRATION
    # =========================================================================

    async def add_causal_links_from_cira(
        self,
        cira_session_id: str,
        causal_relations: List[Dict[str, Any]],
        story_mapping: Optional[Dict[str, str]] = None,
    ) -> List[CausalStoryLink]:
        """
        Add causal links from CiRA analysis results.

        Args:
            cira_session_id: The CiRA session ID
            causal_relations: List of causal relations from CiRA
            story_mapping: Optional mapping from sentence source_id to story_id

        Returns:
            List of created CausalStoryLink objects
        """
        causal_links = []

        for relation in causal_relations:
            # Determine link type based on relation pattern
            link_type = self._determine_causal_link_type(relation)

            # Map source_id to story_id if mapping provided
            cause_story_id = relation.get("cause_source_id", "")
            effect_story_id = relation.get("effect_source_id", "")

            if story_mapping:
                cause_story_id = story_mapping.get(cause_story_id, cause_story_id)
                effect_story_id = story_mapping.get(effect_story_id, effect_story_id)

            # Skip if we can't identify both stories
            if not cause_story_id or not effect_story_id:
                continue

            # Skip self-references
            if cause_story_id == effect_story_id:
                continue

            causal_link = CausalStoryLink(
                id=str(uuid4()),
                cause_story_id=cause_story_id,
                effect_story_id=effect_story_id,
                link_type=link_type,
                confidence=relation.get("confidence", 0.5),
                evidence=relation.get("sentence", ""),
                created_at=datetime.now(timezone.utc),
                created_by="cira",
                cira_session_id=cira_session_id,
            )
            causal_links.append(causal_link)

        logger.info(
            f"Added {len(causal_links)} causal links from CiRA session {cira_session_id}"
        )

        return causal_links

    def _determine_causal_link_type(self, relation: Dict[str, Any]) -> LinkType:
        """
        Determine the type of causal link based on relation patterns.

        Uses keywords in the cause/effect to classify as:
        - BLOCKS: if blocking/prerequisite language is present
        - CAUSES: if enablement language is present
        - DEPENDS_ON: default for dependency relationships
        """
        cause = relation.get("cause", "").lower()
        effect = relation.get("effect", "").lower()
        relation_text = f"{cause} {effect}"

        # Check for blocking patterns
        blocking_keywords = [
            "before", "must be", "required", "prerequisite",
            "cannot", "until", "blocks", "prevent"
        ]
        if any(kw in relation_text for kw in blocking_keywords):
            return LinkType.BLOCKS

        # Check for causation patterns
        causation_keywords = [
            "enables", "allows", "triggers", "leads to",
            "results in", "causes", "makes possible"
        ]
        if any(kw in relation_text for kw in causation_keywords):
            return LinkType.CAUSES

        # Default to dependency
        return LinkType.DEPENDS_ON

    async def build_matrix_with_cira(
        self,
        project_id: int,
        code_elements: List[Dict[str, Any]],
        stories: List[Dict[str, Any]],
        cira_causal_info: Optional[Dict[str, Any]] = None,
        existing_links: Optional[List[Dict[str, Any]]] = None,
        auto_detect: bool = True,
        semantic_match: bool = True,
        semantic_threshold: float = 0.7,
    ) -> TraceabilityMatrixResult:
        """
        Build traceability matrix with optional CiRA causal analysis.

        Week 125: Integrates CiRA causal dependencies into the matrix.

        Args:
            project_id: Project ID
            code_elements: List of code elements from extraction
            stories: List of user stories
            cira_causal_info: Optional CiRA analysis results (CausalDependencyInfo as dict)
            existing_links: Pre-existing manual links
            auto_detect: Auto-detect story references in code
            semantic_match: Enable semantic matching
            semantic_threshold: Minimum similarity for semantic match

        Returns:
            TraceabilityMatrixResult with causal links included
        """
        # Build base matrix
        result = await self.build_matrix(
            project_id=project_id,
            code_elements=code_elements,
            stories=stories,
            existing_links=existing_links,
            auto_detect=auto_detect,
            semantic_match=semantic_match,
            semantic_threshold=semantic_threshold,
        )

        # Add CiRA causal links if provided
        if cira_causal_info:
            cira_session_id = cira_causal_info.get("session_id")
            relations_by_story = cira_causal_info.get("relations_by_story", {})

            # Convert relations_by_story to flat list
            causal_relations = []
            for story_id, relations in relations_by_story.items():
                for rel in relations:
                    causal_relations.append({
                        "cause_source_id": story_id,
                        "effect_source_id": rel.get("effect_story_id", ""),
                        "cause": rel.get("cause", ""),
                        "effect": rel.get("effect", ""),
                        "confidence": float(rel.get("confidence", 0.5)),
                        "sentence": f"{rel.get('cause', '')} -> {rel.get('effect', '')}",
                    })

            if causal_relations:
                result.causal_links = await self.add_causal_links_from_cira(
                    cira_session_id=cira_session_id,
                    causal_relations=causal_relations,
                )
                result.cira_session_id = cira_session_id

            # Add suggested sprint order if available
            result.suggested_sprint_order = cira_causal_info.get(
                "suggested_sprint_order", []
            )

            # Update metrics with causal link counts
            result.metrics.causal_links = len(
                [l for l in result.causal_links if l.link_type == LinkType.CAUSES]
            )
            result.metrics.dependency_links = len(
                [l for l in result.causal_links if l.link_type == LinkType.DEPENDS_ON]
            )
            result.metrics.blocking_links = len(
                [l for l in result.causal_links if l.link_type == LinkType.BLOCKS]
            )

            logger.info(
                f"Matrix enhanced with CiRA: {len(result.causal_links)} causal links, "
                f"suggested sprint order has {len(result.suggested_sprint_order)} items"
            )

        return result

    def get_story_dependencies(
        self,
        story_id: str,
        causal_links: List[CausalStoryLink],
    ) -> Dict[str, List[CausalStoryLink]]:
        """
        Get all dependencies for a story.

        Returns:
            Dict with "blocks", "blocked_by", "causes", "caused_by" lists
        """
        return {
            "blocks": [
                l for l in causal_links
                if l.cause_story_id == story_id and l.link_type == LinkType.BLOCKS
            ],
            "blocked_by": [
                l for l in causal_links
                if l.effect_story_id == story_id and l.link_type == LinkType.BLOCKS
            ],
            "causes": [
                l for l in causal_links
                if l.cause_story_id == story_id and l.link_type == LinkType.CAUSES
            ],
            "caused_by": [
                l for l in causal_links
                if l.effect_story_id == story_id and l.link_type == LinkType.CAUSES
            ],
            "depends_on": [
                l for l in causal_links
                if l.effect_story_id == story_id and l.link_type == LinkType.DEPENDS_ON
            ],
            "depended_by": [
                l for l in causal_links
                if l.cause_story_id == story_id and l.link_type == LinkType.DEPENDS_ON
            ],
        }


def get_traceability_service(db=None) -> TraceabilityMatrixService:
    """Factory function for TraceabilityMatrixService."""
    return TraceabilityMatrixService(db)
