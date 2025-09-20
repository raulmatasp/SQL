from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import asyncio
from datetime import datetime
import sqlparse

from src.providers.llm_provider import OpenAIProvider, NotConfiguredLLMProvider
from src.providers.vector_store import QdrantProvider, NotConfiguredVectorStore
from src.providers.embeddings_provider import OpenAIEmbeddingsProvider, NotConfiguredEmbeddingsProvider
from src.pipelines.sql_generation import SQLGenerationPipeline
from src.web.v1.services.ask import AskService
from src.web.v1.services.chart import ChartService
from src.web.v1.services.schema import SchemaService
from src.web.v1.services.base import initialize_service_container
from src.web.v1.routers.ask import router as ask_router, set_ask_service
from src.web.v1.routers.chart import router as chart_router, set_chart_service
from src.web.v1.routers.schema import router as schema_router, set_schema_service
from src.web.v1.routers.sql_corrections import router as sql_corrections_router
from src.web.v1.routers.relationship_recommendation import router as relationship_recommendation_router

# Import Dagster components
try:
    from dagster import DagsterInstance, execute_job, materialize
    from dagster_project.definitions import defs
    DAGSTER_AVAILABLE = True
except ImportError:
    DAGSTER_AVAILABLE = False
    print("Warning: Dagster not available, running in compatibility mode")

app = FastAPI(
    title="HugData AI Service",
    description="AI-powered SQL generation and analytics service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import logging
logger = logging.getLogger("hugdata-ai")

# Initialize providers
def get_llm_provider():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        return OpenAIProvider(openai_api_key)
    else:
        logger.error("OPENAI_API_KEY not set; LLM completions disabled.")
        return NotConfiguredLLMProvider("OPENAI_API_KEY is missing")

def get_vector_store(embeddings_provider):
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    if not qdrant_url:
        logger.error("QDRANT_URL not set; vector search/indexing disabled.")
        return NotConfiguredVectorStore("QDRANT_URL is missing")
    try:
        return QdrantProvider(url=qdrant_url, api_key=qdrant_api_key, embeddings_provider=embeddings_provider)
    except Exception as e:
        logger.error(f"Qdrant connection failed: {e}")
        return NotConfiguredVectorStore(str(e))

def get_embeddings_provider():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        return OpenAIEmbeddingsProvider(openai_api_key)
    else:
        logger.error("OPENAI_API_KEY not set; embeddings disabled.")
        return NotConfiguredEmbeddingsProvider("OPENAI_API_KEY is missing")

# Global instances
llm_provider = get_llm_provider()
embeddings_provider = get_embeddings_provider()
vector_store = get_vector_store(embeddings_provider)
sql_pipeline = SQLGenerationPipeline(llm_provider, vector_store)

# Initialize service container for new services
service_container = initialize_service_container(
    llm_provider=llm_provider,
    vector_store=vector_store,
    embeddings_provider=embeddings_provider
)

# Initialize WrenAI-style services
ask_service = AskService(llm_provider, vector_store, sql_pipeline)
chart_service = ChartService(llm_provider)
schema_service = SchemaService(vector_store)
set_ask_service(ask_service)
set_chart_service(chart_service)
set_schema_service(schema_service)

# Include WrenAI-style routers
app.include_router(ask_router)
app.include_router(chart_router)
app.include_router(schema_router)

# Include new advanced routers with v1 prefix
app.include_router(sql_corrections_router, prefix="/v1", tags=["SQL Corrections"])
app.include_router(relationship_recommendation_router, prefix="/v1", tags=["Relationship Recommendations"])

# Request/Response Models
class NaturalLanguageQuery(BaseModel):
    query: str
    context: Dict[str, Any]
    database_schema: Dict[str, Any]
    project_id: str
    
class SQLGenerationResponse(BaseModel):
    sql: str
    confidence: float
    explanation: str
    reasoning_steps: List[str]
    
class ChartSuggestion(BaseModel):
    chart_type: str
    configuration: Dict[str, Any]
    confidence: float

class ChartSuggestionRequest(BaseModel):
    data_sample: Dict[str, Any]
    query_intent: str

# Dagster workflow models
class WorkflowTriggerRequest(BaseModel):
    workflow_type: str
    project_id: str
    user_id: str
    workflow_run_id: int
    config: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, str]] = None

