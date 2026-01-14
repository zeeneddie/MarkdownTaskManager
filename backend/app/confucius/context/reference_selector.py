"""
Reference Selector for Context Engineering.

Provides semantic matching to select the most relevant reference
documents for a given task, reducing token usage by 60-80%.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


class ReferenceCategory(str, Enum):
    """Categories of reference documents."""
    LANGUAGE = "language"  # Language-specific patterns (ASP, Python, etc.)
    FRAMEWORK = "framework"  # Framework conventions (FastAPI, SQLAlchemy)
    TESTING = "testing"  # Testing patterns and fixtures
    SECURITY = "security"  # Security patterns and OWASP
    ARCHITECTURE = "architecture"  # Architecture decisions
    STABILITY = "stability"  # Resource leak detection
    ESTIMATION = "estimation"  # FP methodology
    DOCUMENTATION = "documentation"  # Documentation standards
    GENERAL = "general"  # General best practices


@dataclass
class Reference:
    """A reference document for context injection."""
    id: str
    name: str
    category: ReferenceCategory
    path: str
    keywords: List[str]
    description: str
    token_estimate: int = 0
    content: Optional[str] = None
    domains: List[str] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "path": self.path,
            "keywords": self.keywords,
            "description": self.description,
            "token_estimate": self.token_estimate,
            "domains": self.domains,
            "agents": self.agents,
        }


@dataclass
class ReferenceMatch:
    """Result of reference matching."""
    reference: Reference
    score: float
    matched_keywords: List[str]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "reference_id": self.reference.id,
            "reference_name": self.reference.name,
            "score": round(self.score, 3),
            "matched_keywords": self.matched_keywords,
            "reason": self.reason,
            "token_estimate": self.reference.token_estimate,
        }


# Default reference definitions
DEFAULT_REFERENCES: List[Reference] = [
    Reference(
        id="asp-vbscript",
        name="ASP VBScript Patterns",
        category=ReferenceCategory.LANGUAGE,
        path=".claude/reference/asp-vbscript-patterns.md",
        keywords=[
            "asp", "vbscript", "classic asp", "ado", "recordset",
            "connection", "fso", "filesystemobject", "com", "xmlhttp",
            "legacy", "vb", "response", "request", "session", "application",
        ],
        description="Classic ASP and VBScript patterns including ADO cleanup, COM objects, and file handling",
        token_estimate=2500,
        domains=["stability", "metrics", "migration"],
        agents=["Miguel", "Marcus", "Felix"],
    ),
    Reference(
        id="fastapi-conventions",
        name="FastAPI Conventions",
        category=ReferenceCategory.FRAMEWORK,
        path=".claude/reference/fastapi-conventions.md",
        keywords=[
            "fastapi", "router", "endpoint", "api", "rest", "http",
            "pydantic", "validation", "dependency", "injection", "async",
            "swagger", "openapi", "response_model", "status_code",
        ],
        description="FastAPI router structure, error handling, and API conventions",
        token_estimate=2000,
        domains=["architecture", "quality"],
        agents=["Felix", "Quinn"],
    ),
    Reference(
        id="testing-patterns",
        name="Testing Patterns",
        category=ReferenceCategory.TESTING,
        path=".claude/reference/testing-patterns.md",
        keywords=[
            "test", "pytest", "fixture", "mock", "unittest", "coverage",
            "tdd", "bdd", "parametrize", "assert", "integration", "unit",
            "e2e", "regression", "characterization",
        ],
        description="Testing pyramid (70/20/10), fixtures, and test patterns",
        token_estimate=2200,
        domains=["testing", "quality"],
        agents=["Tessa", "Quinn"],
    ),
    Reference(
        id="security-patterns",
        name="Security Patterns",
        category=ReferenceCategory.SECURITY,
        path=".claude/reference/security-patterns.md",
        keywords=[
            "security", "owasp", "sql injection", "xss", "csrf", "cwe",
            "vulnerability", "sanitize", "escape", "authentication",
            "authorization", "encryption", "secret", "credential",
        ],
        description="OWASP Top 10, SQL injection prevention, and security best practices",
        token_estimate=2800,
        domains=["security", "quality"],
        agents=["Quinn", "Felix"],
    ),
    Reference(
        id="stability-analysis",
        name="Stability Analysis",
        category=ReferenceCategory.STABILITY,
        path=".claude/reference/stability-analysis.md",
        keywords=[
            "stability", "leak", "resource", "memory", "ado", "connection",
            "recordset", "close", "dispose", "cleanup", "nothing", "set",
            "finally", "error handling", "on error",
        ],
        description="8 stability categories, resource leak detection patterns",
        token_estimate=2400,
        domains=["stability", "maintenance"],
        agents=["Miguel", "Marcus"],
    ),
    Reference(
        id="python-best-practices",
        name="Python Best Practices",
        category=ReferenceCategory.LANGUAGE,
        path=".claude/reference/python-best-practices.md",
        keywords=[
            "python", "type hint", "async", "await", "dataclass", "enum",
            "logging", "exception", "context manager", "generator", "decorator",
            "pep8", "mypy", "typing", "optional", "union",
        ],
        description="Python type hints, async patterns, and code style",
        token_estimate=2100,
        domains=["architecture", "quality"],
        agents=["Felix", "Quinn", "Diana"],
    ),
    Reference(
        id="fp-methodology",
        name="FP Methodology",
        category=ReferenceCategory.ESTIMATION,
        path=".claude/reference/fp-methodology.md",
        keywords=[
            "function point", "fp", "ifpug", "nesma", "ilf", "eif",
            "ei", "eo", "eq", "estimation", "sizing", "effort",
            "work type", "enhancement", "development", "maintenance",
        ],
        description="IFPUG/NESMA Function Point methodology and work type classification",
        token_estimate=2600,
        domains=["estimation"],
        agents=["Eliza"],
    ),
    Reference(
        id="sqlalchemy-patterns",
        name="SQLAlchemy Patterns",
        category=ReferenceCategory.FRAMEWORK,
        path=".claude/reference/sqlalchemy-patterns.md",
        keywords=[
            "sqlalchemy", "orm", "model", "session", "query", "relationship",
            "alembic", "migration", "database", "postgresql", "transaction",
            "commit", "rollback", "foreign key", "index",
        ],
        description="SQLAlchemy ORM patterns, relationships, and migrations",
        token_estimate=2300,
        domains=["architecture", "quality"],
        agents=["Felix", "Quinn"],
    ),
]


class ReferenceSelector:
    """
    Selects relevant references based on task analysis.

    Uses keyword matching and domain correlation to identify
    which reference documents are most relevant for a given task.

    Example:
    ```python
    selector = ReferenceSelector()
    matches = selector.select(
        task="Analyze ASP code for ADO connection leaks",
        context={"domain": "stability"},
        max_references=3,
    )
    for match in matches:
        print(f"{match.reference.name}: {match.score}")
    ```
    """

    def __init__(
        self,
        references: Optional[List[Reference]] = None,
        min_score: float = 0.1,
    ):
        """
        Initialize selector.

        Args:
            references: List of available references (uses defaults if None)
            min_score: Minimum score threshold for matches
        """
        self._references = references or DEFAULT_REFERENCES.copy()
        self._min_score = min_score
        self._reference_map = {r.id: r for r in self._references}

    def add_reference(self, reference: Reference) -> None:
        """Add a reference to the selector."""
        self._references.append(reference)
        self._reference_map[reference.id] = reference
        logger.info(f"Added reference: {reference.id}")

    def remove_reference(self, reference_id: str) -> bool:
        """Remove a reference by ID."""
        if reference_id in self._reference_map:
            ref = self._reference_map.pop(reference_id)
            self._references.remove(ref)
            logger.info(f"Removed reference: {reference_id}")
            return True
        return False

    def get_reference(self, reference_id: str) -> Optional[Reference]:
        """Get reference by ID."""
        return self._reference_map.get(reference_id)

    def list_references(self) -> List[Reference]:
        """List all available references."""
        return self._references.copy()

    def select(
        self,
        task: str,
        context: Dict[str, Any],
        max_references: int = 3,
        required_categories: Optional[List[ReferenceCategory]] = None,
        agent_name: Optional[str] = None,
    ) -> List[ReferenceMatch]:
        """
        Select relevant references for a task.

        Args:
            task: Task description
            context: Task context (may include domain, agent, etc.)
            max_references: Maximum number of references to return
            required_categories: Categories that must be included
            agent_name: Name of executing agent for filtering

        Returns:
            List of ReferenceMatch sorted by relevance score
        """
        required_categories = required_categories or []
        matches: List[ReferenceMatch] = []

        # Extract keywords from task
        task_keywords = self._extract_keywords(task)
        domain = context.get("domain", "")

        for ref in self._references:
            # Calculate match score
            score, matched_kw = self._calculate_score(
                ref, task_keywords, domain, agent_name
            )

            if score >= self._min_score:
                reason = self._build_reason(matched_kw, domain, agent_name, ref)
                matches.append(ReferenceMatch(
                    reference=ref,
                    score=score,
                    matched_keywords=matched_kw,
                    reason=reason,
                ))

        # Ensure required categories are included
        for cat in required_categories:
            if not any(m.reference.category == cat for m in matches):
                # Find best match for this category
                cat_refs = [r for r in self._references if r.category == cat]
                if cat_refs:
                    ref = cat_refs[0]
                    matches.append(ReferenceMatch(
                        reference=ref,
                        score=self._min_score,
                        matched_keywords=[],
                        reason=f"Required category: {cat.value}",
                    ))

        # Sort by score and limit
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:max_references]

    def select_for_agent(
        self,
        agent_name: str,
        task: str,
        context: Dict[str, Any],
    ) -> List[ReferenceMatch]:
        """
        Select references specifically for an agent.

        Args:
            agent_name: Name of agent (e.g., "Felix", "Quinn")
            task: Task description
            context: Task context

        Returns:
            References relevant for this agent
        """
        # Get references where this agent is listed
        agent_refs = [r for r in self._references if agent_name in r.agents]

        matches = []
        task_keywords = self._extract_keywords(task)

        for ref in agent_refs:
            score, matched_kw = self._calculate_score(
                ref, task_keywords, context.get("domain", ""), agent_name
            )
            # Boost score for agent-specific refs
            score *= 1.2

            matches.append(ReferenceMatch(
                reference=ref,
                score=min(score, 1.0),
                matched_keywords=matched_kw,
                reason=f"Agent-specific reference for {agent_name}",
            ))

        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:3]

    def get_token_estimate(self, matches: List[ReferenceMatch]) -> int:
        """Get total token estimate for matches."""
        return sum(m.reference.token_estimate for m in matches)

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text."""
        # Lowercase and tokenize
        text_lower = text.lower()
        # Split on non-alphanumeric
        tokens = re.split(r'[^a-z0-9]+', text_lower)
        # Filter short tokens
        keywords = {t for t in tokens if len(t) > 2}
        return keywords

    def _calculate_score(
        self,
        ref: Reference,
        task_keywords: Set[str],
        domain: str,
        agent_name: Optional[str],
    ) -> tuple[float, List[str]]:
        """Calculate relevance score for a reference."""
        score = 0.0
        matched = []

        # Keyword matching (0.5 max)
        ref_keywords = set(ref.keywords)
        common = task_keywords & ref_keywords
        if common:
            keyword_score = len(common) / max(len(ref_keywords), 1)
            score += min(keyword_score * 0.6, 0.5)
            matched.extend(list(common))

        # Domain matching (0.25 max)
        if domain and domain.lower() in [d.lower() for d in ref.domains]:
            score += 0.25

        # Agent matching (0.25 max)
        if agent_name and agent_name in ref.agents:
            score += 0.25

        # Partial keyword matching for phrases
        for kw in ref.keywords:
            if kw not in matched and any(kw in tk for tk in task_keywords):
                score += 0.05
                matched.append(kw)

        return min(score, 1.0), matched

    def _build_reason(
        self,
        matched_keywords: List[str],
        domain: str,
        agent_name: Optional[str],
        ref: Reference,
    ) -> str:
        """Build explanation for match."""
        parts = []

        if matched_keywords:
            parts.append(f"Keywords: {', '.join(matched_keywords[:5])}")

        if domain and domain.lower() in [d.lower() for d in ref.domains]:
            parts.append(f"Domain match: {domain}")

        if agent_name and agent_name in ref.agents:
            parts.append(f"Agent match: {agent_name}")

        return "; ".join(parts) if parts else "General relevance"


def create_reference_selector(
    min_score: float = 0.1,
) -> ReferenceSelector:
    """
    Factory function to create reference selector.

    Args:
        min_score: Minimum match score threshold

    Returns:
        Configured ReferenceSelector
    """
    return ReferenceSelector(min_score=min_score)
