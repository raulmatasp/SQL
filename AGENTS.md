# Repository Guidelines

## Project Structure & Module Organization
- `hugdata-app/` — Laravel backend with Inertia + React/TS under `resources/js`, Vite build, Pest/PHPUnit tests under `hugdata-app/tests`.
- `hugdata-ai/` — FastAPI service (`main.py`), AI pipelines under `src/pipelines`, web API under `src/web/v1`, Dagster assets/jobs in `dagster_project`, config/state in `dagster_home`.
- `tests/` — Python integration tests exercising Laravel, FastAPI, and Dagster together.
- `docs/` — Architecture and ops docs. `monitoring/` — Prometheus/Grafana configs.
- `docker-compose.yml` — Local stack: Postgres, Redis, Weaviate, Laravel, FastAPI, Dagster, Nginx.

## Build, Test, and Development Commands
- Run full stack: `docker-compose up -d`
- DB migrate/seed: `docker-compose exec laravel php artisan migrate --seed`
- Laravel dev (manual): `cd hugdata-app && composer install && php artisan serve --port=8000`
- FastAPI dev (manual): `cd hugdata-ai && pip install -r requirements.txt && uvicorn main:app --reload --port 8003`
- Dagster UI: `cd hugdata-ai && export DAGSTER_HOME=$PWD/dagster_home && dagster dev --port 3001`
- Tests (Laravel): `cd hugdata-app && php artisan test`
- Tests (AI): `cd hugdata-ai && python -m pytest tests/`
- Integration tests: `python -m pytest tests/test_integration.py`

## Coding Style & Naming Conventions
- PHP: PSR-12; run `vendor/bin/pint` if installed. Controllers/Requests follow Laravel defaults (`App/Http/...`).
- TypeScript/React: ESLint + Prettier via `npm run lint` and `npm run format` in `hugdata-app`. Components use `PascalCase` filenames.
- Python: Prefer Black + Flake8 style (88 cols, imports grouped). Modules use `snake_case`, classes `PascalCase`, functions `snake_case`.
- SQL/Routes: Use lowercase table/column names; REST routes kebab-case paths.

## Testing Guidelines
- Frameworks: Pest/PHPUnit (Laravel), Pytest (AI), Pytest integration (`tests/`).
- Naming: PHP tests under `hugdata-app/tests`; Python tests under `hugdata-ai/tests` and `tests/` with `test_*.py`.
- Coverage targets: Laravel >80%, Python >75% (aim to maintain). Add tests for all new behavior.

## Commit & Pull Request Guidelines
- Commits: Conventional Commits (e.g., `feat(api): add query endpoint`, `fix(ai): handle empty schema`).
- PRs: Clear description, linked issues, steps to test, and screenshots/GIFs for UI changes. Include migration notes and roll-back steps when relevant.
- CI readiness: Lint passes, tests green, no debug logs, docs updated (`docs/` or inline README snippets) when behavior changes.

## Security & Configuration Tips
- Never commit secrets. Configure `.env` in `hugdata-app` and `hugdata-ai` (see `docs/README.md`).
- Validate external calls and sanitize SQL generation paths. Prefer parameterized queries.
- Health checks: Laravel `GET /api/health`, FastAPI `GET /health`, Dagster UI on `:3001`.

