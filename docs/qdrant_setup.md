**Qdrant Setup (Production Readiness)**

- Required env vars:
  - `QDRANT_URL` (e.g., `http://qdrant:6333` or `http://localhost:6333`)
  - `QDRANT_API_KEY` if your Qdrant requires auth
  - `OPENAI_API_KEY` for LLM and embeddings (OpenAI providers)

- Install dependencies:
  - In `hugdata-ai`: `pip install -r requirements.txt` (includes `qdrant-client`)

- Start Qdrant (example Docker Compose snippet):
  - service `qdrant`:
    - image: `qdrant/qdrant:latest`
    - ports: `6333:6333`
    - volumes: mount a persistent data directory

- Configure the app:
  - Set environment variables (`.env` or container env):
    - `QDRANT_URL=http://qdrant:6333`
    - `OPENAI_API_KEY=...`
  - Optional: `QDRANT_API_KEY=...` if needed

- Bootstrap collections (optional):
  - The service auto-creates collections when indexing. To pre-create:
    - `cd hugdata-ai`
    - `python -m src.utils.qdrant_bootstrap schema_yourproject 1536`
    - Run for other collections as needed (e.g., `table_descriptions_yourproject`, `sql_pairs_yourproject`)

- Health check:
  - `GET /health` returns:
    - `checks.llm_configured`, `checks.embeddings_configured`
    - `checks.vector_store_configured`, `checks.vector_store_ok`, `checks.vector_store_error`
  - Errors indicate missing env or connectivity issues.

- Behavior without configuration:
  - No mock fallbacks are used in production code. If env/config is missing, endpoints return clear errors. Fix env vars and service connectivity to proceed.

