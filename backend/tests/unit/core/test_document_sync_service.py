"""
E2E Tests for Document Sync Service

Week 55 Day 2: End-to-end tests for bi-directional MD ↔ DB synchronization.

Features tested:
- Hash-based change detection
- MD → DB sync (file to database)
- DB → MD sync (database to file)
- Version history tracking
- Git commit integration
- Rollback functionality
- Directory sync
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.document_sync_service import DocumentSyncService
from app.models.council_human_review import (
    DocumentVersion,
    CouncilHumanSession,
    CouncilConsensus,
    DocumentType,
    SessionStatus
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp(prefix="doc_sync_test_")
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_db_session():
    """Mock async database session."""
    mock = MagicMock()
    mock.execute = AsyncMock()
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.add = MagicMock()
    return mock


@pytest.fixture
def sync_service(mock_db_session, temp_project_dir):
    """Create DocumentSyncService with temp directory."""
    return DocumentSyncService(mock_db_session, base_path=str(temp_project_dir))


# ============================================================================
# HASH UTILITY TESTS
# ============================================================================

class TestHashUtilities:
    """Test hash computation and change detection."""

    def test_compute_hash_consistent(self):
        """Test that hash computation is consistent."""
        content = "# Test Document\n\nThis is test content."
        hash1 = DocumentSyncService.compute_hash(content)
        hash2 = DocumentSyncService.compute_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 hex chars

    def test_compute_hash_different_content(self):
        """Test that different content produces different hashes."""
        content1 = "# Document Version 1"
        content2 = "# Document Version 2"

        hash1 = DocumentSyncService.compute_hash(content1)
        hash2 = DocumentSyncService.compute_hash(content2)

        assert hash1 != hash2

    def test_compute_hash_whitespace_sensitive(self):
        """Test that hash is sensitive to whitespace changes."""
        content1 = "Hello World"
        content2 = "Hello  World"  # Extra space

        hash1 = DocumentSyncService.compute_hash(content1)
        hash2 = DocumentSyncService.compute_hash(content2)

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_has_file_changed_new_file(self, sync_service, temp_project_dir, mock_db_session):
        """Test change detection for new file (not in DB)."""
        # Create a new file
        doc_path = "docs/README.md"
        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("# New Document\n\nThis is new.", encoding="utf-8")

        # Mock DB returns no existing version
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute
        has_changed, current_hash = await sync_service.has_file_changed(doc_path)

        # Verify - new file is always "changed"
        assert has_changed is True
        assert current_hash is not None
        assert len(current_hash) == 64

    @pytest.mark.asyncio
    async def test_has_file_changed_unchanged(self, sync_service, temp_project_dir, mock_db_session):
        """Test change detection for unchanged file."""
        # Create file
        doc_path = "docs/README.md"
        content = "# Unchanged Document"
        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        # Mock DB returns version with same hash
        mock_version = MagicMock(spec=DocumentVersion)
        mock_version.content_hash = DocumentSyncService.compute_hash(content)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_version
        mock_db_session.execute.return_value = mock_result

        # Execute
        has_changed, current_hash = await sync_service.has_file_changed(doc_path)

        # Verify
        assert has_changed is False
        assert current_hash == mock_version.content_hash

    @pytest.mark.asyncio
    async def test_has_file_changed_modified(self, sync_service, temp_project_dir, mock_db_session):
        """Test change detection for modified file."""
        # Create file with new content
        doc_path = "docs/README.md"
        new_content = "# Modified Document - Updated"
        old_hash = DocumentSyncService.compute_hash("# Original Document")

        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(new_content, encoding="utf-8")

        # Mock DB returns version with old hash
        mock_version = MagicMock(spec=DocumentVersion)
        mock_version.content_hash = old_hash
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_version
        mock_db_session.execute.return_value = mock_result

        # Execute
        has_changed, current_hash = await sync_service.has_file_changed(doc_path)

        # Verify
        assert has_changed is True
        assert current_hash != old_hash

    @pytest.mark.asyncio
    async def test_has_file_changed_nonexistent_file(self, sync_service, mock_db_session):
        """Test change detection for file that doesn't exist."""
        has_changed, current_hash = await sync_service.has_file_changed("nonexistent.md")

        assert has_changed is False
        assert current_hash is None


