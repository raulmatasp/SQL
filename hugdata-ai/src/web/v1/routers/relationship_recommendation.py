import uuid
from typing import Literal, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from src.web.v1.services.relationship_recommendation_service import RelationshipRecommendationService
from src.web.v1.services.base import get_service_container, ServiceContainer

router = APIRouter()

class RecommendationRequest(BaseModel):
    """Request model for relationship recommendation"""
    mdl: str
    project_id: Optional[str] = None
    language: str = "English"
    configurations: Optional[dict] = None

class RecommendationResponse(BaseModel):
    """Response model for relationship recommendation initiation"""
    id: str
    status: str = "generating"
    message: str = "Relationship recommendation started"

class RecommendationStatusResponse(BaseModel):
    """Response model for relationship recommendation status"""
    id: str
    status: Literal["generating", "finished", "failed"]
    response: Optional[dict] = None
    error: Optional[dict] = None
    trace_id: Optional[str] = None

@router.post("/relationship-recommendations", response_model=RecommendationResponse)
async def recommend_relationships(
    request: RecommendationRequest,
    background_tasks: BackgroundTasks,
    service_container: ServiceContainer = Depends(get_service_container)
) -> RecommendationResponse:
    """
    Initiate relationship recommendations for database models

    Args:
        request: Recommendation request containing MDL and configuration
        background_tasks: FastAPI background tasks
        service_container: Dependency injection container

    Returns:
        Response with ID for tracking recommendation status
    """
    try:
        recommendation_id = str(uuid.uuid4())

        # Get relationship recommendation service
        recommendation_service = service_container.get_relationship_recommendation_service()

        # Initialize recommendation event
        recommendation_service.initialize_recommendation(recommendation_id)

        # Add recommendation task to background
        background_tasks.add_task(
            recommendation_service.recommend_relationships,
            recommendation_id=recommendation_id,
            mdl=request.mdl,
            project_id=request.project_id,
            language=request.language,
            configurations=request.configurations
        )

        return RecommendationResponse(
            id=recommendation_id,
            status="generating",
            message="Relationship recommendation started successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate relationship recommendation: {str(e)}"
        )

@router.get("/relationship-recommendations/{recommendation_id}", response_model=RecommendationStatusResponse)
async def get_recommendation_status(
    recommendation_id: str,
    service_container: ServiceContainer = Depends(get_service_container)
) -> RecommendationStatusResponse:
    """
    Get the status and result of a relationship recommendation request

    Args:
        recommendation_id: Recommendation ID from the request
        service_container: Dependency injection container

    Returns:
        Current status and result of the recommendation
    """
    try:
        # Get relationship recommendation service
        recommendation_service = service_container.get_relationship_recommendation_service()

        # Get recommendation status
        recommendation_data = recommendation_service.get_recommendation_status(recommendation_id)

        if not recommendation_data:
            raise HTTPException(
                status_code=404,
                detail=f"Recommendation {recommendation_id} not found"
            )

        return RecommendationStatusResponse(
            id=recommendation_id,
            status=recommendation_data.get("status", "unknown"),
            response=recommendation_data.get("response"),
            error=recommendation_data.get("error"),
            trace_id=recommendation_data.get("trace_id")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendation status: {str(e)}"
        )

@router.delete("/relationship-recommendations/{recommendation_id}")
async def delete_recommendation(
    recommendation_id: str,
    service_container: ServiceContainer = Depends(get_service_container)
) -> dict:
    """
    Delete a relationship recommendation and its data

    Args:
        recommendation_id: Recommendation ID to delete
        service_container: Dependency injection container

    Returns:
        Confirmation of deletion
    """
    try:
        # Get relationship recommendation service
        recommendation_service = service_container.get_relationship_recommendation_service()

        # Delete the recommendation
        deleted = recommendation_service.delete_recommendation(recommendation_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Recommendation {recommendation_id} not found"
            )

        return {
            "id": recommendation_id,
            "status": "deleted",
            "message": "Recommendation deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete recommendation: {str(e)}"
        )

@router.get("/relationship-recommendations")
async def list_recommendations(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    service_container: ServiceContainer = Depends(get_service_container)
) -> dict:
    """
    List relationship recommendations with optional filtering

    Args:
        project_id: Optional project ID filter
        status: Optional status filter (generating, finished, failed)
        limit: Maximum number of recommendations to return
        service_container: Dependency injection container

    Returns:
        List of recommendations
    """
    try:
        # Get relationship recommendation service
        recommendation_service = service_container.get_relationship_recommendation_service()

        # Get filtered recommendations
        recommendations = recommendation_service.list_recommendations(
            project_id=project_id,
            status=status,
            limit=limit
        )

        return {
            "recommendations": recommendations,
            "total": len(recommendations),
            "filters": {
                "project_id": project_id,
                "status": status,
                "limit": limit
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list recommendations: {str(e)}"
        )

class ModelAnalysisRequest(BaseModel):
    """Request model for model complexity analysis"""
    mdl: str
    project_id: Optional[str] = None

@router.post("/relationship-recommendations/analyze-models")
async def analyze_model_complexity(
    request: ModelAnalysisRequest,
    service_container: ServiceContainer = Depends(get_service_container)
) -> dict:
    """
    Analyze model complexity for relationship recommendations

    Args:
        request: Analysis request containing MDL
        service_container: Dependency injection container

    Returns:
        Model complexity analysis results
    """
    try:
        # Get relationship recommendation service
        recommendation_service = service_container.get_relationship_recommendation_service()

        # Perform model analysis
        analysis = await recommendation_service.analyze_model_complexity(
            mdl=request.mdl,
            project_id=request.project_id
        )

        return {
            "analysis": analysis,
            "project_id": request.project_id,
            "status": "completed"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze model complexity: {str(e)}"
        )

class ValidateRelationshipsRequest(BaseModel):
    """Request model for relationship validation"""
    mdl: str
    relationships: list
    project_id: Optional[str] = None

@router.post("/relationship-recommendations/validate")
async def validate_relationships(
    request: ValidateRelationshipsRequest,
    service_container: ServiceContainer = Depends(get_service_container)
) -> dict:
    """
    Validate proposed relationships against the model

    Args:
        request: Validation request containing MDL and relationships
        service_container: Dependency injection container

    Returns:
        Validation results
    """
    try:
        # Get relationship recommendation service
        recommendation_service = service_container.get_relationship_recommendation_service()

        # Validate relationships
        validation_result = await recommendation_service.validate_relationships(
            mdl=request.mdl,
            relationships=request.relationships,
            project_id=request.project_id
        )

        return {
            "validation": validation_result,
            "project_id": request.project_id,
            "status": "completed"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate relationships: {str(e)}"
        )

@router.get("/relationship-recommendations/statistics")
async def get_recommendation_statistics(
    project_id: Optional[str] = None,
    service_container: ServiceContainer = Depends(get_service_container)
) -> dict:
    """
    Get statistics about relationship recommendations

    Args:
        project_id: Optional project ID filter
        service_container: Dependency injection container

    Returns:
        Statistics about recommendations
    """
    try:
        # Get relationship recommendation service
        recommendation_service = service_container.get_relationship_recommendation_service()

        # Get statistics
        stats = recommendation_service.get_statistics(project_id=project_id)

        return {
            "statistics": stats,
            "project_id": project_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendation statistics: {str(e)}"
        )