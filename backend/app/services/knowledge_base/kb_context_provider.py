"""
Knowledge Base Context Provider

Provides relevant KB context to agents during analysis workflows.
Queries Famous Bugs and Post-Mortems collections based on agent role and task.
"""

from typing import Dict, List, Optional, Any


class KBContextProvider:
    """Provides KB context to agents based on their role and current task."""

    def __init__(self, chroma_service):
        self.chroma_service = chroma_service

    def get_agent_context(
        self,
        agent_name: str,
        task_description: str,
        source_code_snippet: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get relevant KB context for a specific agent.

        Agent-specific query strategies:
        - Betty (code quality): famous_bugs + post_mortems for code quality patterns
        - Diana (security): famous_bugs with CWE filter for security context
        - Marcus (architecture): post_mortems for architectural failure patterns
        - Quinn (security audit): famous_bugs + post_mortems for security audit
        """
        query = task_description
        if source_code_snippet:
            query = f"{task_description}\n\nCode context:\n{source_code_snippet[:500]}"

        context = {
            "agent": agent_name,
            "famous_bugs": [],
            "post_mortems": [],
        }

        agent_lower = agent_name.lower()

        if agent_lower in ("betty", "code_quality"):
            context["famous_bugs"] = self.get_relevant_bugs(query, top_k=3)
            context["post_mortems"] = self.get_relevant_postmortems(query, top_k=2)

        elif agent_lower in ("diana", "security"):
            context["famous_bugs"] = self.get_relevant_bugs(query, top_k=5)

        elif agent_lower in ("marcus", "architecture"):
            context["post_mortems"] = self.get_relevant_postmortems(query, top_k=5)

        elif agent_lower in ("quinn", "security_audit"):
            context["famous_bugs"] = self.get_relevant_bugs(query, top_k=3)
            context["post_mortems"] = self.get_relevant_postmortems(query, top_k=3)

        else:
            # Default: provide some context from both
            context["famous_bugs"] = self.get_relevant_bugs(query, top_k=2)
            context["post_mortems"] = self.get_relevant_postmortems(query, top_k=2)

        context["context_available"] = bool(
            context["famous_bugs"] or context["post_mortems"]
        )

        return context

    def get_relevant_bugs(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query famous bugs collection for relevant entries."""
        try:
            results = self.chroma_service.query(
                collection_name="famous_bugs",
                query_text=query,
                n_results=top_k,
            )
            return self._format_chroma_results(results)
        except Exception:
            return []

    def get_relevant_postmortems(
        self, query: str, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Query post-mortems collection for relevant entries."""
        try:
            results = self.chroma_service.query(
                collection_name="post_mortems",
                query_text=query,
                n_results=top_k,
            )
            return self._format_chroma_results(results)
        except Exception:
            return []

    def _format_chroma_results(self, results: Any) -> List[Dict[str, Any]]:
        """Format ChromaDB query results into a consistent structure."""
        if not results:
            return []

        formatted = []
        # ChromaDB returns results in a specific structure
        documents = results.get("documents", [[]])[0] if isinstance(results, dict) else []
        metadatas = results.get("metadatas", [[]])[0] if isinstance(results, dict) else []
        distances = results.get("distances", [[]])[0] if isinstance(results, dict) else []

        for i, doc in enumerate(documents):
            entry = {
                "content": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "relevance_score": 1.0 - (distances[i] if i < len(distances) else 0),
            }
            formatted.append(entry)

        return formatted