class WorkflowStatusResponse(BaseModel):
    run_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

# Core Endpoints
@app.post("/generate-sql", response_model=SQLGenerationResponse)
async def generate_sql(request: NaturalLanguageQuery):
    """Generate SQL from natural language query"""
    try:
        result = await sql_pipeline.generate_sql(
            query=request.query,
            schema=request.database_schema,
            context=request.context,
            project_id=request.project_id
        )
        
        return SQLGenerationResponse(
            sql=result["sql"],
            confidence=result["confidence"],
            explanation=result["explanation"],
            reasoning_steps=result["reasoning_steps"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain-query")
async def explain_query(sql: str, schema: Optional[Dict[str, Any]] = None):
    """Explain SQL query in natural language"""
    try:
        # Parse SQL and build a structured explanation
        parsed_statements = sqlparse.parse(sql)
        if not parsed_statements:
            raise HTTPException(status_code=400, detail="Invalid SQL provided")

        stmt = parsed_statements[0]
        tokens = list(stmt.flatten())

        explanation_parts = []
        breakdown: Dict[str, str] = {}

        # Basic clause detection
        sql_upper = sql.upper()
        if "SELECT" in sql_upper:
            breakdown["SELECT"] = "Retrieves specified columns"
        if "FROM" in sql_upper:
            breakdown["FROM"] = "Reads from one or more tables"
        if "JOIN" in sql_upper:
            breakdown["JOIN"] = "Combines rows from related tables"
        if "WHERE" in sql_upper:
            breakdown["WHERE"] = "Filters rows based on conditions"
        if "GROUP BY" in sql_upper:
            breakdown["GROUP BY"] = "Aggregates rows into groups"
        if "HAVING" in sql_upper:
            breakdown["HAVING"] = "Filters groups after aggregation"
        if "ORDER BY" in sql_upper:
            breakdown["ORDER BY"] = "Sorts the result set"
        if "LIMIT" in sql_upper:
            breakdown["LIMIT"] = "Limits number of rows returned"

        # Infer tables mentioned after FROM
        tables = []
        in_from = False
        for token in tokens:
            if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'FROM':
                in_from = True
                continue
            if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in ['WHERE', 'GROUP', 'ORDER', 'LIMIT', 'JOIN', 'HAVING']:
                in_from = False
            if in_from and token.ttype is None and token.value.strip():
                cleaned = token.value.strip().strip(',')
                if cleaned and cleaned not in tables:
                    tables.append(cleaned)

        if tables:
            explanation_parts.append(f"It reads from table(s): {', '.join(tables)}")

        # High-level explanation
        if 'WHERE' in sql_upper:
            explanation_parts.append("with filtering conditions applied")
        if 'GROUP BY' in sql_upper:
            explanation_parts.append("aggregating results into groups")
        if 'ORDER BY' in sql_upper:
            explanation_parts.append("and sorts the output")
        if 'LIMIT' in sql_upper:
            explanation_parts.append("with a row limit for safety")

        explanation = "This query retrieves data. " + (" ".join(explanation_parts) if explanation_parts else "")

        return {
            "explanation": explanation.strip(),
            "breakdown": breakdown
        }
    except HTTPException:
        raise
    except Exception as e:
        # As a fallback, attempt an LLM-based explanation when available
        try:
            prompt = f"Explain the following SQL query in simple terms and provide a short breakdown by clause as JSON with keys explanation and breakdown: \n\n{sql}"
            response_text = await llm_provider.generate(prompt=prompt, max_tokens=300, temperature=0.1)
            # Attempt to parse JSON directly
            import json
            return json.loads(response_text)
        except Exception:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/suggest-charts", response_model=List[ChartSuggestion])
async def suggest_charts(request: ChartSuggestionRequest):
    """Suggest appropriate chart types for query results"""
    try:
        data_sample = request.data_sample
        query_intent = request.query_intent.lower()
        
        # Analyze the data structure
        if not data_sample or len(data_sample) == 0:
            return []
            
        # Get column information
        columns = list(data_sample.keys()) if isinstance(data_sample, dict) else []
        if len(columns) == 0:
            return []
        
        suggestions = []
        
        # Analyze columns to determine appropriate chart types
        numeric_columns = []
        text_columns = []
        date_columns = []
        
        for col, value in data_sample.items():
            if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit()):
                numeric_columns.append(col)
            elif any(date_word in col.lower() for date_word in ['date', 'time', 'created', 'updated', 'year', 'month']):
                date_columns.append(col)
            else:
                text_columns.append(col)
        
        # Rule-based chart suggestions
        
        # Bar chart - good for categorical comparisons
        if len(text_columns) >= 1 and len(numeric_columns) >= 1:
            suggestions.append(ChartSuggestion(
                chart_type="bar",
                configuration={
                    "xAxis": text_columns[0],
                    "yAxis": numeric_columns[0],
                    "title": f"{numeric_columns[0].replace('_', ' ').title()} by {text_columns[0].replace('_', ' ').title()}"
                },
                confidence=0.9 if "compare" in query_intent or "by" in query_intent else 0.7
            ))
        
        # Line chart - good for trends over time or continuous data
        if len(date_columns) >= 1 and len(numeric_columns) >= 1:
            suggestions.append(ChartSuggestion(
                chart_type="line",
                configuration={
                    "xAxis": date_columns[0],
                    "yAxis": numeric_columns[0],
                    "title": f"{numeric_columns[0].replace('_', ' ').title()} Over Time"
                },
                confidence=0.9 if any(word in query_intent for word in ["trend", "over time", "growth", "change"]) else 0.8
            ))
        elif len(numeric_columns) >= 2:
            suggestions.append(ChartSuggestion(
                chart_type="line",
                configuration={
                    "xAxis": numeric_columns[0],
                    "yAxis": numeric_columns[1],
                    "title": f"{numeric_columns[1].replace('_', ' ').title()} vs {numeric_columns[0].replace('_', ' ').title()}"
                },
                confidence=0.7
            ))
        
        # Pie chart - good for parts of a whole
        if len(text_columns) >= 1 and len(numeric_columns) >= 1:
            suggestions.append(ChartSuggestion(
                chart_type="pie",
                configuration={
                    "xAxis": text_columns[0],
                    "yAxis": numeric_columns[0],
                    "title": f"{numeric_columns[0].replace('_', ' ').title()} Distribution"
                },
                confidence=0.8 if any(word in query_intent for word in ["distribution", "share", "percentage", "proportion"]) else 0.6
            ))
        
        # Doughnut chart - alternative to pie chart
        if len(text_columns) >= 1 and len(numeric_columns) >= 1:
            suggestions.append(ChartSuggestion(
                chart_type="doughnut",
                configuration={
                    "xAxis": text_columns[0],
                    "yAxis": numeric_columns[0],
                    "title": f"{numeric_columns[0].replace('_', ' ').title()} Breakdown"
                },
                confidence=0.7 if "breakdown" in query_intent else 0.5
            ))
        
        # Sort by confidence and return top suggestions
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[:3]  # Return top 3 suggestions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index-schema")
async def index_schema(schema: Optional[Dict[str, Any]] = None, project_id: Optional[str] = None):
    """Index database schema for semantic search"""
    try:
        # Delegate to SchemaService with minimal data_source_config for now
        if not project_id or not schema:
            raise HTTPException(status_code=500, detail="Missing project_id or schema")

        result = await schema_service.index_schema(
            project_id=project_id,
            data_source_config={},
            schema_data=schema
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dagster workflow endpoints
@app.post("/dagster/trigger")
async def trigger_dagster_workflow(request: WorkflowTriggerRequest):
    """Trigger Dagster workflow execution"""
    if not DAGSTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dagster not available")
    
    try:
        # Get Dagster instance
        instance = DagsterInstance.get()
        
        # Build run configuration
        run_config = _build_dagster_run_config(request)
        
        # Execute based on workflow type
        if request.workflow_type == "schema_ingestion":
            result = materialize(
                [defs.get_asset_graph().get("database_schema")],
                instance=instance,
                tags=request.tags or {},
                run_config=run_config
            )
        elif request.workflow_type == "query_generation":
            result = materialize(
                [defs.get_asset_graph().get("sql_query_asset")],
                instance=instance,
                tags=request.tags or {},
                run_config=run_config
            )
        elif request.workflow_type == "full_pipeline":
            result = materialize(
                list(defs.get_asset_graph().assets),
                instance=instance,
                tags=request.tags or {},
                run_config=run_config
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown workflow type: {request.workflow_type}")
        
        # Update Laravel via webhook
        await _notify_laravel_workflow_started(request.workflow_run_id, result.run_id)
        
        return {
            "run_id": result.run_id,
            "status": "started",
            "workflow_type": request.workflow_type
        }
        
    except Exception as e:
        await _notify_laravel_workflow_failed(request.workflow_run_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dagster/status/{run_id}")
async def get_workflow_status(run_id: str):
    """Get Dagster workflow execution status"""
    if not DAGSTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dagster not available")
    
    try:
        instance = DagsterInstance.get()
        run = instance.get_run_by_id(run_id)
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        return WorkflowStatusResponse(
            run_id=run_id,
            status=run.status.value,
            started_at=run.start_time,
            completed_at=run.end_time,
            error_message=None  # TODO: Extract from run if available
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dagster/runs")
async def list_workflow_runs(project_id: Optional[str] = None, limit: int = 10):
    """List recent workflow runs"""
    if not DAGSTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Dagster not available")
    
    try:
        instance = DagsterInstance.get()
        runs = instance.get_runs(limit=limit)
        
        # Filter by project if specified
        if project_id:
            runs = [run for run in runs if run.tags.get("project_id") == project_id]
        
        return [
            WorkflowStatusResponse(
                run_id=run.run_id,
                status=run.status.value,
                started_at=run.start_time,
                completed_at=run.end_time
            )
            for run in runs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _build_dagster_run_config(request: WorkflowTriggerRequest) -> Dict[str, Any]:
    """Build Dagster run configuration"""
    base_config = {
        "resources": {
            "database_resource": {
                "config": {
                    "laravel_api_url": os.getenv("LARAVEL_API_URL", "http://localhost:8000/api"),
                    "api_token": os.getenv("LARAVEL_API_TOKEN", "")
                }
            },
            "vector_store_resource": {
                "config": {
                    "weaviate_url": os.getenv("WEAVIATE_URL", "http://localhost:8080")
                }
            },
            "llm_provider_resource": {
                "config": {
                    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
                    "model_name": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                }
            }
        }
    }
    
    # Merge with request config
    if request.config:
        base_config.update(request.config)
    
    return base_config

async def _notify_laravel_workflow_started(workflow_run_id: int, dagster_run_id: str):
    """Notify Laravel that workflow started"""
    import httpx
    
    try:
        laravel_url = os.getenv("LARAVEL_API_URL", "http://localhost:8000/api")
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{laravel_url}/workflows/{workflow_run_id}/started",
                json={"dagster_run_id": dagster_run_id},
                headers={"Authorization": f"Bearer {os.getenv('LARAVEL_API_TOKEN', '')}"},
                timeout=10
            )
    except Exception as e:
        print(f"Failed to notify Laravel of workflow start: {e}")

async def _notify_laravel_workflow_failed(workflow_run_id: int, error_message: str):
    """Notify Laravel that workflow failed"""
    import httpx
    
    try:
        laravel_url = os.getenv("LARAVEL_API_URL", "http://localhost:8000/api")
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{laravel_url}/workflows/{workflow_run_id}/failed",
                json={"error_message": error_message},
                headers={"Authorization": f"Bearer {os.getenv('LARAVEL_API_TOKEN', '')}"},
                timeout=10
            )
    except Exception as e:
        print(f"Failed to notify Laravel of workflow failure: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Configuration/Dependency diagnostics
    llm_configured = llm_provider.__class__.__name__ != "NotConfiguredLLMProvider"
    embeddings_configured = embeddings_provider.__class__.__name__ != "NotConfiguredEmbeddingsProvider"
    vector_store_configured = vector_store.__class__.__name__ not in ("NotConfiguredVectorStore",)

    vector_store_ok = False
    vector_store_error = None
    if vector_store_configured:
        try:
            # Try a lightweight call; collection existence will return False or raise on connectivity issues
            _ = await vector_store.collection_exists("health_check")
            vector_store_ok = True
        except Exception as e:
            vector_store_error = str(e)

    return {
        "status": "healthy",
        "service": "hugdata-ai",
        "dagster_available": DAGSTER_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": app.version,
        "checks": {
            "llm_configured": llm_configured,
            "embeddings_configured": embeddings_configured,
            "vector_store_configured": vector_store_configured,
            "vector_store_ok": vector_store_ok,
            "vector_store_error": vector_store_error,
        },
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
