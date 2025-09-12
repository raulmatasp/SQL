from dagster import ConfigurableResource
from typing import Dict, Any, List
import os
import httpx

class DatabaseResource(ConfigurableResource):
    """Database connection resource for schema introspection"""
    
    laravel_api_url: str = "http://localhost:8000/api"
    api_token: str = ""
    
    def get_schema(self, project_id: str) -> Dict[str, Any]:
        """Get database schema from Laravel API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            response = httpx.get(
                f"{self.laravel_api_url}/projects/{project_id}/schema",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            # Fallback to mock schema for development
            return self._get_mock_schema()
    
    def get_data_sources(self, project_id: str) -> List[Dict[str, Any]]:
        """Get available data sources for project"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            response = httpx.get(
                f"{self.laravel_api_url}/projects/{project_id}/data-sources",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            return []
    
    def _get_mock_schema(self) -> Dict[str, Any]:
        """Mock schema for development"""
        return {
            "tables": {
                "users": {
                    "columns": [
                        {"name": "id", "type": "bigint", "nullable": False},
                        {"name": "name", "type": "varchar", "nullable": False},
                        {"name": "email", "type": "varchar", "nullable": False},
                        {"name": "created_at", "type": "timestamp", "nullable": True},
                        {"name": "updated_at", "type": "timestamp", "nullable": True}
                    ]
                },
                "orders": {
                    "columns": [
                        {"name": "id", "type": "bigint", "nullable": False},
                        {"name": "user_id", "type": "bigint", "nullable": False},
                        {"name": "total", "type": "decimal", "nullable": False},
                        {"name": "status", "type": "varchar", "nullable": False},
                        {"name": "created_at", "type": "timestamp", "nullable": True}
                    ]
                }
            },
            "relationships": [
                {
                    "from_table": "orders",
                    "from_column": "user_id",
                    "to_table": "users",
                    "to_column": "id",
                    "type": "belongs_to"
                }
            ]
        }

database_resource = DatabaseResource(
    laravel_api_url=os.getenv("LARAVEL_API_URL", "http://localhost:8000/api"),
    api_token=os.getenv("LARAVEL_API_TOKEN", "")
)