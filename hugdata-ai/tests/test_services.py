import pytest
from unittest.mock import Mock, patch, AsyncMock
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_service import LLMService
from services.database_service import DatabaseService
from services.vector_service import VectorService

class TestLLMService:
    """Test LLM service functionality"""
    
    @pytest.fixture
    def llm_service(self):
        return LLMService()
    
    @patch('services.llm_service.openai')
    def test_generate_sql_success(self, mock_openai, llm_service):
        """Test successful SQL generation"""
        mock_openai.ChatCompletion.create.return_value = {
            "choices": [{"message": {"content": "SELECT * FROM users"}}]
        }
        
        result = llm_service.generate_sql("Get all users", {"tables": []})
        assert result == "SELECT * FROM users"
    
    @patch('services.llm_service.openai')
    def test_generate_sql_error(self, mock_openai, llm_service):
        """Test SQL generation with API error"""
        mock_openai.ChatCompletion.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            llm_service.generate_sql("Get all users", {"tables": []})
    
    @patch('services.llm_service.anthropic')
    def test_fallback_to_anthropic(self, mock_anthropic, llm_service):
        """Test fallback to Anthropic when OpenAI fails"""
        with patch('services.llm_service.openai') as mock_openai:
            mock_openai.ChatCompletion.create.side_effect = Exception("OpenAI Error")
            mock_anthropic.messages.create.return_value = Mock(
                content=[Mock(text="SELECT * FROM products")]
            )
            
            result = llm_service.generate_sql_with_fallback("Get products", {"tables": []})
            assert result == "SELECT * FROM products"
    
    def test_validate_sql(self, llm_service):
        """Test SQL validation"""
        valid_sql = "SELECT id, name FROM users WHERE active = 1"
        invalid_sql = "INVALID SQL STATEMENT"
        
        assert llm_service.validate_sql(valid_sql) is True
        assert llm_service.validate_sql(invalid_sql) is False
    
    def test_extract_insights(self, llm_service):
        """Test insight extraction from query results"""
        mock_data = [
            {"id": 1, "name": "John", "age": 25},
            {"id": 2, "name": "Jane", "age": 30}
        ]
        
        with patch.object(llm_service, 'generate_insights') as mock_generate:
            mock_generate.return_value = "Users average age is 27.5 years"
            
            insights = llm_service.extract_insights(mock_data, "user demographics")
            assert "27.5" in insights

class TestDatabaseService:
    """Test database service functionality"""
    
    @pytest.fixture
    def db_service(self):
        return DatabaseService()
    
    @patch('services.database_service.create_engine')
    def test_connection_success(self, mock_create_engine, db_service):
        """Test successful database connection"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        engine = db_service.get_engine()
        assert engine is not None
    
    @patch('services.database_service.create_engine')
    def test_connection_failure(self, mock_create_engine, db_service):
        """Test database connection failure"""
        mock_create_engine.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            db_service.get_engine()
    
    @patch('services.database_service.text')
    def test_execute_query_success(self, mock_text, db_service):
        """Test successful query execution"""
        mock_connection = Mock()
        mock_result = Mock()
        mock_result.fetchall.return_value = [{"id": 1, "name": "test"}]
        mock_connection.execute.return_value = mock_result
        
        with patch.object(db_service, 'get_connection', return_value=mock_connection):
            result = db_service.execute_query("SELECT * FROM test")
            assert len(result) == 1
            assert result[0]["name"] == "test"
    
    @patch('services.database_service.text')
    def test_execute_query_error(self, mock_text, db_service):
        """Test query execution error"""
        mock_connection = Mock()
        mock_connection.execute.side_effect = Exception("SQL Error")
        
        with patch.object(db_service, 'get_connection', return_value=mock_connection):
            with pytest.raises(Exception):
                db_service.execute_query("INVALID SQL")
    
    def test_get_schema(self, db_service):
        """Test schema retrieval"""
        mock_tables = [
            {"table_name": "users", "column_name": "id", "data_type": "integer"},
            {"table_name": "users", "column_name": "name", "data_type": "varchar"}
        ]
        
        with patch.object(db_service, 'execute_query', return_value=mock_tables):
            schema = db_service.get_database_schema()
            assert "users" in schema["tables"]
            assert len(schema["tables"]["users"]["columns"]) == 2

class TestVectorService:
    """Test vector service functionality"""
    
    @pytest.fixture
    def vector_service(self):
        return VectorService()
    
    @patch('services.vector_service.weaviate')
    def test_connection_success(self, mock_weaviate, vector_service):
        """Test successful Weaviate connection"""
        mock_client = Mock()
        mock_weaviate.Client.return_value = mock_client
        
        client = vector_service.get_client()
        assert client is not None
    
    @patch('services.vector_service.weaviate')
    def test_connection_failure(self, mock_weaviate, vector_service):
        """Test Weaviate connection failure"""
        mock_weaviate.Client.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            vector_service.get_client()
    
    def test_store_embedding_success(self, vector_service):
        """Test successful embedding storage"""
        mock_client = Mock()
        
        with patch.object(vector_service, 'get_client', return_value=mock_client):
            result = vector_service.store_embedding(
                "test query",
                [0.1, 0.2, 0.3],
                {"sql": "SELECT * FROM test"}
            )
            assert result is True
    
    def test_search_similar_queries(self, vector_service):
        """Test similar query search"""
        mock_client = Mock()
        mock_results = {
            "data": {
                "Get": {
                    "Query": [
                        {
                            "query": "similar query",
                            "sql": "SELECT * FROM similar",
                            "_additional": {"distance": 0.1}
                        }
                    ]
                }
            }
        }
        mock_client.query.get.return_value.with_near_vector.return_value.with_limit.return_value.do.return_value = mock_results
        
        with patch.object(vector_service, 'get_client', return_value=mock_client):
            results = vector_service.search_similar_queries([0.1, 0.2, 0.3])
            assert len(results) == 1
            assert results[0]["query"] == "similar query"

if __name__ == "__main__":
    pytest.main([__file__])