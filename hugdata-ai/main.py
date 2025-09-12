from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os

from src.providers.llm_provider import OpenAIProvider, MockLLMProvider
from src.providers.vector_store import WeaviateProvider, MockVectorStore
from src.pipelines.sql_generation import SQLGenerationPipeline

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

# Initialize providers
def get_llm_provider():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        return OpenAIProvider(openai_api_key)
    else:
        print("Warning: No OpenAI API key found, using mock provider")
        return MockLLMProvider()

def get_vector_store():
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    try:
        return WeaviateProvider(weaviate_url)
    except Exception as e:
        print(f"Warning: Weaviate connection failed: {e}, using mock store")
        return MockVectorStore()

# Global instances
llm_provider = get_llm_provider()
vector_store = get_vector_store()
sql_pipeline = SQLGenerationPipeline(llm_provider, vector_store)

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
async def explain_query(sql: str, schema: Dict[str, Any]):
    """Explain SQL query in natural language"""
    try:
        # Mock explanation for now
        # TODO: Implement actual SQL explanation
        return {
            "explanation": f"This query retrieves data from your database tables.",
            "breakdown": {
                "SELECT": "Selects specified columns",
                "FROM": "From the specified table",
                "WHERE": "Filters data based on conditions",
                "LIMIT": "Limits the number of results"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/suggest-charts", response_model=List[ChartSuggestion])
async def suggest_charts(request: ChartSuggestionRequest):
    """Suggest appropriate chart types for query results"""
    try:
        # Mock chart suggestions for now
        # TODO: Implement actual chart suggestion logic
        suggestions = [
            ChartSuggestion(
                chart_type="bar",
                configuration={
                    "xAxis": "category",
                    "yAxis": "value",
                    "title": "Data Distribution"
                },
                confidence=0.9
            ),
            ChartSuggestion(
                chart_type="line",
                configuration={
                    "xAxis": "date",
                    "yAxis": "value",
                    "title": "Trend Over Time"
                },
                confidence=0.8
            )
        ]
        
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index-schema")
async def index_schema(schema: Dict[str, Any], project_id: str):
    """Index database schema for semantic search"""
    try:
        # Mock schema indexing for now
        # TODO: Implement actual schema indexing with vector store
        return {
            "success": True,
            "message": f"Schema indexed for project {project_id}",
            "indexed_tables": len(schema.get("tables", {}))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "hugdata-ai"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)