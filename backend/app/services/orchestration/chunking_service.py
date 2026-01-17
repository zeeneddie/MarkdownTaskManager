"""
Chunking Service - Week 111

Pattern: Chunking (from Gregor Riegler's Augmented Coding Pattern Language)

Purpose: Break down large tasks into manageable chunks that can be
processed incrementally. Prevents context overflow, enables progress
tracking, and supports checkpoint/resume functionality.

Key Concepts:
- Chunk: A discrete, processable unit of work
- ChunkStrategy: How to divide the work (size-based, semantic, dependency-based)
- ChunkState: Track progress of each chunk
- Reassembly: Combine chunk results into final output

Usage:
    service = ChunkingService()

    # Chunk a large file for analysis
    chunks = service.chunk_file(
        file_path="large_codebase.py",
        strategy=ChunkStrategy.SEMANTIC,
        max_size=4000  # tokens
    )

    # Process chunks with progress tracking
    for chunk in chunks:
        result = process_chunk(chunk)
        service.mark_completed(chunk.id, result)

    # Reassemble results
    final_result = service.reassemble(chunks)
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Callable
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class ChunkStrategy(Enum):
    """Strategies for dividing work into chunks."""
    SIZE_BASED = "size_based"        # Fixed size chunks
    LINE_BASED = "line_based"        # Fixed number of lines
    SEMANTIC = "semantic"            # Based on code structure (functions, classes)
    DEPENDENCY = "dependency"        # Based on dependency graph
    PARAGRAPH = "paragraph"          # Based on paragraph breaks
    SECTION = "section"              # Based on section headers


class ChunkStatus(Enum):
    """Status of a chunk in processing."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ChunkType(Enum):
    """Type of content in the chunk."""
    CODE = "code"
    TEXT = "text"
    DATA = "data"
    MIXED = "mixed"


@dataclass
class Chunk:
    """A discrete unit of work."""
    id: UUID
    session_id: UUID
    index: int
    content: str
    chunk_type: ChunkType
    status: ChunkStatus
    metadata: Dict[str, Any]
    start_offset: int = 0
    end_offset: int = 0
    dependencies: List[UUID] = field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


@dataclass
class ChunkSession:
    """Session for chunking and processing."""
    id: UUID
    source: str  # file path or identifier
    strategy: ChunkStrategy
    total_chunks: int
    chunks: List[Chunk]
    config: Dict[str, Any]
    created_at: datetime
    completed_chunks: int = 0
    failed_chunks: int = 0


@dataclass
class ChunkingConfig:
    """Configuration for chunking."""
    max_size: int = 4000          # Max tokens/chars per chunk
    overlap: int = 100            # Overlap between chunks for context
    preserve_boundaries: bool = True  # Don't break mid-word/line
    include_headers: bool = True  # Include section headers in each chunk
    min_size: int = 100           # Minimum chunk size


