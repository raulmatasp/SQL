from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ..services.ask import AskService, AskRequest, AskResponse, StopAskRequest, StopAskResponse

router = APIRouter(prefix="/v1", tags=["ask"])

# This will be dependency injected
_ask_service: AskService = None

def get_ask_service() -> AskService:
    if _ask_service is None:
        raise HTTPException(status_code=500, detail="Ask service not initialized")
    return _ask_service

def set_ask_service(service: AskService):
    global _ask_service
    _ask_service = service


@router.post("/asks", response_model=AskResponse)
async def create_ask(
    ask_request: AskRequest,
    ask_service: AskService = Depends(get_ask_service)
) -> AskResponse:
    """Create a new SQL generation request from natural language query"""
    return await ask_service.create_ask(ask_request)


@router.get("/asks/{query_id}/result")
async def get_ask_result(
    query_id: str,
    ask_service: AskService = Depends(get_ask_service)
) -> Dict[str, Any]:
    """Get the result of a SQL generation request"""
    result = await ask_service.get_ask_result(query_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Query not found or not ready")
    return result.model_dump()


@router.patch("/asks/{query_id}", response_model=StopAskResponse)
async def stop_ask(
    query_id: str,
    stop_request: StopAskRequest,
    ask_service: AskService = Depends(get_ask_service)
) -> StopAskResponse:
    """Stop a running SQL generation request"""
    return await ask_service.stop_ask(query_id)