import uuid
import asyncio
from typing import List, Literal, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from src.web.v1.services.sql_correction_service import SqlCorrectionService
from src.web.v1.services.base import get_service_container, ServiceContainer

router = APIRouter()

class CorrectionRequest(BaseModel):
    """Request model for SQL correction"""
    sql: str
    error: str
    project_id: Optional[str] = None
    retrieved_tables: Optional[List[str]] = None
    use_dry_plan: bool = False
    allow_dry_plan_fallback: bool = True

class CorrectionResponse(BaseModel):
    """Response model for SQL correction initiation"""
    event_id: str
    status: str = "correcting"
    message: str = "SQL correction started"

class CorrectionStatusResponse(BaseModel):
    """Response model for SQL correction status"""
    event_id: str
    status: Literal["correcting", "finished", "failed"]
    response: Optional[dict] = None
    error: Optional[dict] = None
    trace_id: Optional[str] = None
    invalid_sql: Optional[str] = None

@router.post("/sql-corrections", response_model=CorrectionResponse)
async def correct_sql(
    request: CorrectionRequest,
    background_tasks: BackgroundTasks,
    service_container: ServiceContainer = Depends(get_service_container)
) -> CorrectionResponse:
    """
    Initiate SQL correction for a syntactically incorrect SQL query

    Args:
        request: SQL correction request containing SQL and error information
        background_tasks: FastAPI background tasks
        service_container: Dependency injection container

    Returns:
        Response with event ID for tracking correction status
    """
    try:
        event_id = str(uuid.uuid4())

        # Get SQL correction service
        correction_service = service_container.get_sql_correction_service()

        # Initialize correction event
        correction_service.initialize_event(event_id)

        # Add correction task to background
        background_tasks.add_task(
            correction_service.correct_sql,
            event_id=event_id,
            sql=request.sql,
            error=request.error,
            project_id=request.project_id,
            retrieved_tables=request.retrieved_tables,
            use_dry_plan=request.use_dry_plan,
            allow_dry_plan_fallback=request.allow_dry_plan_fallback
        )

        return CorrectionResponse(
            event_id=event_id,
            status="correcting",
            message="SQL correction started successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate SQL correction: {str(e)}"
        )

@router.get("/sql-corrections/{event_id}", response_model=CorrectionStatusResponse)
async def get_correction_status(
    event_id: str,
    service_container: ServiceContainer = Depends(get_service_container)
) -> CorrectionStatusResponse:
    """
    Get the status and result of a SQL correction request

    Args:
        event_id: Event ID from the correction request
        service_container: Dependency injection container

    Returns:
        Current status and result of the correction
    """
    try:
        # Get SQL correction service
        correction_service = service_container.get_sql_correction_service()

        # Get correction event status
        event_data = correction_service.get_event_status(event_id)

        if not event_data:
            raise HTTPException(
                status_code=404,
                detail=f"Correction event {event_id} not found"
            )

        return CorrectionStatusResponse(
            event_id=event_id,
            status=event_data.get("status", "unknown"),
            response=event_data.get("response"),
            error=event_data.get("error"),
            trace_id=event_data.get("trace_id"),
            invalid_sql=event_data.get("invalid_sql")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get correction status: {str(e)}"
        )

@router.delete("/sql-corrections/{event_id}")
async def delete_correction_event(
    event_id: str,
    service_container: ServiceContainer = Depends(get_service_container)
) -> dict:
    """
    Delete a SQL correction event and its data

    Args:
        event_id: Event ID to delete
        service_container: Dependency injection container

    Returns:
        Confirmation of deletion
    """
    try:
        # Get SQL correction service
        correction_service = service_container.get_sql_correction_service()

        # Delete the event
        deleted = correction_service.delete_event(event_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Correction event {event_id} not found"
            )

        return {
            "event_id": event_id,
            "status": "deleted",
            "message": "Correction event deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete correction event: {str(e)}"
        )

@router.get("/sql-corrections")
async def list_correction_events(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    service_container: ServiceContainer = Depends(get_service_container)
) -> dict:
    """
    List SQL correction events with optional filtering

    Args:
        project_id: Optional project ID filter
        status: Optional status filter (correcting, finished, failed)
        limit: Maximum number of events to return
        service_container: Dependency injection container

    Returns:
        List of correction events
    """
    try:
        # Get SQL correction service
        correction_service = service_container.get_sql_correction_service()

        # Get filtered events
        events = correction_service.list_events(
            project_id=project_id,
            status=status,
            limit=limit
        )

        return {
            "events": events,
            "total": len(events),
            "filters": {
                "project_id": project_id,
                "status": status,
                "limit": limit
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list correction events: {str(e)}"
        )

class BulkCorrectionRequest(BaseModel):
    """Request model for bulk SQL correction"""
    corrections: List[CorrectionRequest]
    project_id: Optional[str] = None

@router.post("/sql-corrections/bulk", response_model=dict)
async def bulk_correct_sql(
    request: BulkCorrectionRequest,
    background_tasks: BackgroundTasks,
    service_container: ServiceContainer = Depends(get_service_container)
) -> dict:
    """
    Initiate bulk SQL corrections for multiple queries

    Args:
        request: Bulk correction request
        background_tasks: FastAPI background tasks
        service_container: Dependency injection container

    Returns:
        Response with event IDs for tracking all corrections
    """
    try:
        if not request.corrections:
            raise HTTPException(
                status_code=400,
                detail="No corrections provided"
            )

        if len(request.corrections) > 10:  # Limit bulk operations
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 corrections allowed per bulk request"
            )

        # Get SQL correction service
        correction_service = service_container.get_sql_correction_service()

        event_ids = []

        # Process each correction
        for correction in request.corrections:
            event_id = str(uuid.uuid4())
            event_ids.append(event_id)

            # Initialize correction event
            correction_service.initialize_event(event_id)

            # Add correction task to background
            background_tasks.add_task(
                correction_service.correct_sql,
                event_id=event_id,
                sql=correction.sql,
                error=correction.error,
                project_id=correction.project_id or request.project_id,
                retrieved_tables=correction.retrieved_tables,
                use_dry_plan=correction.use_dry_plan,
                allow_dry_plan_fallback=correction.allow_dry_plan_fallback
            )

        return {
            "event_ids": event_ids,
            "total_corrections": len(event_ids),
            "status": "correcting",
            "message": f"Bulk SQL correction started for {len(event_ids)} queries"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate bulk SQL correction: {str(e)}"
        )