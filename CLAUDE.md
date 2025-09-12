# CLAUDE.md

This file provides guidance for Claude Code (claude.ai/code) and all contributors working with this repository, which is a Laravel + React adaptation of the WrenAI project. The following conventions and best practices are required for all code in this codebase.

---

## Project Overview

This project is a Laravel (PHP 8+) and React (with TanStack Query) reimplementation of the WrenAI GenBI Agent. It enables natural language queries to databases, generating SQL, charts, and AI insights. The architecture is split into:

- **Backend**: Laravel 11+ (API, business logic, database, queue, auth)
- **Frontend**: React (functional components, hooks, TanStack Query)
- **Supporting Services**: Dockerized dependencies (vector DB, query engine, etc.)

---

## Laravel Backend: Architecture & Code Style

**General Principles**
- Follow Laravel conventions: keep controllers thin, move business logic to Services/Actions, keep routes and Blade free of logic.
- Enforce a single code style using Laravel Pint (preset: `laravel` or `psr12`). Add `pint.json` and a pre-commit hook to auto-fix style; run Pint in CI.
- Use PSR-4 autoloading, one class per file, and keep classes/methods small.
- Prefer constructor injection for dependencies; avoid facades in domain code except where they clarify intent.
- Centralize all configuration and constants in `config/*.php`. Never hardcode secrets.
- Use DTOs/Value Objects for request→domain boundaries to prevent array shape drift.
- Keep Blade templates minimal; move view logic to ViewModels/Presenters as needed.
- Use PHP 8+ features (enums, readonly, match) to encode domain constraints.
- Use Laravel’s container and contracts; avoid “clever” magic outside framework idioms.

**Domain, Eloquent & Database**
- One Eloquent model per table; keep business rules out of migrations.
- Guard mass assignment with `$fillable` or `$guarded = []` only when using strict FormRequests.
- Prevent N+1 queries: always eager load (`with`, `loadMissing`) and profile queries.
- Use chunking, cursor pagination, and `lazy()` for large datasets.
- Write explicit query scopes; never leak query logic into controllers.
- Prefer database constraints (FK, unique, check) over trusting code.
- Use API Resource classes for shaping API responses, never return raw models.
- Use soft deletes only when real recovery is needed; otherwise, hard delete with audit logs.
- Add indexes for read paths; use composite indexes for filters/sorts.
- Keep transactions short; move slow I/O to queued jobs.

**HTTP/API Layer**
- Validate all input with FormRequest classes; never trust client shape.
- Use correct HTTP verbs and status codes; version your API from day one.
- Use API Resources (with pagination meta) as the single response layer.
- Rate-limit sensitive endpoints; enable CORS explicitly.
- Emit problem details for errors; never leak stack traces in production.

**Security (OWASP-aligned)**
- Use Laravel’s CSRF and encryption by default; do not disable unless necessary.
- Validate and escape all untrusted input; never use `{!! !!}` in Blade.
- Enforce HTTPS everywhere; set secure cookies, SameSite, and HSTS.
- Lock down file uploads (mimes, size, storage outside webroot, scan if needed).
- Store secrets only in `.env` or a Secrets Manager; rotate keys and use least privilege.

**Auth for React Front-Ends**
- For SPA (same-site), use Laravel Sanctum cookie auth; do not roll your own token scheme.
- For cross-domain/public APIs, use Bearer tokens with short TTL and refresh strategy.
- Keep auth endpoints CSRF-protected when using cookie sessions.
- If using server-driven React, Inertia.js + React is recommended with Laravel 11.
- Otherwise, expose clean REST (or GraphQL) APIs and consume from React with TanStack Query.

**Queues, Events & Jobs**
- Offload slow work to queues (mail, webhooks, imports); set retries/backoff; handlers must be idempotent.
- Use domain Events/Listeners for side-effects; Observers for model lifecycle.
- Monitor queue health (failed jobs table + alerting).

**Testing & Quality**
- Use Pest for expressive tests; isolate with a dedicated test DB and factories.
- Write feature tests for HTTP flows and unit tests for pure domain rules; mock externals.
- Seed minimal fixtures; avoid global state; parallelize tests where safe.
- Add smoke tests for migrations and critical commands.

**Performance & Ops**
- Cache smartly (config/routes/views/query caching); bust caches on deploy.
- Use Octane/Swoole/RoadRunner only if measured and beneficial.
- Keep responses small (JSON resources, pagination, select() projection).
- Ship environment-specific error handling; never show detailed exceptions in production.
- Add health checks and structured logs; centralize with your APM.

---

## React Frontend: Practices

- Use functional components and hooks; co-locate files by feature.
- Split UI state vs server state (use TanStack Query for server state).
- Use Suspense/Concurrent features incrementally, with clear boundaries and fallbacks.
- Only use production builds for performance checks; code-split routes; avoid unnecessary state lifting.

---

## Development Setup

### Backend (Laravel)
- **Language**: PHP 8.2+
- **Framework**: Laravel 11+
- **Package Manager**: Composer
- **Task Runner**: Artisan, Pint, Pest
- remember we are going to use '/Users/raulmata/Projetos/Hug/Company/SQL/hugdata-ai' for the python files. do not create inside @hugdata-app/ (only for lavavel files)