from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ..services.chart import ChartService, ChartRequest, ChartResponse

router = APIRouter(prefix="/v1", tags=["chart"])

# Global service instance
_chart_service: ChartService = None

def get_chart_service() -> ChartService:
    if _chart_service is None:
        raise HTTPException(status_code=500, detail="Chart service not initialized")
    return _chart_service

def set_chart_service(service: ChartService):
    global _chart_service
    _chart_service = service


@router.post("/charts/suggest", response_model=ChartResponse)
async def suggest_chart(
    chart_request: ChartRequest,
    chart_service: ChartService = Depends(get_chart_service)
) -> ChartResponse:
    """Generate chart suggestions based on query results"""
    try:
        return await chart_service.suggest_chart(chart_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")


@router.post("/charts/adjust")
async def adjust_chart(
    adjustment_request: Dict[str, Any],
    chart_service: ChartService = Depends(get_chart_service)
) -> Dict[str, Any]:
    """Adjust existing chart based on user feedback"""
    # This would implement chart adjustment logic
    # For now, return a simple response
    return {
        "message": "Chart adjustment feature coming soon",
        "request": adjustment_request
    }