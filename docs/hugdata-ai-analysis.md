**HugData AI Service — Codebase Analysis (hugdata-ai)**

- Scope: FastAPI app, providers, pipelines, v1 web services/routers, and Dagster assets/resources under `hugdata-ai/`.
- Focus: Identify mocked or incomplete functionality and concrete defects; propose test-first tasks to drive fixes.

**High-Level Architecture**

- FastAPI app: `main.py` wires providers, pipelines, services, and routes (v1 ask/chart/schema + SQL corrections + relationship recommendations; Dagster control endpoints).
- Providers: `src/providers/` abstractions and implementations for LLM, embeddings, and vector store (Qdrant). Mock and NotConfigured variants included.
- Pipelines: `src/pipelines/` for SQL generation, SQL correction, relationship recommendation, and schema indexing (`indexing/`).
- Web services: `src/web/v1/services/` with DI container; routers in `src/web/v1/routers/` expose HTTP endpoints.
- Dagster: `hugdata-ai/dagster_project/` assets/jobs/resources/sensors. Several assets intentionally mock analytics/optimization.
- Tests: `hugdata-ai/tests/` basic endpoint and service tests; use mocks for providers and vector store.

**Key Modules and Responsibilities**

- `main.py`
  - Initializes `OpenAIProvider`/`QdrantProvider`/`OpenAIEmbeddingsProvider` when configured; else NotConfigured variants.
  - Binds services: Ask, Chart, Schema; includes v1 routers and advanced routers (SQL corrections, relationship recommendations).
  - Provides endpoints: `/generate-sql`, `/explain-query`, `/suggest-charts`, `/index-schema`, and Dagster endpoints.
  - Health check reports configuration and vector store connectivity.

- Providers
  - LLM: `OpenAIProvider` (async, chat completions), `MockLLMProvider` (returns canned SQL), `NotConfiguredLLMProvider` (clear error).
  - Embeddings: `OpenAIEmbeddingsProvider` (async embeddings), `HuggingFaceEmbeddingsProvider` (sync model wrapped via executor), `MockEmbeddingsProvider`, `NotConfiguredEmbeddingsProvider`.
  - Vector store: `QdrantProvider` (collection mgmt, upsert, search, counts), `MockVectorStore`, `NotConfiguredVectorStore`.

- Pipelines
  - SQL generation (`SQLGenerationPipeline`): RAG-style prompt building, LLM call, SQL extraction/cleanup, simple confidence metric.
  - SQL correction (`SQLCorrectionPipeline`): error analysis, prompt building, LLM correction, cleanup, simple validation.
  - Relationship recommendation: cleans MDL, prompts LLM for JSON relationships, normalizes and validates against model.
  - Indexing (`SchemaIndexingPipeline`): Generates and upserts table/column/relationship docs into vector store.

- Web v1 services and routers
  - Ask: background NL→SQL generation via pipeline; in-memory tracking.
  - Chart: suggests chart type via LLM with heuristics fallback; generates Vega-Lite schema.
  - Schema: index/search/summarize schema using indexing pipeline and vector store.
  - SQL corrections and Relationship recommendations: job/event style background operations with status polling.

- Dagster project
  - Assets: schema ingestion, vector indexing, SQL generation, semantic modeling, analytics and optimization assets; several mock/heuristic analyses.
  - Resources: `LLMProviderResource`, `VectorStoreResource`, `DatabaseResource` (has mock schema fallback); Jobs & sensors defined.

**Mocked / Incomplete / Placeholder Areas**

- NotConfigured providers: `NotConfiguredLLMProvider`, `NotConfiguredEmbeddingsProvider`, `NotConfiguredVectorStore` are explicit “disabled” implementations for missing config.
- Mock providers: `MockLLMProvider`, `MockEmbeddingsProvider`, `MockVectorStore` used in tests and local dev.
- Dagster resources intentionally not implemented for indexing/search:
  - `dagster_project/resources/vector_store.py`: `index_schema` and `similarity_search` raise RuntimeError indicating API service should be used instead.
- Dagster analytics/optimization assets contain mock calculations and heuristics (e.g., query execution plan, KPI trends, entity health).
- Chart router `/v1/charts/adjust` explicitly returns “coming soon” placeholder response.
- Ask service stores state in-memory; no persistence/backpressure/cancellation integration.
- `SQLGenerationPipeline.generate_sql` currently ignores `mdl_hash` and `histories` (accepted args but unused), implying future enhancement planned.

