import logging
import uuid
import json
import os
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path
from src.providers.vector_store import VectorStore
from src.providers.embeddings_provider import EmbeddingsProvider

logger = logging.getLogger("hugdata-ai")

@dataclass
class SqlPair:
    """Represents a SQL question-answer pair"""
    id: str
    sql: str
    question: str
    metadata: Optional[Dict[str, Any]] = None

class SqlPairsIndexingPipeline:
    """Pipeline for indexing SQL question-answer pairs into vector store"""

    def __init__(
        self,
        embeddings_provider: EmbeddingsProvider,
        vector_store: VectorStore,
        sql_pairs_path: Optional[str] = None
    ):
        self.embeddings_provider = embeddings_provider
        self.vector_store = vector_store
        self.sql_pairs_path = sql_pairs_path or "sql_pairs.json"
        self.external_pairs = self._load_external_sql_pairs()

    def _load_external_sql_pairs(self) -> Dict[str, Any]:
        """Load external SQL pairs from file if available"""
        if not self.sql_pairs_path or not os.path.exists(self.sql_pairs_path):
            logger.info(f"SQL pairs file not found: {self.sql_pairs_path}")
            return {}

        try:
            with open(self.sql_pairs_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                logger.info(f"Loaded external SQL pairs from {self.sql_pairs_path}")
                return data
        except Exception as e:
            logger.error(f"Error loading SQL pairs file: {e}")
            return {}

    async def index_sql_pairs(
        self,
        mdl_str: str,
        project_id: str = "",
        external_pairs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Index SQL pairs based on MDL boilerplates

        Args:
            mdl_str: JSON string containing the model definition
            project_id: Project identifier for scoping
            external_pairs: Additional external SQL pairs

        Returns:
            Dict containing indexing results
        """
        try:
            # 1. Parse MDL and extract boilerplates
            boilerplates = self._extract_boilerplates(mdl_str)

            if not boilerplates:
                logger.info(f"No boilerplates found in MDL for project {project_id}")
                return {
                    "indexed_count": 0,
                    "project_id": project_id,
                    "status": "success",
                    "message": "No boilerplates found to match SQL pairs"
                }

            # 2. Combine external pairs
            combined_pairs = {
                **self.external_pairs,
                **(external_pairs or {})
            }

            # 3. Extract SQL pairs for matching boilerplates
            sql_pairs = self._extract_sql_pairs(boilerplates, combined_pairs)

            if not sql_pairs:
                logger.info(f"No matching SQL pairs found for project {project_id}")
                return {
                    "indexed_count": 0,
                    "project_id": project_id,
                    "status": "success",
                    "message": "No matching SQL pairs found for boilerplates",
                    "boilerplates": list(boilerplates)
                }

            # 4. Clean existing pairs for this project
            await self._clean_existing_pairs(project_id)

            # 5. Convert to documents for embedding
            documents = self._create_documents_from_pairs(sql_pairs, project_id)

            # 6. Generate embeddings
            embedded_documents = await self._generate_embeddings(documents)

            # 7. Store in vector store
            collection_name = f"sql_pairs_{project_id}" if project_id else "sql_pairs"
            await self._store_documents(embedded_documents, collection_name)

            logger.info(f"Successfully indexed {len(sql_pairs)} SQL pairs for project {project_id}")

            return {
                "indexed_count": len(sql_pairs),
                "project_id": project_id,
                "status": "success",
                "collection": collection_name,
                "boilerplates": list(boilerplates),
                "pairs": [pair.__dict__ for pair in sql_pairs]
            }

        except Exception as e:
            logger.error(f"SQL pairs indexing failed: {str(e)}")
            raise Exception(f"SQL pairs indexing failed: {str(e)}")

    def _extract_boilerplates(self, mdl_str: str) -> Set[str]:
        """Extract boilerplates from MDL models"""
        try:
            mdl = json.loads(mdl_str)
            boilerplates = set()

            for model in mdl.get("models", []):
                properties = model.get("properties", {})
                boilerplate = properties.get("boilerplate")
                if boilerplate:
                    boilerplates.add(boilerplate.lower())

            return boilerplates

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in MDL string: {str(e)}")

    def _extract_sql_pairs(
        self,
        boilerplates: Set[str],
        external_pairs: Dict[str, Any]
    ) -> List[SqlPair]:
        """Extract SQL pairs for matching boilerplates"""
        sql_pairs = []

        for boilerplate in boilerplates:
            if boilerplate in external_pairs:
                pairs_data = external_pairs[boilerplate]

                if isinstance(pairs_data, list):
                    for pair_data in pairs_data:
                        if isinstance(pair_data, dict):
                            sql_pair = SqlPair(
                                id=pair_data.get("id", str(uuid.uuid4())),
                                question=pair_data.get("question", ""),
                                sql=pair_data.get("sql", ""),
                                metadata={
                                    "boilerplate": boilerplate,
                                    "source": "external_pairs"
                                }
                            )
                            sql_pairs.append(sql_pair)

        return sql_pairs

    async def _clean_existing_pairs(self, project_id: str) -> None:
        """Clean existing SQL pairs for the project"""
        try:
            collection_name = f"sql_pairs_{project_id}" if project_id else "sql_pairs"

            # Check if collection exists and delete it
            if await self.vector_store.collection_exists(collection_name):
                await self.vector_store.delete_collection(collection_name)
                logger.info(f"Cleaned existing SQL pairs for project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to clean existing SQL pairs: {str(e)}")

    def _create_documents_from_pairs(
        self,
        sql_pairs: List[SqlPair],
        project_id: str = ""
    ) -> List[Dict[str, Any]]:
        """Create documents from SQL pairs for embedding"""
        documents = []

        for pair in sql_pairs:
            # Create content for embedding - focus on the question
            content = pair.question

            # Create metadata
            metadata = {
                "sql_pair_id": pair.id,
                "sql": pair.sql,
                "question": pair.question,
                "type": "SQL_PAIR"
            }

            if project_id:
                metadata["project_id"] = project_id

            if pair.metadata:
                metadata.update(pair.metadata)

            document = {
                "id": str(uuid.uuid4()),
                "content": content,
                "metadata": metadata
            }

            documents.append(document)

        return documents

    async def _generate_embeddings(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for documents"""
        try:
            # Extract content for embedding
            contents = [doc["content"] for doc in documents]

            # Generate embeddings
            embeddings = await self.embeddings_provider.embed_documents(contents)

            # Add embeddings to documents
            embedded_documents = []
            for i, doc in enumerate(documents):
                embedded_doc = doc.copy()
                embedded_doc["embedding"] = embeddings[i]
                embedded_documents.append(embedded_doc)

            return embedded_documents

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise

    async def _store_documents(
        self,
        documents: List[Dict[str, Any]],
        collection_name: str
    ) -> None:
        """Store documents in vector store"""
        try:
            # Create collection if it doesn't exist
            if not await self.vector_store.collection_exists(collection_name):
                await self.vector_store.create_collection(collection_name)

            # Store documents
            await self.vector_store.add_documents(collection_name, documents)

            logger.info(f"Stored {len(documents)} SQL pair documents in collection {collection_name}")

        except Exception as e:
            logger.error(f"Failed to store documents: {str(e)}")
            raise

    async def clean_sql_pairs(
        self,
        project_id: Optional[str] = None,
        sql_pair_ids: List[str] = None,
        delete_all: bool = False
    ) -> Dict[str, Any]:
        """
        Clean SQL pairs from vector store

        Args:
            project_id: Project identifier for scoping
            sql_pair_ids: Specific SQL pair IDs to delete
            delete_all: Whether to delete all pairs

        Returns:
            Dict containing cleanup results
        """
        try:
            collection_name = f"sql_pairs_{project_id}" if project_id else "sql_pairs"

            if not await self.vector_store.collection_exists(collection_name):
                return {
                    "deleted_count": 0,
                    "status": "success",
                    "message": "Collection does not exist"
                }

            if delete_all:
                # Delete entire collection
                await self.vector_store.delete_collection(collection_name)
                return {
                    "deleted_count": "all",
                    "status": "success",
                    "message": "Deleted entire collection"
                }

            if sql_pair_ids:
                # Delete specific pairs
                deleted_count = 0
                for pair_id in sql_pair_ids:
                    filter_criteria = {"sql_pair_id": pair_id}
                    if project_id:
                        filter_criteria["project_id"] = project_id

                    count = await self.vector_store.delete_documents(
                        collection_name,
                        filter_criteria
                    )
                    deleted_count += count

                return {
                    "deleted_count": deleted_count,
                    "status": "success",
                    "message": f"Deleted {deleted_count} SQL pairs"
                }

            return {
                "deleted_count": 0,
                "status": "success",
                "message": "No deletion criteria specified"
            }

        except Exception as e:
            logger.error(f"Failed to clean SQL pairs: {str(e)}")
            return {
                "deleted_count": 0,
                "status": "error",
                "message": str(e)
            }

    async def search_sql_pairs(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant SQL pairs

        Args:
            query: Search query
            project_id: Project identifier for scoping
            limit: Maximum number of results

        Returns:
            List of relevant SQL pairs
        """
        try:
            collection_name = f"sql_pairs_{project_id}" if project_id else "sql_pairs"

            # Check if collection exists
            if not await self.vector_store.collection_exists(collection_name):
                logger.warning(f"Collection {collection_name} does not exist")
                return []

            # Perform similarity search
            results = await self.vector_store.similarity_search(
                query=query,
                collection=collection_name,
                limit=limit
            )

            return results

        except Exception as e:
            logger.error(f"SQL pairs search failed: {str(e)}")
            return []

    async def get_sql_pairs_stats(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about indexed SQL pairs

        Args:
            project_id: Project identifier for scoping

        Returns:
            Dict containing statistics
        """
        try:
            collection_name = f"sql_pairs_{project_id}" if project_id else "sql_pairs"

            # Check if collection exists
            if not await self.vector_store.collection_exists(collection_name):
                return {
                    "total_pairs": 0,
                    "collection_exists": False,
                    "project_id": project_id
                }

            # Get collection statistics
            stats = await self.vector_store.get_collection_stats(collection_name)

            return {
                "total_pairs": stats.get("document_count", 0),
                "collection_exists": True,
                "project_id": project_id,
                "collection_name": collection_name,
                "last_updated": stats.get("last_updated")
            }

        except Exception as e:
            logger.error(f"Failed to get SQL pairs stats: {str(e)}")
            return {
                "total_pairs": 0,
                "collection_exists": False,
                "project_id": project_id,
                "error": str(e)
            }

    def add_external_pairs(self, pairs_data: Dict[str, Any]) -> None:
        """Add external pairs to the pipeline"""
        self.external_pairs.update(pairs_data)

    def set_sql_pairs_path(self, path: str) -> None:
        """Set the SQL pairs file path and reload"""
        self.sql_pairs_path = path
        self.external_pairs = self._load_external_sql_pairs()
