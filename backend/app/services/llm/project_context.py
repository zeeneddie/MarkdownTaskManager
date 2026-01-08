"""
Project Context Parser - Week 101

Parses PROJECT_CONTEXT.md files into structured ProjectContext objects.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class TechStack:
    """Technology stack configuration."""
    primary_language: str = ""
    framework: str = ""
    database: str = ""
    cache: str = ""
    message_queue: str = ""


@dataclass
class ArchitecturePattern:
    """Architecture pattern configuration."""
    style: str = ""  # Monolith, Microservices, etc.
    layers: str = ""  # 3-tier, Clean Architecture, etc.
    api_style: str = ""  # REST, GraphQL, etc.


@dataclass
class SecurityModel:
    """Security configuration."""
    authentication: str = ""  # JWT, OAuth2, etc.
    authorization: str = ""  # RBAC, ABAC, etc.
    password_hashing: str = ""
    token_expiry: str = ""
    compliance_requirements: List[str] = field(default_factory=list)


@dataclass
class NamingConventions:
    """Naming convention rules."""
    classes: str = "PascalCase"
    functions: str = "snake_case"
    files: str = "snake_case"
    constants: str = "SCREAMING_SNAKE_CASE"
    private_fields: str = "_underscore_prefix"


@dataclass
class DomainTerm:
    """Domain vocabulary term."""
    term: str
    definition: str
    code_entity: str = ""


@dataclass
class ProjectContext:
    """
    Universal project context structure.

    Parsed from PROJECT_CONTEXT.md and used by LLM Context Adapters
    to generate provider-specific context files.
    """
    # Core Identity
    project_name: str = ""
    version: str = ""
    status: str = "active"
    start_date: str = ""

    # Technical Configuration
    tech_stack: TechStack = field(default_factory=TechStack)
    architecture: ArchitecturePattern = field(default_factory=ArchitecturePattern)
    security: SecurityModel = field(default_factory=SecurityModel)
    naming_conventions: NamingConventions = field(default_factory=NamingConventions)

    # Domain Knowledge
    domain_vocabulary: List[DomainTerm] = field(default_factory=list)
    aggregate_roots: Dict[str, str] = field(default_factory=dict)

    # Guidelines
    implementation_order: List[str] = field(default_factory=list)
    testing_requirements: Dict[str, Any] = field(default_factory=dict)

    # Environment
    environment_variables: Dict[str, str] = field(default_factory=dict)
    feature_flags: Dict[str, Any] = field(default_factory=dict)

    # Notes for AI
    dos: List[str] = field(default_factory=list)
    donts: List[str] = field(default_factory=list)
    questions_to_ask: List[str] = field(default_factory=list)

    # Raw content for fallback
    raw_content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "project_name": self.project_name,
            "version": self.version,
            "status": self.status,
            "tech_stack": {
                "primary_language": self.tech_stack.primary_language,
                "framework": self.tech_stack.framework,
                "database": self.tech_stack.database,
                "cache": self.tech_stack.cache,
                "message_queue": self.tech_stack.message_queue,
            },
            "architecture": {
                "style": self.architecture.style,
                "layers": self.architecture.layers,
                "api_style": self.architecture.api_style,
            },
            "security": {
                "authentication": self.security.authentication,
                "authorization": self.security.authorization,
                "compliance": self.security.compliance_requirements,
            },
            "naming_conventions": {
                "classes": self.naming_conventions.classes,
                "functions": self.naming_conventions.functions,
                "files": self.naming_conventions.files,
            },
            "domain_vocabulary": [
                {"term": t.term, "definition": t.definition, "entity": t.code_entity}
                for t in self.domain_vocabulary
            ],
            "implementation_order": self.implementation_order,
            "dos": self.dos,
            "donts": self.donts,
        }


class ProjectContextParser:
    """
    Parser for PROJECT_CONTEXT.md files.

    Extracts structured context from markdown format.
    """

    def __init__(self):
        self._section_patterns = {
            "project_identity": r"###?\s*Project Identity\s*\n(.*?)(?=###|\Z)",
            "tech_stack": r"###?\s*Tech Stack\s*\n(.*?)(?=###|\Z)",
            "architecture": r"###?\s*Architecture Pattern\s*\n(.*?)(?=###|\Z)",
            "security": r"###?\s*Security Patterns?\s*\n(.*?)(?=###|\Z)",
            "naming": r"###?\s*Naming Conventions?\s*\n(.*?)(?=###|\Z)",
            "domain_vocabulary": r"###?\s*(?:Business Terms|Domain Vocabulary)\s*\n(.*?)(?=###|\Z)",
            "implementation_order": r"###?\s*Implementation Order\s*\n(.*?)(?=###|\Z)",
            "dos": r"###?\s*Do'?s\s*\n(.*?)(?=###|\Z)",
            "donts": r"###?\s*Don'?ts\s*\n(.*?)(?=###|\Z)",
        }

    def parse_file(self, file_path: str) -> ProjectContext:
        """
        Parse a PROJECT_CONTEXT.md file.

        Args:
            file_path: Path to the markdown file

        Returns:
            ProjectContext object with parsed data
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Context file not found: {file_path}")

        content = path.read_text(encoding="utf-8")
        return self.parse_content(content)

    def parse_content(self, content: str) -> ProjectContext:
        """
        Parse PROJECT_CONTEXT.md content.

        Args:
            content: Markdown content string

        Returns:
            ProjectContext object with parsed data
        """
        context = ProjectContext(raw_content=content)

        # Parse each section
        context.project_name = self._extract_field(content, "Project Name")
        context.version = self._extract_field(content, "Version")
        context.status = self._extract_field(content, "Status") or "active"

        # Parse tech stack
        context.tech_stack = self._parse_tech_stack(content)

        # Parse architecture
        context.architecture = self._parse_architecture(content)

        # Parse security
        context.security = self._parse_security(content)

        # Parse naming conventions
        context.naming_conventions = self._parse_naming(content)

        # Parse domain vocabulary
        context.domain_vocabulary = self._parse_domain_vocabulary(content)

        # Parse implementation order
        context.implementation_order = self._parse_ordered_list(content, "Implementation Order")

        # Parse dos and donts
        context.dos = self._parse_list_section(content, "Do's")
        context.donts = self._parse_list_section(content, "Don'ts")
        context.questions_to_ask = self._parse_list_section(content, "Questions to Ask")

        return context

    def _extract_field(self, content: str, field_name: str) -> str:
        """Extract a single field value."""
        patterns = [
            rf"\*\*{field_name}:\*\*\s*\[?([^\]\n]+)\]?",
            rf"-\s*\*\*{field_name}:\*\*\s*\[?([^\]\n]+)\]?",
            rf"{field_name}:\s*\[?([^\]\n]+)\]?",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Remove placeholder brackets
                value = re.sub(r"\[|\]", "", value)
                if value and not value.startswith("["):
                    return value
        return ""

    def _parse_tech_stack(self, content: str) -> TechStack:
        """Parse tech stack section."""
        return TechStack(
            primary_language=self._extract_field(content, "Primary Language"),
            framework=self._extract_field(content, "Framework"),
            database=self._extract_field(content, "Database"),
            cache=self._extract_field(content, "Cache"),
            message_queue=self._extract_field(content, "Message Queue"),
        )

    def _parse_architecture(self, content: str) -> ArchitecturePattern:
        """Parse architecture pattern section."""
        return ArchitecturePattern(
            style=self._extract_field(content, "Style"),
            layers=self._extract_field(content, "Layers"),
            api_style=self._extract_field(content, "API Style"),
        )

    def _parse_security(self, content: str) -> SecurityModel:
        """Parse security model section."""
        # Extract compliance requirements (checkboxes)
        compliance = []
        compliance_pattern = r"-\s*\[x\]\s*(\w+)"
        for match in re.finditer(compliance_pattern, content, re.IGNORECASE):
            compliance.append(match.group(1))

        return SecurityModel(
            authentication=self._extract_field(content, "Authentication"),
            authorization=self._extract_field(content, "Authorization"),
            password_hashing=self._extract_field(content, "Password Hashing"),
            token_expiry=self._extract_field(content, "Token Expiry"),
            compliance_requirements=compliance,
        )

    def _parse_naming(self, content: str) -> NamingConventions:
        """Parse naming conventions section."""
        return NamingConventions(
            classes=self._extract_field(content, "Classes") or "PascalCase",
            functions=self._extract_field(content, "Functions") or "snake_case",
            files=self._extract_field(content, "Files") or "snake_case",
            constants=self._extract_field(content, "Constants") or "SCREAMING_SNAKE_CASE",
            private_fields=self._extract_field(content, "Private Fields") or "_underscore_prefix",
        )

    def _parse_domain_vocabulary(self, content: str) -> List[DomainTerm]:
        """Parse domain vocabulary table."""
        terms = []

        # Match table rows: | Term | Definition | Entity |
        table_pattern = r"\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"

        for match in re.finditer(table_pattern, content):
            term = match.group(1).strip()
            definition = match.group(2).strip()
            entity = match.group(3).strip()

            # Skip header row and placeholder rows
            if term.lower() in ("term", "---", "-") or term.startswith("["):
                continue

            terms.append(DomainTerm(
                term=term,
                definition=definition,
                code_entity=entity,
            ))

        return terms

    def _parse_ordered_list(self, content: str, section_name: str) -> List[str]:
        """Parse an ordered list section."""
        items = []

        # Find section
        section_pattern = rf"###?\s*{section_name}\s*\n(.*?)(?=###|\Z)"
        match = re.search(section_pattern, content, re.IGNORECASE | re.DOTALL)

        if match:
            section_content = match.group(1)
            # Match ordered list items
            item_pattern = r"\d+\.\s*\*\*([^*]+)\*\*"
            for item_match in re.finditer(item_pattern, section_content):
                items.append(item_match.group(1).strip())

        return items

    def _parse_list_section(self, content: str, section_name: str) -> List[str]:
        """Parse a bullet list section."""
        items = []

        # Find section
        section_pattern = rf"###?\s*{section_name}\s*\n(.*?)(?=###|\Z)"
        match = re.search(section_pattern, content, re.IGNORECASE | re.DOTALL)

        if match:
            section_content = match.group(1)
            # Match bullet list items
            item_pattern = r"-\s*(.+)"
            for item_match in re.finditer(item_pattern, section_content):
                item = item_match.group(1).strip()
                if item and not item.startswith("["):
                    items.append(item)

        return items
