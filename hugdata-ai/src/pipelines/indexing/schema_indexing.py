import logging
from typing import Dict, Any, List, Optional
import asyncio
from src.providers.vector_store import VectorStore

logger = logging.getLogger("hugdata-ai")


class SchemaIndexingPipeline:
    """
    Pipeline for indexing database schemas into vector store
    Similar to WrenAI's table_description_indexing and sql_tables_extraction
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    async def index_database_schema(
        self,
        project_id: str,
        data_source_config: Dict[str, Any],
        schema_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Index database schema information for semantic search"""

        try:
            # Extract and index table descriptions
            table_docs = await self._process_table_descriptions(
                project_id, schema_data
            )

            # Extract and index column information
            column_docs = await self._process_table_columns(
                project_id, schema_data
            )

            # Index relationships if available
            relationship_docs = await self._process_relationships(
                project_id, schema_data
            )

            # Store in vector store
            all_docs = table_docs + column_docs + relationship_docs

            if all_docs:
                await self.vector_store.add_documents(
                    collection_name=f"schema_{project_id}",
                    documents=all_docs,
                )

            return {
                "status": "success",
                "indexed_tables": len(table_docs),
                "indexed_columns": len(column_docs),
                "indexed_relationships": len(relationship_docs),
                "total_documents": len(all_docs)
            }

        except Exception as e:
            logger.error(f"Schema indexing failed for project {project_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "indexed_tables": 0,
                "indexed_columns": 0,
                "indexed_relationships": 0
            }

    async def _process_table_descriptions(
        self,
        project_id: str,
        schema_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process table descriptions for indexing"""

        table_docs = []
        tables = schema_data.get("tables", {})

        for table_name, table_info in tables.items():
            # Generate table description document
            description = self._generate_table_description(table_name, table_info)

            doc = {
                "content": description,
                "metadata": {
                    "type": "table_description",
                    "project_id": project_id,
                    "table_name": table_name,
                    "column_count": len(table_info.get("columns", [])),
                    "table_type": table_info.get("type", "table")
                }
            }
            table_docs.append(doc)

        return table_docs

    async def _process_table_columns(
        self,
        project_id: str,
        schema_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process individual column information for indexing"""

        column_docs = []
        tables = schema_data.get("tables", {})

        for table_name, table_info in tables.items():
            columns = table_info.get("columns", [])

            for column in columns:
                if isinstance(column, dict):
                    col_name = column.get("name", "")
                    col_type = column.get("type", "")
                    col_description = column.get("description", "")

                    # Generate column description
                    description = self._generate_column_description(
                        table_name, col_name, col_type, col_description
                    )

                    doc = {
                        "content": description,
                        "metadata": {
                            "type": "table_columns",
                            "project_id": project_id,
                            "table_name": table_name,
                            "column_name": col_name,
                            "column_type": col_type,
                            "nullable": column.get("nullable", True),
                            "is_primary_key": column.get("is_primary_key", False)
                        }
                    }
                    column_docs.append(doc)

        return column_docs

    async def _process_relationships(
        self,
        project_id: str,
        schema_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process table relationships for indexing"""

        relationship_docs = []
        relationships = schema_data.get("relationships", [])

        for rel in relationships:
            if isinstance(rel, dict):
                description = self._generate_relationship_description(rel)

                doc = {
                    "content": description,
                    "metadata": {
                        "type": "relationship",
                        "project_id": project_id,
                        "from_table": rel.get("from_table"),
                        "to_table": rel.get("to_table"),
                        "relationship_type": rel.get("type", "foreign_key")
                    }
                }
                relationship_docs.append(doc)

        return relationship_docs

    def _generate_table_description(
        self,
        table_name: str,
        table_info: Dict[str, Any]
    ) -> str:
        """Generate a comprehensive description of a database table"""

        description_parts = [f"Table: {table_name}"]

        # Add table comment/description if available
        if table_info.get("description"):
            description_parts.append(f"Description: {table_info['description']}")

        # Add column information
        columns = table_info.get("columns", [])
        if columns:
            col_names = []
            for col in columns:
                if isinstance(col, dict):
                    col_name = col.get("name", "")
                    col_type = col.get("type", "")
                    col_names.append(f"{col_name} ({col_type})")
                else:
                    col_names.append(str(col))

            description_parts.append(f"Columns: {', '.join(col_names)}")

        # Add table statistics if available
        if table_info.get("row_count"):
            description_parts.append(f"Approximate rows: {table_info['row_count']}")

        return ". ".join(description_parts)

    def _generate_column_description(
        self,
        table_name: str,
        col_name: str,
        col_type: str,
        col_description: str = ""
    ) -> str:
        """Generate description for a database column"""

        parts = [
            f"Column {col_name} in table {table_name}",
            f"Type: {col_type}"
        ]

        if col_description:
            parts.append(f"Description: {col_description}")

        return ". ".join(parts)

    def _generate_relationship_description(self, rel: Dict[str, Any]) -> str:
        """Generate description for a table relationship"""

        from_table = rel.get("from_table", "")
        to_table = rel.get("to_table", "")
        from_column = rel.get("from_column", "")
        to_column = rel.get("to_column", "")
        rel_type = rel.get("type", "foreign_key")

        return (
            f"{rel_type.replace('_', ' ').title()} relationship: "
            f"{from_table}.{from_column} -> {to_table}.{to_column}"
        )

    async def update_schema_index(
        self,
        project_id: str,
        schema_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing schema index with changes"""

        try:
            # For now, we'll do a full re-index
            # In a production system, this would be more granular
            collection_name = f"schema_{project_id}"

            # Clear existing documents
            await self.vector_store.delete_collection(collection_name)

            # Re-index with new schema
            return await self.index_database_schema(
                project_id, {}, schema_changes
            )

        except Exception as e:
            logger.error(f"Schema index update failed: {e}")
            return {"status": "error", "error": str(e)}

    async def get_schema_summary(self, project_id: str) -> Dict[str, Any]:
        """Get a summary of indexed schema information"""

        try:
            collection_name = f"schema_{project_id}"

            # Get document counts by type
            table_count = await self.vector_store.count_documents(
                collection_name, {"type": "table_description"}
            )

            column_count = await self.vector_store.count_documents(
                collection_name, {"type": "table_columns"}
            )

            relationship_count = await self.vector_store.count_documents(
                collection_name, {"type": "relationship"}
            )

            return {
                "status": "success",
                "project_id": project_id,
                "tables_indexed": table_count,
                "columns_indexed": column_count,
                "relationships_indexed": relationship_count,
                "total_documents": table_count + column_count + relationship_count
            }

        except Exception as e:
            logger.error(f"Failed to get schema summary: {e}")
            return {
                "status": "error",
                "error": str(e),
                "tables_indexed": 0,
                "columns_indexed": 0,
                "relationships_indexed": 0
            }