# ============================================================================
# MD → DB SYNC TESTS
# ============================================================================

class TestMdToDbSync:
    """Test syncing files from filesystem to database."""

    @pytest.mark.asyncio
    async def test_sync_new_file_to_db(self, sync_service, temp_project_dir, mock_db_session):
        """Test syncing a new file creates version 1."""
        # Create file
        doc_path = "docs/ONBOARDING.md"
        content = "# Developer Onboarding\n\n## Getting Started\n\nWelcome!"
        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        # Mock DB - no existing version
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute
        version = await sync_service.sync_file_to_db(
            document_path=doc_path,
            document_type="onboarding",
            project_id=1,
            created_by="test"
        )

        # Verify
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_awaited_once()
        mock_db_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sync_unchanged_file_returns_none(self, sync_service, temp_project_dir, mock_db_session):
        """Test that syncing unchanged file returns None."""
        # Create file
        doc_path = "docs/README.md"
        content = "# Unchanged"
        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        # Mock DB - existing version with same hash
        mock_version = MagicMock(spec=DocumentVersion)
        mock_version.content_hash = DocumentSyncService.compute_hash(content)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_version
        mock_db_session.execute.return_value = mock_result

        # Execute
        version = await sync_service.sync_file_to_db(
            document_path=doc_path,
            document_type="readme"
        )

        # Verify - no new version created
        assert version is None
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_modified_file_increments_version(self, sync_service, temp_project_dir, mock_db_session):
        """Test that syncing modified file creates new version."""
        # Create file with modified content
        doc_path = "docs/ARCHITECTURE.md"
        new_content = "# Architecture v2\n\nUpdated architecture."
        old_hash = DocumentSyncService.compute_hash("# Architecture v1")

        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(new_content, encoding="utf-8")

        # Mock DB - existing version with old hash
        mock_version = MagicMock(spec=DocumentVersion)
        mock_version.content_hash = old_hash
        mock_version.version = 3

        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            result.scalars.return_value.first.return_value = mock_version
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Execute
        version = await sync_service.sync_file_to_db(
            document_path=doc_path,
            document_type="architecture",
            project_id=1
        )

        # Verify - new version created
        mock_db_session.add.assert_called_once()
        added_version = mock_db_session.add.call_args[0][0]
        assert added_version.version == 4  # Incremented from 3

    @pytest.mark.asyncio
    async def test_sync_file_with_metadata(self, sync_service, temp_project_dir, mock_db_session):
        """Test syncing file with custom metadata."""
        # Create file
        doc_path = "docs/API.md"
        content = "# API Documentation"
        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        # Mock DB
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        metadata = {
            "source": "manual_update",
            "reviewer": "john_doe",
            "tags": ["api", "rest", "v2"]
        }

        # Execute
        await sync_service.sync_file_to_db(
            document_path=doc_path,
            document_type="api_docs",
            metadata=metadata
        )

        # Verify metadata passed
        added_version = mock_db_session.add.call_args[0][0]
        assert added_version.extra_metadata == metadata

    @pytest.mark.asyncio
    async def test_sync_nonexistent_file_returns_none(self, sync_service, mock_db_session):
        """Test that syncing nonexistent file returns None."""
        version = await sync_service.sync_file_to_db(
            document_path="nonexistent/file.md",
            document_type="other"
        )

        assert version is None
        mock_db_session.add.assert_not_called()


# ============================================================================
# DIRECTORY SYNC TESTS
# ============================================================================

