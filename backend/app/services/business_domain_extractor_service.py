"""
Business Domain Extractor Service

Week 159: Extract business domains from code analysis results.

This service analyzes code structure (modules, dependencies, file patterns)
to identify business domains that can be used to generate more meaningful
epics and stories.

Key Features:
- Cluster modules based on dependencies
- Analyze file/function names for domain hints
- Extract entities from code (classes, tables, forms)
- Match with common healthcare/physio domains (FysioOne specific)
- Generate structured business domains with source references

Used by Brown Paper workflow to improve epic/story generation.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
import networkx as nx

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class ExtractedEntity:
    """An entity extracted from code analysis."""
    name: str
    entity_type: str  # class, table, form, interface
    source_file: str
    line_number: Optional[int] = None
    properties: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)


@dataclass
class ModuleCluster:
    """A cluster of related modules."""
    name: str
    modules: List[str]
    cohesion_score: float  # 0.0 - 1.0
    central_module: str
    dependency_count: int
    entities: List[ExtractedEntity] = field(default_factory=list)


@dataclass
class BusinessDomainCandidate:
    """A candidate business domain identified from code analysis."""
    name: str
    description: str
    modules: List[str]
    entities: List[ExtractedEntity]
    use_cases: List[str]
    source_files: List[str]
    complexity: str  # low, medium, high, very_high
    confidence: float  # 0.0 - 1.0
    domain_hints: List[str] = field(default_factory=list)
    code_patterns: List[str] = field(default_factory=list)


@dataclass
class BusinessDomainExtractionResult:
    """Result of business domain extraction."""
    domains: List[BusinessDomainCandidate]
    module_clusters: List[ModuleCluster]
    total_modules_analyzed: int
    total_entities_found: int
    extraction_time_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# DOMAIN PATTERNS FOR HEALTHCARE/PHYSIO
# =============================================================================


# Healthcare/Physio domain patterns (FysioOne specific)
HEALTHCARE_DOMAIN_PATTERNS = {
    "patient_management": {
        "keywords": ["patient", "patiënt", "client", "cliënt", "bsn", "naw", "persoon"],
        "file_patterns": [r"patient", r"client", r"person", r"bsn"],
        "entities": ["Patient", "Adres", "Verzekering", "BSN", "Contact"],
        "use_cases": [
            "Patient registratie",
            "Patient zoeken",
            "NAW gegevens beheren",
            "BSN validatie",
            "Verzekering koppelen",
        ],
    },
    "treatment_plans": {
        "keywords": ["behandel", "diagnose", "icpc", "zorgplan", "therapie", "indicatie"],
        "file_patterns": [r"behandel", r"diagnos", r"icpc", r"zorgplan", r"therapy"],
        "entities": ["Behandelplan", "Diagnose", "ICPC_Code", "Verrichting", "Indicatie"],
        "use_cases": [
            "Diagnose registreren",
            "Behandelplan opstellen",
            "ICPC code selecteren",
            "Verrichtingen vastleggen",
            "Behandelvoortgang volgen",
        ],
    },
    "appointments": {
        "keywords": ["agenda", "afspraak", "rooster", "planning", "appointment", "schedule"],
        "file_patterns": [r"agenda", r"afspraak", r"rooster", r"schedul", r"appoint"],
        "entities": ["Afspraak", "Agenda", "Rooster", "Therapeut", "Locatie", "Tijdslot"],
        "use_cases": [
            "Afspraak plannen",
            "Agenda beheren",
            "Rooster inzien",
            "Beschikbaarheid checken",
            "Herinnering sturen",
        ],
    },
    "billing_declarations": {
        "keywords": ["declaratie", "factuur", "vecozo", "tarief", "nota", "betaling"],
        "file_patterns": [r"declar", r"factuur", r"vecozo", r"tarief", r"billing"],
        "entities": ["Declaratie", "Factuur", "Tarief", "Betaling", "Vecozo", "Nota"],
        "use_cases": [
            "Declaratie aanmaken",
            "Vecozo koppeling",
            "Factuur genereren",
            "Tarief beheren",
            "Betaling verwerken",
        ],
    },
    "reporting": {
        "keywords": ["rapport", "statistiek", "export", "overzicht", "kpi", "dashboard"],
        "file_patterns": [r"rapport", r"report", r"stat", r"export", r"overview"],
        "entities": ["Rapport", "Statistiek", "Export", "KPI", "Dashboard"],
        "use_cases": [
            "Rapport genereren",
            "Statistieken bekijken",
            "Data exporteren",
            "KPI dashboard",
            "Overzicht maken",
        ],
    },
    "user_management": {
        "keywords": ["gebruiker", "login", "authenticatie", "rechten", "rol", "user"],
        "file_patterns": [r"user", r"gebruiker", r"login", r"auth", r"rights", r"role"],
        "entities": ["Gebruiker", "Rol", "Recht", "Login", "Sessie"],
        "use_cases": [
            "Gebruiker aanmaken",
            "Rechten toewijzen",
            "Login/logout",
            "Wachtwoord reset",
            "Rollen beheren",
        ],
    },
    "system_config": {
        "keywords": ["config", "instelling", "setup", "settings", "systeem", "parameter"],
        "file_patterns": [r"config", r"setting", r"setup", r"param", r"system"],
        "entities": ["Configuratie", "Instelling", "Parameter", "Systeem"],
        "use_cases": [
            "Systeeminstellingen",
            "Configuratie beheren",
            "Parameters aanpassen",
        ],
    },
}

# Generic domain patterns (not healthcare specific)
GENERIC_DOMAIN_PATTERNS = {
    "crud_operations": {
        "keywords": ["create", "read", "update", "delete", "list", "add", "remove"],
        "file_patterns": [r"crud", r"_dao", r"repository"],
        "entities": [],
        "use_cases": ["Create", "Read", "Update", "Delete", "List"],
    },
    "data_access": {
        "keywords": ["database", "sql", "query", "connection", "transaction"],
        "file_patterns": [r"database", r"sql", r"db_", r"_db"],
        "entities": ["Database", "Connection", "Query"],
        "use_cases": ["Database connectie", "Query uitvoeren", "Transactie beheren"],
    },
    "api_layer": {
        "keywords": ["api", "endpoint", "rest", "soap", "webservice"],
        "file_patterns": [r"api", r"endpoint", r"webservice", r"asmx", r"svc"],
        "entities": ["Endpoint", "API", "Service"],
        "use_cases": ["API endpoint", "Service aanroep"],
    },
}


# =============================================================================
# BUSINESS DOMAIN EXTRACTOR SERVICE
# =============================================================================


class BusinessDomainExtractorService:
    """
    Extract business domains from code analysis results.

    This service analyzes:
    1. Module structure and dependencies
    2. File and function naming patterns
    3. Entity/class definitions
    4. Form/screen references

    To identify meaningful business domains that map to epics.
    """

    def __init__(
        self,
        domain_patterns: Optional[Dict[str, Dict]] = None,
        use_healthcare_patterns: bool = True,
    ):
        """
        Initialize the extractor.

        Args:
            domain_patterns: Custom domain patterns (optional)
            use_healthcare_patterns: Include healthcare/physio specific patterns
        """
        self.domain_patterns = {}

        # Add healthcare patterns if enabled
        if use_healthcare_patterns:
            self.domain_patterns.update(HEALTHCARE_DOMAIN_PATTERNS)

        # Add generic patterns
        self.domain_patterns.update(GENERIC_DOMAIN_PATTERNS)

        # Add custom patterns
        if domain_patterns:
            self.domain_patterns.update(domain_patterns)

        self._dependency_graph: Optional[nx.DiGraph] = None

    async def extract_domains(
        self,
        modules: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]],
        file_contents: Optional[Dict[str, str]] = None,
        scan_path: Optional[str] = None,
    ) -> BusinessDomainExtractionResult:
        """
        Extract business domains from code analysis results.

        Args:
            modules: List of code modules (from Phase 1 analysis)
            dependencies: List of dependency edges between modules
            file_contents: Optional dict of file path -> content
            scan_path: Root path of the project

        Returns:
            BusinessDomainExtractionResult with identified domains
        """
        import time
        start_time = time.time()

        logger.info(f"Starting business domain extraction for {len(modules)} modules")

        # Step 1: Build dependency graph
        self._build_dependency_graph(modules, dependencies)

        # Step 2: Cluster modules based on dependencies
        clusters = self._cluster_modules(modules)

        # Step 3: Extract entities from modules
        entities = self._extract_entities(modules, file_contents)

        # Step 4: Match modules to domain patterns
        domain_matches = self._match_domain_patterns(modules, entities)

        # Step 5: Generate domain candidates
        domains = self._generate_domain_candidates(
            clusters, entities, domain_matches, modules
        )

        # Step 6: Calculate complexity and confidence
        domains = self._score_domains(domains, modules, dependencies)

        # Sort by confidence
        domains.sort(key=lambda d: d.confidence, reverse=True)

        extraction_time_ms = int((time.time() - start_time) * 1000)

        result = BusinessDomainExtractionResult(
            domains=domains,
            module_clusters=clusters,
            total_modules_analyzed=len(modules),
            total_entities_found=len(entities),
            extraction_time_ms=extraction_time_ms,
            metadata={
                "patterns_used": list(self.domain_patterns.keys()),
                "scan_path": scan_path,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(
            f"Extracted {len(domains)} business domains from {len(modules)} modules "
            f"in {extraction_time_ms}ms"
        )

        return result

    def _build_dependency_graph(
        self,
        modules: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]],
    ) -> None:
        """Build NetworkX graph from dependencies."""
        self._dependency_graph = nx.DiGraph()

        # Add nodes for each module
        for module in modules:
            name = module.get("name") or module.get("path", "unknown")
            self._dependency_graph.add_node(name, **module)

        # Add edges for dependencies
        for dep in dependencies:
            source = dep.get("source") or dep.get("from", "")
            target = dep.get("target") or dep.get("to", "")
            if source and target:
                self._dependency_graph.add_edge(source, target, **dep)

    def _cluster_modules(
        self,
        modules: List[Dict[str, Any]],
    ) -> List[ModuleCluster]:
        """
        Cluster modules based on dependencies and naming patterns.

        Uses community detection on the dependency graph.
        """
        clusters = []

        if not self._dependency_graph or len(self._dependency_graph.nodes) == 0:
            return clusters

        try:
            # Convert to undirected for community detection
            undirected = self._dependency_graph.to_undirected()

            # Find connected components first
            components = list(nx.connected_components(undirected))

            for i, component in enumerate(components):
                component_modules = list(component)

                if len(component_modules) == 0:
                    continue

                # Find central module (highest degree)
                subgraph = self._dependency_graph.subgraph(component_modules)
                degrees = dict(subgraph.degree())
                central_module = max(degrees, key=degrees.get) if degrees else component_modules[0]

                # Calculate cohesion (ratio of internal edges to possible edges)
                internal_edges = subgraph.number_of_edges()
                possible_edges = len(component_modules) * (len(component_modules) - 1) / 2
                cohesion = internal_edges / possible_edges if possible_edges > 0 else 1.0

                cluster = ModuleCluster(
                    name=f"Cluster-{i+1}",
                    modules=component_modules,
                    cohesion_score=min(cohesion, 1.0),
                    central_module=central_module,
                    dependency_count=internal_edges,
                )
                clusters.append(cluster)

        except Exception as e:
            logger.warning(f"Error clustering modules: {e}")
            # Fallback: each module is its own cluster
            for module in modules:
                name = module.get("name") or module.get("path", "unknown")
                clusters.append(ModuleCluster(
                    name=name,
                    modules=[name],
                    cohesion_score=1.0,
                    central_module=name,
                    dependency_count=0,
                ))

        return clusters

    def _extract_entities(
        self,
        modules: List[Dict[str, Any]],
        file_contents: Optional[Dict[str, str]] = None,
    ) -> List[ExtractedEntity]:
        """
        Extract entities (classes, tables, forms) from modules.
        """
        entities = []

        for module in modules:
            # Get classes from module
            classes = module.get("classes", [])
            path = module.get("path", "")

            for class_name in classes:
                if isinstance(class_name, str):
                    entity = ExtractedEntity(
                        name=class_name,
                        entity_type="class",
                        source_file=path,
                    )
                    entities.append(entity)
                elif isinstance(class_name, dict):
                    entity = ExtractedEntity(
                        name=class_name.get("name", "Unknown"),
                        entity_type=class_name.get("type", "class"),
                        source_file=path,
                        line_number=class_name.get("line"),
                        properties=class_name.get("properties", []),
                    )
                    entities.append(entity)

            # Check for forms (ASP.NET, VB.NET)
            if any(ext in path.lower() for ext in [".aspx", ".vb", ".ascx"]):
                # Extract form name from path
                form_name = Path(path).stem
                entities.append(ExtractedEntity(
                    name=form_name,
                    entity_type="form",
                    source_file=path,
                ))

        # Also extract from file contents if provided
        if file_contents:
            entities.extend(self._extract_entities_from_content(file_contents))

        return entities

    def _extract_entities_from_content(
        self,
        file_contents: Dict[str, str],
    ) -> List[ExtractedEntity]:
        """
        Extract entities from actual file contents using regex patterns.
        """
        entities = []

        # Patterns for different entity types
        patterns = {
            # VB.NET classes
            "vb_class": (r"(?:Public|Private|Friend)?\s*Class\s+(\w+)", "class"),
            # C# classes
            "cs_class": (r"(?:public|private|internal)?\s*class\s+(\w+)", "class"),
            # SQL tables
            "sql_table": (r"CREATE\s+TABLE\s+(?:\[?dbo\]?\.)?\[?(\w+)\]?", "table"),
            # VB.NET Forms
            "vb_form": (r"Inherits\s+System\.Windows\.Forms\.Form", "form"),
            # ASP.NET controls
            "asp_control": (r"<%@\s+Control.*?Inherits\s*=\s*\"([^\"]+)\"", "control"),
        }

        for file_path, content in file_contents.items():
            if not content:
                continue

            for pattern_name, (pattern, entity_type) in patterns.items():
                for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                    name = match.group(1) if match.groups() else Path(file_path).stem
                    entities.append(ExtractedEntity(
                        name=name,
                        entity_type=entity_type,
                        source_file=file_path,
                    ))

        return entities

    def _match_domain_patterns(
        self,
        modules: List[Dict[str, Any]],
        entities: List[ExtractedEntity],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Match modules and entities to predefined domain patterns.

        Returns a dict of domain_name -> list of matching items.
        """
        matches: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for domain_name, patterns in self.domain_patterns.items():
            keywords = patterns.get("keywords", [])
            file_patterns = patterns.get("file_patterns", [])
            entity_patterns = patterns.get("entities", [])

            # Check modules
            for module in modules:
                name = module.get("name", "").lower()
                path = module.get("path", "").lower()

                # Match keywords
                if any(kw.lower() in name or kw.lower() in path for kw in keywords):
                    matches[domain_name].append({
                        "type": "module",
                        "item": module,
                        "match_type": "keyword",
                    })
                    continue

                # Match file patterns
                if any(re.search(fp, path, re.IGNORECASE) for fp in file_patterns):
                    matches[domain_name].append({
                        "type": "module",
                        "item": module,
                        "match_type": "file_pattern",
                    })

            # Check entities
            for entity in entities:
                entity_name = entity.name.lower()

                # Match entity patterns
                if any(ep.lower() in entity_name or entity_name in ep.lower()
                       for ep in entity_patterns):
                    matches[domain_name].append({
                        "type": "entity",
                        "item": entity,
                        "match_type": "entity_pattern",
                    })

        return matches

    def _generate_domain_candidates(
        self,
        clusters: List[ModuleCluster],
        entities: List[ExtractedEntity],
        domain_matches: Dict[str, List[Dict[str, Any]]],
        modules: List[Dict[str, Any]],
    ) -> List[BusinessDomainCandidate]:
        """
        Generate business domain candidates from analysis results.
        """
        candidates = []
        used_modules: Set[str] = set()

        # First, create domains from pattern matches
        for domain_name, matches in domain_matches.items():
            if not matches:
                continue

            patterns = self.domain_patterns.get(domain_name, {})

            # Collect modules and entities for this domain
            domain_modules = []
            domain_entities = []
            source_files = []

            for match in matches:
                if match["type"] == "module":
                    module = match["item"]
                    module_name = module.get("name") or module.get("path", "")
                    if module_name not in used_modules:
                        domain_modules.append(module_name)
                        used_modules.add(module_name)
                        source_files.append(module.get("path", ""))
                elif match["type"] == "entity":
                    entity = match["item"]
                    domain_entities.append(entity)
                    source_files.append(entity.source_file)

            if not domain_modules and not domain_entities:
                continue

            # Create human-readable domain name
            readable_name = self._make_readable_domain_name(domain_name)

            candidate = BusinessDomainCandidate(
                name=readable_name,
                description=f"Business domain covering {readable_name.lower()} functionality",
                modules=domain_modules,
                entities=domain_entities,
                use_cases=patterns.get("use_cases", []),
                source_files=list(set(source_files)),
                complexity="medium",  # Will be calculated later
                confidence=0.0,  # Will be calculated later
                domain_hints=patterns.get("keywords", []),
                code_patterns=patterns.get("file_patterns", []),
            )
            candidates.append(candidate)

        # Then, create domains from remaining module clusters
        for cluster in clusters:
            # Check if cluster modules are already assigned
            unassigned_modules = [m for m in cluster.modules if m not in used_modules]
            if not unassigned_modules:
                continue

            # Determine domain name from cluster analysis
            domain_name = self._infer_domain_name(unassigned_modules)

            candidate = BusinessDomainCandidate(
                name=domain_name,
                description=f"Functional area covering {domain_name.lower()} modules",
                modules=unassigned_modules,
                entities=[],
                use_cases=self._infer_use_cases(unassigned_modules),
                source_files=unassigned_modules,
                complexity="medium",
                confidence=0.0,
                domain_hints=[],
                code_patterns=[],
            )
            candidates.append(candidate)
            used_modules.update(unassigned_modules)

        return candidates

    def _make_readable_domain_name(self, domain_key: str) -> str:
        """Convert domain key to readable name."""
        name_map = {
            "patient_management": "Patiënt Beheer",
            "treatment_plans": "Behandelplan & Diagnose",
            "appointments": "Agenda & Planning",
            "billing_declarations": "Declaraties & Facturatie",
            "reporting": "Rapportages & Statistiek",
            "user_management": "Gebruikersbeheer & Rechten",
            "system_config": "Systeem & Configuratie",
            "crud_operations": "CRUD Operaties",
            "data_access": "Data Access",
            "api_layer": "API Layer",
        }
        return name_map.get(domain_key, domain_key.replace("_", " ").title())

    def _infer_domain_name(self, modules: List[str]) -> str:
        """Infer a domain name from module names."""
        # Find common prefix/suffix in module names
        if not modules:
            return "Unknown Domain"

        # Extract meaningful words from module names
        words = []
        for module in modules:
            # Remove path and extension
            name = Path(module).stem.lower()
            # Split on common separators
            parts = re.split(r'[_\-./\\]', name)
            words.extend(p for p in parts if len(p) > 2)

        if not words:
            return "Generic Module"

        # Find most common word
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1

        most_common = max(word_counts, key=word_counts.get)
        return most_common.title() + " Module"

    def _infer_use_cases(self, modules: List[str]) -> List[str]:
        """Infer use cases from module names."""
        use_cases = []

        # Common action patterns
        action_patterns = [
            (r"create|add|new|insert", "Create"),
            (r"read|get|fetch|load|list", "Read"),
            (r"update|edit|modify|change", "Update"),
            (r"delete|remove|drop", "Delete"),
            (r"search|find|filter", "Search"),
            (r"export|download", "Export"),
            (r"import|upload", "Import"),
            (r"validate|check|verify", "Validate"),
        ]

        for module in modules:
            name = Path(module).stem.lower()
            for pattern, action in action_patterns:
                if re.search(pattern, name):
                    use_cases.append(f"{action} {name.replace('_', ' ').title()}")
                    break

        return list(set(use_cases))[:5]  # Limit to 5 use cases

    def _score_domains(
        self,
        domains: List[BusinessDomainCandidate],
        modules: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]],
    ) -> List[BusinessDomainCandidate]:
        """
        Calculate complexity and confidence scores for domains.
        """
        total_modules = len(modules) if modules else 1

        for domain in domains:
            # Calculate confidence based on:
            # - Number of modules (more = higher confidence)
            # - Number of entities (more = higher confidence)
            # - Number of pattern matches (domain_hints)

            module_score = min(len(domain.modules) / 10, 0.3)  # Max 0.3
            entity_score = min(len(domain.entities) / 5, 0.3)  # Max 0.3
            hint_score = min(len(domain.domain_hints) / 3, 0.2)  # Max 0.2
            use_case_score = min(len(domain.use_cases) / 5, 0.2)  # Max 0.2

            domain.confidence = module_score + entity_score + hint_score + use_case_score

            # Calculate complexity based on:
            # - Number of modules
            # - Number of dependencies

            module_count = len(domain.modules)
            if module_count > 30:
                domain.complexity = "very_high"
            elif module_count > 20:
                domain.complexity = "high"
            elif module_count > 10:
                domain.complexity = "medium"
            else:
                domain.complexity = "low"

        return domains

    def to_brown_paper_domains(
        self,
        result: BusinessDomainExtractionResult,
    ) -> List[Dict[str, Any]]:
        """
        Convert extraction result to Brown Paper domain format.

        Returns format compatible with existing BrownPaperService.
        """
        brown_paper_domains = []

        for i, domain in enumerate(result.domains):
            bp_domain = {
                "name": domain.name,
                "description": domain.description,
                "modules": domain.modules,
                "entities": [e.name for e in domain.entities],
                "use_cases": domain.use_cases,
                "complexity": domain.complexity,
                "priority": len(result.domains) - i,  # Higher priority for first domains
                "source_files": domain.source_files,
                "confidence": domain.confidence,
                "metadata": {
                    "domain_hints": domain.domain_hints,
                    "code_patterns": domain.code_patterns,
                    "entity_details": [
                        {
                            "name": e.name,
                            "type": e.entity_type,
                            "source": e.source_file,
                        }
                        for e in domain.entities
                    ],
                },
            }
            brown_paper_domains.append(bp_domain)

        return brown_paper_domains


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def get_business_domain_extractor(
    use_healthcare_patterns: bool = True,
    custom_patterns: Optional[Dict[str, Dict]] = None,
) -> BusinessDomainExtractorService:
    """
    Factory function to create BusinessDomainExtractorService.

    Args:
        use_healthcare_patterns: Include FysioOne/healthcare specific patterns
        custom_patterns: Additional custom domain patterns

    Returns:
        Configured BusinessDomainExtractorService instance
    """
    return BusinessDomainExtractorService(
        domain_patterns=custom_patterns,
        use_healthcare_patterns=use_healthcare_patterns,
    )
