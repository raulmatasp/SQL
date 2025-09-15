import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from src.providers.llm_provider import LLMProvider
from src.providers.vector_store import VectorStore
from src.providers.embeddings_provider import EmbeddingsProvider

logger = logging.getLogger("hugdata-ai")

class BaseService(ABC):
    """Base class for all services"""

    def __init__(
        self,
        llm_provider: LLMProvider,
        vector_store: VectorStore,
        embeddings_provider: EmbeddingsProvider
    ):
        self.llm_provider = llm_provider
        self.vector_store = vector_store
        self.embeddings_provider = embeddings_provider

class ServiceContainer:
    """Dependency injection container for services"""

    def __init__(
        self,
        llm_provider: LLMProvider,
        vector_store: VectorStore,
        embeddings_provider: EmbeddingsProvider
    ):
        self.llm_provider = llm_provider
        self.vector_store = vector_store
        self.embeddings_provider = embeddings_provider

        # Initialize services
        self._sql_correction_service = None
        self._relationship_recommendation_service = None

    def get_sql_correction_service(self):
        """Get SQL correction service (lazy initialization)"""
        if self._sql_correction_service is None:
            from .sql_correction_service import SqlCorrectionService
            self._sql_correction_service = SqlCorrectionService(
                self.llm_provider,
                self.vector_store,
                self.embeddings_provider
            )
        return self._sql_correction_service

    def get_relationship_recommendation_service(self):
        """Get relationship recommendation service (lazy initialization)"""
        if self._relationship_recommendation_service is None:
            from .relationship_recommendation_service import RelationshipRecommendationService
            self._relationship_recommendation_service = RelationshipRecommendationService(
                self.llm_provider,
                self.vector_store,
                self.embeddings_provider
            )
        return self._relationship_recommendation_service

# Global service container instance
_service_container: Optional[ServiceContainer] = None

def initialize_service_container(
    llm_provider: LLMProvider,
    vector_store: VectorStore,
    embeddings_provider: EmbeddingsProvider
) -> ServiceContainer:
    """Initialize the global service container"""
    global _service_container
    _service_container = ServiceContainer(
        llm_provider,
        vector_store,
        embeddings_provider
    )
    return _service_container

def get_service_container() -> ServiceContainer:
    """Get the global service container"""
    global _service_container
    if _service_container is None:
        raise RuntimeError("Service container not initialized")
    return _service_container