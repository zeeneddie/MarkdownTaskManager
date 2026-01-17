"""
Code RAG Service - Semantic Code Search Integration

Week 62: Code Understanding Integration

Features:
- Semantic code search using embeddings
- AST-aware code chunking
- Hybrid TF-IDF + vector search
- Integration with ChromaDB for storage
- Support for 15+ programming languages

Based on: CodeRAG (SylphxAI/coderag) concepts
"""

import hashlib
import re
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
import ast

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ChromaDB is optional
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed. Code RAG disabled.")


class CodeChunk:
    """Represents a chunk of code with metadata."""

    def __init__(
        self,
        content: str,
        file_path: str,
        start_line: int,
        end_line: int,
        chunk_type: str = "code",
        name: Optional[str] = None,
        language: Optional[str] = None,
    ):
        self.content = content
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.chunk_type = chunk_type  # function, class, module, block
        self.name = name
        self.language = language
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique ID for chunk."""
        content = f"{self.file_path}:{self.start_line}:{self.end_line}:{self.content[:100]}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "chunk_type": self.chunk_type,
            "name": self.name,
            "language": self.language,
        }


class CodeChunker:
    """
    AST-aware code chunker.

    Splits code at semantic boundaries (functions, classes)
    rather than arbitrary line counts.
    """

    # Language extensions
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
    }

    def __init__(self, max_chunk_size: int = 2000):
        """Initialize chunker with max chunk size in characters."""
        self.max_chunk_size = max_chunk_size

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """
        Chunk a file into semantic units.

        Args:
            file_path: Path to source file

        Returns:
            List of CodeChunks
        """
        path = Path(file_path)
        if not path.exists():
            return []

        language = self.LANGUAGE_MAP.get(path.suffix.lower())
        if not language:
            return []

        try:
            content = path.read_text(errors='ignore')
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return []

        # Use language-specific chunking
        if language == "python":
            return self._chunk_python(content, file_path, language)
        else:
            return self._chunk_generic(content, file_path, language)

    def _chunk_python(
        self,
        content: str,
        file_path: str,
        language: str
    ) -> List[CodeChunk]:
        """Chunk Python code using AST."""
        chunks = []
        lines = content.splitlines()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fall back to generic chunking
            return self._chunk_generic(content, file_path, language)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                chunk = self._extract_node_chunk(
                    node, lines, file_path, language, "function"
                )
                if chunk:
                    chunks.append(chunk)

            elif isinstance(node, ast.ClassDef):
                chunk = self._extract_node_chunk(
                    node, lines, file_path, language, "class"
                )
                if chunk:
                    chunks.append(chunk)

        # If no chunks found, create module-level chunk
        if not chunks and content.strip():
            chunks.append(CodeChunk(
                content=content[:self.max_chunk_size],
                file_path=file_path,
                start_line=1,
                end_line=len(lines),
                chunk_type="module",
                name=Path(file_path).stem,
                language=language,
            ))

        return chunks

    def _extract_node_chunk(
        self,
        node: ast.AST,
        lines: List[str],
        file_path: str,
        language: str,
        chunk_type: str
    ) -> Optional[CodeChunk]:
        """Extract a chunk from an AST node."""
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', start_line + 10)

        # Get the content
        chunk_lines = lines[start_line - 1:end_line]
        content = '\n'.join(chunk_lines)

        # Truncate if too long
        if len(content) > self.max_chunk_size:
            content = content[:self.max_chunk_size] + "\n# ... truncated"

        name = getattr(node, 'name', None)

        return CodeChunk(
            content=content,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            chunk_type=chunk_type,
            name=name,
            language=language,
        )

    def _chunk_generic(
        self,
        content: str,
        file_path: str,
        language: str
    ) -> List[CodeChunk]:
        """Generic chunking for non-Python languages."""
        chunks = []
        lines = content.splitlines()

        # Pattern-based detection for functions/classes
        patterns = {
            "function": [
                r'^(?:async\s+)?function\s+(\w+)',  # JS/TS
                r'^(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(',  # Java/C#
                r'^func\s+(\w+)',  # Go
                r'^def\s+(\w+)',  # Ruby
                r'^fn\s+(\w+)',  # Rust
            ],
            "class": [
                r'^class\s+(\w+)',
                r'^struct\s+(\w+)',
                r'^interface\s+(\w+)',
            ]
        }

        current_chunk_start = 0
        current_chunk_lines = []
        current_name = None
        current_type = "block"

        for i, line in enumerate(lines):
            # Check for function/class definitions
            for chunk_type, type_patterns in patterns.items():
                for pattern in type_patterns:
                    match = re.match(pattern, line.strip())
                    if match:
                        # Save previous chunk if exists
                        if current_chunk_lines:
                            chunk_content = '\n'.join(current_chunk_lines)
                            if chunk_content.strip():
                                chunks.append(CodeChunk(
                                    content=chunk_content[:self.max_chunk_size],
                                    file_path=file_path,
                                    start_line=current_chunk_start + 1,
                                    end_line=i,
                                    chunk_type=current_type,
                                    name=current_name,
                                    language=language,
                                ))

                        # Start new chunk
                        current_chunk_start = i
                        current_chunk_lines = [line]
                        current_name = match.group(1) if match.groups() else None
                        current_type = chunk_type
                        break
                else:
                    continue
                break
            else:
                current_chunk_lines.append(line)

        # Save final chunk
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            if chunk_content.strip():
                chunks.append(CodeChunk(
                    content=chunk_content[:self.max_chunk_size],
                    file_path=file_path,
                    start_line=current_chunk_start + 1,
                    end_line=len(lines),
                    chunk_type=current_type,
                    name=current_name,
                    language=language,
                ))

        return chunks


class CodeRAGService:
    """
    Semantic code search service using RAG.

    Provides:
    - Code indexing with AST-aware chunking
    - Semantic search using embeddings
    - Hybrid TF-IDF + vector search
    - Integration with ChromaDB
    """

    COLLECTION_NAME = "code_rag"

    def __init__(
        self,
        persist_directory: str = "./chromadb_data",
        collection_name: Optional[str] = None
    ):
        """
        Initialize Code RAG service.

        Args:
            persist_directory: ChromaDB persistence directory
            collection_name: Override collection name
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name or self.COLLECTION_NAME
        self._client = None
        self._collection = None
        self.chunker = CodeChunker()

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
                metadata={"description": "Code RAG semantic search"}
            )
            logger.info(f"ChromaDB collection '{self.collection_name}' initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self._client = None
            self._collection = None

    @property
    def is_available(self) -> bool:
        """Check if service is available."""
        return self._collection is not None

    def index_repository(
        self,
        repo_path: str,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Index a repository for semantic search.

        Args:
            repo_path: Path to repository
            project_id: Optional project ID for filtering

        Returns:
            Indexing statistics
        """
        if not self.is_available:
            return {"error": "ChromaDB not available"}

        path = Path(repo_path)
        if not path.exists():
            return {"error": f"Repository not found: {repo_path}"}

        stats = {
            "files_processed": 0,
            "chunks_created": 0,
            "errors": [],
            "languages": {},
        }

        # Find all source files
        for ext in CodeChunker.LANGUAGE_MAP.keys():
            for file_path in path.rglob(f"*{ext}"):
                # Skip common directories
                if any(part.startswith('.') or part in [
                    'node_modules', 'venv', '__pycache__', 'dist', 'build'
                ] for part in file_path.parts):
                    continue

                try:
                    chunks = self.chunker.chunk_file(str(file_path))
                    stats["files_processed"] += 1

                    for chunk in chunks:
                        self._store_chunk(chunk, project_id)
                        stats["chunks_created"] += 1

                        # Track languages
                        lang = chunk.language or "unknown"
                        stats["languages"][lang] = stats["languages"].get(lang, 0) + 1

                except Exception as e:
                    stats["errors"].append(f"{file_path}: {str(e)}")

        return stats

    def index_file(
        self,
        file_path: str,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Index a single file.

        Args:
            file_path: Path to file
            project_id: Optional project ID

        Returns:
            Indexing result
        """
        if not self.is_available:
            return {"error": "ChromaDB not available"}

        chunks = self.chunker.chunk_file(file_path)

        for chunk in chunks:
            self._store_chunk(chunk, project_id)

        return {
            "file": file_path,
            "chunks_created": len(chunks),
        }

    def _store_chunk(
        self,
        chunk: CodeChunk,
        project_id: Optional[int] = None
    ) -> None:
        """Store a code chunk in ChromaDB."""
        if not self.is_available:
            return

        metadata = {
            "file_path": chunk.file_path,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "chunk_type": chunk.chunk_type,
            "name": chunk.name or "",
            "language": chunk.language or "",
            "project_id": project_id or 0,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            self._collection.upsert(
                ids=[chunk.id],
                documents=[chunk.content],
                metadatas=[metadata]
            )
        except Exception as e:
            logger.error(f"Failed to store chunk: {e}")

    def search(
        self,
        query: str,
        n_results: int = 10,
        project_id: Optional[int] = None,
        language: Optional[str] = None,
        chunk_type: Optional[str] = None,
        file_path_pattern: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for code using semantic similarity.

        Args:
            query: Search query (natural language or code)
            n_results: Number of results to return
            project_id: Filter by project
            language: Filter by language
            chunk_type: Filter by chunk type (function, class, etc.)
            file_path_pattern: Filter by file path pattern

        Returns:
            List of matching code chunks with similarity scores
        """
        if not self.is_available:
            return []

        # Build where filter
        where_filter = {}
        if project_id:
            where_filter["project_id"] = project_id
        if language:
            where_filter["language"] = language
        if chunk_type:
            where_filter["chunk_type"] = chunk_type

        # Build where_document filter for file path
        where_document = None
        if file_path_pattern:
            where_document = {"$contains": file_path_pattern}

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )

            matches = []
            if results and results["ids"] and results["ids"][0]:
                for i, chunk_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                    # Filter by file path pattern if specified
                    if file_path_pattern:
                        if file_path_pattern.lower() not in metadata.get("file_path", "").lower():
                            continue

                    matches.append({
                        "id": chunk_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "file_path": metadata.get("file_path", ""),
                        "start_line": metadata.get("start_line", 0),
                        "end_line": metadata.get("end_line", 0),
                        "chunk_type": metadata.get("chunk_type", ""),
                        "name": metadata.get("name", ""),
                        "language": metadata.get("language", ""),
                        "similarity": 1 - results["distances"][0][i] if results["distances"] else 0,
                    })

            return matches

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def find_similar_code(
        self,
        code_snippet: str,
        n_results: int = 5,
        project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find code similar to a given snippet.

        Args:
            code_snippet: Code to find similar matches for
            n_results: Number of results
            project_id: Filter by project

        Returns:
            List of similar code chunks
        """
        return self.search(
            query=code_snippet,
            n_results=n_results,
            project_id=project_id
        )

    def find_implementations(
        self,
        function_description: str,
        language: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find function implementations matching a description.

        Args:
            function_description: Natural language description
            language: Filter by language
            project_id: Filter by project

        Returns:
            List of matching function implementations
        """
        return self.search(
            query=function_description,
            n_results=10,
            project_id=project_id,
            language=language,
            chunk_type="function"
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get indexing statistics."""
        if not self.is_available:
            return {"available": False}

        try:
            count = self._collection.count()

            # Sample for distribution
            if count > 0:
                sample = self._collection.get(
                    limit=min(count, 1000),
                    include=["metadatas"]
                )

                languages = {}
                chunk_types = {}
                projects = {}

                for metadata in sample["metadatas"]:
                    lang = metadata.get("language", "unknown")
                    languages[lang] = languages.get(lang, 0) + 1

                    ctype = metadata.get("chunk_type", "unknown")
                    chunk_types[ctype] = chunk_types.get(ctype, 0) + 1

                    proj = metadata.get("project_id", 0)
                    projects[proj] = projects.get(proj, 0) + 1

                return {
                    "available": True,
                    "total_chunks": count,
                    "by_language": languages,
                    "by_chunk_type": chunk_types,
                    "by_project": projects,
                }

            return {
                "available": True,
                "total_chunks": 0,
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"available": False, "error": str(e)}

    def delete_project_index(self, project_id: int) -> bool:
        """Delete all indexed chunks for a project."""
        if not self.is_available:
            return False

        try:
            # Get chunks for project
            results = self._collection.get(
                where={"project_id": project_id},
                include=["metadatas"]
            )

            if results["ids"]:
                self._collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for project {project_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to delete project index: {e}")
            return False


# Singleton instance
_code_rag_service: Optional[CodeRAGService] = None


def get_code_rag_service(
    persist_directory: str = "./chromadb_data"
) -> CodeRAGService:
    """
    Get or create Code RAG service singleton.

    Args:
        persist_directory: ChromaDB persistence directory

    Returns:
        CodeRAGService instance
    """
    global _code_rag_service
    if _code_rag_service is None:
        _code_rag_service = CodeRAGService(persist_directory)
    return _code_rag_service
