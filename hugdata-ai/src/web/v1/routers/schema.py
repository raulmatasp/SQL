from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from pydantic import BaseModel
from ..services.schema import SchemaService

router = APIRouter(prefix="/v1", tags=["schema"])

# Global service instance
_schema_service: 'SchemaService' = None

def get_schema_service() -> 'SchemaService':
    if _schema_service is None:
        raise HTTPException(status_code=500, detail="Schema service not initialized")
    return _schema_service

def set_schema_service(service: 'SchemaService'):
    global _schema_service
    _schema_service = service


class SchemaIndexRequest(BaseModel):
    project_id: str
    data_source_config: Dict[str, Any]
    schema_data: Dict[str, Any]


class SchemaIndexResponse(BaseModel):
    status: str
    indexed_tables: int
    indexed_columns: int
    indexed_relationships: int
    total_documents: int
    error: str = None


@router.post("/schema/index", response_model=SchemaIndexResponse)
async def index_schema(
    request: SchemaIndexRequest,
    schema_service: 'SchemaService' = Depends(get_schema_service)
) -> SchemaIndexResponse:
    """Index database schema for semantic search"""
    try:
        result = await schema_service.index_schema(
            request.project_id,
            request.data_source_config,
            request.schema_data
        )
        return SchemaIndexResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema indexing failed: {str(e)}")


@router.get("/schema/{project_id}/summary")
async def get_schema_summary(
    project_id: str,
    schema_service: 'SchemaService' = Depends(get_schema_service)
) -> Dict[str, Any]:
    """Get summary of indexed schema information"""
    try:
        return await schema_service.get_schema_summary(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schema summary: {str(e)}")


@router.post("/schema/{project_id}/update")
async def update_schema_index(
    project_id: str,
    schema_changes: Dict[str, Any],
    schema_service: 'SchemaService' = Depends(get_schema_service)
) -> Dict[str, Any]:
    """Update existing schema index with changes"""
    try:
        return await schema_service.update_schema_index(project_id, schema_changes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema update failed: {str(e)}")


@router.delete("/schema/{project_id}")
async def delete_schema_index(
    project_id: str,
    schema_service: 'SchemaService' = Depends(get_schema_service)
) -> Dict[str, Any]:
    """Delete schema index for a project"""
    try:
        result = await schema_service.delete_schema_index(project_id)
        return {"status": "success", "message": f"Schema index for project {project_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema deletion failed: {str(e)}")


@router.get("/schema/{project_id}/search")
async def search_schema(
    project_id: str,
    query: str,
    limit: int = 10,
    schema_service: 'SchemaService' = Depends(get_schema_service)
) -> Dict[str, Any]:
    """Search schema information for a project"""
    try:
        results = await schema_service.search_schema(project_id, query, limit)
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema search failed: {str(e)}")