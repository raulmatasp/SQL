from dagster import asset, AssetExecutionContext
from typing import Dict, Any, List
from ..resources.vector_store import VectorStoreResource

@asset(deps=["database_schema"], group_name="semantic_processing")
def schema_vector_index(
    context: AssetExecutionContext, 
    database_schema: Dict[str, Any], 
    vector_store_resource: VectorStoreResource
) -> Dict[str, Any]:
    """
    Create semantic vector index of database schema
    
    This asset processes the database schema to create searchable embeddings:
    - Table and column descriptions
    - Relationship information
    - Data type semantics
    """
    context.log.info("Starting schema vector indexing")
    
    project_id = database_schema.get("metadata", {}).get("project_id", "default")
    tables = database_schema.get("tables", {})
    
    try:
        # Prepare documents for indexing
        documents = _prepare_schema_documents(tables, database_schema.get("relationships", []))
        
        context.log.info(f"Prepared {len(documents)} documents for indexing")
        
        # Index documents in vector store
        success = vector_store_resource.index_schema(
            schema=database_schema,
            project_id=project_id
        )
        
        if not success:
            context.log.warning("Vector store indexing returned failure status")
        
        index_metadata = {
            "project_id": project_id,
            "indexed_at": context.instance.get_current_timestamp(),
            "document_count": len(documents),
            "table_count": len(tables),
            "success": success
        }
        
        context.log.info(f"Schema vector indexing completed for project {project_id}")
        
        return {
            "metadata": index_metadata,
            "documents": documents[:10]  # Sample for inspection
        }
        
    except Exception as e:
        context.log.error(f"Vector indexing failed: {str(e)}")
        raise e

def _prepare_schema_documents(tables: Dict[str, Any], relationships: List[Dict]) -> List[Dict]:
    """Prepare schema information as documents for vector indexing"""
    
    documents = []
    
    # Create documents for each table and column
    for table_name, table_info in tables.items():
        # Table-level document
        table_doc = {
            "id": f"table_{table_name}",
            "type": "table",
            "table_name": table_name,
            "content": f"Table {table_name} contains data about {_infer_table_purpose(table_name)}",
            "metadata": {
                "column_count": len(table_info.get("columns", [])),
                "columns": [col.get("name") for col in table_info.get("columns", [])]
            }
        }
        documents.append(table_doc)
        
        # Column-level documents
        for column in table_info.get("columns", []):
            col_name = column.get("name", "unknown")
            col_type = column.get("type", "unknown")
            
            column_doc = {
                "id": f"column_{table_name}_{col_name}",
                "type": "column",
                "table_name": table_name,
                "column_name": col_name,
                "column_type": col_type,
                "content": f"Column {col_name} in table {table_name} stores {_infer_column_purpose(col_name, col_type)} data",
                "metadata": {
                    "nullable": column.get("nullable", True),
                    "primary_key": column.get("primary_key", False),
                    "foreign_key": column.get("foreign_key")
                }
            }
            documents.append(column_doc)
    
    # Create documents for relationships
    for rel in relationships:
        rel_doc = {
            "id": f"relationship_{rel.get('from_table')}_{rel.get('to_table')}",
            "type": "relationship",
            "content": f"Table {rel.get('from_table')} is related to {rel.get('to_table')} through {rel.get('type', 'unknown')} relationship",
            "metadata": rel
        }
        documents.append(rel_doc)
    
    return documents

def _infer_table_purpose(table_name: str) -> str:
    """Infer table purpose from name for better semantic understanding"""
    name_lower = table_name.lower()
    
    if "user" in name_lower:
        return "users and user accounts"
    elif "order" in name_lower:
        return "orders and transactions"
    elif "product" in name_lower:
        return "products and inventory"
    elif "payment" in name_lower:
        return "payments and billing"
    elif "log" in name_lower or "audit" in name_lower:
        return "logs and audit trails"
    else:
        return f"{table_name.replace('_', ' ')}"

def _infer_column_purpose(column_name: str, column_type: str) -> str:
    """Infer column purpose from name and type"""
    name_lower = column_name.lower()
    type_lower = column_type.lower()
    
    if "id" in name_lower:
        return "identifier"
    elif "name" in name_lower:
        return "name or title"
    elif "email" in name_lower:
        return "email address"
    elif "date" in name_lower or "time" in name_lower:
        return "date and time"
    elif "amount" in name_lower or "price" in name_lower or "cost" in name_lower:
        return "monetary amount"
    elif "status" in name_lower:
        return "status or state"
    elif "count" in name_lower or "total" in name_lower:
        return "numeric count"
    elif "text" in type_lower or "varchar" in type_lower:
        return "text"
    elif "int" in type_lower or "number" in type_lower:
        return "numeric"
    else:
        return f"{column_type}"