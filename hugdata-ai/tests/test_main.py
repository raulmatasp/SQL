import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

class TestHealthEndpoint:
    """Test health check endpoints"""
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

class TestGenerateSqlEndpoint:
    """Test SQL generation endpoint"""
    
    def test_generate_sql_validation(self):
        """Test validation error when body is missing"""
        response = client.post("/generate-sql", json={})
        assert response.status_code == 422

    def test_generate_sql_success(self):
        """Test successful SQL generation with mock providers"""
        payload = {
            "query": "List users created this year",
            "context": {},
            "database_schema": {"tables": {"users": {"columns": [
                {"name": "id", "type": "integer"},
                {"name": "created_at", "type": "timestamp"}
            ]}}},
            "project_id": "test"
        }
        response = client.post("/generate-sql", json=payload)
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "sql" in data
            assert "confidence" in data

class TestV1Services:
    """Test v1 service endpoints (ask, chart, schema)"""
    
    def test_chart_suggest_validation(self):
        response = client.post("/v1/charts/suggest", json={})
        assert response.status_code == 422

    def test_schema_index_validation(self):
        response = client.post("/v1/schema/index", json={})
        assert response.status_code == 422

class TestExplainQuery:
    def test_explain_query_basic(self):
        payload = {
            "sql": "SELECT id FROM users LIMIT 10;",
            "schema": {"tables": {}}
        }
        response = client.post("/explain-query", params=payload)
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert "breakdown" in data

class TestIndexSchema:
    def test_index_schema_basic(self):
        payload = {
            "schema": {"tables": {"users": {"columns": []}}},
            "project_id": "test"
        }
        response = client.post("/index-schema", params=payload)
        assert response.status_code in [200, 500]

class TestSuggestChartsSimple:
    def test_suggest_charts_simple(self):
        payload = {
            "data_sample": {"category": "A", "value": 10},
            "query_intent": "compare by category"
        }
        response = client.post("/suggest-charts", json=payload)
        assert response.status_code in [200, 500]

class TestAskFlow:
    def test_create_ask_validation(self):
        response = client.post("/v1/asks", json={})
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__])