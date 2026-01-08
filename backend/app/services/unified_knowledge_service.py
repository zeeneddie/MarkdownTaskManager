"""
Unified Knowledge Service - Combined Knowledge Sources

Week 62: Code Understanding Integration

Combines multiple knowledge sources:
- CodeWiki (module structure, documentation)
- CodeRAG (semantic code search)
- ChromaDB (general embeddings)
- HCI-CRS Knowledge (project-specific docs)

Provides unified query interface for agents.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import logging
from enum import Enum

from sqlalchemy.orm import Session

from app.services.codewiki_service import CodeWikiService
from app.services.code_rag_service import CodeRAGService, get_code_rag_service

logger = logging.getLogger(__name__)


class KnowledgeSource(str, Enum):
    """Available knowledge sources."""
    CODEWIKI = "codewiki"
    CODERAG = "coderag"
    CHROMADB = "chromadb"
    HCI_CRS = "hci_crs"
    ALL = "all"


class QueryType(str, Enum):
    """Types of knowledge queries."""
    ARCHITECTURE = "architecture"
    CODE_SEARCH = "code_search"
    DOCUMENTATION = "documentation"
    DEPENDENCIES = "dependencies"
    SIMILAR_CODE = "similar_code"
    IMPLEMENTATION = "implementation"


class UnifiedKnowledgeService:
    """
    Unified interface for querying multiple knowledge sources.

    Provides:
    - Combined queries across sources
    - Source-specific queries
    - Result ranking and merging
    - Agent-optimized context generation
    """

    def __init__(self, db: Session):
        """Initialize unified knowledge service."""
        self.db = db
        self.codewiki_service = CodeWikiService(db)
        self.coderag_service = get_code_rag_service()

    def query(
        self,
        query: str,
        project_id: int,
        sources: List[KnowledgeSource] = None,
        query_type: QueryType = None,
        n_results: int = 10,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query knowledge sources.

        Args:
            query: Search query
            project_id: Project ID to search within
            sources: Knowledge sources to query (default: all)
            query_type: Type of query for optimization
            n_results: Maximum results per source
            language: Filter by programming language

        Returns:
            Combined results from all sources
        """
        sources = sources or [KnowledgeSource.ALL]

        results = {
            "query": query,
            "project_id": project_id,
            "query_type": query_type.value if query_type else None,
            "sources_queried": [],
            "results": [],
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "total_results": 0,
            }
        }

        # Determine which sources to query
        if KnowledgeSource.ALL in sources:
            sources_to_query = [
                KnowledgeSource.CODEWIKI,
                KnowledgeSource.CODERAG,
            ]
        else:
            sources_to_query = sources

        # Query each source
        for source in sources_to_query:
            source_results = self._query_source(
                source=source,
                query=query,
                project_id=project_id,
                query_type=query_type,
                n_results=n_results,
                language=language
            )

            results["sources_queried"].append(source.value)
            results["results"].extend(source_results)

        # Rank and deduplicate results
        results["results"] = self._rank_results(results["results"])
        results["metadata"]["total_results"] = len(results["results"])

        return results

    def _query_source(
        self,
        source: KnowledgeSource,
        query: str,
        project_id: int,
        query_type: Optional[QueryType],
        n_results: int,
        language: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Query a specific knowledge source."""
        try:
            if source == KnowledgeSource.CODEWIKI:
                return self._query_codewiki(query, project_id, query_type, n_results)
            elif source == KnowledgeSource.CODERAG:
                return self._query_coderag(query, project_id, query_type, n_results, language)
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to query {source}: {e}")
            return []

    def _query_codewiki(
        self,
        query: str,
        project_id: int,
        query_type: Optional[QueryType],
        n_results: int
    ) -> List[Dict[str, Any]]:
        """Query CodeWiki knowledge."""
        results = []

        # Get latest analysis
        analysis = self.codewiki_service.get_latest_analysis(project_id)
        if not analysis:
            return []

        # Get modules
        modules = self.codewiki_service.get_modules(analysis.id)

        # Simple text matching for modules
        query_lower = query.lower()
        for module in modules:
            score = 0
            if module.name and query_lower in module.name.lower():
                score += 0.8
            if module.description and query_lower in module.description.lower():
                score += 0.5
            if module.purpose and query_lower in module.purpose.lower():
                score += 0.3

            if score > 0:
                results.append({
                    "source": "codewiki",
                    "type": "module",
                    "id": f"codewiki_module_{module.id}",
                    "title": module.name,
                    "content": module.description or module.purpose or f"Module: {module.name}",
                    "metadata": {
                        "path": module.path,
                        "file_count": module.file_count,
                        "level": module.level,
                    },
                    "score": min(score, 1.0),
                })

        # Get diagrams if architecture query
        if query_type == QueryType.ARCHITECTURE:
            diagrams = self.codewiki_service.get_diagrams(analysis.id)
            for diagram in diagrams[:n_results]:
                results.append({
                    "source": "codewiki",
                    "type": "diagram",
                    "id": f"codewiki_diagram_{diagram.id}",
                    "title": diagram.name,
                    "content": diagram.mermaid_code[:500],
                    "metadata": {
                        "diagram_type": diagram.diagram_type.value if diagram.diagram_type else None,
                    },
                    "score": 0.7,
                })

        # Sort by score and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:n_results]

    def _query_coderag(
        self,
        query: str,
        project_id: int,
        query_type: Optional[QueryType],
        n_results: int,
        language: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Query CodeRAG semantic search."""
        if not self.coderag_service.is_available:
            return []

        # Determine chunk type filter
        chunk_type = None
        if query_type == QueryType.IMPLEMENTATION:
            chunk_type = "function"

        # Search
        matches = self.coderag_service.search(
            query=query,
            n_results=n_results,
            project_id=project_id,
            language=language,
            chunk_type=chunk_type
        )

        results = []
        for match in matches:
            results.append({
                "source": "coderag",
                "type": match.get("chunk_type", "code"),
                "id": f"coderag_{match.get('id', '')}",
                "title": match.get("name") or f"{match.get('file_path', '')}:{match.get('start_line', 0)}",
                "content": match.get("content", "")[:500],
                "metadata": {
                    "file_path": match.get("file_path"),
                    "start_line": match.get("start_line"),
                    "end_line": match.get("end_line"),
                    "language": match.get("language"),
                },
                "score": match.get("similarity", 0),
            })

        return results

    def _rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank and deduplicate results."""
        # Sort by score
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Deduplicate by content similarity (simple)
        seen_titles = set()
        unique_results = []

        for result in results:
            title = result.get("title", "").lower()
            if title not in seen_titles:
                seen_titles.add(title)
                unique_results.append(result)

        return unique_results

    # ============ Agent-Specific Methods ============

    def get_agent_context(
        self,
        agent_name: str,
        project_id: int,
        task_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get optimized context for a specific agent.

        Args:
            agent_name: Agent name (felix, miguel, quinn, diana, etc.)
            project_id: Project ID
            task_description: Optional task description for context

        Returns:
            Agent-optimized knowledge context
        """
        context = {
            "agent": agent_name,
            "project_id": project_id,
            "timestamp": datetime.utcnow().isoformat(),
            "sections": [],
        }

        # Get CodeWiki agent context if available
        analysis = self.codewiki_service.get_latest_analysis(project_id)
        if analysis:
            codewiki_context = self.codewiki_service.get_agent_context(
                analysis.id, agent_name.lower()
            )
            if codewiki_context:
                context["sections"].append({
                    "source": "codewiki",
                    "title": f"{agent_name.title()} Context",
                    "summary": codewiki_context.context_summary,
                    "details": codewiki_context.context_details,
                })

        # Add task-specific code search if description provided
        if task_description:
            code_results = self._query_coderag(
                query=task_description,
                project_id=project_id,
                query_type=QueryType.CODE_SEARCH,
                n_results=5,
                language=None
            )
            if code_results:
                context["sections"].append({
                    "source": "coderag",
                    "title": "Relevant Code",
                    "results": code_results,
                })

        return context

    def get_architecture_context(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """Get architecture-focused context for Felix."""
        return self.query(
            query="architecture modules components",
            project_id=project_id,
            query_type=QueryType.ARCHITECTURE,
            n_results=15
        )

    def get_dependency_context(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """Get dependency-focused context for Miguel."""
        context = {
            "project_id": project_id,
            "dependencies": {},
        }

        analysis = self.codewiki_service.get_latest_analysis(project_id)
        if analysis:
            modules = self.codewiki_service.get_modules(analysis.id)

            internal_deps = set()
            external_deps = set()

            for module in modules:
                internal_deps.update(module.dependencies or [])
                external_deps.update(module.external_dependencies or [])

            context["dependencies"] = {
                "internal": list(internal_deps),
                "external": list(external_deps),
                "module_count": len(modules),
            }

        return context

    def find_similar_implementations(
        self,
        code_snippet: str,
        project_id: int,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find similar code implementations."""
        return self._query_coderag(
            query=code_snippet,
            project_id=project_id,
            query_type=QueryType.SIMILAR_CODE,
            n_results=10,
            language=language
        )

    def search_functions(
        self,
        description: str,
        project_id: int,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for function implementations by description."""
        return self._query_coderag(
            query=description,
            project_id=project_id,
            query_type=QueryType.IMPLEMENTATION,
            n_results=10,
            language=language
        )

    # ============ Index Management ============

    def index_project(self, project_id: int, repo_path: str) -> Dict[str, Any]:
        """
        Index a project across all knowledge sources.

        Args:
            project_id: Project ID
            repo_path: Repository path

        Returns:
            Indexing results from all sources
        """
        results = {
            "project_id": project_id,
            "repo_path": repo_path,
            "sources": {},
        }

        # Index with CodeRAG
        if self.coderag_service.is_available:
            coderag_result = self.coderag_service.index_repository(
                repo_path=repo_path,
                project_id=project_id
            )
            results["sources"]["coderag"] = coderag_result

        return results

    def get_index_statistics(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Get indexing statistics across sources."""
        stats = {
            "sources": {},
        }

        # CodeRAG stats
        coderag_stats = self.coderag_service.get_statistics()
        stats["sources"]["coderag"] = coderag_stats

        # CodeWiki stats
        if project_id:
            analysis = self.codewiki_service.get_latest_analysis(project_id)
            if analysis:
                stats["sources"]["codewiki"] = {
                    "analysis_id": analysis.id,
                    "status": analysis.status.value if analysis.status else None,
                    "total_modules": analysis.total_modules,
                    "total_files": analysis.total_files,
                }

        return stats
