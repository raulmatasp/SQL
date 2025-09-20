# HugData AI – Mocks, Stubs, and Incomplete Areas

Scope: Analysis of `hugdata-ai/` and top-level `tests/` to identify mocked components, placeholders, and incomplete or inconsistent implementations.

Generated: current workspace snapshot

## High-Level Summary

- The FastAPI app in `hugdata-ai` is operational with multiple services and routers, but many dependencies are intentionally mocked for local/dev use (LLM, embeddings, vector store, Dagster resources).
- Several pipelines and services reference vector-store methods that do not exist or have mismatched signatures, indicating incomplete integration work.
- Dagster assets and resources include mock implementations and generated data for development.
- Tests (both `hugdata-ai/tests` and top-level `tests/test_integration.py`) function largely as smoke tests; they tolerate broad status codes and use skips when services are unavailable.

## Mocked and Stubbed Components

- LLM Provider (`hugdata-ai/src/providers/llm_provider.py`)
  - `MockLLMProvider.generate(...)` returns canned SQL snippets or a generic fallback based on prompt keywords.
  - `OpenAIProvider` exists but requires environment/API key; `main.py` defaults to mock if `OPENAI_API_KEY` is absent.

- Embeddings Provider (`hugdata-ai/src/providers/embeddings_provider.py`)
  - `MockEmbeddingsProvider` generates deterministic pseudo-random vectors from text hashes.
  - `OpenAIEmbeddingsProvider` and `HuggingFaceEmbeddingsProvider` are available for real embeddings but aren’t used by default without proper env/deps.

- Vector Store (`hugdata-ai/src/providers/vector_store.py`)
  - `WeaviateProvider` is effectively a stub: client import is commented out; methods return hard-coded mock data and `True` for writes; prints a warning on init.
  - `MockVectorStore` provides in-memory storage for `add_documents`, `delete_collection`, and `count_documents`, and returns canned results for `similarity_search`.

- Dagster Resources and Assets (`hugdata-ai/dagster_project/...`)
  - `resources/llm_provider.py`: wraps a client, but falls back to `MockLLMClient` and returns mock completions when OpenAI isn’t configured.
  - `resources/vector_store.py`: attempts to create a client but falls back to `MockVectorStoreClient`; `index_schema` and `similarity_search` return mock success/data.
  - `resources/database.py`: fetches from Laravel; on failure returns a mock schema (users/orders with a simple relationship).
  - `assets/analytics.py`: multiple places explicitly generate “mock” metrics and trends (e.g., “Generate KPI trends (mock data for now)”, mock performance estimates).

- FastAPI main (`hugdata-ai/main.py`)
  - Provider factory functions fall back to mock providers when env is missing or connection fails.
  - TODO present: `error_message=None  # TODO: Extract from run if available` in Dagster run status response.

## Incomplete or Inconsistent Implementations

1) Vector store interface drift (multiple files)
- Current abstract `VectorStore` exposes: `similarity_search(query, collection, limit)`, `index_document(...)`, `add_documents(documents, collection_name)`, `delete_collection(collection_name)`, `count_documents(collection_name, filters=None)`.
- Several pipelines/services reference methods not defined in `VectorStore` and/or use mismatched signatures:
  - `src/web/v1/services/schema.py` calls `self.vector_store.search(...)` with filters and collection name, which does not exist on `VectorStore` or `MockVectorStore`.
  - `src/pipelines/indexing/table_description.py` expects `collection_exists`, `create_collection`, `get_collection_stats`, and `delete_documents`; also calls `add_documents(collection_name, documents)` (reversed arg order from the abstract signature).
  - `src/pipelines/indexing/sql_pairs.py` also expects `collection_exists`, `create_collection`, `get_collection_stats`, and `delete_documents`; calls `add_documents(collection_name, documents)` (again reversed).

Impact: These code paths will break at runtime unless the vector-store interface is expanded or the pipelines/services are refactored to align with the current interface.

2) Weaviate provider is a placeholder
- `WeaviateProvider` in `src/providers/vector_store.py` has the weaviate client/commented-out schema management and returns mock data. It logs/prints a warning during initialization rather than establishing a real connection.

