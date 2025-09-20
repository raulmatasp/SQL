**HugData AI — Fix Plan and Corresponding Tests**

Objective: Stabilize core pipelines/services and Dagster integration by addressing concrete defects and codifying intent with tests. This plan lists the changes and the exact tests we’ll add to drive implementation.

**Fixes Overview**

- Fix A: SQLCorrectionPipeline uses wrong parameter name when calling vector store
  - Change `collection` → `collection_name` in `similarity_search` call.
  - Rationale: Aligns with `VectorStore.similarity_search` signature to avoid runtime errors.

- Fix B: Dagster LLMProviderResource is async but used synchronously in assets
  - Make `LLMProviderResource.generate` a synchronous function.
  - Rationale: Dagster assets are synchronous; returning a coroutine breaks parsing.

- Fix C: SchemaService expects nested `metadata` while Qdrant provider returns flattened payloads
  - Update `SchemaService.get_table_info` and `suggest_joins` to read fields from top-level or nested `metadata`.
  - Rationale: Ensure correct behavior with Qdrant-flattened payloads and mocks.

- Fix D (contract stabilization): Chart adjust endpoint placeholder
  - Maintain current behavior but add a small test to lock the basic contract.

**Tests To Add**

1) tests/pipelines/test_sql_correction_pipeline.py
   - should_call_similarity_search_with_collection_name
     - Setup: Fake vector store records kwargs; Fake LLM returns CORRECTED_SQL block.
     - Assert: `collection_name` present and `collection` absent in call; result contains `corrected_sql` ending with `;` and no dangerous keywords.

2) tests/resources/test_llm_provider_resource.py
   - generate_should_be_synchronous
     - Assert via `inspect.iscoroutinefunction(LLMProviderResource.generate) is False` (no OpenAI dependency at runtime).

3) tests/services/test_schema_service_shape.py
   - get_table_info_should_handle_flat_relationship_payload
     - Setup: Fake vector store returns relationship docs with top-level `from_table`/`to_table`.
     - Assert: `get_table_info(...)["relationships"]` includes the relationship.

4) tests/routers/test_chart_adjust.py
   - chart_adjust_placeholder_contract
     - POST `/v1/charts/adjust` returns 200, includes `message` and echoes `request`.

**Implementation Steps**

1. Apply Fix A in `src/pipelines/sql_correction.py`.
2. Apply Fix B in `dagster_project/resources/llm_provider.py` (make `generate` synchronous def).
3. Apply Fix C in `src/web/v1/services/schema.py` (helper to read key from top-level or nested metadata; update callers).
4. Keep Fix D as-is; rely on the new test to lock behavior.

**Out of Scope (documented by tests or analysis)**

- Dagster VectorStoreResource methods are intentionally unimplemented; add tests later if we choose to codify error messages or introduce API pass-through.
- `/explain-query` LLM JSON fallback hardening; can be tackled post-core stabilization.

**Validation**

- Run: `cd hugdata-ai && python -m pytest tests/`.
- Expected: New tests pass (after fixes), existing tests unaffected.

