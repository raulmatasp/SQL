import pytest
from typing import Any, Dict, List

from src.pipelines.sql_correction import SQLCorrectionPipeline, SQLError


class _FakeVectorStore:
    def __init__(self):
        self.last_kwargs: Dict[str, Any] = {}

    async def similarity_search(self, *args, **kwargs) -> List[Dict[str, Any]]:
        self.last_kwargs = kwargs
        return []


class _FakeLLM:
    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        # Return a minimal but valid correction response
        return (
            "CORRECTED_SQL:\n"
            "SELECT id FROM users LIMIT 100;\n\n"
            "EXPLANATION:\nFixed missing FROM clause and added LIMIT.\n\n"
            "CHANGES_MADE:\n- added FROM\n- added LIMIT\n"
        )


@pytest.mark.asyncio
async def test_sql_correction_calls_collection_name_param():
    store = _FakeVectorStore()
    llm = _FakeLLM()
    pipeline = SQLCorrectionPipeline(llm, store)

    err = SQLError(sql="SELECT id users", error="syntax error")

    result = await pipeline.correct_sql(sql_error=err, schema=None, project_id="p1", context={})

    # Ensure the provider was called with the correct parameter name
    assert "collection_name" in store.last_kwargs
    assert "collection" not in store.last_kwargs

    # Validate corrected SQL shape & safety
    corrected = result["corrected_sql"]
    assert corrected.endswith(";")
    for bad in ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]:
        assert bad not in corrected.upper()