3) Error handling and TODOs
- `main.py` Dagster status: `error_message` is left as a TODO; error extraction from Dagster run is not implemented.
- Multiple pipelines raise generic `Exception` wrappers; more granular error types could be useful but not strictly required.

4) Tests reflect incomplete endpoints and mock usage
- `hugdata-ai/tests/test_main.py` and `hugdata-ai/tests/test_services.py` rely on mock providers; they accept broad ranges of status codes (200/422/500) and do not fail if the service returns an error, serving as smoke checks.
- Top-level `tests/test_integration.py` purposefully `skip`s if services aren’t running and tolerates 404/500 for not-yet-implemented routes. One test ends with a bare `pass` in an exception clause, explicitly allowing the failure path.

## File-Level Notes (selected)

- `src/web/v1/services/schema.py`
  - Uses `await self.vector_store.search(...)` with `filters` and `collection_name`. No such method on `VectorStore`/`MockVectorStore`. Should likely call `similarity_search(...)` and filter client-side, or extend `VectorStore` accordingly.

- `src/pipelines/indexing/table_description.py`
  - Uses undefined vector-store methods: `collection_exists`, `create_collection`, `get_collection_stats`, `delete_documents`.
  - Calls `add_documents(collection_name, documents)` — argument order mismatch vs abstract interface (`add_documents(documents, collection_name)`).

- `src/pipelines/indexing/sql_pairs.py`
  - Same undefined methods as above; same `add_documents` arg order issue.

- `src/providers/vector_store.py`
  - `WeaviateProvider` is mock/stub. `MockVectorStore` supports a subset of expected methods, but lacks the extra collection-management API used by indexing pipelines.

- `dagster_project/assets/analytics.py`
  - Multiple explicit mock data generation blocks and comments (e.g., KPI trends, performance estimates).

- `main.py`
  - Provider getters default to mocks in absence of env/key or failed connections.
  - Dagster status endpoint leaves `error_message` extraction as TODO.

## Recommendations and Next Steps

Short-term fixes (to unblock usage and tests):
- Align `VectorStore` interface:
  - Option A: Extend `VectorStore` and `MockVectorStore` with the collection-management/search methods used by indexing pipelines: `collection_exists`, `create_collection`, `get_collection_stats`, `delete_documents`, and optional `search(query, collection_name, limit, filters)`.
  - Option B: Refactor pipelines/services to only use the currently defined methods. For filtering, use `similarity_search(...)` then filter results in code via metadata.
  - Fix argument order in calls to `add_documents(...)` within `table_description.py` and `sql_pairs.py`.

- Implement `SchemaService.search_schema` using supported operations:
  - Either implement `VectorStore.search(...)` or translate to `similarity_search(...)` and perform client-side filtering by `metadata`.

- Replace remaining `print` warnings with `logging` for consistency (`WeaviateProvider` and `main.py` provider getters).

- Implement Dagster run `error_message` extraction in `/dagster/status/{run_id}` if available from run metadata.

Longer-term improvements:
- Flesh out `WeaviateProvider` with real client init, schema ensure, and CRUD operations; gate with configuration and feature flags to keep local dev flow smooth.
- Harden error types and messages in pipelines (avoid generic `Exception` where actionable typed errors help).
- Make tests assert on narrower, expected behaviors (minimize 200/422/500 catch-alls) as endpoints stabilize; consider adding unit tests for indexing pipelines once vector-store interface is settled.

## Quick Reference: Observed Mocks/Placeholders

- LLM: `MockLLMProvider`, Dagster `MockLLMClient`.
- Embeddings: `MockEmbeddingsProvider`.
- Vector Store: `WeaviateProvider` stub; `MockVectorStore` in-memory and partial API.
- Dagster Analytics: mock trend/performance/coverage calculations.
- Tests: smoke-level acceptance of multiple status codes; skips for non-running services.

## Potential Breakpoints (most likely to raise at runtime)

- Calls to missing vector-store methods (collection existence/stats/creation, delete by filter, generic search).
- Reversed argument order for `add_documents(...)` in indexing pipelines.
- `SchemaService.search_schema` attempting to use nonexistent `vector_store.search(...)`.

Addressing the above will consolidate the API boundary for the vector store and make indexing/search features executable end-to-end without mocks.

