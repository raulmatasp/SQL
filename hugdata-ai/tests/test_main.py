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

    def test_health_check_detailed(self):
        """Test detailed health check with dependencies"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "timestamp" in data

class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

class TestQueryEndpoint:
    """Test AI query endpoint"""
    
    @patch('main.process_query')
    def test_query_endpoint_success(self, mock_process_query):
        """Test successful query processing"""
        mock_process_query.return_value = {
            "query": "test query",
            "sql": "SELECT * FROM test",
            "result": [{"id": 1, "name": "test"}],
            "insights": "Test insight"
        }
        
        response = client.post("/query", json={
            "query": "test query",
            "database_schema": {"tables": []}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert data["sql"] == "SELECT * FROM test"

    def test_query_endpoint_invalid_input(self):
        """Test query endpoint with invalid input"""
        response = client.post("/query", json={})
        assert response.status_code == 422  # Validation error

    @patch('main.process_query')
    def test_query_endpoint_processing_error(self, mock_process_query):
        """Test query endpoint with processing error"""
        mock_process_query.side_effect = Exception("Processing error")
        
        response = client.post("/query", json={
            "query": "test query",
            "database_schema": {"tables": []}
        })
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data

class TestSchemaEndpoint:
    """Test database schema endpoint"""
    
    @patch('main.get_database_schema')
    def test_schema_endpoint_success(self, mock_get_schema):
        """Test successful schema retrieval"""
        mock_get_schema.return_value = {
            "tables": [
                {"name": "users", "columns": [{"name": "id", "type": "integer"}]}
            ]
        }
        
        response = client.get("/schema")
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
        assert len(data["tables"]) == 1

    @patch('main.get_database_schema')
    def test_schema_endpoint_error(self, mock_get_schema):
        """Test schema endpoint with error"""
        mock_get_schema.side_effect = Exception("Database connection error")
        
        response = client.get("/schema")
        assert response.status_code == 500

class TestChatEndpoint:
    """Test chat endpoint"""
    
    @patch('main.process_chat_message')
    def test_chat_endpoint_success(self, mock_process_chat):
        """Test successful chat message processing"""
        mock_process_chat.return_value = {
            "message": "test response",
            "context": "test context"
        }
        
        response = client.post("/chat", json={
            "message": "Hello",
            "context": []
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "test response"

    def test_chat_endpoint_invalid_input(self):
        """Test chat endpoint with invalid input"""
        response = client.post("/chat", json={})
        assert response.status_code == 422

class TestMetricsEndpoint:
    """Test metrics endpoint"""
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint returns Prometheus format"""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Check if it's Prometheus format
        assert "# HELP" in response.text or "# TYPE" in response.text

class TestConfigEndpoint:
    """Test configuration endpoint"""
    
    def test_config_endpoint(self):
        """Test configuration endpoint returns system info"""
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "environment" in data
        assert "debug" in data

if __name__ == "__main__":
    pytest.main([__file__])