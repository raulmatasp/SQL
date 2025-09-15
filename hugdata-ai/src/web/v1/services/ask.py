import asyncio
import logging
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from uuid import uuid4

logger = logging.getLogger("hugdata-ai")


class AskHistory(BaseModel):
    sql: str
    question: str


class AskRequest(BaseModel):
    query: str
    mdl_hash: Optional[str] = None
    histories: Optional[List[AskHistory]] = Field(default_factory=list)
    ignore_sql_generation_reasoning: bool = False
    enable_column_pruning: bool = False
    use_dry_plan: bool = False
    allow_dry_plan_fallback: bool = True
    custom_instruction: Optional[str] = None


class AskResponse(BaseModel):
    query_id: str


class StopAskRequest(BaseModel):
    status: Literal["stopped"]


class StopAskResponse(BaseModel):
    query_id: str


class AskResult(BaseModel):
    sql: str
    reasoning: Optional[str] = None
    data: Optional[List[Dict]] = None
    columns: Optional[List[str]] = None


class AskService:
    def __init__(self, llm_provider, vector_store, sql_pipeline):
        self.llm_provider = llm_provider
        self.vector_store = vector_store
        self.sql_pipeline = sql_pipeline
        self._queries = {}  # In-memory storage for now

    async def create_ask(self, ask_request: AskRequest) -> AskResponse:
        query_id = str(uuid4())

        # Store query for tracking
        self._queries[query_id] = {
            "request": ask_request,
            "status": "pending",
            "result": None,
            "error": None
        }

        # Start background processing
        asyncio.create_task(self._process_query(query_id))

        return AskResponse(query_id=query_id)

    async def _process_query(self, query_id: str):
        try:
            query_data = self._queries[query_id]
            request = query_data["request"]

            # Use the SQL generation pipeline
            result = await self.sql_pipeline.generate_sql(
                query=request.query,
                mdl_hash=request.mdl_hash,
                histories=request.histories
            )

            query_data["result"] = AskResult(
                sql=result.get("sql", ""),
                reasoning=result.get("reasoning"),
                data=result.get("data"),
                columns=result.get("columns")
            )
            query_data["status"] = "completed"

        except Exception as e:
            logger.error(f"Error processing query {query_id}: {e}")
            self._queries[query_id]["error"] = str(e)
            self._queries[query_id]["status"] = "failed"

    async def get_ask_result(self, query_id: str) -> Optional[AskResult]:
        if query_id in self._queries:
            query_data = self._queries[query_id]
            if query_data["status"] == "completed":
                return query_data["result"]
            elif query_data["status"] == "failed":
                raise Exception(query_data["error"])
        return None

    async def stop_ask(self, query_id: str) -> StopAskResponse:
        if query_id in self._queries:
            self._queries[query_id]["status"] = "stopped"
        return StopAskResponse(query_id=query_id)