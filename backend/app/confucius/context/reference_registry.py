"""
Reference Registry for Context Engineering.

Manages the loading, caching, and retrieval of reference documents
from the filesystem.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import hashlib

from .reference_selector import Reference, ReferenceCategory, DEFAULT_REFERENCES

logger = logging.getLogger(__name__)


@dataclass
class CachedReference:
    """Cached reference content with metadata."""
    reference: Reference
    content: str
    loaded_at: datetime
    content_hash: str
    word_count: int
    line_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **self.reference.to_dict(),
            "content_hash": self.content_hash,
            "word_count": self.word_count,
            "line_count": self.line_count,
            "loaded_at": self.loaded_at.isoformat(),
        }


class ReferenceRegistry:
    """
    Registry for managing reference documents.

    Handles loading from filesystem, caching, and content retrieval.

    Example:
    ```python
    registry = ReferenceRegistry(base_path="/project/.claude")
    registry.load_all()

    content = registry.get_content("asp-vbscript")
    stats = registry.get_statistics()
    ```
    """

    def __init__(
        self,
        base_path: Optional[str] = None,
        auto_load: bool = True,
    ):
        """
        Initialize registry.

        Args:
            base_path: Base path for reference files (defaults to .claude/)
            auto_load: Whether to auto-load references on init
        """
        self._base_path = Path(base_path) if base_path else Path(".claude")
        self._cache: Dict[str, CachedReference] = {}
        self._references: Dict[str, Reference] = {}

        # Initialize with default references
        for ref in DEFAULT_REFERENCES:
            self._references[ref.id] = ref

        if auto_load:
            self.load_all()

    def load_all(self) -> Dict[str, bool]:
        """
        Load all registered references from filesystem.

        Returns:
            Dictionary of reference_id -> success status
        """
        results = {}
        for ref_id, ref in self._references.items():
            results[ref_id] = self.load_reference(ref_id)
        return results

    def load_reference(self, reference_id: str) -> bool:
        """
        Load a single reference from filesystem.

        Args:
            reference_id: ID of reference to load

        Returns:
            True if loaded successfully
        """
        if reference_id not in self._references:
            logger.warning(f"Unknown reference: {reference_id}")
            return False

        ref = self._references[reference_id]
        file_path = self._base_path / ref.path.lstrip(".claude/")

        try:
            if not file_path.exists():
                logger.debug(f"Reference file not found: {file_path}")
                return False

            content = file_path.read_text(encoding="utf-8")
            content_hash = hashlib.md5(content.encode()).hexdigest()

            self._cache[reference_id] = CachedReference(
                reference=ref,
                content=content,
                loaded_at=datetime.now(timezone.utc),
                content_hash=content_hash,
                word_count=len(content.split()),
                line_count=len(content.splitlines()),
            )

            # Update token estimate based on actual content
            ref.token_estimate = len(content.split()) * 1.3  # Rough estimate

            logger.info(f"Loaded reference: {ref.name} ({len(content)} chars)")
            return True

        except Exception as e:
            logger.error(f"Failed to load reference {reference_id}: {e}")
            return False

    def get_content(self, reference_id: str) -> Optional[str]:
        """
        Get content of a reference.

        Args:
            reference_id: ID of reference

        Returns:
            Reference content or None if not loaded
        """
        cached = self._cache.get(reference_id)
        return cached.content if cached else None

    def get_cached(self, reference_id: str) -> Optional[CachedReference]:
        """Get cached reference with metadata."""
        return self._cache.get(reference_id)

    def get_multiple_content(
        self,
        reference_ids: List[str],
    ) -> Dict[str, str]:
        """
        Get content for multiple references.

        Args:
            reference_ids: List of reference IDs

        Returns:
            Dictionary of reference_id -> content
        """
        result = {}
        for ref_id in reference_ids:
            content = self.get_content(ref_id)
            if content:
                result[ref_id] = content
        return result

    def is_loaded(self, reference_id: str) -> bool:
        """Check if a reference is loaded."""
        return reference_id in self._cache

    def reload_reference(self, reference_id: str) -> bool:
        """
        Reload a reference from filesystem.

        Args:
            reference_id: ID of reference to reload

        Returns:
            True if reloaded successfully
        """
        if reference_id in self._cache:
            del self._cache[reference_id]
        return self.load_reference(reference_id)

    def reload_all(self) -> Dict[str, bool]:
        """Reload all references."""
        self._cache.clear()
        return self.load_all()

    def register_reference(self, reference: Reference) -> None:
        """
        Register a new reference.

        Args:
            reference: Reference to register
        """
        self._references[reference.id] = reference
        logger.info(f"Registered reference: {reference.id}")

    def unregister_reference(self, reference_id: str) -> bool:
        """
        Unregister a reference.

        Args:
            reference_id: ID of reference to remove

        Returns:
            True if removed
        """
        if reference_id in self._references:
            del self._references[reference_id]
            if reference_id in self._cache:
                del self._cache[reference_id]
            return True
        return False

    def list_references(self) -> List[Reference]:
        """List all registered references."""
        return list(self._references.values())

    def list_loaded(self) -> List[str]:
        """List IDs of loaded references."""
        return list(self._cache.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry stats
        """
        total_words = sum(c.word_count for c in self._cache.values())
        total_lines = sum(c.line_count for c in self._cache.values())
        total_tokens = sum(c.reference.token_estimate for c in self._cache.values())

        by_category: Dict[str, int] = {}
        for ref in self._references.values():
            cat = ref.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total_registered": len(self._references),
            "total_loaded": len(self._cache),
            "total_words": total_words,
            "total_lines": total_lines,
            "estimated_tokens": int(total_tokens),
            "by_category": by_category,
            "base_path": str(self._base_path),
        }

    def get_reference_info(self, reference_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed info about a reference.

        Args:
            reference_id: ID of reference

        Returns:
            Reference info or None
        """
        if reference_id not in self._references:
            return None

        ref = self._references[reference_id]
        cached = self._cache.get(reference_id)

        info = ref.to_dict()
        info["is_loaded"] = cached is not None
        if cached:
            info["word_count"] = cached.word_count
            info["line_count"] = cached.line_count
            info["content_hash"] = cached.content_hash
            info["loaded_at"] = cached.loaded_at.isoformat()

        return info


def create_reference_registry(
    base_path: Optional[str] = None,
    auto_load: bool = True,
) -> ReferenceRegistry:
    """
    Factory function to create reference registry.

    Args:
        base_path: Base path for reference files
        auto_load: Whether to auto-load on init

    Returns:
        Configured ReferenceRegistry
    """
    return ReferenceRegistry(base_path=base_path, auto_load=auto_load)
