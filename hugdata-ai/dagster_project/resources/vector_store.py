from dagster import ConfigurableResource
from typing import Dict, Any, List
import os

class VectorStoreResource(ConfigurableResource):
    """Vector store resource for semantic search (Qdrant)"""

    qdrant_url: str = ""
    qdrant_api_key: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = None

    @property
    def client(self):
        """Lazy load Qdrant client or raise if not configured"""
        if self._client is None:
            if not self.qdrant_url:
                raise RuntimeError("Qdrant not configured: set QDRANT_URL for Dagster VectorStoreResource")
            from qdrant_client import QdrantClient
            self._client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key or None)
        return self._client
    
    def index_schema(self, schema: Dict[str, Any], project_id: str) -> bool:
        """Index database schema for semantic search"""
        raise RuntimeError(
            "Indexing via Dagster VectorStoreResource is not implemented. "
            "Use the API service schema indexing pipeline instead."
        )
    
    def similarity_search(self, query: str, collection: str, limit: int = 10) -> List[Dict]:
        """Search for similar schema elements"""
        raise RuntimeError(
            "Similarity search in Dagster resource is not available without embeddings. "
            "Use the API service which injects an embeddings provider."
        )

vector_store_resource = VectorStoreResource(
    qdrant_url=os.getenv("QDRANT_URL", ""),
    qdrant_api_key=os.getenv("QDRANT_API_KEY", ""),
)
