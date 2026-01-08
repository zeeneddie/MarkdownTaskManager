"""
Script to embed HCI-CRS project documentation into ChromaDB

This script indexes:
1. ARCHITECTURE.md - Technical architecture analysis
2. Epic and Feature documentation
3. User Stories with tasks
4. Code location mappings

Usage:
    python -m app.scripts.embed_hci_crs_docs
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.chroma_service import ChromaService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HCI-CRS project configuration
HCI_CRS_PROJECT_ID = 1000  # Use a high ID to avoid conflicts
HCI_CRS_BASE_PATH = Path("/opt/projecten/hci-crs/doc/project")


def read_markdown_file(file_path: Path) -> str:
    """Read a markdown file and return its contents"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return ""


def get_all_markdown_files(base_path: Path) -> list:
    """Recursively find all markdown files in a directory"""
    return list(base_path.rglob("*.md"))


def determine_document_type(file_path: Path) -> str:
    """Determine document type from file path"""
    path_str = str(file_path).lower()

    if "architecture" in path_str:
        return "architecture"
    elif "epic" in path_str and "feature" not in path_str:
        return "epic"
    elif "feature" in path_str and "story" not in path_str and "task" not in path_str:
        return "feature"
    elif "story" in path_str or "us-" in path_str:
        return "user_story"
    elif "task" in path_str:
        return "task"
    elif "project.md" in path_str:
        return "project_overview"
    else:
        return "documentation"


def extract_metadata_from_path(file_path: Path, base_path: Path) -> dict:
    """Extract metadata from file path structure"""
    relative_path = file_path.relative_to(base_path)
    parts = relative_path.parts

    metadata = {
        "project_name": "HCI-CRS",
        "relative_path": str(relative_path),
        "file_name": file_path.name,
    }

    # Extract epic name if present
    for part in parts:
        if part.startswith("EPIC-"):
            metadata["epic"] = part
            break

    # Extract feature name if present
    for part in parts:
        if part.startswith("FEATURE-"):
            metadata["feature"] = part
            break

    # Extract story name if present
    for part in parts:
        if part.startswith("US-") or part.startswith("STORY-"):
            metadata["story"] = part
            break

    return metadata


def embed_hci_crs_documents():
    """Main function to embed all HCI-CRS documentation"""
    logger.info("Starting HCI-CRS documentation embedding...")

    # Initialize ChromaDB service
    try:
        chroma = ChromaService()
        logger.info("ChromaDB service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        return

    # Check if base path exists
    if not HCI_CRS_BASE_PATH.exists():
        logger.error(f"HCI-CRS base path not found: {HCI_CRS_BASE_PATH}")
        return

    # Find all markdown files
    md_files = get_all_markdown_files(HCI_CRS_BASE_PATH)
    logger.info(f"Found {len(md_files)} markdown files to process")

    # Track statistics
    stats = {
        "total_files": len(md_files),
        "processed": 0,
        "failed": 0,
        "chunks_created": 0,
        "by_type": {}
    }

    # Process each file
    for file_path in md_files:
        try:
            # Read content
            content = read_markdown_file(file_path)
            if not content:
                stats["failed"] += 1
                continue

            # Determine document type
            doc_type = determine_document_type(file_path)

            # Extract metadata
            metadata = extract_metadata_from_path(file_path, HCI_CRS_BASE_PATH)
            metadata["indexed_at"] = datetime.now().isoformat()

            # Store document
            doc_ids = chroma.store_document(
                project_id=HCI_CRS_PROJECT_ID,
                document_type=doc_type,
                content=content,
                metadata=metadata,
                chunk_size=512,
                chunk_overlap=50
            )

            # Update statistics
            stats["processed"] += 1
            stats["chunks_created"] += len(doc_ids)
            stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1

            logger.info(f"Embedded: {file_path.name} ({doc_type}) -> {len(doc_ids)} chunks")

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            stats["failed"] += 1

    # Print summary
    logger.info("\n" + "="*50)
    logger.info("HCI-CRS Documentation Embedding Complete")
    logger.info("="*50)
    logger.info(f"Total files: {stats['total_files']}")
    logger.info(f"Processed: {stats['processed']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Chunks created: {stats['chunks_created']}")
    logger.info("\nBy document type:")
    for doc_type, count in stats["by_type"].items():
        logger.info(f"  {doc_type}: {count} files")

    return stats


if __name__ == "__main__":
    embed_hci_crs_documents()
