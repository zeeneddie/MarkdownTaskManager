"""
Thinking Pattern Store - ChromaDB integration for pattern analysis

Week 61: Enhanced Observability Integration

Stores thinking patterns in vector database for:
- Pattern similarity search
- Reasoning quality analysis
- LLM behavior clustering
- Knowledge retrieval
"""

import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# ChromaDB is optional - gracefully handle missing dependency
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed. Pattern storage disabled.")


class ThinkingPatternStore:
    """
    Vector store for thinking pattern analysis.

    Uses ChromaDB to store and query thinking blocks
    for pattern analysis and similarity search.

    If ChromaDB is not installed, operations are no-ops.
    """

    COLLECTION_NAME = "thinking_patterns"

    def __init__(
        self,
        persist_directory: str = "./chromadb_data",
        collection_name: str = None
    ):
        """
        Initialize pattern store.

        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Override collection name
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name or self.COLLECTION_NAME
        self._client = None
        self._collection = None

        if CHROMADB_AVAILABLE:
            self._init_chromadb()

    def _init_chromadb(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "CCTrace thinking patterns"}
            )
            logger.info(f"ChromaDB collection '{self.collection_name}' initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self._client = None
            self._collection = None

    @property
    def is_available(self) -> bool:
        """Check if pattern store is available."""
        return self._collection is not None

    def store_thinking_pattern(
        self,
        content: str,
        block_type: str,
        provider: str,
        model: str,
        session_id: Optional[str] = None,
        action_id: Optional[int] = None,
        token_count: int = 0,
        extra_metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Store a thinking pattern.

        Args:
            content: Thinking block content
            block_type: Type (thinking, reasoning, cot)
            provider: LLM provider
            model: Model name
            session_id: Session identifier
            action_id: Agent action ID
            token_count: Token count
            extra_metadata: Additional metadata

        Returns:
            Pattern ID if stored, None if not available
        """
        if not self.is_available:
            return None

        # Generate ID from content hash
        pattern_id = self._generate_id(content)

        metadata = {
            "block_type": block_type,
            "provider": provider,
            "model": model,
            "session_id": session_id or "",
            "action_id": action_id or 0,
            "token_count": token_count,
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "content_length": len(content),
        }

        if extra_metadata:
            # Flatten extra metadata (ChromaDB requires flat structure)
            for key, value in extra_metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[f"extra_{key}"] = value

        try:
            self._collection.upsert(
                ids=[pattern_id],
                documents=[content],
                metadatas=[metadata]
            )
            return pattern_id
        except Exception as e:
            logger.error(f"Failed to store pattern: {e}")
            return None

    def find_similar_patterns(
        self,
        query: str,
        n_results: int = 5,
        provider: Optional[str] = None,
        block_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar thinking patterns.

        Args:
            query: Search query (thinking content)
            n_results: Number of results to return
            provider: Filter by provider
            block_type: Filter by block type

        Returns:
            List of similar patterns with metadata
        """
        if not self.is_available:
            return []

        where_filter = {}
        if provider:
            where_filter["provider"] = provider
        if block_type:
            where_filter["block_type"] = block_type

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )

            patterns = []
            if results and results["ids"] and results["ids"][0]:
                for i, pattern_id in enumerate(results["ids"][0]):
                    patterns.append({
                        "id": pattern_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "similarity": 1 - results["distances"][0][i] if results["distances"] else 0,
                    })

            return patterns
        except Exception as e:
            logger.error(f"Failed to search patterns: {e}")
            return []

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored patterns.

        Returns:
            Dict with pattern counts and distributions
        """
        if not self.is_available:
            return {"available": False}

        try:
            count = self._collection.count()

            # Get sample for distribution analysis
            if count > 0:
                sample = self._collection.get(
                    limit=min(count, 1000),
                    include=["metadatas"]
                )

                providers = {}
                block_types = {}
                models = {}

                for metadata in sample["metadatas"]:
                    provider = metadata.get("provider", "unknown")
                    providers[provider] = providers.get(provider, 0) + 1

                    block_type = metadata.get("block_type", "unknown")
                    block_types[block_type] = block_types.get(block_type, 0) + 1

                    model = metadata.get("model", "unknown")
                    models[model] = models.get(model, 0) + 1

                return {
                    "available": True,
                    "total_patterns": count,
                    "by_provider": providers,
                    "by_block_type": block_types,
                    "by_model": models,
                }

            return {
                "available": True,
                "total_patterns": 0,
                "by_provider": {},
                "by_block_type": {},
                "by_model": {},
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"available": False, "error": str(e)}

    def delete_pattern(self, pattern_id: str) -> bool:
        """
        Delete a pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            True if deleted, False otherwise
        """
        if not self.is_available:
            return False

        try:
            self._collection.delete(ids=[pattern_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete pattern: {e}")
            return False

    def clear_all_patterns(self) -> bool:
        """
        Clear all patterns (use with caution).

        Returns:
            True if cleared, False otherwise
        """
        if not self.is_available:
            return False

        try:
            # Delete and recreate collection
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"description": "CCTrace thinking patterns"}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to clear patterns: {e}")
            return False

    def _generate_id(self, content: str) -> str:
        """Generate unique ID from content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


# Singleton instance for convenience
_pattern_store: Optional[ThinkingPatternStore] = None


def get_pattern_store(
    persist_directory: str = "./chromadb_data"
) -> ThinkingPatternStore:
    """
    Get or create pattern store singleton.

    Args:
        persist_directory: ChromaDB persistence directory

    Returns:
        ThinkingPatternStore instance
    """
    global _pattern_store
    if _pattern_store is None:
        _pattern_store = ThinkingPatternStore(persist_directory)
    return _pattern_store
