"""
Code to Functionality Mapper.

Maps code locations (files, functions, classes) to functionality units
(Epic/Feature/Story) using traceability data and code analysis.
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class FunctionalityMapping:
    """Mapping of code to functionality."""
    epic_id: Optional[str] = None
    epic_name: Optional[str] = None
    feature_id: Optional[str] = None
    feature_name: Optional[str] = None
    story_id: Optional[str] = None
    story_name: Optional[str] = None
    confidence: float = 0.0
    match_reason: str = ""


@dataclass
class ModuleMapping:
    """Mapping of a module/file to domain and functionality."""
    module_path: str
    domain: str = ""
    business_capability: str = ""
    functionalities: List[FunctionalityMapping] = field(default_factory=list)


class CodeToFunctionalityMapper:
    """
    Maps code locations to Epic/Feature/Story using:
    1. Brown Paper domain mappings
    2. Traceability data
    3. File path heuristics
    4. Function name analysis
    """

    def __init__(
        self,
        domain_mappings: Optional[Dict[str, Dict[str, Any]]] = None,
        traceability_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize mapper with optional pre-loaded data.

        Args:
            domain_mappings: Brown Paper domain -> functionality mappings
            traceability_data: Story -> code file traceability
        """
        self.domain_mappings = domain_mappings or {}
        self.traceability_data = traceability_data or {}
        self._build_reverse_index()

    def _build_reverse_index(self):
        """Build reverse index from file paths to functionality."""
        self.file_to_functionality: Dict[str, List[FunctionalityMapping]] = {}

        # Index from traceability data
        for story_id, story_data in self.traceability_data.items():
            if isinstance(story_data, dict):
                files = story_data.get("files", [])
                for file_path in files:
                    if file_path not in self.file_to_functionality:
                        self.file_to_functionality[file_path] = []
                    self.file_to_functionality[file_path].append(
                        FunctionalityMapping(
                            epic_id=story_data.get("epic_id"),
                            epic_name=story_data.get("epic_name"),
                            feature_id=story_data.get("feature_id"),
                            feature_name=story_data.get("feature_name"),
                            story_id=story_id,
                            story_name=story_data.get("story_name", ""),
                            confidence=0.9,
                            match_reason="Traceability data",
                        )
                    )

    def map_code_location(
        self,
        file_path: str,
        function_name: Optional[str] = None,
        class_name: Optional[str] = None,
    ) -> FunctionalityMapping:
        """
        Map a code location to functionality.

        Args:
            file_path: Path to the source file
            function_name: Optional function/method name
            class_name: Optional class name

        Returns:
            FunctionalityMapping with best match
        """
        # 1. Check direct traceability
        if file_path in self.file_to_functionality:
            mappings = self.file_to_functionality[file_path]
            if mappings:
                best = max(mappings, key=lambda m: m.confidence)
                return best

        # 2. Check domain mappings based on file path
        domain_match = self._match_domain_from_path(file_path)
        if domain_match:
            return domain_match

        # 3. Use heuristics based on file name and function
        heuristic_match = self._match_from_heuristics(
            file_path, function_name, class_name
        )
        if heuristic_match:
            return heuristic_match

        # 4. Return unknown mapping
        return FunctionalityMapping(
            confidence=0.1,
            match_reason="No direct mapping found",
        )

    def _match_domain_from_path(self, file_path: str) -> Optional[FunctionalityMapping]:
        """Match functionality based on file path and domain mappings."""
        file_lower = file_path.lower()

        for domain_name, domain_data in self.domain_mappings.items():
            patterns = domain_data.get("path_patterns", [])
            for pattern in patterns:
                if re.search(pattern, file_lower):
                    return FunctionalityMapping(
                        epic_id=domain_data.get("epic_id"),
                        epic_name=domain_data.get("epic_name", domain_name),
                        feature_id=domain_data.get("feature_id"),
                        feature_name=domain_data.get("feature_name"),
                        confidence=0.7,
                        match_reason=f"Domain pattern match: {domain_name}",
                    )
        return None

    def _match_from_heuristics(
        self,
        file_path: str,
        function_name: Optional[str],
        class_name: Optional[str],
    ) -> Optional[FunctionalityMapping]:
        """Use naming heuristics to match functionality."""
        file_lower = file_path.lower()
        func_lower = (function_name or "").lower()

        # Common business domain patterns
        domain_patterns = {
            "declaratie": ("Declaratieverwerking", "Declaratie Management"),
            "patient": ("Patientbeheer", "Patient Management"),
            "agenda": ("Agendabeheer", "Appointment Scheduling"),
            "facturatie": ("Facturatie", "Billing"),
            "vecozo": ("Vecozo Integratie", "Vecozo Integration"),
            "zorgverlener": ("Zorgverlenerbeheer", "Provider Management"),
            "dossier": ("Dossierbeheer", "Medical Records"),
            "rapportage": ("Rapportage", "Reporting"),
            "authenticatie": ("Authenticatie", "Authentication"),
            "login": ("Authenticatie", "Authentication"),
            "security": ("Security", "Security"),
            "admin": ("Beheer", "Administration"),
            "config": ("Configuratie", "Configuration"),
            "export": ("Data Export", "Data Export"),
            "import": ("Data Import", "Data Import"),
            "api": ("API Services", "API Services"),
            "batch": ("Batch Processing", "Batch Processing"),
        }

        # Check file path and function name
        combined = f"{file_lower} {func_lower}"
        for pattern, (dutch_name, english_name) in domain_patterns.items():
            if pattern in combined:
                return FunctionalityMapping(
                    epic_name=dutch_name,
                    feature_name=english_name,
                    confidence=0.5,
                    match_reason=f"Heuristic pattern match: {pattern}",
                )

        return None

    def load_domain_mappings(self, domains: List[Dict[str, Any]]):
        """
        Load domain mappings from Brown Paper analysis.

        Args:
            domains: List of domain dictionaries with path patterns
        """
        for domain in domains:
            domain_name = domain.get("name", "")
            if domain_name:
                self.domain_mappings[domain_name] = {
                    "epic_id": domain.get("epic_id"),
                    "epic_name": domain.get("epic_name", domain_name),
                    "feature_id": domain.get("feature_id"),
                    "feature_name": domain.get("feature_name"),
                    "path_patterns": domain.get("path_patterns", []),
                    "modules": domain.get("modules", []),
                }

    def load_traceability(self, traceability: Dict[str, Any]):
        """
        Load traceability data for file -> story mappings.

        Args:
            traceability: Dictionary mapping story IDs to file lists
        """
        self.traceability_data = traceability
        self._build_reverse_index()

    def get_module_mapping(self, file_path: str) -> ModuleMapping:
        """
        Get full module mapping including domain and all functionalities.

        Args:
            file_path: Path to the source file

        Returns:
            ModuleMapping with all associated functionality
        """
        functionalities = []

        # Get direct traceability mappings
        if file_path in self.file_to_functionality:
            functionalities.extend(self.file_to_functionality[file_path])

        # Get domain-based mapping
        domain_match = self._match_domain_from_path(file_path)
        if domain_match:
            functionalities.append(domain_match)

        # Determine primary domain
        domain = ""
        if functionalities:
            best = max(functionalities, key=lambda f: f.confidence)
            domain = best.epic_name or best.feature_name or ""

        return ModuleMapping(
            module_path=file_path,
            domain=domain,
            functionalities=functionalities,
        )

    def batch_map(
        self,
        locations: List[Dict[str, Any]],
    ) -> Dict[str, FunctionalityMapping]:
        """
        Map multiple code locations in batch.

        Args:
            locations: List of {"file": str, "function": str, "class": str}

        Returns:
            Dictionary mapping file paths to functionality
        """
        results = {}
        for loc in locations:
            file_path = loc.get("file", "")
            if file_path and file_path not in results:
                results[file_path] = self.map_code_location(
                    file_path=file_path,
                    function_name=loc.get("function"),
                    class_name=loc.get("class"),
                )
        return results
