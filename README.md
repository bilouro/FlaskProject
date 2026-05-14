<div align="center">

# Books API — Flask edition

**A reference-grade, modern Flask REST API — built with SQLAlchemy 2, Pydantic v2, and Alembic.**

[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-d71f00)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-e92063)](https://docs.pydantic.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](#testing)
[![Tests](https://img.shields.io/badge/tests-60%20passing-brightgreen)](#testing)
[![License: BSD-2-Clause](https://img.shields.io/badge/license-BSD--2--Clause-blue.svg)](LICENSE)

[Quickstart](#quickstart) ·
[API Reference](#api-reference) ·
[Architecture](#architecture) ·
[Configuration](#configuration) ·
[Testing](#testing) ·
[Benchmark vs FastAPI](#benchmark-vs-fastapi) ·
[Roadmap](#roadmap)

</div>

> **Mirror project:** [`bilouro/FastAPIProject`](https://github.com/bilouro/FastAPIProject) — same domain, same contract, same tests philosophy, rebuilt around async. Use the [benchmark harness](#benchmark-vs-fastapi) in this repo to compare both side by side under controlled load.

---

## Overview

**Books API (Flask edition)** is a small, opinionated CRUD service that shows what an *idiomatic, production-shaped* Flask project looks like in 2026 — long after Flask stopped being trendy and became the workhorse.

Every choice is intentional: a clean separation of HTTP / domain / data layers, strict typing at every boundary via Pydantic v2, real Alembic migrations, JSON-structured logs, an OpenAPI spec generated from the schemas, and a hermetic test suite that runs in under a second at **100 % branch coverage**.

### Why this exists

- Show that Flask, in 2026, can deliver the same quality bar as the async crowd — when you bring SQLAlchemy 2, Pydantic v2, and proper layering to the table.
- Provide a copy-pasteable foundation for new services: app factory, settings, logging, error envelope, repository pattern, tests — all wired up.
- Form one half of a side-by-side benchmark against [its FastAPI twin](#benchmark-vs-fastapi).

### What you get

- Idiomatic Flask 3 with an **application factory** (`create_app`) and blueprints.
- **SQLAlchemy 2** ORM with typed declarative mapping (`Mapped[T]`) and `psycopg2`.
- **Pydantic v2** request schemas with `extra="forbid"` and strict types.
- **Pydantic-settings** for typed config (no `os.getenv` scattered across files; required secrets refuse to start the app).
- One unified **error envelope** (RFC 9457-style) across `4xx` / `5xx`.
- **OpenAPI 3.1 spec** generated automatically from the Pydantic schemas — no hand-rolled JSON drifting from code.
- **Structured JSON logging** ready for any log shipper.
- A **Wagtail-grade test suite**: 60 tests, **100 % branch coverage**, no DB mocks, no external services.
- A `Dockerfile`, a `docker-compose.yml`, **and** a side-by-side benchmark harness vs FastAPI.

---

## Table of Contents

- [Overview](#overview)
- [Quickstart](#quickstart)
- [Architecture](#architecture)
- [Project Layout](#project-layout)
- [API Reference](#api-reference)
- [Error Envelope](#error-envelope)
- [Configuration](#configuration)
- [Database & Migrations](#database--migrations)
- [Testing](#testing)
- [Observability](#observability)
- [Benchmark vs FastAPI](#benchmark-vs-fastapi)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Security](#security)
- [FAQ](#faq)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Quickstart

### One-liner (Docker Compose)

```bash
git clone https://github.com/bilouro/FlaskProject.git
cd FlaskProject
docker compose -f docker_compose_flask_postgresql.yml up --build
```

Wait a few seconds, then:

```bash
curl http://localhost:5001/health
# {"status":"ok","database":"ok","version":"1.0.0"}
```

Open Swagger UI: <http://localhost:5001/docs>

### Local development (no Docker)

```bash
git clone https://github.com/bilouro/FlaskProject.git
cd FlaskProject

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env                 # edit APP_DB_PASSWORD etc.

alembic upgrade head
python app.py
```

That's it. Visit:

| URL                                           | What it serves                   |
| --------------------------------------------- | -------------------------------- |
| <http://localhost:5001>                       | Service index (JSON)             |
| <http://localhost:5001/v1/books>              | Books resource                   |
| <http://localhost:5001/health>                | Liveness + DB readiness probe    |
| <http://localhost:5001/docs>                  | Swagger UI                       |
| <http://localhost:5001/swagger.json>          | OpenAPI 3.1 schema (auto-built)  |

---

## Architecture

```
                ┌──────────────────────────────────────────┐
                │            WSGI server (gunicorn)        │
                └────────────────────┬─────────────────────┘
                                     │
                ┌────────────────────▼─────────────────────┐
                │              Flask app                   │
                │  · error handlers · X-Response-Time      │
                │  · app factory · blueprints              │
                └────────────────────┬─────────────────────┘
                                     │
      ┌──────────────────────────────┼──────────────────────────────┐
      │                              │                              │
┌─────▼──────┐         ┌─────────────▼─────────────┐        ┌───────▼────────┐
│ /v1/books  │         │     /health · /docs       │        │ /swagger.json  │
│ Blueprint  │         │     · /v1/sleep · /       │        │ (Pydantic gen) │
└─────┬──────┘         └───────────────────────────┘        └────────────────┘
      │
┌─────▼──────────────────────────────────────────────────────┐
│ Pydantic v2 schemas  (BookCreate / BookReplace / BookPatch)│
│  · extra="forbid"    · strict=True       · model_validator │
└─────┬──────────────────────────────────────────────────────┘
      │
┌─────▼──────────────────────────────────────────────────────┐
│             books.repository  (typed domain errors)        │
│  list_books · get_book · create_book · replace_book        │
│  · update_book · delete_book                               │
└─────┬──────────────────────────────────────────────────────┘
      │
┌─────▼──────────────────────────────────────────────────────┐
│    SQLAlchemy 2  Session  ──►  psycopg2  ──►  PostgreSQL 16│
└────────────────────────────────────────────────────────────┘
```

### Request lifecycle

1. **gunicorn** terminates HTTP and hands the WSGI environ to Flask.
2. The blueprint resolves the path to a route function.
3. The route calls `BookCreate.model_validate(request.json)` (or sibling) — Pydantic raises on bad input.
4. The route delegates to `books.repository`, which speaks SQLAlchemy 2 to `psycopg2`.
5. Domain exceptions (`BookNotFoundError`, `DuplicateISBNError`) and `ValidationError` are converted to a unified JSON envelope by `@app.errorhandler` registrations in `app.py`.
6. An `after_request` middleware adds `X-Response-Time` header (ms) on every response.

### Layering rules

- **Blueprints** never touch SQL. They orchestrate Pydantic ↔ repository.
- **Repository** never raises framework exceptions. Domain failures become `DomainError` subclasses.
- **Schemas** are the only place data shapes are declared. ORM models stay private to the persistence layer.
- **Settings** are read once at startup; cached via `lru_cache`.

---

## Project Layout

```
.
├── app.py                            # Flask factory, error handlers, /health, /, middleware
├── config.py                         # pydantic-settings + Flask config classes
├── openapi.py                        # OpenAPI 3.1 spec built from Pydantic schemas
├── logging_config.py                 # structured JSON logging
├── books/
│   ├── __init__.py
│   ├── models.py                     # SQLAlchemy 2.x Book ORM model
│   ├── schemas.py                    # Pydantic v2 request / response models
│   ├── repository.py                 # CRUD with typed errors, lazy engine
│   ├── routes.py                     # /v1/books blueprint
│   ├── exceptions.py                 # DomainError + subclasses
│   └── sleep.py                      # /v1/sleep benchmark endpoint
├── migrations/                       # Alembic
│   ├── env.py
│   └── versions/
│       └── 4fb6da201c1f_create_books_table.py
├── tests/                            # 60 tests, 100 % coverage
│   ├── conftest.py                   # Flask test_client + in-memory SQLite
│   ├── test_app.py · test_routes.py
│   ├── test_repository.py · test_coverage_extras.py
│   └── test_functional_app.py
├── benchmark/                        # k6 harness vs FastAPI (see below)
├── alembic.ini
├── Dockerfile
├── docker_compose_flask_postgresql.yml
├── dbfixtures.sql
├── pyproject.toml                    # pytest, coverage
├── requirements.txt
├── .env.example
└── LICENSE
```

---

## API Reference

All resource endpoints live under the **`/v1`** prefix. Cross-cutting endpoints (`/health`, `/docs`, ...) stay at the root.

| Method   | Path                | Body            | Success | Failure                                       |
| -------- | ------------------- | --------------- | ------- | --------------------------------------------- |
| `GET`    | `/health`           | —               | `200`   | always 200; DB state in `database` field      |
| `GET`    | `/v1/books`         | —               | `200`   | —                                             |
| `GET`    | `/v1/books/{id}`    | —               | `200`   | `404`                                         |
| `POST`   | `/v1/books`         | `BookCreate`    | `201`   | `422` (validation), `409` (duplicate ISBN)    |
| `PUT`    | `/v1/books/{id}`    | `BookReplace`   | `200`   | `404`, `422`, `409`                           |
| `PATCH`  | `/v1/books/{id}`    | `BookPatch`     | `200`   | `404`, `422` (no fields / unknown field)      |
| `DELETE` | `/v1/books/{id}`    | —               | `204`   | `404`                                         |
| `GET`    | `/v1/sleep?ms=N`    | —               | `200`   | benchmark helper (issues `pg_sleep(N/1000)`)  |

### Resource schema

```jsonc
{
  "id":         42,                       // int, server-assigned
  "title":      "1984",                   // string, required, 1..255
  "author":     "George Orwell",          // string, required, 1..255
  "year":       1949,                     // int, required, -3000..9999
  "isbn":       "978-0451524935",         // string, required, 1..32, unique
  "status":     "active",                 // string, default "active"
  "created_at": "2026-05-12T22:58:00Z",   // server-managed
  "updated_at": "2026-05-12T22:58:00Z"    // server-managed
}
```

### Examples

```bash
# Create
curl -X POST http://localhost:5001/v1/books \
  -H 'content-type: application/json' \
  -d '{"title":"1984","author":"George Orwell","year":1949,"isbn":"978-0451524935"}'

# List
curl http://localhost:5001/v1/books

# Partial update
curl -X PATCH http://localhost:5001/v1/books/1 \
  -H 'content-type: application/json' \
  -d '{"status":"archived"}'

# Replace
curl -X PUT http://localhost:5001/v1/books/1 \
  -H 'content-type: application/json' \
  -d '{"title":"1984","author":"George Orwell","year":1949,"isbn":"978-0451524935"}'

# Delete
curl -X DELETE http://localhost:5001/v1/books/1 -i
```

---

## Error Envelope

Every non-2xx response shares a single shape, inspired by [RFC 9457 (Problem Details for HTTP APIs)](https://www.rfc-editor.org/rfc/rfc9457.html):

```json
{
  "error":   "Not Found",
  "message": "Book not found",
  "code":    404,
  "path":    "/v1/books/999"
}
```

Validation failures (HTTP 422) include a `details` list of structured field errors from Pydantic:

```json
{
  "error":   "Unprocessable Content",
  "message": "isbn: Field required",
  "code":    422,
  "path":    "/v1/books",
  "details": [
    { "type": "missing", "loc": ["isbn"], "msg": "Field required", "input": {} }
  ]
}
```

The same envelope is produced for `404` (unknown route), `405`, `409` (duplicate ISBN), `415`, and unhandled `500` errors — clients only ever parse one shape.

---

## Configuration

All settings come from environment variables (prefixed `APP_`) and/or a `.env` file. See [`.env.example`](.env.example).

| Variable              | Default       | Purpose                                    |
| --------------------- | ------------- | ------------------------------------------ |
| `APP_ENV`             | `dev`         | One of `dev` · `test` · `prod`             |
| `APP_DB_HOST`         | `127.0.0.1`   | Postgres host                              |
| `APP_DB_PORT`         | `5432`        | Postgres port                              |
| `APP_DB_NAME`         | `app_db`      | Postgres database                          |
| `APP_DB_USER`         | `app_user`    | Postgres user                              |
| `APP_DB_PASSWORD`     | _(required)_  | Postgres password — refuses to start if unset |
| `APP_DATABASE_URL`    | _(unset)_     | Full override DSN (skips per-var assembly) |

The DSN is computed as:

```
postgresql+psycopg2://<user>:<password>@<host>:<port>/<name>
```

Unless `APP_DATABASE_URL` is set, in which case that value wins.

---

## Database & Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new revision after model changes
alembic revision --autogenerate -m "describe change"

# Roll back the most recent migration
alembic downgrade -1

# Seed sample data
psql -h "$APP_DB_HOST" -U "$APP_DB_USER" -d "$APP_DB_NAME" -f dbfixtures.sql
```

The Alembic environment reuses the DSN computed by `config.Settings`. There is no separate sync/async config to maintain.

---

## Testing

```bash
pytest                                  # full suite + 100 % coverage gate
pytest tests/test_routes.py -v          # one module
pytest -k duplicate                     # by keyword
pytest --cov-report=html                # generate htmlcov/index.html
```

### Highlights

- **60 tests** (+ 2 functional, skipped unless a server is running) spanning config, repository, routes, error envelope, OpenAPI spec, and the benchmark helpers.
- **100 % branch & line coverage** on `app.py`, `books/*`, `config.py`, `openapi.py`, `logging_config.py`, enforced by `--cov-fail-under=100` in `pyproject.toml`.
- **No external services needed.** The conftest swaps `SQLALCHEMY_DATABASE_URI` for an in-memory SQLite + `StaticPool`.
- **Flask test client + Pydantic** drive the app in-process — fast, deterministic.

```text
$ pytest -q
............................................................                [100%]
TOTAL                   385      0     46      0   100%
Required test coverage of 100% reached. Total coverage: 100.00%
60 passed, 2 skipped in 0.21s
```

---

## Observability

`logging_config.configure_logging()` installs a JSON formatter on stdout for all loggers, including `werkzeug` and `gunicorn`:

```json
{"asctime": "2026-05-12 22:58:00,000", "levelname": "INFO", "name": "app", "message": "starting app env=prod version=1.0.0"}
```

Drop this straight into Loki, CloudWatch, Datadog, or any log shipper that understands JSON lines — no parsers, no regex.

Every response carries an `X-Response-Time` header (handler time, in milliseconds) for client-side latency observability — also consumed by the [benchmark harness](#benchmark-vs-fastapi).

The `sqlalchemy.engine` logger is pinned at `WARNING` by default so query noise stays out of production logs.

---

## Benchmark vs FastAPI

This repo ships a **side-by-side load benchmark** comparing this Flask service against its FastAPI twin under controlled identical conditions: same Postgres, same schema, same Docker host, equal CPU budgets.

Headline finding from the I/O-fanout workload (the canonical async use case — every request triggers `pg_sleep(50ms)` server-side):

| Metric | Flask (gunicorn 4w/4t) | FastAPI (uvicorn 4w) |
|---|---:|---:|
| Throughput (req/s) | **265** | **992** |
| Client p50 (ms) | 905 | 226 |
| Client p95 (ms) | 2,615 | 733 |

→ **FastAPI ≈ 3.7× throughput at ~1/4 the client p50** on this workload.

On read-light and mixed CRUD workloads, the gap shrinks to **7-14%**. Full results, every percentile, and per-workload analysis are in [`benchmark/RESULTS.md`](benchmark/RESULTS.md).

### How to run

Prereqs: Docker, `k6` (e.g. `brew install k6`), Python with `psycopg2-binary` (`pip install psycopg2-binary`), and the [FastAPIProject](https://github.com/bilouro/FastAPIProject) repo cloned **next to this one** so docker-compose can build both contexts.

```bash
# 1. Bring up Postgres + both APIs (FastAPI runs alembic; Flask reuses the same schema)
docker compose -f benchmark/docker-compose-bench.yml up --build -d

# 2. Wait until both health endpoints return 200
curl -fsS http://localhost:5001/health && echo " flask ok"
curl -fsS http://localhost:8000/health && echo " fastapi ok"

# 3. Seed 10,000 books into Postgres (shared by both APIs)
python benchmark/seed.py --count 10000 --reset

# 4. Run the full sweep: 3 workloads × 2 APIs × 3 runs = 18 k6 invocations (~26 min)
bash benchmark/run.sh

# 5. Aggregate the 18 raw k6 JSONs into a CSV + markdown table
python benchmark/results/aggregate.py

# 6. Tear everything down
docker compose -f benchmark/docker-compose-bench.yml down -v
```

### Workloads

| Script              | Endpoint                              | Shape                                                        | Purpose                       |
| ------------------- | ------------------------------------- | ------------------------------------------------------------ | ----------------------------- |
| `benchmark/k6/read.js`   | `GET /v1/books/{random_id}`     | ramp **50 → 1000 VUs**, 90 s                                | Read-light, latency-bound     |
| `benchmark/k6/mixed.js`  | 70 % GET / 25 % POST / 5 % PATCH | ramp **100 → 500 VUs**, 80 s                                | Realistic CRUD mix            |
| `benchmark/k6/fanout.js` | `GET /v1/sleep?ms=50`           | ramp **50 → 500 VUs**, 80 s — the async-vs-sync stress test | I/O fanout (slow upstream)    |

Every script reads the server's `X-Response-Time` header into a custom `server_time_ms` k6 trend so the final report distinguishes **client wall-clock** from **handler-only time**.

### Hardware caveat

The reference results were taken on an **Apple Silicon MacBook**, each container capped at **2 CPUs / 1 GB RAM** via `deploy.resources.limits`. Treat the numbers as a **relative comparison under controlled identical conditions**, not absolute production capacity.

---

## Roadmap

- [x] SQLAlchemy 2 ORM with typed declarative mapping
- [x] Strict Pydantic v2 schemas
- [x] Repository pattern with typed domain errors
- [x] Unified error envelope (RFC 9457-inspired)
- [x] OpenAPI 3.1 generated from Pydantic schemas
- [x] Structured JSON logging
- [x] `X-Response-Time` middleware
- [x] 100 % test coverage
- [x] Side-by-side benchmark harness vs FastAPI
- [x] API versioning under `/v1`
- [ ] GitHub Actions CI (pytest + ruff)
- [ ] Pagination (`limit` / `offset`, then keyset)
- [ ] Filtering and full-text search on title / author
- [ ] Authentication (OAuth2 / JWT bearer)
- [ ] Rate limiting middleware
- [ ] OpenTelemetry traces & metrics
- [ ] Pre-commit hooks (ruff format + ruff check)

---

## Contributing

Issues and PRs are welcome.

1. Fork the repo and create a feature branch from `main`.
2. Run `pytest` and ensure coverage stays at 100 %.
3. Open a PR with a clear description and curl examples for behavioural changes.

For larger refactors, please open an issue first so we can align on scope.

---

## Security

Found a security issue? Please **do not** open a public issue. Email the maintainer (see `git log` for contact) with details and a reproduction. We'll respond within a few business days.

Secrets are never read at import time — only inside `Settings()`, which is instantiated lazily. `APP_DB_PASSWORD` is required (no fallback) so a misconfigured deploy fails loudly instead of silently using a weak default.

---

## FAQ

**Why Flask in 2026? Isn't FastAPI strictly better?**
For low-concurrency CRUD, the difference is below the noise (see [benchmark](#benchmark-vs-fastapi)). Flask is mature, has a huge ecosystem of extensions, and is easier to hire for. Use the right tool — async is tooling, not a religion.

**Why SQLAlchemy when SQLModel exists?**
SQLModel is great for prototypes but conflates the ORM and the API schema. Keeping them separate (SQLAlchemy + Pydantic) costs ~20 lines and is much easier to evolve when the public contract and the database shape diverge.

**Why an in-memory SQLite in tests instead of testcontainers / Postgres?**
Suite speed and friction. The tests run in **< 1 s** and need nothing but Python. For an integration smoke against real Postgres, point `APP_DATABASE_URL` at it and start the server — that's the deployment path you're going to use anyway.

**Why `pytest --cov-fail-under=100`?**
Because "97 %" never improves. The gate forces you to either delete dead code or write the missing test before merging.

**Why is OpenAPI built by hand from Pydantic instead of using `flask-smorest` / `apispec`?**
The hand-rolled `openapi.py` is ~150 lines, has zero dependencies, and emits exactly the spec we want. We pay no plugin lock-in and the generator's behaviour is fully under our control.

---

## License

[BSD 2-Clause](LICENSE) © Victor H. Bilouro.

---

## Acknowledgments

Built on the shoulders of:

- [Flask](https://flask.palletsprojects.com/) by Armin Ronacher and contributors
- [SQLAlchemy](https://www.sqlalchemy.org/) by Mike Bayer and contributors
- [Pydantic](https://docs.pydantic.dev/) by Samuel Colvin and contributors
- [psycopg](https://www.psycopg.org/) by Federico Di Gregorio
- [Alembic](https://alembic.sqlalchemy.org/) by Mike Bayer
- [k6](https://k6.io/) by Grafana Labs
- The team behind [PostgreSQL](https://www.postgresql.org/)
