import pytest
from typing import Any, Dict, List, Optional

from src.web.v1.services.schema import SchemaService


class _FlatVectorStore:
    """Fake vector store that returns flat payloads like QdrantProvider does."""

    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = docs

    async def similarity_search(self, query: str, collection_name: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None):
        return self._docs[:limit]

    async def delete_collection(self, collection_name: str) -> bool:
        return True

    async def count_documents(self, collection_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        return len(self._docs)


@pytest.mark.asyncio
async def test_get_table_info_handles_flat_relationship_payload():
    # One table doc and one relationship doc with top-level fields
    docs = [
        {
            "type": "table_description",
            "table_name": "users",
            "content": "Table: users",
            "project_id": "p1",
        },
        {
            "type": "relationship",
            "from_table": "users",
            "to_table": "orders",
            "from_column": "id",
            "to_column": "user_id",
            "project_id": "p1",
            "score": 0.9,
        },
    ]

    service = SchemaService(_FlatVectorStore(docs))
    info = await service.get_table_info(project_id="p1", table_name="users")

    assert info is not None
    assert info["table_info"]["table_name"] == "users"
    # Relationship should be detected from flat doc
    assert any(r.get("from_table") == "users" for r in info["relationships"]) or any(
        r.get("metadata", {}).get("from_table") == "users" for r in info["relationships"]
    )