**Defects and Design Inconsistencies**

1) SQLCorrectionPipeline uses wrong parameter name for vector search
   - File: `src/pipelines/sql_correction.py`
   - Code: `self.vector_store.similarity_search(..., collection=f"schema_{project_id}", ...)`
   - Vector store interface expects `collection_name`, not `collection` (see `VectorStore.similarity_search`).
   - Effect: TypeError at runtime when correcting SQL with a configured vector store.
   - Test-first TODO:
     - Add a unit test asserting `correct_sql` calls `similarity_search` with `collection_name` and returns a corrected SQL string with a `;` and no dangerous keywords.
     - Example: create a stub vector store that records kwargs and returns empty context; assert no `collection` kwarg; assert `corrected_sql` ends with `;` and confidence ∈ [0,1].

2) Dagster LLMProviderResource declared async but used synchronously in assets
   - File: `dagster_project/resources/llm_provider.py` has `async def generate(...)`.
   - File: `dagster_project/assets/query_generation.py` calls `llm_provider_resource.generate(...)` without `await` in a synchronous asset.
   - Effect: A coroutine object would be passed to `_parse_llm_response`, breaking SQL parsing.
   - Test-first TODO:
     - Add a test asserting `inspect.iscoroutinefunction(LLMProviderResource.generate)` is False, or exercising `sql_query_asset` with a fake resource whose `generate` returns a string; the current code should fail, guiding a change to make `generate` synchronous.

3) Schema search result shape mismatch (metadata nesting)
   - Qdrant provider flattens document fields and merges `metadata` into the top-level payload on write, then returns that flattened payload at search time.
   - `SchemaService.get_table_info` and join suggestion logic sometimes expect nested `metadata` (e.g., `rel.get("metadata", {}).get("from_table")`).
   - Effect: When backed by Qdrant, `get_table_info` relationship filtering can silently fail (fields like `from_table` present at top-level, not under `metadata`).
   - Test-first TODO:
     - Add tests for `SchemaService.get_table_info` and `suggest_joins` with a fake vector store returning flat payload documents (top-level `type`, `table_name`, `from_table`, `to_table`), verifying relationships/joins are found. This will fail until service logic is updated to handle flat payloads.

4) Dagster VectorStoreResource functions unimplemented by design
   - File: `dagster_project/resources/vector_store.py` raises `RuntimeError` for `index_schema` and `similarity_search`.
   - Effect: Any asset that tries to use these will fail; current assets call them (e.g., `schema_vector_index` does `vector_store_resource.index_schema(...)`). If run, that asset will raise.
   - Test-first TODO:
     - Add a unit test asserting these methods raise with the current clear message. Optionally, propose implementing a minimal “pass-through” to the API or a mock in Dagster context; but codify intent with tests so failures are explicit.

5) `/v1/charts/adjust` is a placeholder
   - Returns a simple message: "Chart adjustment feature coming soon".
   - Test-first TODO:
     - Add an API test that asserts HTTP 200 and that the response contains a `message` and echoes back `request`, so future behavior can evolve under a tested contract.

6) SQL generation extras accepted but unused
   - `SQLGenerationPipeline.generate_sql` accepts `mdl_hash` and `histories` but ignores them.
   - Effect: Ask service passes them but they have no effect; risk of confusion.
   - Test-first TODO:
     - Add a unit test documenting current behavior (they are ignored) to lock the contract, or a design test specifying how they should influence prompt/SQL; then implement accordingly (e.g., include last history in prompt context).

7) Minor robustness gap in `main.py` Dagster status
   - `get_workflow_status` returns `error_message=None  # TODO:`; missing extraction from Dagster run if available.
   - Test-first TODO:
     - Add a test fixture that fakes Dagster instance/run object to include an error; assert `error_message` is populated from the run when present.

8) Explain-query JSON fallback may not strictly return JSON
   - In `/explain-query`, the LLM-based fallback requests JSON but attempts `json.loads` on raw output; model drift may return prose.
   - Test-first TODO:
     - Add a unit test that simulates a non-JSON LLM output and asserts the endpoint returns HTTP 500 (current) or a robust fallback structure; then harden parsing with tolerant extraction and a safe default.

