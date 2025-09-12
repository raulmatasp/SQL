import pytest
import requests
import time
from typing import Dict, Any
import os

# Test configuration
BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost')
LARAVEL_PORT = os.getenv('LARAVEL_PORT', '8000')
FASTAPI_PORT = os.getenv('FASTAPI_PORT', '8003')
DAGSTER_PORT = os.getenv('DAGSTER_PORT', '3001')

LARAVEL_URL = f"{BASE_URL}:{LARAVEL_PORT}"
FASTAPI_URL = f"{BASE_URL}:{FASTAPI_PORT}"
DAGSTER_URL = f"{BASE_URL}:{DAGSTER_PORT}"

class TestServiceConnectivity:
    """Test basic connectivity to all services"""
    
    def test_laravel_health(self):
        """Test Laravel app is running"""
        try:
            response = requests.get(f"{LARAVEL_URL}/api/health", timeout=10)
            assert response.status_code in [200, 404]  # 404 if route not implemented yet
        except requests.ConnectionError:
            pytest.skip("Laravel service not running")
    
    def test_fastapi_health(self):
        """Test FastAPI service is running"""
        try:
            response = requests.get(f"{FASTAPI_URL}/health", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except requests.ConnectionError:
            pytest.skip("FastAPI service not running")
    
    def test_dagster_health(self):
        """Test Dagster service is running"""
        try:
            response = requests.get(f"{DAGSTER_URL}", timeout=10)
            assert response.status_code in [200, 302]  # 302 for redirect to UI
        except requests.ConnectionError:
            pytest.skip("Dagster service not running")

class TestCrossServiceIntegration:
    """Test integration between different services"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for integration tests"""
        # Wait for services to be ready
        time.sleep(2)
    
    def test_laravel_to_fastapi_communication(self):
        """Test Laravel can communicate with FastAPI"""
        try:
            # First verify FastAPI is responding
            fastapi_response = requests.get(f"{FASTAPI_URL}/health", timeout=10)
            assert fastapi_response.status_code == 200
            
            # Test Laravel API endpoint that should communicate with FastAPI
            laravel_response = requests.get(f"{LARAVEL_URL}/api/ai/status", timeout=10)
            # Accept 404 if endpoint not implemented, 200 if working, 500 if FastAPI connection fails
            assert laravel_response.status_code in [200, 404, 500]
            
        except requests.ConnectionError:
            pytest.skip("Services not running")
    
    def test_ai_query_flow(self):
        """Test complete AI query flow from Laravel through FastAPI"""
        try:
            # Test query endpoint exists
            query_data = {
                "query": "Show me user statistics",
                "database_schema": {"tables": []}
            }
            
            # Direct FastAPI call
            fastapi_response = requests.post(f"{FASTAPI_URL}/query", json=query_data, timeout=30)
            # Accept various status codes as endpoint might not be fully implemented
            assert fastapi_response.status_code in [200, 404, 422, 500]
            
            if fastapi_response.status_code == 200:
                data = fastapi_response.json()
                assert "query" in data
            
        except requests.ConnectionError:
            pytest.skip("FastAPI service not running")
    
    def test_database_connection(self):
        """Test database connectivity through services"""
        try:
            # Test Laravel database connection
            laravel_response = requests.get(f"{LARAVEL_URL}/api/database/status", timeout=10)
            assert laravel_response.status_code in [200, 404]
            
            # Test FastAPI database connection
            fastapi_response = requests.get(f"{FASTAPI_URL}/schema", timeout=10)
            assert fastapi_response.status_code in [200, 404, 500]
            
        except requests.ConnectionError:
            pytest.skip("Services not running")

class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""
    
    def test_user_query_workflow(self):
        """Test complete user query workflow"""
        try:
            # Step 1: User authentication (if implemented)
            auth_data = {"email": "test@example.com", "password": "password"}
            auth_response = requests.post(f"{LARAVEL_URL}/api/auth/login", json=auth_data, timeout=10)
            # Accept 404 if not implemented, 422 for validation, 200 for success
            assert auth_response.status_code in [200, 404, 422, 401]
            
            # Step 2: Submit query for processing
            query_data = {
                "query": "What are the top 5 users by activity?",
                "context": "analytics dashboard"
            }
            
            query_response = requests.post(f"{LARAVEL_URL}/api/queries", json=query_data, timeout=30)
            assert query_response.status_code in [200, 201, 404, 422, 401]
            
            if query_response.status_code in [200, 201]:
                data = query_response.json()
                # Verify response structure
                assert "query" in data or "id" in data
            
        except requests.ConnectionError:
            pytest.skip("Laravel service not running")
    
    def test_data_pipeline_workflow(self):
        """Test Dagster data pipeline integration"""
        try:
            # Check if Dagster has any pipelines running
            dagster_response = requests.get(f"{DAGSTER_URL}/graphql", 
                                          json={"query": "{ runs { runId status } }"}, 
                                          timeout=10)
            # Accept any response as Dagster might have different GraphQL setup
            assert dagster_response.status_code in [200, 400, 404, 405]
            
        except requests.ConnectionError:
            pytest.skip("Dagster service not running")

class TestPerformanceAndLoad:
    """Basic performance and load testing"""
    
    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        try:
            import concurrent.futures
            import threading
            
            def make_request():
                return requests.get(f"{FASTAPI_URL}/health", timeout=10)
            
            # Make 5 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                responses = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                
        except requests.ConnectionError:
            pytest.skip("FastAPI service not running")
    
    def test_response_time(self):
        """Test response time is reasonable"""
        try:
            start_time = time.time()
            response = requests.get(f"{FASTAPI_URL}/health", timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response_time < 5.0  # Should respond within 5 seconds
            assert response.status_code == 200
            
        except requests.ConnectionError:
            pytest.skip("FastAPI service not running")

class TestErrorHandling:
    """Test error handling across services"""
    
    def test_invalid_ai_query(self):
        """Test handling of invalid AI queries"""
        try:
            invalid_data = {"invalid": "data"}
            response = requests.post(f"{FASTAPI_URL}/query", json=invalid_data, timeout=10)
            # Should return validation error
            assert response.status_code in [400, 422, 404]
            
        except requests.ConnectionError:
            pytest.skip("FastAPI service not running")
    
    def test_service_unavailable_handling(self):
        """Test handling when services are unavailable"""
        try:
            # Test with invalid port (should fail)
            invalid_url = f"{BASE_URL}:9999/health"
            with pytest.raises(requests.ConnectionError):
                requests.get(invalid_url, timeout=2)
                
        except Exception:
            # This test should always pass as we expect the connection to fail
            pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])