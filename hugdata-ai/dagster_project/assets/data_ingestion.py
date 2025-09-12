from dagster import asset, AssetExecutionContext
from typing import Dict, Any
from ..resources.database import DatabaseResource

@asset(group_name="data_ingestion")
def database_schema(context: AssetExecutionContext, database_resource: DatabaseResource) -> Dict[str, Any]:
    """
    Ingest and normalize database schema from Laravel API
    
    This asset fetches the current database schema structure including:
    - Tables and columns
    - Data types and constraints
    - Relationships between tables
    """
    context.log.info("Starting database schema ingestion")
    
    # Get project ID from context or use default
    project_id = context.run.tags.get("project_id", "default")
    
    try:
        # Fetch schema from Laravel API
        schema = database_resource.get_schema(project_id)
        
        context.log.info(f"Successfully ingested schema for project {project_id}")
        context.log.info(f"Found {len(schema.get('tables', {}))} tables")
        
        # Normalize schema format
        normalized_schema = _normalize_schema(schema)
        
        # Add metadata
        normalized_schema["metadata"] = {
            "project_id": project_id,
            "ingested_at": context.instance.get_current_timestamp(),
            "table_count": len(normalized_schema.get("tables", {}))
        }
        
        return normalized_schema
        
    except Exception as e:
        context.log.error(f"Schema ingestion failed: {str(e)}")
        raise e

def _normalize_schema(raw_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize schema format for consistent processing"""
    
    normalized = {
        "tables": {},
        "relationships": raw_schema.get("relationships", [])
    }
    
    # Normalize table structures
    for table_name, table_info in raw_schema.get("tables", {}).items():
        normalized_table = {
            "name": table_name,
            "columns": []
        }
        
        # Handle different column formats
        if isinstance(table_info, list):
            # Simple list of column names
            for col in table_info:
                normalized_table["columns"].append({
                    "name": col,
                    "type": "unknown",
                    "nullable": True
                })
        elif isinstance(table_info, dict) and "columns" in table_info:
            # Detailed column information
            for col in table_info["columns"]:
                if isinstance(col, dict):
                    normalized_table["columns"].append({
                        "name": col.get("name", "unknown"),
                        "type": col.get("type", "unknown"),
                        "nullable": col.get("nullable", True),
                        "primary_key": col.get("primary_key", False),
                        "foreign_key": col.get("foreign_key", None)
                    })
                else:
                    normalized_table["columns"].append({
                        "name": str(col),
                        "type": "unknown",
                        "nullable": True
                    })
        
        normalized["tables"][table_name] = normalized_table
    
    return normalized