9) Indexing pipeline and embeddings coupling
   - `SchemaIndexingPipeline` upserts docs without embeddings; `QdrantProvider.add_documents` computes embeddings if an embeddings provider is configured; otherwise raises.
   - Effect: If `QdrantProvider` is constructed without embeddings provider, indexing fails.
   - Test-first TODO:
     - Add an integration-style test that constructs `QdrantProvider` with `NotConfiguredEmbeddingsProvider` and asserts `SchemaService.index_schema` returns an error status. Alternatively, prefer explicit failure detection up-front in service with a specific message and test for it.

**Quick Wins / Suggested Fixes (guided by tests above)**

- Fix 1: In `SQLCorrectionPipeline`, rename `collection` to `collection_name` in the similarity search call.
- Fix 2: Make `LLMProviderResource.generate` synchronous (def), or `await` it within assets (Dagster assets are sync today, so prefer sync def to keep assets simple). Update tests accordingly.
- Fix 3: Normalize schema document shape across the stack. EITHER:
  - Update `QdrantProvider.similarity_search` to return a nested `metadata` field (preserving a flat mirror if needed), OR
  - Update `SchemaService` to read from top-level fields instead of `metadata`. Drive with tests for `get_table_info` and `suggest_joins` using flat payloads.
- Fix 4: In Dagster assets that currently call unimplemented resource methods, replace with no-op or API call (behind env-guard), or skip asset execution unless configured. Keep tests asserting current error until implemented.
- Fix 5: Either remove `/index-schema` ad-hoc endpoint in `main.py` in favor of `/v1/schema/index` or ensure parity. Add tests to favor v1 route.

**Test Coverage Gaps (additions recommended)**

- Pipeline tests
  - SQL correction end-to-end with mocked LLM and vector store; ensure parameter naming and cleaning rules enforced.
  - Relationship recommendation parsing/validation with malformed LLM outputs.

- Service tests
  - SchemaService.get_table_info/suggest_joins with flat and nested metadata shapes to lock behavior.
  - AskService lifecycle: create → result polling → stop.

- Endpoint tests
  - `/v1/sql-corrections` flow: start, poll, delete; also bulk corrections with limit enforcement.
  - `/v1/relationship-recommendations` flow: start, poll, validate, export.
  - `/v1/charts/adjust` placeholder contract.

- Dagster units (lightweight, no engine)
  - Assert `LLMProviderResource.generate` sync behavior.
  - Assert `VectorStoreResource` methods raise with informative messages.

**Concrete Test-first Task List**

- tests/pipelines/test_sql_correction_pipeline.py
  - should call similarity_search with collection_name
  - should return corrected SQL with terminal semicolon and no dangerous keywords

- tests/resources/test_llm_provider_resource.py
  - generate is synchronous (not coroutine)
  - sql_query_asset accepts string return from generate and parses correctly (with a fake resource)

- tests/services/test_schema_service_shape.py
  - get_table_info handles flat payload (top-level from_table/to_table)
  - suggest_joins detects relationships from flat documents

- tests/routers/test_chart_adjust.py
  - POST /v1/charts/adjust returns 200 and contains message + request echo

- tests/pipelines/test_sql_generation_history.py
  - histories included in prompt (assert via injecting a fake LLM that records the prompt)

- tests/main/test_explain_query_fallback.py
  - non-JSON LLM fallback handled with safe default (expected shape) or 500 explicitly (decide and encode behavior)

**Operational Notes**

- Configuration: `OPENAI_API_KEY` gates LLM and embeddings; `QDRANT_URL` gates vector store. Health endpoint surfaces configuration/connection diagnostics.
- Networking: `/dagster/*` endpoints attempt callbacks to Laravel via `httpx` and require network. Expect failures in restricted environments; these are logged and do not crash the service initialization.

**Summary**

- The core HTTP service and pipelines are largely complete with clear fallbacks for unconfigured providers. There are a few correctness issues (param mismatch; async vs sync misuse) and several intentional stubs (Dagster vector store resource methods; chart adjust). Driving fixes with targeted tests will stabilize the core behavior and align shapes across vector store results and schema services.