@dataclass
class ReassemblyResult:
    """Result of reassembling chunks."""
    session_id: UUID
    total_chunks: int
    successful_chunks: int
    failed_chunks: int
    combined_result: Any
    metadata: Dict[str, Any]
    reassembled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ChunkingService:
    """
    Week 111: Chunking Service

    Break down large tasks into manageable chunks for incremental processing.
    """

    # Regex patterns for semantic chunking
    PYTHON_PATTERNS = {
        "class": re.compile(r'^class\s+\w+', re.MULTILINE),
        "function": re.compile(r'^(?:async\s+)?def\s+\w+', re.MULTILINE),
        "method": re.compile(r'^\s{4}(?:async\s+)?def\s+\w+', re.MULTILINE),
    }

    JAVASCRIPT_PATTERNS = {
        "class": re.compile(r'^(?:export\s+)?class\s+\w+', re.MULTILINE),
        "function": re.compile(r'^(?:export\s+)?(?:async\s+)?function\s+\w+', re.MULTILINE),
        "arrow": re.compile(r'^(?:export\s+)?const\s+\w+\s*=\s*(?:async\s+)?\(', re.MULTILINE),
    }

    MARKDOWN_PATTERNS = {
        "h1": re.compile(r'^#\s+', re.MULTILINE),
        "h2": re.compile(r'^##\s+', re.MULTILINE),
        "h3": re.compile(r'^###\s+', re.MULTILINE),
    }

    def __init__(self):
        self._sessions: Dict[UUID, ChunkSession] = {}
        self._chunks: Dict[UUID, Chunk] = {}

    def chunk_text(
        self,
        text: str,
        strategy: ChunkStrategy = ChunkStrategy.SIZE_BASED,
        config: Optional[ChunkingConfig] = None,
        source: str = "text",
    ) -> ChunkSession:
        """
        Chunk text content.

        Args:
            text: The text to chunk
            strategy: Chunking strategy to use
            config: Chunking configuration
            source: Source identifier

        Returns:
            ChunkSession with chunks
        """
        config = config or ChunkingConfig()

        # Create session
        session = ChunkSession(
            id=uuid4(),
            source=source,
            strategy=strategy,
            total_chunks=0,
            chunks=[],
            config=config.__dict__,
            created_at=datetime.now(timezone.utc),
        )

        # Generate chunks based on strategy
        if strategy == ChunkStrategy.SIZE_BASED:
            chunks = self._chunk_by_size(session.id, text, config)
        elif strategy == ChunkStrategy.LINE_BASED:
            chunks = self._chunk_by_lines(session.id, text, config)
        elif strategy == ChunkStrategy.SEMANTIC:
            chunks = self._chunk_semantically(session.id, text, config, source)
        elif strategy == ChunkStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraphs(session.id, text, config)
        elif strategy == ChunkStrategy.SECTION:
            chunks = self._chunk_by_sections(session.id, text, config)
        else:
            chunks = self._chunk_by_size(session.id, text, config)

        session.chunks = chunks
        session.total_chunks = len(chunks)
        self._sessions[session.id] = session

        # Index chunks
        for chunk in chunks:
            self._chunks[chunk.id] = chunk

        logger.info(f"Created chunking session {session.id}: {len(chunks)} chunks from {source}")
        return session

    def chunk_file(
        self,
        file_path: str,
        strategy: ChunkStrategy = ChunkStrategy.SEMANTIC,
        config: Optional[ChunkingConfig] = None,
    ) -> ChunkSession:
        """
        Chunk a file.

        Args:
            file_path: Path to the file
            strategy: Chunking strategy
            config: Chunking configuration

        Returns:
            ChunkSession with chunks
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text(encoding="utf-8")
        return self.chunk_text(content, strategy, config, source=file_path)

    def chunk_files(
        self,
        file_paths: List[str],
        strategy: ChunkStrategy = ChunkStrategy.SEMANTIC,
        config: Optional[ChunkingConfig] = None,
    ) -> ChunkSession:
        """
        Chunk multiple files into a single session.

        Args:
            file_paths: List of file paths
            strategy: Chunking strategy
            config: Chunking configuration

        Returns:
            ChunkSession with chunks from all files
        """
        config = config or ChunkingConfig()

        # Create combined session
        session = ChunkSession(
            id=uuid4(),
            source=",".join(file_paths[:3]) + ("..." if len(file_paths) > 3 else ""),
            strategy=strategy,
            total_chunks=0,
            chunks=[],
            config=config.__dict__,
            created_at=datetime.now(timezone.utc),
        )

        all_chunks = []
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Skipping non-existent file: {file_path}")
                continue

            content = path.read_text(encoding="utf-8")

            # Add file header to content
            file_content = f"# File: {file_path}\n\n{content}"

            # Chunk this file
            if strategy == ChunkStrategy.SEMANTIC:
                chunks = self._chunk_semantically(session.id, file_content, config, file_path)
            else:
                chunks = self._chunk_by_size(session.id, file_content, config)

            # Add file metadata to chunks
            for chunk in chunks:
                chunk.metadata["source_file"] = file_path

            all_chunks.extend(chunks)

        # Re-index chunks
        for i, chunk in enumerate(all_chunks):
            chunk.index = i

        session.chunks = all_chunks
        session.total_chunks = len(all_chunks)
        self._sessions[session.id] = session

        for chunk in all_chunks:
            self._chunks[chunk.id] = chunk

        logger.info(f"Created multi-file session {session.id}: {len(all_chunks)} chunks from {len(file_paths)} files")
        return session

    def get_chunk(self, chunk_id: UUID) -> Optional[Chunk]:
        """Get a chunk by ID."""
        return self._chunks.get(chunk_id)

    def get_session(self, session_id: UUID) -> Optional[ChunkSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_next_chunk(self, session_id: UUID) -> Optional[Chunk]:
        """Get the next pending chunk to process."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        for chunk in session.chunks:
            if chunk.status == ChunkStatus.PENDING:
                # Check dependencies
                deps_satisfied = all(
                    self._chunks.get(dep_id, Chunk(uuid4(), session_id, 0, "", ChunkType.CODE, ChunkStatus.COMPLETED, {})).status == ChunkStatus.COMPLETED
                    for dep_id in chunk.dependencies
                )
                if deps_satisfied:
                    return chunk

        return None

    def mark_in_progress(self, chunk_id: UUID) -> None:
        """Mark a chunk as in progress."""
        chunk = self._chunks.get(chunk_id)
        if chunk:
            chunk.status = ChunkStatus.IN_PROGRESS

    def mark_completed(
        self,
        chunk_id: UUID,
        result: Any,
    ) -> None:
        """
        Mark a chunk as completed with result.

        Args:
            chunk_id: The chunk to mark
            result: The processing result
        """
        chunk = self._chunks.get(chunk_id)
        if not chunk:
            raise ValueError(f"Chunk {chunk_id} not found")

        chunk.status = ChunkStatus.COMPLETED
        chunk.result = result
        chunk.completed_at = datetime.now(timezone.utc)

        # Update session
        session = self._sessions.get(chunk.session_id)
        if session:
            session.completed_chunks += 1

        logger.debug(f"Chunk {chunk_id} completed")

    def mark_failed(
        self,
        chunk_id: UUID,
        error: str,
    ) -> None:
        """
        Mark a chunk as failed.

        Args:
            chunk_id: The chunk to mark
            error: The error message
        """
        chunk = self._chunks.get(chunk_id)
        if not chunk:
            raise ValueError(f"Chunk {chunk_id} not found")

        chunk.status = ChunkStatus.FAILED
        chunk.error = error
        chunk.completed_at = datetime.now(timezone.utc)

        # Update session
        session = self._sessions.get(chunk.session_id)
        if session:
            session.failed_chunks += 1

        logger.warning(f"Chunk {chunk_id} failed: {error}")

    def get_progress(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get progress for a session.

        Args:
            session_id: Session to check

        Returns:
            Progress information
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        return {
            "session_id": str(session_id),
            "total": session.total_chunks,
            "completed": session.completed_chunks,
            "failed": session.failed_chunks,
            "pending": session.total_chunks - session.completed_chunks - session.failed_chunks,
            "progress_percent": (session.completed_chunks / session.total_chunks * 100) if session.total_chunks > 0 else 0,
            "is_complete": session.completed_chunks + session.failed_chunks == session.total_chunks,
        }

    def reassemble(
        self,
        session_id: UUID,
        combiner: Optional[Callable[[List[Any]], Any]] = None,
    ) -> ReassemblyResult:
        """
        Reassemble chunk results into final output.

        Args:
            session_id: Session to reassemble
            combiner: Optional function to combine results (default: concatenate)

        Returns:
            ReassemblyResult with combined output
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Collect results
        results = []
        for chunk in session.chunks:
            if chunk.status == ChunkStatus.COMPLETED and chunk.result is not None:
                results.append(chunk.result)

        # Combine results
        if combiner:
            combined = combiner(results)
        elif all(isinstance(r, str) for r in results):
            combined = "\n\n".join(results)
        elif all(isinstance(r, list) for r in results):
            combined = []
            for r in results:
                combined.extend(r)
        elif all(isinstance(r, dict) for r in results):
            combined = {}
            for r in results:
                combined.update(r)
        else:
            combined = results

        return ReassemblyResult(
            session_id=session_id,
            total_chunks=session.total_chunks,
            successful_chunks=session.completed_chunks,
            failed_chunks=session.failed_chunks,
            combined_result=combined,
            metadata={
                "strategy": session.strategy.value,
                "source": session.source,
            },
        )

    def iterate_chunks(self, session_id: UUID) -> Iterator[Chunk]:
        """
        Iterate over chunks in order.

        Args:
            session_id: Session to iterate

        Yields:
            Chunks in order
        """
        session = self._sessions.get(session_id)
        if session:
            yield from session.chunks

    def _chunk_by_size(
        self,
        session_id: UUID,
        text: str,
        config: ChunkingConfig,
    ) -> List[Chunk]:
        """Chunk by fixed size with overlap."""
        chunks = []
        offset = 0
        index = 0

        while offset < len(text):
            # Calculate end position
            end = min(offset + config.max_size, len(text))

            # Preserve word boundaries if configured
            if config.preserve_boundaries and end < len(text):
                # Find last space before end
                last_space = text.rfind(' ', offset, end)
                if last_space > offset:
                    end = last_space

            content = text[offset:end]

            chunk = Chunk(
                id=uuid4(),
                session_id=session_id,
                index=index,
                content=content,
                chunk_type=ChunkType.TEXT,
                status=ChunkStatus.PENDING,
                metadata={"strategy": "size_based"},
                start_offset=offset,
                end_offset=end,
            )
            chunks.append(chunk)

            # Move offset with overlap
            offset = end - config.overlap if end < len(text) else end
            index += 1

        return chunks

    def _chunk_by_lines(
        self,
        session_id: UUID,
        text: str,
        config: ChunkingConfig,
    ) -> List[Chunk]:
        """Chunk by number of lines."""
        lines = text.split('\n')
        lines_per_chunk = max(1, config.max_size // 80)  # Assume ~80 chars per line
        chunks = []
        index = 0

        for i in range(0, len(lines), lines_per_chunk):
            chunk_lines = lines[i:i + lines_per_chunk]
            content = '\n'.join(chunk_lines)

            if len(content) >= config.min_size:
                chunk = Chunk(
                    id=uuid4(),
                    session_id=session_id,
                    index=index,
                    content=content,
                    chunk_type=ChunkType.TEXT,
                    status=ChunkStatus.PENDING,
                    metadata={"strategy": "line_based", "line_range": (i, i + len(chunk_lines))},
                    start_offset=sum(len(l) + 1 for l in lines[:i]),
                    end_offset=sum(len(l) + 1 for l in lines[:i + len(chunk_lines)]),
                )
                chunks.append(chunk)
                index += 1

        return chunks

    def _chunk_semantically(
        self,
        session_id: UUID,
        text: str,
        config: ChunkingConfig,
        source: str,
    ) -> List[Chunk]:
        """Chunk based on code structure (functions, classes)."""
        # Detect language from source
        ext = Path(source).suffix.lower() if source else ""

        if ext in ['.py']:
            patterns = self.PYTHON_PATTERNS
            chunk_type = ChunkType.CODE
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            patterns = self.JAVASCRIPT_PATTERNS
            chunk_type = ChunkType.CODE
        elif ext in ['.md', '.markdown']:
            patterns = self.MARKDOWN_PATTERNS
            chunk_type = ChunkType.TEXT
        else:
            # Fall back to size-based for unknown types
            return self._chunk_by_size(session_id, text, config)

        # Find all semantic boundaries
        boundaries = [0]
        for pattern in patterns.values():
            for match in pattern.finditer(text):
                boundaries.append(match.start())
        boundaries.append(len(text))
        boundaries = sorted(set(boundaries))

        # Create chunks from boundaries
        chunks = []
        index = 0

        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            content = text[start:end].strip()

            # Skip too small chunks or merge with previous
            if len(content) < config.min_size and chunks:
                # Merge with previous chunk
                chunks[-1].content += "\n\n" + content
                chunks[-1].end_offset = end
                continue

            # Split if too large
            if len(content) > config.max_size:
                # Sub-chunk by size
                sub_chunks = self._chunk_by_size(
                    session_id,
                    content,
                    ChunkingConfig(max_size=config.max_size, overlap=config.overlap)
                )
                for sub in sub_chunks:
                    sub.chunk_type = chunk_type
                    sub.start_offset += start
                    sub.end_offset += start
                    sub.index = index
                    sub.metadata["strategy"] = "semantic_sub"
                    index += 1
                chunks.extend(sub_chunks)
            else:
                chunk = Chunk(
                    id=uuid4(),
                    session_id=session_id,
                    index=index,
                    content=content,
                    chunk_type=chunk_type,
                    status=ChunkStatus.PENDING,
                    metadata={"strategy": "semantic"},
                    start_offset=start,
                    end_offset=end,
                )
                chunks.append(chunk)
                index += 1

        return chunks

    def _chunk_by_paragraphs(
        self,
        session_id: UUID,
        text: str,
        config: ChunkingConfig,
    ) -> List[Chunk]:
        """Chunk by paragraph breaks."""
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        index = 0
        current_content = ""
        current_start = 0
        offset = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                offset += 2  # Account for paragraph break
                continue

            # Check if adding this paragraph exceeds max size
            if current_content and len(current_content) + len(para) + 2 > config.max_size:
                # Create chunk from current content
                chunk = Chunk(
                    id=uuid4(),
                    session_id=session_id,
                    index=index,
                    content=current_content,
                    chunk_type=ChunkType.TEXT,
                    status=ChunkStatus.PENDING,
                    metadata={"strategy": "paragraph"},
                    start_offset=current_start,
                    end_offset=offset,
                )
                chunks.append(chunk)
                index += 1
                current_content = para
                current_start = offset
            else:
                if current_content:
                    current_content += "\n\n" + para
                else:
                    current_content = para
                    current_start = offset

            offset += len(para) + 2  # Account for paragraph + break

        # Don't forget the last chunk
        if current_content and len(current_content) >= config.min_size:
            chunk = Chunk(
                id=uuid4(),
                session_id=session_id,
                index=index,
                content=current_content,
                chunk_type=ChunkType.TEXT,
                status=ChunkStatus.PENDING,
                metadata={"strategy": "paragraph"},
                start_offset=current_start,
                end_offset=len(text),
            )
            chunks.append(chunk)

        return chunks

    def _chunk_by_sections(
        self,
        session_id: UUID,
        text: str,
        config: ChunkingConfig,
    ) -> List[Chunk]:
        """Chunk by section headers (markdown-style)."""
        # Find section headers
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        matches = list(header_pattern.finditer(text))

        if not matches:
            # No headers found, fall back to paragraphs
            return self._chunk_by_paragraphs(session_id, text, config)

        chunks = []
        index = 0

        # Add content before first header if any
        if matches[0].start() > 0:
            pre_content = text[:matches[0].start()].strip()
            if len(pre_content) >= config.min_size:
                chunk = Chunk(
                    id=uuid4(),
                    session_id=session_id,
                    index=index,
                    content=pre_content,
                    chunk_type=ChunkType.TEXT,
                    status=ChunkStatus.PENDING,
                    metadata={"strategy": "section", "header": "Preamble"},
                    start_offset=0,
                    end_offset=matches[0].start(),
                )
                chunks.append(chunk)
                index += 1

        # Create chunks from sections
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            header = match.group(2)

            # Skip too small sections
            if len(content) < config.min_size:
                continue

            # Split if too large
            if len(content) > config.max_size:
                sub_chunks = self._chunk_by_size(
                    session_id,
                    content,
                    ChunkingConfig(max_size=config.max_size, overlap=config.overlap)
                )
                for j, sub in enumerate(sub_chunks):
                    sub.index = index
                    sub.start_offset += start
                    sub.end_offset += start
                    sub.metadata = {"strategy": "section_sub", "header": header, "part": j + 1}
                    index += 1
                chunks.extend(sub_chunks)
            else:
                chunk = Chunk(
                    id=uuid4(),
                    session_id=session_id,
                    index=index,
                    content=content,
                    chunk_type=ChunkType.TEXT,
                    status=ChunkStatus.PENDING,
                    metadata={"strategy": "section", "header": header},
                    start_offset=start,
                    end_offset=end,
                )
                chunks.append(chunk)
                index += 1

        return chunks
