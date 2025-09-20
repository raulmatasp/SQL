import logging
from abc import ABC, abstractmethod
from typing import List, Optional
import openai
import numpy as np

logger = logging.getLogger("hugdata-ai")

class EmbeddingsProvider(ABC):
    """Abstract base class for embeddings providers"""

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents

        Args:
            texts: List of text documents to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors

        Returns:
            Embedding dimension
        """
        pass


class NotConfiguredEmbeddingsProvider(EmbeddingsProvider):
    """Embeddings provider that raises clear configuration errors."""

    def __init__(self, reason: str = "Embeddings provider not configured"):
        self.reason = reason

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise RuntimeError(
            f"Embeddings provider is not configured: {self.reason}. "
            f"Provide OPENAI_API_KEY (for OpenAI) or configure HuggingFace model."
        )

    async def embed_query(self, text: str) -> List[float]:
        raise RuntimeError(
            f"Embeddings provider is not configured: {self.reason}. "
            f"Provide OPENAI_API_KEY (for OpenAI) or configure HuggingFace model."
        )

    def get_embedding_dimension(self) -> int:
        raise RuntimeError(
            f"Embeddings provider is not configured: {self.reason}."
        )

class OpenAIEmbeddingsProvider(EmbeddingsProvider):
    """OpenAI embeddings provider using text-embedding-ada-002"""

    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimension = 1536  # text-embedding-ada-002 dimension

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents"""
        try:
            # OpenAI API has a limit on batch size
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                response = await self.client.embeddings.create(
                    input=batch,
                    model=self.model
                )

                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)

            logger.info(f"Generated embeddings for {len(texts)} documents")
            return all_embeddings

        except Exception as e:
            logger.error(f"Failed to generate document embeddings: {str(e)}")
            raise

    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query"""
        try:
            response = await self.client.embeddings.create(
                input=[text],
                model=self.model
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Failed to generate query embedding: {str(e)}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension"""
        return self.dimension

class MockEmbeddingsProvider(EmbeddingsProvider):
    """Mock embeddings provider for testing"""

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for documents"""
        logger.info(f"Generating mock embeddings for {len(texts)} documents")

        embeddings = []
        for text in texts:
            # Generate deterministic but varied embeddings based on text hash
            hash_value = hash(text)
            np.random.seed(hash_value % (2**32))  # Ensure positive seed
            embedding = np.random.normal(0, 1, self.dimension).tolist()
            embeddings.append(embedding)

        return embeddings

    async def embed_query(self, text: str) -> List[float]:
        """Generate mock embedding for a query"""
        logger.info(f"Generating mock embedding for query: {text[:50]}...")

        # Generate deterministic embedding based on text hash
        hash_value = hash(text)
        np.random.seed(hash_value % (2**32))  # Ensure positive seed
        embedding = np.random.normal(0, 1, self.dimension).tolist()

        return embedding

    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension"""
        return self.dimension

class HuggingFaceEmbeddingsProvider(EmbeddingsProvider):
    """HuggingFace embeddings provider for local models"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Initialized HuggingFace embeddings with model: {model_name}")
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for HuggingFaceEmbeddingsProvider. "
                "Install it with: pip install sentence-transformers"
            )

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for documents using HuggingFace model"""
        try:
            # Run in thread pool since sentence-transformers is synchronous
            import asyncio
            loop = asyncio.get_event_loop()

            embeddings = await loop.run_in_executor(
                None,
                self.model.encode,
                texts
            )

            logger.info(f"Generated HuggingFace embeddings for {len(texts)} documents")
            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Failed to generate HuggingFace document embeddings: {str(e)}")
            raise

    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a query using HuggingFace model"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()

            embedding = await loop.run_in_executor(
                None,
                self.model.encode,
                [text]
            )

            return embedding[0].tolist()

        except Exception as e:
            logger.error(f"Failed to generate HuggingFace query embedding: {str(e)}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension"""
        return self.dimension
