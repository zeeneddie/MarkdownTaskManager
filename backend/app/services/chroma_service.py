"""
ChromaDB Service - Vector Database for RAG Knowledge Storage

This service manages all ChromaDB operations including:
- Collection initialization (project_documents, historical_projects, code_analysis, bmad_sessions)
- Document embedding and storage
- Semantic search and similarity queries
- Project knowledge retrieval
- Historical project comparison

Collections:
- project_documents: All project documentation embeddings (constitution, spec, tasks, PRD, etc.)
- historical_projects: Full project metadata for cross-project similarity search
- code_analysis: Quality scan results and technical debt tracking
- bmad_sessions: Green-paper and brown-paper session outputs
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class ChromaService:
    """ChromaDB service for vector database operations"""

    def __init__(self):
        """Initialize ChromaDB client and collections"""
        # Get connection settings from environment
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8001"))

        # Initialize ChromaDB client
        self.client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize embedding function (sentence-transformers)
        # Using all-MiniLM-L6-v2: 384 dimensions, fast, good quality
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Initialize collections
        self._initialize_collections()

        logger.info(f"ChromaDB service initialized - Host: {chroma_host}:{chroma_port}")

    def _initialize_collections(self):
        """Create or get all required collections"""
        try:
            # Collection 1: Project Documents
            # Stores all project documentation with embeddings
            self.project_documents = self.client.get_or_create_collection(
                name="project_documents",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "All project documentation embeddings",
                    "hnsw:space": "cosine"
                }
            )

            # Collection 2: Historical Projects
            # Full project metadata for similarity search
            self.historical_projects = self.client.get_or_create_collection(
                name="historical_projects",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Full project metadata for cross-project similarity",
                    "hnsw:space": "cosine"
                }
            )

            # Collection 3: Code Analysis
            # Quality scan results and technical debt
            self.code_analysis = self.client.get_or_create_collection(
                name="code_analysis",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Quality scan results and technical debt tracking",
                    "hnsw:space": "cosine"
                }
            )

            # Collection 4: BMAD Sessions
            # Green-paper and brown-paper session outputs
            self.bmad_sessions = self.client.get_or_create_collection(
                name="bmad_sessions",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "BMAD green-paper and brown-paper session outputs",
                    "hnsw:space": "cosine"
                }
            )

            # Collection 5: Project Constitutions
            # Week 10 - Constitution embeddings for similarity search
            self.project_constitutions = self.client.get_or_create_collection(
                name="project_constitutions",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Week 10 - Constitution embeddings for similarity search",
                    "hnsw:space": "cosine"
                }
            )

            logger.info("All ChromaDB collections initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB collections: {str(e)}")
            raise

    # ========== PROJECT DOCUMENTS OPERATIONS ==========

    def store_document(
        self,
        project_id: int,
        document_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ) -> List[str]:
        """
        Store a document with embeddings in ChromaDB

        Args:
            project_id: ID of the project
            document_type: Type of document (constitution, specification, tasks, prd, etc.)
            content: Full document content (markdown)
            metadata: Additional metadata
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks

        Returns:
            List of document IDs created
        """
        try:
            # Chunk the document
            chunks = self._chunk_document(content, chunk_size, chunk_overlap)

            # Prepare document IDs
            timestamp = datetime.now().isoformat()
            doc_ids = [
                f"{document_type}-{project_id}-{i}-{timestamp}"
                for i in range(len(chunks))
            ]

            # Prepare metadata for each chunk
            base_metadata = metadata or {}
            metadatas = [
                {
                    **base_metadata,
                    "project_id": str(project_id),
                    "document_type": document_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "created_at": timestamp
                }
                for i in range(len(chunks))
            ]

            # Add to collection
            self.project_documents.add(
                documents=chunks,
                metadatas=metadatas,
                ids=doc_ids
            )

            logger.info(f"Stored {len(chunks)} chunks for {document_type} (project {project_id})")
            return doc_ids

        except Exception as e:
            logger.error(f"Failed to store document: {str(e)}")
            raise

    def query_project_knowledge(
        self,
        query: str,
        project_id: Optional[int] = None,
        document_types: Optional[List[str]] = None,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Query project knowledge base with semantic search

        Args:
            query: Search query
            project_id: Optional project ID to filter by
            document_types: Optional list of document types to filter
            top_k: Number of results to return

        Returns:
            Dict with results, distances, and metadatas
        """
        try:
            # Build where filter
            where_filter = {}
            if project_id:
                where_filter["project_id"] = str(project_id)
            if document_types:
                where_filter["document_type"] = {"$in": document_types}

            # Query collection
            results = self.project_documents.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter if where_filter else None
            )

            return {
                "query": query,
                "results": results["documents"][0] if results["documents"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "count": len(results["documents"][0]) if results["documents"] else 0
            }

        except Exception as e:
            logger.error(f"Failed to query project knowledge: {str(e)}")
            raise

    def delete_project_documents(
        self,
        project_id: int,
        document_type: Optional[str] = None
    ):
        """
        Delete all documents for a project (or specific document type)

        Args:
            project_id: ID of the project
            document_type: Optional specific document type to delete
        """
        try:
            where_filter = {"project_id": str(project_id)}
            if document_type:
                where_filter["document_type"] = document_type

            self.project_documents.delete(where=where_filter)

            logger.info(f"Deleted documents for project {project_id}" +
                       (f" (type: {document_type})" if document_type else ""))

        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            raise

    # ========== HISTORICAL PROJECTS OPERATIONS ==========

    def store_historical_project(
        self,
        project_id: int,
        project_data: Dict[str, Any]
    ) -> str:
        """
        Store complete project metadata for historical comparison

        Args:
            project_id: ID of the project
            project_data: Complete project data (metadata, metrics, outcomes)

        Returns:
            Document ID
        """
        try:
            # Create searchable text representation
            project_text = self._project_to_text(project_data)

            # Document ID
            doc_id = f"project-{project_id}-{datetime.now().isoformat()}"

            # Store in collection
            self.historical_projects.add(
                documents=[project_text],
                metadatas=[{
                    "project_id": str(project_id),
                    "project_name": project_data.get("name", ""),
                    "project_type": project_data.get("type", ""),
                    "status": project_data.get("status", ""),
                    "created_at": datetime.now().isoformat(),
                    **project_data.get("metadata", {})
                }],
                ids=[doc_id]
            )

            logger.info(f"Stored historical project {project_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to store historical project: {str(e)}")
            raise

    def find_similar_projects(
        self,
        project_id: Optional[int] = None,
        project_description: Optional[str] = None,
        project_type: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Find similar historical projects based on description or existing project

        Args:
            project_id: ID of existing project (will use its data for similarity)
            project_description: Text description to find similar projects
            project_type: Filter by project type (greenfield/brownfield)
            top_k: Number of similar projects to return

        Returns:
            Dict with similar projects and similarity scores
        """
        try:
            # Determine query text
            if project_id:
                # Get project data from collection
                result = self.historical_projects.get(
                    where={"project_id": str(project_id)}
                )
                if not result["documents"]:
                    raise ValueError(f"Project {project_id} not found in historical data")
                query_text = result["documents"][0]
            elif project_description:
                query_text = project_description
            else:
                raise ValueError("Either project_id or project_description must be provided")

            # Build where filter
            where_filter = None
            if project_type:
                where_filter = {"project_type": project_type}

            # Query similar projects
            results = self.historical_projects.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where_filter
            )

            return {
                "similar_projects": [
                    {
                        "metadata": metadata,
                        "similarity": 1 - distance,  # Convert distance to similarity
                        "content": content
                    }
                    for metadata, distance, content in zip(
                        results["metadatas"][0],
                        results["distances"][0],
                        results["documents"][0]
                    )
                ] if results["documents"] else [],
                "count": len(results["documents"][0]) if results["documents"] else 0
            }

        except Exception as e:
            logger.error(f"Failed to find similar projects: {str(e)}")
            raise

    # ========== CODE ANALYSIS OPERATIONS ==========

    def store_quality_scan(
        self,
        project_id: int,
        scan_results: Dict[str, Any],
        scan_id: Optional[str] = None
    ) -> str:
        """
        Store quality scan results

        Args:
            project_id: ID of the project
            scan_results: Complete scan results (scores, violations, recommendations)
            scan_id: Optional custom scan ID

        Returns:
            Document ID
        """
        try:
            # Create scan ID if not provided
            if not scan_id:
                scan_id = f"scan-{project_id}-{datetime.now().isoformat()}"

            # Create searchable text from scan results
            scan_text = self._scan_to_text(scan_results)

            # Store in collection
            self.code_analysis.add(
                documents=[scan_text],
                metadatas=[{
                    "project_id": str(project_id),
                    "scan_id": scan_id,
                    "overall_score": scan_results.get("overall_score", 0),
                    "total_violations": scan_results.get("total_violations", 0),
                    "scanned_at": datetime.now().isoformat()
                }],
                ids=[scan_id]
            )

            logger.info(f"Stored quality scan for project {project_id}")
            return scan_id

        except Exception as e:
            logger.error(f"Failed to store quality scan: {str(e)}")
            raise

    def get_quality_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a quality scan by ID

        Args:
            scan_id: ID of the scan

        Returns:
            Scan data or None if not found
        """
        try:
            result = self.code_analysis.get(ids=[scan_id])

            if not result["documents"]:
                return None

            return {
                "scan_id": scan_id,
                "content": result["documents"][0],
                "metadata": result["metadatas"][0]
            }

        except Exception as e:
            logger.error(f"Failed to get quality scan: {str(e)}")
            raise

    # ========== BMAD SESSIONS OPERATIONS ==========

    def store_bmad_session(
        self,
        project_id: int,
        session_type: str,  # 'green-paper' or 'brown-paper'
        session_data: Dict[str, Any],
        session_content: str
    ) -> str:
        """
        Store BMAD session (green-paper or brown-paper)

        Args:
            project_id: ID of the project
            session_type: Type of session (green-paper or brown-paper)
            session_data: Structured session data
            session_content: Full markdown content of session

        Returns:
            Document ID
        """
        try:
            # Document ID
            doc_id = f"{session_type}-{project_id}-{datetime.now().isoformat()}"

            # Store in collection
            self.bmad_sessions.add(
                documents=[session_content],
                metadatas=[{
                    "project_id": str(project_id),
                    "session_type": session_type,
                    "created_at": datetime.now().isoformat(),
                    **session_data.get("metadata", {})
                }],
                ids=[doc_id]
            )

            logger.info(f"Stored BMAD {session_type} session for project {project_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to store BMAD session: {str(e)}")
            raise

    def get_bmad_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a BMAD session by ID

        Args:
            session_id: ID of the session

        Returns:
            Session data or None if not found
        """
        try:
            result = self.bmad_sessions.get(ids=[session_id])

            if not result["documents"]:
                return None

            return {
                "session_id": session_id,
                "content": result["documents"][0],
                "metadata": result["metadatas"][0]
            }

        except Exception as e:
            logger.error(f"Failed to get BMAD session: {str(e)}")
            raise

    # ========== GENERIC COLLECTION OPERATIONS ==========

    async def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """
        Add documents to a specific collection

        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: List of document IDs
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to {collection_name}")
        except Exception as e:
            logger.error(f"Failed to add documents to {collection_name}: {str(e)}")
            raise

    async def query(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query a specific collection

        Args:
            collection_name: Name of the collection
            query_texts: List of query texts
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Query results with ids, documents, metadatas, distances
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query {collection_name}: {str(e)}")
            raise

    # ========== UTILITY METHODS ==========

    def _chunk_document(
        self,
        content: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ) -> List[str]:
        """
        Split document into overlapping chunks

        Args:
            content: Document content
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        content_length = len(content)

        while start < content_length:
            # Get chunk
            end = min(start + chunk_size, content_length)
            chunk = content[start:end]

            # Try to break at sentence boundary
            if end < content_length:
                # Look for sentence end markers
                for marker in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    last_marker = chunk.rfind(marker)
                    if last_marker > chunk_size * 0.5:  # At least halfway through
                        chunk = chunk[:last_marker + len(marker)]
                        end = start + len(chunk)
                        break

            chunks.append(chunk.strip())

            # Move to next chunk with overlap
            start = end - chunk_overlap if end < content_length else content_length

        return chunks

    def _project_to_text(self, project_data: Dict[str, Any]) -> str:
        """Convert project data to searchable text"""
        text_parts = [
            f"Project: {project_data.get('name', '')}",
            f"Type: {project_data.get('type', '')}",
            f"Description: {project_data.get('description', '')}",
            f"Tech Stack: {', '.join(project_data.get('tech_stack', []))}",
            f"Team Size: {project_data.get('team_size', 'unknown')}",
            f"Duration: {project_data.get('duration_days', 'unknown')} days",
            f"Complexity: {project_data.get('complexity', 'unknown')}"
        ]
        return "\n".join(text_parts)

    def _scan_to_text(self, scan_results: Dict[str, Any]) -> str:
        """Convert scan results to searchable text"""
        text_parts = [
            f"Overall Score: {scan_results.get('overall_score', 0)}%",
            f"Total Violations: {scan_results.get('total_violations', 0)}",
            f"Security Score: {scan_results.get('security_score', 0)}%",
            f"Quality Score: {scan_results.get('quality_score', 0)}%",
            f"Test Coverage: {scan_results.get('test_coverage', 0)}%",
            f"Technical Debt: {scan_results.get('tech_debt_days', 0)} days",
        ]

        # Add top violations
        violations = scan_results.get('violations', [])
        if violations:
            text_parts.append("Top Violations:")
            for v in violations[:10]:
                text_parts.append(f"- {v.get('type', '')}: {v.get('description', '')}")

        return "\n".join(text_parts)

    def health_check(self) -> bool:
        """Check if ChromaDB is healthy"""
        try:
            self.client.heartbeat()
            return True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {str(e)}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get ChromaDB statistics"""
        try:
            return {
                "collections": {
                    "project_documents": self.project_documents.count(),
                    "historical_projects": self.historical_projects.count(),
                    "code_analysis": self.code_analysis.count(),
                    "bmad_sessions": self.bmad_sessions.count(),
                    "project_constitutions": self.project_constitutions.count()
                },
                "total_documents": sum([
                    self.project_documents.count(),
                    self.historical_projects.count(),
                    self.code_analysis.count(),
                    self.bmad_sessions.count(),
                    self.project_constitutions.count()
                ]),
                "healthy": self.health_check()
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {"error": str(e)}


# Singleton instance
_chroma_service = None


def get_chroma_service() -> ChromaService:
    """Get or create ChromaDB service instance"""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service
