from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("hugdata-ai")


class VectorStore(ABC):
    """Abstract base class for vector stores"""

    @abstractmethod
    async def similarity_search(
        self,
        query: str,
        collection_name: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search by query text; may require embeddings provider."""
        raise NotImplementedError

    @abstractmethod
    async def add_documents(self, collection_name: str, documents: List[Dict[str, Any]]) -> bool:
        """Bulk add documents (expects precomputed embeddings in `embedding`)."""
        raise NotImplementedError

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def count_documents(self, collection_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        raise NotImplementedError

    # Extended management API used by indexing pipelines
    @abstractmethod
    async def collection_exists(self, collection_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def create_collection(self, collection_name: str, vector_size: int = 1536, distance: str = "Cosine") -> bool:
        raise NotImplementedError

    @abstractmethod
    async def delete_documents(self, collection_name: str, filters: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        raise NotImplementedError


class NotConfiguredVectorStore(VectorStore):
    """Vector store that raises clear configuration errors when used."""

    def __init__(self, reason: str):
        self.reason = reason

    def _err(self) -> None:
        raise RuntimeError(
            f"Vector store is not configured: {self.reason}. "
            f"Set QDRANT_URL (and optionally QDRANT_API_KEY) and ensure Qdrant is reachable."
        )

    async def similarity_search(self, query: str, collection_name: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        self._err()

    async def add_documents(self, collection_name: str, documents: List[Dict[str, Any]]) -> bool:
        self._err()

    async def delete_collection(self, collection_name: str) -> bool:
        self._err()

    async def count_documents(self, collection_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        self._err()

    async def collection_exists(self, collection_name: str) -> bool:
        self._err()

    async def create_collection(self, collection_name: str, vector_size: int = 1536, distance: str = "Cosine") -> bool:
        self._err()

    async def delete_documents(self, collection_name: str, filters: Dict[str, Any]) -> int:
        self._err()

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        self._err()


class QdrantProvider(VectorStore):
    """Qdrant-backed Vector Store Provider"""

    def __init__(self, url: str, api_key: Optional[str] = None, embeddings_provider: Optional[Any] = None, collection_vector_size: int = 1536):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import Distance, VectorParams
        except Exception as e:
            raise RuntimeError(
                "qdrant-client is required. Install with: pip install qdrant-client"
            ) from e

        self._Distance = Distance
        self._VectorParams = VectorParams
        self.client = QdrantClient(url=url, api_key=api_key)  # supports http(s) and grpc
        self.embeddings_provider = embeddings_provider
        self.default_vector_size = collection_vector_size

    async def collection_exists(self, collection_name: str) -> bool:
        try:
            info = self.client.get_collection(collection_name)
            return info is not None
        except Exception:
            return False

    async def create_collection(self, collection_name: str, vector_size: int = 1536, distance: str = "Cosine") -> bool:
        try:
            if await self.collection_exists(collection_name):
                return True
            dist = getattr(self._Distance, distance.upper(), self._Distance.COSINE)
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=self._VectorParams(size=vector_size or self.default_vector_size, distance=dist),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise

    async def add_documents(self, collection_name: str, documents: List[Dict[str, Any]]) -> bool:
        try:
            # Each document should have: id (optional), embedding (list[float]), metadata (dict), content (str)
            points = []
            for doc in documents:
                embedding = doc.get("embedding")
                if embedding is None:
                    # Try to compute from content if embeddings provider is available
                    if self.embeddings_provider and doc.get("content"):
                        emb = await self.embeddings_provider.embed_documents([doc["content"]])
                        embedding = emb[0]
                    else:
                        raise ValueError("Document missing 'embedding' and no embeddings provider configured")

                payload = {
                    **{k: v for k, v in doc.items() if k not in ["embedding"]},
                    **doc.get("metadata", {}),
                }
                point_id = doc.get("id")
                points.append({"id": point_id, "vector": embedding, "payload": payload})

            self.client.upsert(collection_name=collection_name, points=points)
            return True
        except Exception as e:
            logger.error(f"Failed to add documents to {collection_name}: {e}")
            raise

    async def similarity_search(
        self,
        query: str,
        collection_name: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        try:
            if not self.embeddings_provider:
                raise RuntimeError("Embeddings provider is required for similarity_search but not configured")

            query_vector = await self.embeddings_provider.embed_query(query)

            # Build Qdrant filter
            qdrant_filter = None
            if filters:
                from qdrant_client.http.models import Filter, FieldCondition, MatchValue
                conditions = []
                for k, v in filters.items():
                    conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))
                qdrant_filter = Filter(must=conditions)

            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=qdrant_filter,
                with_payload=True,
            )

            normalized = []
            for r in results:
                payload = r.payload or {}
                # unify metadata shape
                normalized.append({
                    **payload,
                    "score": r.score,
                })
            return normalized
        except Exception as e:
            logger.error(f"Similarity search failed on {collection_name}: {e}")
            raise

    async def delete_collection(self, collection_name: str) -> bool:
        try:
            self.client.delete_collection(collection_name)
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            raise

    async def count_documents(self, collection_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        try:
            from qdrant_client.http.models import CountRequest, Filter, FieldCondition, MatchValue
            qdrant_filter = None
            if filters:
                conditions = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()]
                qdrant_filter = Filter(must=conditions)
            res = self.client.count(collection_name=collection_name, count_request=CountRequest(exact=True, filter=qdrant_filter))
            return int(res.count or 0)
        except Exception as e:
            logger.error(f"Failed to count documents in {collection_name}: {e}")
            return 0

    async def delete_documents(self, collection_name: str, filters: Dict[str, Any]) -> int:
        try:
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            qdrant_filter = Filter(must=[FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()])
            res = self.client.delete(collection_name=collection_name, points_selector=qdrant_filter)
            # Qdrant delete returns an operation result; we cannot easily get count. Return -1 to indicate unknown.
            return -1
        except Exception as e:
            logger.error(f"Failed to delete documents in {collection_name}: {e}")
            return 0

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        try:
            info = self.client.get_collection(collection_name)
            # Try to fetch count
            count = await self.count_documents(collection_name)
            return {
                "document_count": count,
                "vectors_count": getattr(info, "vectors_count", None),
                "status": getattr(info, "status", None),
                "last_updated": None,
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            return {"document_count": 0}


class MockVectorStore(VectorStore):
    """Mock Vector Store for testing only"""

    def __init__(self):
        self.storage: Dict[str, List[Dict[str, Any]]] = {}

    async def similarity_search(self, query: str, collection_name: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Return deterministic canned results; ignore filters for simplicity
        return [
            {
                "table_name": "users",
                "column_name": "created_at",
                "column_type": "timestamp",
                "description": "User creation timestamp",
                "relevance": 0.9,
                "metadata": {"project_id": "test"}
            },
            {
                "table_name": "users",
                "column_name": "id",
                "column_type": "integer",
                "description": "Unique user identifier",
                "relevance": 0.8,
                "metadata": {"project_id": "test"}
            },
        ][:limit]

    async def add_documents(self, collection_name: str, documents: List[Dict[str, Any]]) -> bool:
        if collection_name not in self.storage:
            self.storage[collection_name] = []
        for doc in documents:
            if "metadata" not in doc:
                doc["metadata"] = {}
            self.storage[collection_name].append(doc)
        return True

    async def delete_collection(self, collection_name: str) -> bool:
        if collection_name in self.storage:
            del self.storage[collection_name]
        return True

    async def count_documents(self, collection_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        docs = self.storage.get(collection_name, [])
        if not filters:
            return len(docs)
        count = 0
        for doc in docs:
            metadata = doc.get("metadata", {})
            if all(metadata.get(k) == v for k, v in (filters or {}).items()):
                count += 1
        return count

    async def collection_exists(self, collection_name: str) -> bool:
        return collection_name in self.storage

    async def create_collection(self, collection_name: str, vector_size: int = 1536, distance: str = "Cosine") -> bool:
        if collection_name not in self.storage:
            self.storage[collection_name] = []
        return True

    async def delete_documents(self, collection_name: str, filters: Dict[str, Any]) -> int:
        docs = self.storage.get(collection_name, [])
        before = len(docs)
        remaining = []
        for doc in docs:
            metadata = doc.get("metadata", {})
            if all(metadata.get(k) == v for k, v in filters.items()):
                continue
            remaining.append(doc)
        self.storage[collection_name] = remaining
        return before - len(remaining)

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        return {
            "document_count": len(self.storage.get(collection_name, [])),
            "status": "mock",
        }