class TestDirectorySync:
    """Test syncing entire directories."""

    @pytest.mark.asyncio
    async def test_sync_directory_to_db(self, sync_service, temp_project_dir, mock_db_session):
        """Test syncing all markdown files in a directory."""
        # Create multiple files
        docs_dir = temp_project_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        (docs_dir / "README.md").write_text("# README", encoding="utf-8")
        (docs_dir / "ARCHITECTURE.md").write_text("# Architecture", encoding="utf-8")
        (docs_dir / "API.md").write_text("# API", encoding="utf-8")
        (docs_dir / "notes.txt").write_text("Not a markdown file", encoding="utf-8")

        # Mock DB - no existing versions
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute
        versions = await sync_service.sync_directory_to_db(
            directory_path="docs",
            document_type="documentation",
            project_id=1
        )

        # Verify - should sync 3 .md files (not .txt)
        assert mock_db_session.add.call_count == 3

    @pytest.mark.asyncio
    async def test_sync_directory_custom_pattern(self, sync_service, temp_project_dir, mock_db_session):
        """Test syncing with custom file pattern."""
        # Create files
        docs_dir = temp_project_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        (docs_dir / "spec.txt").write_text("Spec file", encoding="utf-8")
        (docs_dir / "notes.txt").write_text("Notes file", encoding="utf-8")
        (docs_dir / "readme.md").write_text("# README", encoding="utf-8")

        # Mock DB
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute with *.txt pattern
        versions = await sync_service.sync_directory_to_db(
            directory_path="docs",
            document_type="specs",
            file_pattern="*.txt"
        )

        # Verify - should sync 2 .txt files
        assert mock_db_session.add.call_count == 2

    @pytest.mark.asyncio
    async def test_sync_nonexistent_directory(self, sync_service, mock_db_session):
        """Test syncing nonexistent directory returns empty list."""
        versions = await sync_service.sync_directory_to_db(
            directory_path="nonexistent_dir",
            document_type="other"
        )

        assert versions == []
        mock_db_session.add.assert_not_called()


# ============================================================================
# DB → MD SYNC TESTS
# ============================================================================

class TestDbToMdSync:
    """Test syncing from database to filesystem."""

    def test_write_document_to_file(self, sync_service, temp_project_dir):
        """Test writing document version to filesystem."""
        # Setup
        mock_version = MagicMock(spec=DocumentVersion)
        mock_version.document_path = "docs/output.md"
        mock_version.content = "# Generated Document\n\nThis was generated by council."
        mock_version.version = 1

        # Execute
        result_path = sync_service.write_document_to_file(mock_version, create_backup=False)

        # Verify
        assert result_path.exists()
        assert result_path.read_text(encoding="utf-8") == mock_version.content

    def test_write_document_creates_parent_dirs(self, sync_service, temp_project_dir):
        """Test that writing creates parent directories."""
        mock_version = MagicMock(spec=DocumentVersion)
        mock_version.document_path = "deep/nested/path/document.md"
        mock_version.content = "# Deep Document"
        mock_version.version = 1

        result_path = sync_service.write_document_to_file(mock_version, create_backup=False)

        assert result_path.exists()
        assert result_path.parent.exists()

    def test_write_document_creates_backup(self, sync_service, temp_project_dir):
        """Test that backup is created when enabled."""
        # Create existing file
        doc_path = "docs/existing.md"
        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        original_content = "# Original Content"
        full_path.write_text(original_content, encoding="utf-8")

        # Write new version
        mock_version = MagicMock(spec=DocumentVersion)
        mock_version.document_path = doc_path
        mock_version.content = "# New Content"
        mock_version.version = 2

        sync_service.write_document_to_file(mock_version, create_backup=True)

        # Verify backup created
        backup_path = temp_project_dir / "docs/existing.v1.backup.md"
        assert backup_path.exists()
        assert backup_path.read_text(encoding="utf-8") == original_content

    @pytest.mark.asyncio
    async def test_write_council_consensus_to_file(self, sync_service, temp_project_dir, mock_db_session):
        """Test writing approved council consensus to file."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)
        mock_session.id = session_id
        mock_session.project_id = 1
        mock_session.document_type = DocumentType.ONBOARDING.value
        mock_session.document_name = "Developer Onboarding"

        mock_consensus = MagicMock(spec=CouncilConsensus)
        mock_consensus.session_id = session_id
        mock_consensus.version = 2
        mock_consensus.consensus_content = "# Developer Onboarding\n\nGenerated by LLM Council."
        mock_consensus.is_approved = True
        mock_consensus.approved_at = datetime.now(timezone.utc)
        mock_consensus.human_additions = None

        # Setup mock execute calls
        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:  # Get session
                result.scalars.return_value.first.return_value = mock_session
            elif call_count[0] == 2:  # Get consensus
                result.scalars.return_value.first.return_value = mock_consensus
            else:  # Get latest version
                result.scalars.return_value.first.return_value = None
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Execute
        result_path = await sync_service.write_council_consensus_to_file(session_id)

        # Verify
        assert result_path is not None
        assert result_path.exists()
        assert mock_db_session.add.called
        mock_db_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_write_council_consensus_not_found(self, sync_service, mock_db_session):
        """Test writing consensus when session not found."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await sync_service.write_council_consensus_to_file(uuid4())

        assert result is None


