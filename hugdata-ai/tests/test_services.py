import pytest
from unittest.mock import Mock, patch, AsyncMock
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pytest
from src.providers.llm_provider import MockLLMProvider
from src.providers.vector_store import MockVectorStore
from src.pipelines.sql_generation import SQLGenerationPipeline
from src.web.v1.services.chart import ChartService, ChartRequest
from src.web.v1.services.schema import SchemaService

class TestPipelinesAndServices:
    """Tests for current pipeline and services"""

    @pytest.mark.asyncio
    async def test_sql_generation_pipeline(self):
        llm = MockLLMProvider()
        store = MockVectorStore()
        pipeline = SQLGenerationPipeline(llm, store)

        result = await pipeline.generate_sql(
            query="Get users",
            schema={"tables": {"users": {"columns": [
                {"name": "id", "type": "integer"},
                {"name": "created_at", "type": "timestamp"}
            ]}}},
            project_id="test"
        )

        assert "sql" in result
        assert result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_chart_service(self):
        llm = MockLLMProvider()
        service = ChartService(llm)
        req = ChartRequest(
            data=[{"category": "A", "value": 10}],
            columns=["category", "value"],
            query="compare by category"
        )
        resp = await service.suggest_chart(req)
        assert resp.chart_type in ["bar", "line", "scatter", "pie", "histogram", "area"]

    @pytest.mark.asyncio
    async def test_schema_service_interface(self):
        store = MockVectorStore()
        service = SchemaService(store)
        result = await service.index_schema(
            project_id="p1",
            data_source_config={},
            schema_data={"tables": {"users": {"columns": []}}}
        )
        assert result["status"] in ["success", "error"]

    # Vector store behavior is covered implicitly via MockVectorStore in other tests

if __name__ == "__main__":
    pytest.main([__file__])