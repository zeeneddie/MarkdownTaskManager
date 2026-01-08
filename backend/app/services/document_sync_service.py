"""
Document Sync Service

Week 55: Human-in-the-Loop Council
Bi-directional synchronization between MD files and database.

Features:
- MD → DB sync (read file changes)
- DB → MD sync (write approved documents)
- SHA256 hash-based change detection
- Version history tracking
- Git commit integration (optional)
"""

import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.council_human_review import (
    DocumentVersion,
    CouncilHumanSession,
    CouncilConsensus,
    DocumentType,
    SessionStatus
)


class DocumentSyncService:
    """
    Bi-directional sync service for MD files and database.

    Responsibilities:
    - Detect file changes via SHA256 hash
    - Create new versions in database when files change
    - Write approved council documents to filesystem
    - Optionally create Git commits
    """

    def __init__(self, db: AsyncSession, base_path: Optional[str] = None):
        """
        Initialize the sync service.

        Args:
            db: SQLAlchemy async database session
            base_path: Base path for project files (defaults to current directory)
        """
        self.db = db
        self.base_path = Path(base_path) if base_path else Path.cwd()

    # =========================================================================
    # Hash Utilities
    # =========================================================================

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    async def has_file_changed(self, document_path: str, project_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if file has changed since last sync.

        Args:
            document_path: Relative path to document
            project_id: Optional project ID

        Returns:
            Tuple of (has_changed, current_hash)
        """
        full_path = self.base_path / document_path

        if not full_path.exists():
            return False, None

        current_content = full_path.read_text(encoding='utf-8')
        current_hash = self.compute_hash(current_content)

        # Get latest version from database
        stmt = select(DocumentVersion).where(
            DocumentVersion.document_path == document_path,
            DocumentVersion.project_id == project_id
        ).order_by(desc(DocumentVersion.version)).limit(1)

        result = await self.db.execute(stmt)
        latest_version = result.scalars().first()

        if not latest_version:
            return True, current_hash  # New file

        return latest_version.content_hash != current_hash, current_hash

    # =========================================================================
    # MD → DB Sync
    # =========================================================================

    async def sync_file_to_db(
        self,
        document_path: str,
        document_type: str,
        project_id: Optional[int] = None,
        created_by: str = "sync",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[DocumentVersion]:
        """
        Sync a file from filesystem to database.

        Args:
            document_path: Relative path to document
            document_type: Type of document (onboarding, architecture, etc.)
            project_id: Optional project ID
            created_by: Who created this version (sync, human, council)
            metadata: Additional metadata

        Returns:
            New DocumentVersion if created, None if unchanged
        """
        full_path = self.base_path / document_path

        if not full_path.exists():
            return None

        has_changed, current_hash = await self.has_file_changed(document_path, project_id)

        if not has_changed:
            return None  # No changes

        # Read content
        content = full_path.read_text(encoding='utf-8')

        # Get next version number
        stmt = select(DocumentVersion).where(
            DocumentVersion.document_path == document_path,
            DocumentVersion.project_id == project_id
        ).order_by(desc(DocumentVersion.version)).limit(1)

        result = await self.db.execute(stmt)
        latest_version = result.scalars().first()

        next_version = (latest_version.version + 1) if latest_version else 1

        # Create new version
        new_version = DocumentVersion(
            project_id=project_id,
            document_path=document_path,
            document_type=document_type,
            version=next_version,
            content=content,
            content_hash=current_hash,
            created_by=created_by,
            extra_metadata=metadata or {}
        )

        self.db.add(new_version)
        await self.db.commit()
        await self.db.refresh(new_version)

        return new_version

    async def sync_directory_to_db(
        self,
        directory_path: str,
        document_type: str,
        project_id: Optional[int] = None,
        file_pattern: str = "*.md"
    ) -> List[DocumentVersion]:
        """
        Sync all matching files in a directory to database.

        Args:
            directory_path: Relative path to directory
            document_type: Type of documents
            project_id: Optional project ID
            file_pattern: Glob pattern for files (default: *.md)

        Returns:
            List of newly created DocumentVersions
        """
        full_path = self.base_path / directory_path

        if not full_path.exists() or not full_path.is_dir():
            return []

        new_versions = []
        for file_path in full_path.glob(file_pattern):
            relative_path = str(file_path.relative_to(self.base_path))
            version = await self.sync_file_to_db(
                document_path=relative_path,
                document_type=document_type,
                project_id=project_id,
                created_by="sync"
            )
            if version:
                new_versions.append(version)

        return new_versions

    # =========================================================================
    # DB → MD Sync
    # =========================================================================

    def write_document_to_file(
        self,
        document_version: DocumentVersion,
        create_backup: bool = True
    ) -> Path:
        """
        Write a document version to filesystem.

        Args:
            document_version: The document version to write
            create_backup: Whether to create a backup of existing file

        Returns:
            Path to the written file
        """
        full_path = self.base_path / document_version.document_path

        # Create directory if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if file exists
        if create_backup and full_path.exists():
            backup_path = full_path.with_suffix(f".v{document_version.version - 1}.backup.md")
            existing_content = full_path.read_text(encoding='utf-8')
            backup_path.write_text(existing_content, encoding='utf-8')

        # Write new content
        full_path.write_text(document_version.content, encoding='utf-8')

        return full_path

    async def write_council_consensus_to_file(
        self,
        session_id: UUID,
        output_path: Optional[str] = None
    ) -> Optional[Path]:
        """
        Write approved council consensus to filesystem.

        Args:
            session_id: Council session ID
            output_path: Optional custom output path

        Returns:
            Path to written file, or None if no approved consensus
        """
        # Get the session
        stmt = select(CouncilHumanSession).where(
            CouncilHumanSession.id == session_id
        )
        result = await self.db.execute(stmt)
        session = result.scalars().first()

        if not session:
            return None

        # Get the latest approved consensus
        stmt = select(CouncilConsensus).where(
            CouncilConsensus.session_id == session_id,
            CouncilConsensus.is_approved == True
        ).order_by(desc(CouncilConsensus.version)).limit(1)

        result = await self.db.execute(stmt)
        consensus = result.scalars().first()

        if not consensus:
            return None

        # Determine output path
        if output_path:
            document_path = output_path
        else:
            # Generate default path based on document type
            type_paths = {
                DocumentType.ONBOARDING.value: "docs/ONBOARDING.md",
                DocumentType.ARCHITECTURE.value: "docs/ARCHITECTURE.md",
                DocumentType.ADR.value: f"docs/adr/ADR-{datetime.utcnow().strftime('%Y%m%d')}.md",
                DocumentType.SPECIFICATION.value: "docs/SPECIFICATION.md",
                DocumentType.README.value: "README.md",
                DocumentType.API_DOCS.value: "docs/API.md",
                DocumentType.OTHER.value: f"docs/{session.document_name or 'document'}.md",
            }
            document_path = type_paths.get(
                session.document_type,
                f"docs/{session.document_type}.md"
            )

        # Create document version
        await self.has_file_changed(document_path, session.project_id)

        # Get next version
        stmt = select(DocumentVersion).where(
            DocumentVersion.document_path == document_path,
            DocumentVersion.project_id == session.project_id
        ).order_by(desc(DocumentVersion.version)).limit(1)

        result = await self.db.execute(stmt)
        latest = result.scalars().first()

        next_version = (latest.version + 1) if latest else 1

        # Create version record
        doc_version = DocumentVersion(
            project_id=session.project_id,
            document_path=document_path,
            document_type=session.document_type,
            version=next_version,
            content=consensus.consensus_content,
            content_hash=self.compute_hash(consensus.consensus_content),
            council_session_id=session_id,
            created_by="council",
            extra_metadata={
                "consensus_version": consensus.version,
                "human_additions": consensus.human_additions is not None,
                "approved_at": consensus.approved_at.isoformat() if consensus.approved_at else None
            }
        )

        self.db.add(doc_version)
        await self.db.commit()

        # Write to filesystem
        return self.write_document_to_file(doc_version, create_backup=True)

    # =========================================================================
    # Git Integration
    # =========================================================================

    def git_commit_document(
        self,
        document_path: str,
        message: Optional[str] = None,
        author: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a Git commit for a document.

        Args:
            document_path: Path to document (relative to base_path)
            message: Commit message (auto-generated if not provided)
            author: Git author string (e.g., "Name <email>")

        Returns:
            Commit hash if successful, None otherwise
        """
        full_path = self.base_path / document_path

        if not full_path.exists():
            return None

        try:
            # Add file to staging
            subprocess.run(
                ["git", "add", str(full_path)],
                cwd=str(self.base_path),
                check=True,
                capture_output=True
            )

            # Generate commit message
            if not message:
                message = f"docs: Update {document_path} via Council"

            # Build commit command
            commit_cmd = ["git", "commit", "-m", message]
            if author:
                commit_cmd.extend(["--author", author])

            # Create commit
            result = subprocess.run(
                commit_cmd,
                cwd=str(self.base_path),
                check=True,
                capture_output=True,
                text=True
            )

            # Get commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.base_path),
                check=True,
                capture_output=True,
                text=True
            )

            return hash_result.stdout.strip()

        except subprocess.CalledProcessError:
            return None

    # =========================================================================
    # Query Methods
    # =========================================================================

    async def get_document_history(
        self,
        document_path: str,
        project_id: Optional[int] = None,
        limit: int = 10
    ) -> List[DocumentVersion]:
        """Get version history for a document."""
        stmt = select(DocumentVersion).where(
            DocumentVersion.document_path == document_path
        )

        if project_id is not None:
            stmt = stmt.where(DocumentVersion.project_id == project_id)

        stmt = stmt.order_by(desc(DocumentVersion.version)).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_version(
        self,
        document_path: str,
        project_id: Optional[int] = None
    ) -> Optional[DocumentVersion]:
        """Get the latest version of a document."""
        stmt = select(DocumentVersion).where(
            DocumentVersion.document_path == document_path
        )

        if project_id is not None:
            stmt = stmt.where(DocumentVersion.project_id == project_id)

        stmt = stmt.order_by(desc(DocumentVersion.version)).limit(1)

        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_documents_by_type(
        self,
        document_type: str,
        project_id: Optional[int] = None
    ) -> List[DocumentVersion]:
        """Get latest versions of all documents of a type."""
        # Create subquery for max version per document path
        subq = select(
            DocumentVersion.document_path,
            func.max(DocumentVersion.version).label('max_version')
        ).where(
            DocumentVersion.document_type == document_type
        )

        if project_id is not None:
            subq = subq.where(DocumentVersion.project_id == project_id)

        subq = subq.group_by(DocumentVersion.document_path).subquery()

        # Main query joins with subquery
        stmt = select(DocumentVersion).join(
            subq,
            (DocumentVersion.document_path == subq.c.document_path) &
            (DocumentVersion.version == subq.c.max_version)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def compare_versions(
        self,
        document_path: str,
        version1: int,
        version2: int,
        project_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Compare two versions of a document.

        Returns a dict with both contents for diff display.
        """
        stmt1 = select(DocumentVersion).where(
            DocumentVersion.document_path == document_path,
            DocumentVersion.version == version1,
            DocumentVersion.project_id == project_id
        )
        result1 = await self.db.execute(stmt1)
        v1 = result1.scalars().first()

        stmt2 = select(DocumentVersion).where(
            DocumentVersion.document_path == document_path,
            DocumentVersion.version == version2,
            DocumentVersion.project_id == project_id
        )
        result2 = await self.db.execute(stmt2)
        v2 = result2.scalars().first()

        if not v1 or not v2:
            return None

        return {
            "version1": {
                "version": v1.version,
                "content": v1.content,
                "created_at": v1.created_at.isoformat(),
                "created_by": v1.created_by
            },
            "version2": {
                "version": v2.version,
                "content": v2.content,
                "created_at": v2.created_at.isoformat(),
                "created_by": v2.created_by
            }
        }

    # =========================================================================
    # Rollback
    # =========================================================================

    async def rollback_to_version(
        self,
        document_path: str,
        target_version: int,
        project_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Optional[DocumentVersion]:
        """
        Rollback a document to a previous version.

        Creates a new version with the content from the target version.
        """
        # Get target version
        stmt = select(DocumentVersion).where(
            DocumentVersion.document_path == document_path,
            DocumentVersion.version == target_version,
            DocumentVersion.project_id == project_id
        )
        result = await self.db.execute(stmt)
        target = result.scalars().first()

        if not target:
            return None

        # Get current latest version
        latest = await self.get_latest_version(document_path, project_id)
        next_version = (latest.version + 1) if latest else 1

        # Create new version with old content
        rollback_version = DocumentVersion(
            project_id=project_id,
            document_path=document_path,
            document_type=target.document_type,
            version=next_version,
            content=target.content,
            content_hash=target.content_hash,
            created_by="rollback",
            extra_metadata={
                "rolled_back_from": latest.version if latest else None,
                "rolled_back_to": target_version,
                "reason": reason
            }
        )

        self.db.add(rollback_version)
        await self.db.commit()
        await self.db.refresh(rollback_version)

        # Write to filesystem
        self.write_document_to_file(rollback_version, create_backup=True)

        return rollback_version
