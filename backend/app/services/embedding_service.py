"""
Embedding Service - Local Sentence Transformers for Text Embeddings

This service provides text embedding capabilities using local sentence-transformers models.
No cloud dependencies - runs completely offline.

Models:
- all-MiniLM-L6-v2: 384 dimensions, fast, good quality (default)
- multi-qa-MiniLM-L6-cos-v1: 384 dimensions, optimized for Q&A
- paraphrase-MiniLM-L6-v2: 384 dimensions, best for paraphrasing

Features:
- Batch embedding for efficiency
- Caching for frequently embedded texts
- Model warm-up for faster first requests
- Token tracking and statistics
"""

import logging
from typing import List, Dict, Any, Optional
import hashlib
from functools import lru_cache
import numpy as np

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Local embedding service using sentence-transformers"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service with specified model

        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model_name = model_name
        self.model = None
        self._embedding_cache = {}
        self._stats = {
            "total_embeddings": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_tokens": 0
        }

        # Load model
        self._load_model()

        logger.info(f"Embedding service initialized with model: {model_name}")

    def _load_model(self):
        """Load the sentence-transformers model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model {self.model_name} loaded successfully")

            # Warm up model with dummy text
            self.model.encode(["warm up text"], convert_to_numpy=True)
            logger.info("Model warm-up complete")

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {str(e)}")
            raise

    def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed
            use_cache: Whether to use cache for this embedding

        Returns:
            Embedding vector as list of floats
        """
        try:
            # Check cache
            if use_cache:
                cache_key = self._get_cache_key(text)
                if cache_key in self._embedding_cache:
                    self._stats["cache_hits"] += 1
                    return self._embedding_cache[cache_key]

            # Generate embedding
            embedding = self.model.encode(
                [text],
                convert_to_numpy=True,
                show_progress_bar=False
            )[0]

            # Convert to list and cache
            embedding_list = embedding.tolist()

            if use_cache:
                cache_key = self._get_cache_key(text)
                self._embedding_cache[cache_key] = embedding_list
                self._stats["cache_misses"] += 1

            # Update stats
            self._stats["total_embeddings"] += 1
            self._stats["total_tokens"] += len(text.split())

            return embedding_list

        except Exception as e:
            logger.error(f"Failed to embed text: {str(e)}")
            raise

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            use_cache: Whether to use cache

        Returns:
            List of embedding vectors
        """
        try:
            embeddings = []
            uncached_texts = []
            uncached_indices = []

            # Check cache first
            for i, text in enumerate(texts):
                if use_cache:
                    cache_key = self._get_cache_key(text)
                    if cache_key in self._embedding_cache:
                        embeddings.append(self._embedding_cache[cache_key])
                        self._stats["cache_hits"] += 1
                        continue

                # Not in cache
                uncached_texts.append(text)
                uncached_indices.append(i)

            # Generate embeddings for uncached texts
            if uncached_texts:
                new_embeddings = self.model.encode(
                    uncached_texts,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    show_progress_bar=len(uncached_texts) > 100
                )

                # Cache and add to results
                for i, (text, embedding) in enumerate(zip(uncached_texts, new_embeddings)):
                    embedding_list = embedding.tolist()

                    if use_cache:
                        cache_key = self._get_cache_key(text)
                        self._embedding_cache[cache_key] = embedding_list
                        self._stats["cache_misses"] += 1

                    # Insert at correct position
                    original_index = uncached_indices[i]
                    embeddings.insert(original_index, embedding_list)

                    # Update stats
                    self._stats["total_embeddings"] += 1
                    self._stats["total_tokens"] += len(text.split())

            return embeddings

        except Exception as e:
            logger.error(f"Failed to embed batch: {str(e)}")
            raise

    def similarity(
        self,
        text1: str,
        text2: str,
        metric: str = "cosine"
    ) -> float:
        """
        Calculate similarity between two texts

        Args:
            text1: First text
            text2: Second text
            metric: Similarity metric (cosine, euclidean, dot)

        Returns:
            Similarity score (higher = more similar for cosine/dot)
        """
        try:
            # Get embeddings
            emb1 = np.array(self.embed_text(text1))
            emb2 = np.array(self.embed_text(text2))

            # Calculate similarity
            if metric == "cosine":
                similarity = np.dot(emb1, emb2) / (
                    np.linalg.norm(emb1) * np.linalg.norm(emb2)
                )
            elif metric == "euclidean":
                similarity = -np.linalg.norm(emb1 - emb2)  # Negative for "higher = better"
            elif metric == "dot":
                similarity = np.dot(emb1, emb2)
            else:
                raise ValueError(f"Unknown metric: {metric}")

            return float(similarity)

        except Exception as e:
            logger.error(f"Failed to calculate similarity: {str(e)}")
            raise

    def find_most_similar(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find most similar texts from a list of candidates

        Args:
            query: Query text
            candidates: List of candidate texts
            top_k: Number of most similar to return

        Returns:
            List of dicts with {text, similarity, index}
        """
        try:
            # Get embeddings
            query_emb = np.array(self.embed_text(query))
            candidate_embs = np.array(self.embed_batch(candidates))

            # Calculate cosine similarities
            similarities = np.dot(candidate_embs, query_emb) / (
                np.linalg.norm(candidate_embs, axis=1) * np.linalg.norm(query_emb)
            )

            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]

            # Build results
            results = [
                {
                    "text": candidates[i],
                    "similarity": float(similarities[i]),
                    "index": int(i)
                }
                for i in top_indices
            ]

            return results

        except Exception as e:
            logger.error(f"Failed to find most similar: {str(e)}")
            raise

    def clear_cache(self):
        """Clear the embedding cache"""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """Get embedding service statistics"""
        cache_hit_rate = 0
        if self._stats["cache_hits"] + self._stats["cache_misses"] > 0:
            cache_hit_rate = (
                self._stats["cache_hits"] /
                (self._stats["cache_hits"] + self._stats["cache_misses"]) * 100
            )

        return {
            **self._stats,
            "cache_size": len(self._embedding_cache),
            "cache_hit_rate": f"{cache_hit_rate:.2f}%",
            "model_name": self.model_name,
            "embedding_dimension": self.model.get_sentence_embedding_dimension()
        }

    @staticmethod
    def _get_cache_key(text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()

    @staticmethod
    @lru_cache(maxsize=1000)
    def _normalize_text(text: str) -> str:
        """Normalize text for better embeddings"""
        # Remove extra whitespace
        text = " ".join(text.split())
        return text.strip()


# Singleton instance
_embedding_service = None


def get_embedding_service(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingService:
    """Get or create embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_name)
    return _embedding_service
