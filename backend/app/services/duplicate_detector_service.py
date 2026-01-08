# backend/app/services/duplicate_detector_service.py
"""
Duplicate Detector Service - Week 118

Uses ChromaDB for semantic similarity search to detect
duplicate or similar feature requests.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.portal_enhancements import (
    FeatureDuplicate,
    DuplicateStatus,
)

# ChromaDB import (optional - graceful fallback)
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class DuplicateDetectorService:
    """Service for detecting duplicate feature requests."""

    # Similarity thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.70
    MIN_SIMILARITY_THRESHOLD = 0.60

    # ChromaDB collection name
    COLLECTION_NAME = "feature_requests"

    def __init__(self, db: AsyncSession):
        self.db = db
        self._chroma_client = None
        self._collection = None

    def _get_chroma_client(self):
        """Get or create ChromaDB client."""
        if not CHROMADB_AVAILABLE:
            return None

        if self._chroma_client is None:
            try:
                self._chroma_client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory="./chromadb_data",
                    anonymized_telemetry=False,
                ))
            except Exception:
                # Fallback to ephemeral client
                self._chroma_client = chromadb.Client()

        return self._chroma_client

    def _get_collection(self):
        """Get or create ChromaDB collection."""
        if self._collection is not None:
            return self._collection

        client = self._get_chroma_client()
        if client is None:
            return None

        try:
            self._collection = client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Feature requests for duplicate detection"}
            )
            return self._collection
        except Exception:
            return None

    async def index_feature(
        self,
        feature_id: int,
        title: str,
        description: str,
        project_id: Optional[int] = None,
    ) -> bool:
        """Index a feature request for similarity search."""
        collection = self._get_collection()
        if collection is None:
            return False

        try:
            # Combine title and description for embedding
            text = f"{title}\n\n{description}"

            collection.upsert(
                ids=[str(feature_id)],
                documents=[text],
                metadatas=[{
                    "feature_id": feature_id,
                    "title": title[:200],  # Truncate for metadata
                    "project_id": project_id or 0,
                    "indexed_at": datetime.utcnow().isoformat(),
                }]
            )
            return True
        except Exception:
            return False

    async def find_similar(
        self,
        feature_id: int,
        title: str,
        description: str,
        project_id: Optional[int] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find similar feature requests."""
        collection = self._get_collection()

        if collection is None:
            # Fallback to keyword-based matching
            return await self._keyword_similarity(
                feature_id, title, description, project_id, limit
            )

        try:
            # Combine for query
            query_text = f"{title}\n\n{description}"

            # Query ChromaDB
            results = collection.query(
                query_texts=[query_text],
                n_results=limit + 1,  # +1 to filter self
                where={"project_id": project_id} if project_id else None,
            )

            # Process results
            similar = []
            for i, doc_id in enumerate(results['ids'][0]):
                if int(doc_id) == feature_id:
                    continue  # Skip self

                # ChromaDB returns distances, convert to similarity
                distance = results['distances'][0][i] if results.get('distances') else 0
                similarity = max(0, 1 - distance)  # Convert distance to similarity

                if similarity >= self.MIN_SIMILARITY_THRESHOLD:
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    similar.append({
                        "feature_id": int(doc_id),
                        "title": metadata.get("title", ""),
                        "similarity_score": round(similarity, 3),
                        "confidence": self._get_confidence_level(similarity),
                        "detection_method": "chromadb",
                    })

            return similar[:limit]

        except Exception as e:
            # Fallback on error
            return await self._keyword_similarity(
                feature_id, title, description, project_id, limit
            )

    async def _keyword_similarity(
        self,
        feature_id: int,
        title: str,
        description: str,
        project_id: Optional[int],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Fallback keyword-based similarity when ChromaDB unavailable."""
        # Extract keywords
        text = f"{title} {description}".lower()
        # Remove common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'to', 'of', 'and', 'in', 'that', 'have', 'for', 'on', 'with',
                      'as', 'at', 'this', 'by', 'from', 'or', 'which', 'but', 'not'}
        words = set(re.findall(r'\b\w{3,}\b', text)) - stop_words

        # This would need to query existing features from database
        # For now, return empty (needs feature table access)
        return []

    def _get_confidence_level(self, similarity: float) -> str:
        """Get confidence level from similarity score."""
        if similarity >= self.HIGH_CONFIDENCE_THRESHOLD:
            return "high"
        elif similarity >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return "medium"
        else:
            return "low"

    async def check_for_duplicates(
        self,
        feature_id: int,
        title: str,
        description: str,
        project_id: Optional[int] = None,
        auto_record: bool = True,
    ) -> Dict[str, Any]:
        """Check for duplicates and optionally record them."""
        similar = await self.find_similar(
            feature_id=feature_id,
            title=title,
            description=description,
            project_id=project_id,
            limit=10,
        )

        # Filter by threshold
        duplicates = [s for s in similar if s["similarity_score"] >= self.MEDIUM_CONFIDENCE_THRESHOLD]

        # Record duplicates in database if requested
        recorded_ids = []
        if auto_record and duplicates:
            for dup in duplicates:
                record = await self._record_duplicate(
                    source_feature_id=feature_id,
                    source_title=title,
                    source_description=description,
                    duplicate_feature_id=dup["feature_id"],
                    duplicate_title=dup.get("title", ""),
                    similarity_score=dup["similarity_score"],
                    detection_method=dup.get("detection_method", "chromadb"),
                    project_id=project_id,
                )
                if record:
                    recorded_ids.append(str(record.id))

        return {
            "feature_id": feature_id,
            "duplicates_found": len(duplicates),
            "high_confidence": sum(1 for d in duplicates if d["confidence"] == "high"),
            "medium_confidence": sum(1 for d in duplicates if d["confidence"] == "medium"),
            "duplicates": duplicates,
            "recorded_ids": recorded_ids,
            "recommendation": self._get_recommendation(duplicates),
        }

    def _get_recommendation(self, duplicates: List[Dict]) -> str:
        """Get recommendation based on duplicates found."""
        if not duplicates:
            return "No duplicates detected. Feature is unique."

        high_conf = [d for d in duplicates if d["confidence"] == "high"]
        if high_conf:
            return f"High confidence duplicate detected! Consider merging with feature #{high_conf[0]['feature_id']}."

        return f"Potential duplicates found ({len(duplicates)}). Please review before proceeding."

    async def _record_duplicate(
        self,
        source_feature_id: int,
        source_title: str,
        source_description: str,
        duplicate_feature_id: int,
        duplicate_title: str,
        similarity_score: float,
        detection_method: str,
        project_id: Optional[int] = None,
    ) -> Optional[FeatureDuplicate]:
        """Record a detected duplicate in the database."""
        # Check if already recorded
        result = await self.db.execute(
            select(FeatureDuplicate).where(
                and_(
                    FeatureDuplicate.source_feature_id == source_feature_id,
                    FeatureDuplicate.duplicate_feature_id == duplicate_feature_id,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        # Create new record
        duplicate = FeatureDuplicate(
            id=uuid4(),
            project_id=project_id,
            source_feature_id=source_feature_id,
            source_title=source_title,
            source_description=source_description[:500] if source_description else None,
            duplicate_feature_id=duplicate_feature_id,
            duplicate_title=duplicate_title,
            similarity_score=similarity_score,
            detection_method=detection_method,
            status=DuplicateStatus.PENDING.value,
        )

        self.db.add(duplicate)
        await self.db.commit()
        await self.db.refresh(duplicate)
        return duplicate

    async def get_pending_duplicates(
        self,
        project_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get pending duplicate detections for review."""
        query = select(FeatureDuplicate).where(
            FeatureDuplicate.status == DuplicateStatus.PENDING.value
        ).order_by(FeatureDuplicate.similarity_score.desc()).limit(limit)

        if project_id:
            query = query.where(FeatureDuplicate.project_id == project_id)

        result = await self.db.execute(query)
        duplicates = result.scalars().all()

        return [
            {
                "id": str(d.id),
                "source_feature_id": d.source_feature_id,
                "source_title": d.source_title,
                "duplicate_feature_id": d.duplicate_feature_id,
                "duplicate_title": d.duplicate_title,
                "similarity_score": d.similarity_score,
                "confidence": self._get_confidence_level(d.similarity_score),
                "detection_method": d.detection_method,
                "created_at": d.created_at.isoformat(),
            }
            for d in duplicates
        ]

    async def resolve_duplicate(
        self,
        duplicate_id: UUID,
        resolution: str,  # confirmed, rejected, merged
        resolved_by: str,
        merge_target_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Resolve a duplicate detection."""
        result = await self.db.execute(
            select(FeatureDuplicate).where(FeatureDuplicate.id == duplicate_id)
        )
        duplicate = result.scalar_one_or_none()

        if not duplicate:
            return {"success": False, "error": "Duplicate record not found"}

        duplicate.status = resolution
        duplicate.resolved_by = resolved_by
        duplicate.resolved_at = datetime.utcnow()
        if merge_target_id:
            duplicate.merge_target_id = merge_target_id

        await self.db.commit()

        return {
            "success": True,
            "duplicate_id": str(duplicate.id),
            "resolution": resolution,
            "resolved_by": resolved_by,
        }

    async def merge_features(
        self,
        source_feature_id: int,
        target_feature_id: int,
        resolved_by: str,
    ) -> Dict[str, Any]:
        """Merge duplicate features (mark source as merged into target)."""
        # Find related duplicate records
        result = await self.db.execute(
            select(FeatureDuplicate).where(
                or_(
                    and_(
                        FeatureDuplicate.source_feature_id == source_feature_id,
                        FeatureDuplicate.duplicate_feature_id == target_feature_id,
                    ),
                    and_(
                        FeatureDuplicate.source_feature_id == target_feature_id,
                        FeatureDuplicate.duplicate_feature_id == source_feature_id,
                    ),
                )
            )
        )
        duplicates = result.scalars().all()

        for dup in duplicates:
            dup.status = DuplicateStatus.MERGED.value
            dup.resolved_by = resolved_by
            dup.resolved_at = datetime.utcnow()
            dup.merge_target_id = target_feature_id

        await self.db.commit()

        return {
            "success": True,
            "source_feature_id": source_feature_id,
            "target_feature_id": target_feature_id,
            "records_updated": len(duplicates),
            "message": f"Feature #{source_feature_id} merged into #{target_feature_id}",
        }

    async def get_statistics(
        self,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get duplicate detection statistics."""
        base_query = select(FeatureDuplicate)
        if project_id:
            base_query = base_query.where(FeatureDuplicate.project_id == project_id)

        result = await self.db.execute(base_query)
        all_duplicates = result.scalars().all()

        # Calculate stats
        by_status = {}
        for dup in all_duplicates:
            by_status[dup.status] = by_status.get(dup.status, 0) + 1

        avg_similarity = sum(d.similarity_score for d in all_duplicates) / len(all_duplicates) if all_duplicates else 0

        return {
            "total_detected": len(all_duplicates),
            "by_status": by_status,
            "pending_review": by_status.get(DuplicateStatus.PENDING.value, 0),
            "confirmed": by_status.get(DuplicateStatus.CONFIRMED.value, 0),
            "merged": by_status.get(DuplicateStatus.MERGED.value, 0),
            "rejected": by_status.get(DuplicateStatus.REJECTED.value, 0),
            "average_similarity": round(avg_similarity, 3),
        }
