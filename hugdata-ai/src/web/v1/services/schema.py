import logging
from typing import Dict, Any, List, Optional
from src.pipelines.indexing.schema_indexing import SchemaIndexingPipeline
from src.providers.vector_store import VectorStore

logger = logging.getLogger("hugdata-ai")


class SchemaService:
    """Service for managing database schema indexing and retrieval"""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.indexing_pipeline = SchemaIndexingPipeline(vector_store)

    async def index_schema(
        self,
        project_id: str,
        data_source_config: Dict[str, Any],
        schema_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Index database schema for semantic search"""

        logger.info(f"Starting schema indexing for project {project_id}")

        try:
            result = await self.indexing_pipeline.index_database_schema(
                project_id, data_source_config, schema_data
            )

            logger.info(
                f"Schema indexing completed for project {project_id}: "
                f"{result.get('total_documents', 0)} documents indexed"
            )

            return result

        except Exception as e:
            logger.error(f"Schema indexing failed for project {project_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "indexed_tables": 0,
                "indexed_columns": 0,
                "indexed_relationships": 0,
                "total_documents": 0
            }

    async def get_schema_summary(self, project_id: str) -> Dict[str, Any]:
        """Get summary of indexed schema information"""
        return await self.indexing_pipeline.get_schema_summary(project_id)

    async def update_schema_index(
        self,
        project_id: str,
        schema_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing schema index with changes"""
        return await self.indexing_pipeline.update_schema_index(
            project_id, schema_changes
        )

    async def delete_schema_index(self, project_id: str) -> Dict[str, Any]:
        """Delete schema index for a project"""
        try:
            collection_name = f"schema_{project_id}"
            await self.vector_store.delete_collection(collection_name)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Failed to delete schema index: {e}")
            return {"status": "error", "error": str(e)}

    async def search_schema(
        self,
        project_id: str,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search schema information for a project"""
        try:
            collection_name = f"schema_{project_id}"

            # Build search filters
            search_filters = {"project_id": project_id}
            if filters:
                search_filters.update(filters)

            # Perform semantic search (with optional filters)
            results = await self.vector_store.similarity_search(
                query=query,
                collection_name=collection_name,
                limit=limit,
                filters=search_filters,
            )

            return results

        except Exception as e:
            logger.error(f"Schema search failed: {e}")
            return []

    async def get_table_info(
        self,
        project_id: str,
        table_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific table"""
        try:
            # Search for table description
            table_docs = await self.search_schema(
                project_id,
                f"table {table_name}",
                limit=1,
                filters={"type": "table_description", "table_name": table_name}
            )

            if not table_docs:
                return None

            # Get column information
            column_docs = await self.search_schema(
                project_id,
                f"table {table_name} columns",
                limit=50,
                filters={"type": "table_columns", "table_name": table_name}
            )

            # Get relationships
            relationship_docs = await self.search_schema(
                project_id,
                f"table {table_name} relationships",
                limit=20,
                filters={"type": "relationship"}
            )

            # Filter relationships that involve this table
            relevant_relationships = []
            for rel in relationship_docs:
                # Accept both flattened payload and nested metadata
                meta = rel.get("metadata", {}) if isinstance(rel, dict) else {}
                from_table = rel.get("from_table") or meta.get("from_table")
                to_table = rel.get("to_table") or meta.get("to_table")
                if from_table == table_name or to_table == table_name:
                    relevant_relationships.append(rel)

            return {
                "table_info": table_docs[0],
                "columns": column_docs,
                "relationships": relevant_relationships
            }

        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return None

    async def get_column_info(
        self,
        project_id: str,
        table_name: str,
        column_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific column"""
        try:
            results = await self.search_schema(
                project_id,
                f"column {column_name} table {table_name}",
                limit=1,
                filters={
                    "type": "table_columns",
                    "table_name": table_name,
                    "column_name": column_name
                }
            )

            return results[0] if results else None

        except Exception as e:
            logger.error(f"Failed to get column info: {e}")
            return None

    async def suggest_joins(
        self,
        project_id: str,
        table_names: List[str]
    ) -> List[Dict[str, Any]]:
        """Suggest possible joins between tables"""
        try:
            join_suggestions = []

            # Search for relationships involving these tables
            for table in table_names:
                relationships = await self.search_schema(
                    project_id,
                    f"relationship {table}",
                    limit=20,
                    filters={"type": "relationship"}
                )

                for rel in relationships:
                    meta = rel.get("metadata", {}) if isinstance(rel, dict) else {}
                    from_table = rel.get("from_table") or meta.get("from_table")
                    to_table = rel.get("to_table") or meta.get("to_table")

                    # Check if this relationship connects our tables
                    if from_table in table_names and to_table in table_names:
                        join_suggestions.append({
                            "from_table": from_table,
                            "to_table": to_table,
                            "from_column": rel.get("from_column") or meta.get("from_column"),
                            "to_column": rel.get("to_column") or meta.get("to_column"),
                            "relationship_type": rel.get("relationship_type") or meta.get("relationship_type"),
                            "confidence": rel.get("score", 0.5)
                        })

            return join_suggestions

        except Exception as e:
            logger.error(f"Failed to suggest joins: {e}")
            return []
