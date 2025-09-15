import logging
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from src.providers.vector_store import VectorStore
from src.providers.embeddings_provider import EmbeddingsProvider

logger = logging.getLogger("hugdata-ai")

@dataclass
class TableDescription:
    """Represents a table description for indexing"""
    name: str
    description: str
    columns: str
    mdl_type: str  # MODEL, METRIC, VIEW

class TableDescriptionIndexingPipeline:
    """Pipeline for indexing table descriptions into vector store"""

    def __init__(self, embeddings_provider: EmbeddingsProvider, vector_store: VectorStore):
        self.embeddings_provider = embeddings_provider
        self.vector_store = vector_store

    async def index_table_descriptions(
        self,
        mdl_str: str,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Index table descriptions from MDL into vector store

        Args:
            mdl_str: JSON string containing the model definition
            project_id: Project identifier for scoping

        Returns:
            Dict containing indexing results
        """
        try:
            # 1. Validate and parse MDL
            mdl = self._validate_and_parse_mdl(mdl_str)

            # 2. Extract table descriptions
            table_descriptions = self._extract_table_descriptions(mdl)

            if not table_descriptions:
                logger.info(f"No table descriptions found for project {project_id}")
                return {
                    "indexed_count": 0,
                    "project_id": project_id,
                    "status": "success",
                    "message": "No table descriptions to index"
                }

            # 3. Clean existing descriptions for this project
            if project_id:
                await self._clean_existing_descriptions(project_id)

            # 4. Convert to documents for embedding
            documents = self._create_documents(table_descriptions, project_id)

            # 5. Generate embeddings
            embedded_documents = await self._generate_embeddings(documents)

            # 6. Store in vector store
            collection_name = f"table_descriptions_{project_id}" if project_id else "table_descriptions"
            await self._store_documents(embedded_documents, collection_name)

            logger.info(f"Successfully indexed {len(table_descriptions)} table descriptions for project {project_id}")

            return {
                "indexed_count": len(table_descriptions),
                "project_id": project_id,
                "status": "success",
                "collection": collection_name,
                "descriptions": [desc.__dict__ for desc in table_descriptions]
            }

        except Exception as e:
            logger.error(f"Table description indexing failed: {str(e)}")
            raise Exception(f"Table description indexing failed: {str(e)}")

    def _validate_and_parse_mdl(self, mdl_str: str) -> Dict[str, Any]:
        """Validate and parse the MDL string"""
        import json

        try:
            mdl = json.loads(mdl_str)
            if not isinstance(mdl, dict):
                raise ValueError("MDL must be a valid JSON object")
            return mdl
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in MDL string: {str(e)}")

    def _extract_table_descriptions(self, mdl: Dict[str, Any]) -> List[TableDescription]:
        """Extract table descriptions from MDL structure"""
        descriptions = []

        # Process models
        for model in mdl.get("models", []):
            description = self._extract_description_from_resource(model, "MODEL")
            if description:
                descriptions.append(description)

        # Process metrics
        for metric in mdl.get("metrics", []):
            description = self._extract_description_from_resource(metric, "METRIC")
            if description:
                descriptions.append(description)

        # Process views
        for view in mdl.get("views", []):
            description = self._extract_description_from_resource(view, "VIEW")
            if description:
                descriptions.append(description)

        return descriptions

    def _extract_description_from_resource(
        self,
        resource: Dict[str, Any],
        mdl_type: str
    ) -> Optional[TableDescription]:
        """Extract description from a single resource (model, metric, or view)"""
        name = resource.get("name")
        if not name:
            return None

        # Extract columns
        columns = []
        for column in resource.get("columns", []):
            if isinstance(column, dict):
                columns.append(column.get("name", ""))
            elif isinstance(column, str):
                columns.append(column)

        # Extract description from properties
        properties = resource.get("properties", {})
        description = properties.get("description", "")

        return TableDescription(
            name=name,
            description=description,
            columns=", ".join(filter(None, columns)),
            mdl_type=mdl_type
        )

    async def _clean_existing_descriptions(self, project_id: str) -> None:
        """Clean existing table descriptions for the project"""
        try:
            collection_name = f"table_descriptions_{project_id}"

            # Check if collection exists and delete it
            if await self.vector_store.collection_exists(collection_name):
                await self.vector_store.delete_collection(collection_name)
                logger.info(f"Cleaned existing table descriptions for project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to clean existing descriptions: {str(e)}")

    def _create_documents(
        self,
        table_descriptions: List[TableDescription],
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Create documents from table descriptions for embedding"""
        documents = []

        for desc in table_descriptions:
            # Create content for embedding
            content_parts = [
                f"Table: {desc.name}",
                f"Type: {desc.mdl_type}"
            ]

            if desc.description:
                content_parts.append(f"Description: {desc.description}")

            if desc.columns:
                content_parts.append(f"Columns: {desc.columns}")

            content = "\n".join(content_parts)

            # Create metadata
            metadata = {
                "type": "TABLE_DESCRIPTION",
                "name": desc.name,
                "mdl_type": desc.mdl_type,
                "table_name": desc.name
            }

            if project_id:
                metadata["project_id"] = project_id

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

            logger.info(f"Stored {len(documents)} documents in collection {collection_name}")

        except Exception as e:
            logger.error(f"Failed to store documents: {str(e)}")
            raise

    async def search_table_descriptions(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant table descriptions

        Args:
            query: Search query
            project_id: Project identifier for scoping
            limit: Maximum number of results

        Returns:
            List of relevant table descriptions
        """
        try:
            collection_name = f"table_descriptions_{project_id}" if project_id else "table_descriptions"

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
            logger.error(f"Table description search failed: {str(e)}")
            return []

    async def get_table_description_stats(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about indexed table descriptions

        Args:
            project_id: Project identifier for scoping

        Returns:
            Dict containing statistics
        """
        try:
            collection_name = f"table_descriptions_{project_id}" if project_id else "table_descriptions"

            # Check if collection exists
            if not await self.vector_store.collection_exists(collection_name):
                return {
                    "total_descriptions": 0,
                    "collection_exists": False,
                    "project_id": project_id
                }

            # Get collection statistics
            stats = await self.vector_store.get_collection_stats(collection_name)

            return {
                "total_descriptions": stats.get("document_count", 0),
                "collection_exists": True,
                "project_id": project_id,
                "collection_name": collection_name,
                "last_updated": stats.get("last_updated")
            }

        except Exception as e:
            logger.error(f"Failed to get table description stats: {str(e)}")
            return {
                "total_descriptions": 0,
                "collection_exists": False,
                "project_id": project_id,
                "error": str(e)
            }