# ============================================================================
# GIT INTEGRATION TESTS
# ============================================================================

class TestGitIntegration:
    """Test Git commit functionality."""

    def test_git_commit_document_success(self, sync_service, temp_project_dir):
        """Test successful git commit."""
        # Create file
        doc_path = "docs/README.md"
        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("# README", encoding="utf-8")

        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=str(temp_project_dir), capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(temp_project_dir), capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(temp_project_dir), capture_output=True)

        # Execute
        commit_hash = sync_service.git_commit_document(
            document_path=doc_path,
            message="test: Add README"
        )

        # Verify
        assert commit_hash is not None
        assert len(commit_hash) == 40  # SHA-1 hash length

    def test_git_commit_nonexistent_file(self, sync_service, temp_project_dir):
        """Test git commit with nonexistent file."""
        result = sync_service.git_commit_document("nonexistent.md")
        assert result is None

    def test_git_commit_no_git_repo(self, sync_service, temp_project_dir):
        """Test git commit when not in a git repo."""
        # Create file without git init
        doc_path = "docs/README.md"
        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("# README", encoding="utf-8")

        result = sync_service.git_commit_document(doc_path)
        assert result is None


# ============================================================================
# QUERY METHOD TESTS
# ============================================================================

class TestQueryMethods:
    """Test query and listing methods."""

    @pytest.mark.asyncio
    async def test_get_document_history(self, sync_service, mock_db_session):
        """Test getting document version history."""
        mock_versions = [
            MagicMock(spec=DocumentVersion, version=3),
            MagicMock(spec=DocumentVersion, version=2),
            MagicMock(spec=DocumentVersion, version=1),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_versions
        mock_db_session.execute.return_value = mock_result

        history = await sync_service.get_document_history("docs/README.md", project_id=1)

        assert len(history) == 3
        mock_db_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_latest_version(self, sync_service, mock_db_session):
        """Test getting latest document version."""
        mock_version = MagicMock(spec=DocumentVersion, version=5)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_version
        mock_db_session.execute.return_value = mock_result

        latest = await sync_service.get_latest_version("docs/README.md")

        assert latest.version == 5

    @pytest.mark.asyncio
    async def test_get_documents_by_type(self, sync_service, mock_db_session):
        """Test getting documents by type."""
        mock_versions = [
            MagicMock(spec=DocumentVersion, document_type="architecture"),
            MagicMock(spec=DocumentVersion, document_type="architecture"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_versions
        mock_db_session.execute.return_value = mock_result

        docs = await sync_service.get_documents_by_type("architecture", project_id=1)

        assert len(docs) == 2

    @pytest.mark.asyncio
    async def test_compare_versions(self, sync_service, mock_db_session):
        """Test comparing two document versions."""
        mock_v1 = MagicMock(spec=DocumentVersion)
        mock_v1.version = 1
        mock_v1.content = "# Version 1"
        mock_v1.created_at = datetime.now(timezone.utc)
        mock_v1.created_by = "user1"

        mock_v2 = MagicMock(spec=DocumentVersion)
        mock_v2.version = 2
        mock_v2.content = "# Version 2"
        mock_v2.created_at = datetime.now(timezone.utc)
        mock_v2.created_by = "user2"

        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.scalars.return_value.first.return_value = mock_v1
            else:
                result.scalars.return_value.first.return_value = mock_v2
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        comparison = await sync_service.compare_versions("docs/README.md", 1, 2)

        assert comparison is not None
        assert comparison["version1"]["version"] == 1
        assert comparison["version2"]["version"] == 2

    @pytest.mark.asyncio
    async def test_compare_versions_not_found(self, sync_service, mock_db_session):
        """Test comparing when version not found."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        comparison = await sync_service.compare_versions("docs/README.md", 1, 99)

        assert comparison is None


# ============================================================================
# ROLLBACK TESTS
# ============================================================================

class TestRollback:
    """Test rollback functionality."""

    @pytest.mark.asyncio
    async def test_rollback_to_version(self, sync_service, temp_project_dir, mock_db_session):
        """Test rolling back to a previous version."""
        # Setup target version
        mock_target = MagicMock(spec=DocumentVersion)
        mock_target.version = 2
        mock_target.document_type = "onboarding"
        mock_target.content = "# Version 2 Content"
        mock_target.content_hash = DocumentSyncService.compute_hash("# Version 2 Content")
        mock_target.document_path = "docs/ONBOARDING.md"

        # Setup current latest version
        mock_latest = MagicMock(spec=DocumentVersion)
        mock_latest.version = 5

        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:  # Get target version
                result.scalars.return_value.first.return_value = mock_target
            else:  # Get latest version
                result.scalars.return_value.first.return_value = mock_latest
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Create the target file location
        doc_path = temp_project_dir / "docs/ONBOARDING.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text("# Current Content", encoding="utf-8")

        # Execute
        rollback_version = await sync_service.rollback_to_version(
            document_path="docs/ONBOARDING.md",
            target_version=2,
            project_id=1,
            reason="Reverting due to errors"
        )

        # Verify
        mock_db_session.add.assert_called_once()
        added_version = mock_db_session.add.call_args[0][0]
        assert added_version.version == 6  # 5 + 1
        assert added_version.content == mock_target.content
        assert added_version.created_by == "rollback"
        assert "rolled_back_to" in added_version.extra_metadata

    @pytest.mark.asyncio
    async def test_rollback_to_nonexistent_version(self, sync_service, mock_db_session):
        """Test rollback when target version doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await sync_service.rollback_to_version(
            document_path="docs/README.md",
            target_version=999
        )

        assert result is None
        mock_db_session.add.assert_not_called()


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_sync_empty_file(self, sync_service, temp_project_dir, mock_db_session):
        """Test syncing an empty file."""
        # Create empty file
        doc_path = "docs/empty.md"
        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("", encoding="utf-8")

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        version = await sync_service.sync_file_to_db(
            document_path=doc_path,
            document_type="other"
        )

        # Should still sync (empty content is valid)
        mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_unicode_content(self, sync_service, temp_project_dir, mock_db_session):
        """Test syncing file with unicode content."""
        # Create file with unicode
        doc_path = "docs/unicode.md"
        content = "# Документація\n\n日本語テスト\n\n🎉 Emoji support!"
        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        await sync_service.sync_file_to_db(
            document_path=doc_path,
            document_type="other"
        )

        added_version = mock_db_session.add.call_args[0][0]
        assert added_version.content == content

    def test_write_document_unicode(self, sync_service, temp_project_dir):
        """Test writing document with unicode content."""
        mock_version = MagicMock(spec=DocumentVersion)
        mock_version.document_path = "docs/unicode_out.md"
        mock_version.content = "# 测试文档\n\n✅ Unicode works!"
        mock_version.version = 1

        result_path = sync_service.write_document_to_file(mock_version, create_backup=False)

        written_content = result_path.read_text(encoding="utf-8")
        assert written_content == mock_version.content

    @pytest.mark.asyncio
    async def test_sync_large_file(self, sync_service, temp_project_dir, mock_db_session):
        """Test syncing a large file."""
        # Create large file (1MB)
        doc_path = "docs/large.md"
        content = "# Large Document\n\n" + ("Content line.\n" * 50000)
        full_path = temp_project_dir / doc_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        await sync_service.sync_file_to_db(
            document_path=doc_path,
            document_type="other"
        )

        added_version = mock_db_session.add.call_args[0][0]
        assert len(added_version.content) > 500000  # > 500KB
