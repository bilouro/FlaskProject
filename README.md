# Books API (FlaskProject)

Before using or modifying this backend, it is important to understand the problem it solves and the main architectural choices. This avoids treating it as a black box and makes extensions and refactors much safer.

This repository implements a **RESTful Books API** using **Python** and **Flask**, backed by a **PostgreSQL** database and managed via **Alembic** migrations. The design emphasizes:

- A clear separation between:
  - HTTP layer (Flask routes/blueprints),
  - data-access layer (repository),
  - persistence layer (SQLAlchemy models).
- Explicit configuration per environment (Dev, Test, Prod).
- Database schema evolution via migrations.
- API documentation via OpenAPI/Swagger.
- JSON error handling with a consistent structure.
- Automated tests (unit + functional).

The core domain entity is the `Book`, managed via CRUD endpoints under `/books`. The application also exposes a health check endpoint and embedded API docs.

---

## Table of Contents

Listing the sections up front makes the README easy to scan and helps you jump straight to what you need (installation, usage, tests, contributions, etc.).

1. [Project Overview](#project-overview)  
2. [Project Structure](#project-structure)  
3. [Technology Stack & Rationale](#technology-stack--rationale)  
4. [Prerequisites](#prerequisites)  
5. [Configuration](#configuration)  
6. [Installation](#installation)  
7. [Database Setup & Migrations](#database-setup--migrations)  
8. [Running the Application](#running-the-application)  
9. [API Usage & Examples](#api-usage--examples)  
10. [Testing](#testing)  
11. [Contributing](#contributing)  
12. [License](#license)  
13. [Contact & References](#contact--references)

---

## Project Overview

Before focusing on the implementation details, it helps to clarify the functional scope and the data model. This provides context for the routes, repository functions, and SQLAlchemy models.

- **Domain object:** `Book`
  - `id`: integer primary key (auto-increment).
  - `title`: string, required.
  - `author`: string, required.
  - `year`: integer, required.
  - `isbn`: string, required, unique.
  - `created_at`: timestamp (set on insert).
  - `updated_at`: timestamp (set on update).
  - `status`: string with default `"active"`.

- **Main capabilities:**
  - List, retrieve, create, replace, partially update, and delete books via `/books` endpoints.
  - Validate incoming JSON payloads and allowed fields before calling the repository layer.
  - Monitor basic application and database health via `/health`.
  - Explore and inspect API endpoints via Swagger UI at `/docs`, backed by `/swagger.json`.
  - Apply database schema changes declaratively using Alembic migrations.
  - Run automated tests to prevent regressions during changes.

---

## Project Structure

Knowing the directory layout in advance helps you quickly find where to add new endpoints, models, migrations, or tests, and avoids mixing concerns.

The repository is organized as follows:

    FlaskProject
    books
        __init__.py
        models.py
        repository.py
        routes.py
    migrations
        versions
            4fb6da201c1f_create_books_table.py
            8c6a44c5fe32_add_metadata_fields_to_books.py
        env.py
        script.py.mako
    static
    templates
    tests
        test_app.py
        test_functional_app.py
    alembic.ini
    app.py
    config.py
    db.py
    dbfixtures.sql
    README.md

Key elements:

- `app.py`  
  Defines the **application factory** `create_app`, registers the `books` blueprint, configures error handlers, and exposes utility endpoints (`/health`, `/swagger.json`, `/docs`). It also defines a global `app` instance for direct execution with `python app.py`.

- `config.py`  
  Centralized configuration:
  - `BaseConfig`: shared defaults (e.g., DB connection string).
  - `DevConfig`: development-friendly (e.g., `DEBUG = True`).
  - `TestConfig`: test-oriented (e.g., `TESTING = True`).
  - `ProdConfig`: production-safe defaults.

- `db.py`  
  Encapsulates low-level DB connection handling (e.g., `get_connection()`), so routes do not need to know connection details.

- `books/models.py`  
  Contains the SQLAlchemy `Base` and the `Book` model definition, mapping Python attributes to database columns.

- `books/repository.py`  
  Implements the data-access logic (CRUD operations) for books. By routing all DB operations through this module, you keep business logic out of the HTTP layer and make the code easier to test.

- `books/routes.py`  
  Contains the Flask blueprint with all `/books` endpoints and helper functions for:
  - JSON body requirements (`_require_json_object`).
  - Field validation and type checking (`_validate_fields`).

- `migrations/` and `alembic.ini`  
  Provide Alembic configuration and versioned migration scripts to manage the evolution of the `books` table and its metadata columns.

- `tests/`  
  Includes automated tests for app behavior and endpoints:
  - `test_app.py`: usually more unit-style tests for Flask-level behavior.
  - `test_functional_app.py`: more functional/integration style.

- `dbfixtures.sql`  
  Optional SQL script to seed the database with example data, making local development and manual testing easier.

---

## Technology Stack & Rationale

Understanding why each tool is used helps you judge whether the stack fits your needs and informs future technical decisions.

- **Python 3.x**  
  Offers mature ecosystem support for web services and testing. Type hints (as seen in the models and routes) improve maintainability and tooling support.

- **Flask**  
  Provides a lightweight, extensible web framework ideal for small to medium APIs. The blueprint structure in `books/routes.py` demonstrates how to keep functionality modular.

- **PostgreSQL**  
  A reliable, feature-rich relational database well suited for structured data and transactional operations. It is a de-facto standard in many production systems.

- **SQLAlchemy (ORM)**  
  Abstracts raw SQL, providing a Pythonic interface for defining models (`Book`) and handling DB operations. It also integrates well with Alembic for migrations.

- **Alembic**  
  Manages database schema history. Migration scripts (e.g., `create_books_table`, `add_metadata_fields_to_books`) document how the schema evolved and can be replayed on new environments.

- **pytest**  
  A flexible, expressive testing framework. It encourages small, focused tests and integrates well with fixtures, making it straightforward to test Flask applications.

- **Swagger UI / OpenAPI**  
  Having `/swagger.json` and `/docs` makes the API self-describing and easier to explore, and it helps consumers generate clients automatically if needed.

---

## Prerequisites

Before running any commands, it is important to verify that your environment has the required tools. This prevents errors that originate from missing interpreters, missing compilers, or incompatible versions.

You will need:

- **Python 3.10+**  
  Newer Python versions help ensure compatibility with modern Flask and SQLAlchemy releases.

- **PostgreSQL** (local or remote)  
  Required for persistence:
  - You need a running PostgreSQL instance.
  - You need credentials that match or override the defaults in `config.py`.

- **Virtual environment tool** (`python -m venv`, `virtualenv`, etc.)  
  Isolates project dependencies from your global Python environment, avoiding version conflicts and making the setup reproducible.

- **Git** (recommended)  
  Facilitates cloning the project and collaborating via branches and pull requests.

---

## Configuration

Before starting the app, you should understand how configuration works and how to influence it via environment variables. This allows you to separate code from environment-specific settings (credentials, hosts, ports).

The `BaseConfig` class in `config.py` reads database-related environment variables and constructs a PostgreSQL DSN:

- `APP_DB_HOST` (default `127.0.0.1`)
- `APP_DB_PORT` (default `5432`)
- `APP_DB_NAME` (default `app_db`)
- `APP_DB_USER` (default `app_user`)
- `APP_DB_PASSWORD` (default `bsd0030`)

They are combined into:

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

To actually configure the environment for a local development run, you typically export these variables in your shell before launching the app. This pattern provides flexibility and keeps secrets out of source code.

Here is how you might set them for a development environment:

    export APP_DB_HOST="127.0.0.1"
    export APP_DB_PORT="5432"
    export APP_DB_NAME="app_db"
    export APP_DB_USER="app_user"
    export APP_DB_PASSWORD="bsd0030"

You can override these values to point to any PostgreSQL instance you control. In production, these values should be more secure and defined by your deployment platform (e.g., Docker secrets, Kubernetes config, etc.).

---

## Installation

Before running the application or tests, you need a local copy of the project and a proper Python environment containing all required packages. The steps below isolate dependencies and give you a reproducible setup.

The process is:

1. Get the project code on your machine.
2. Create and activate a virtual environment.
3. Install dependencies listed in `requirements.txt`.

After that explanation, you can execute the following commands from a terminal:

    # 1. Clone the repository (replace with the actual URL)
    git clone <YOUR_REPOSITORY_URL> FlaskProject
    cd FlaskProject

    # 2. Create a virtual environment dedicated to this project
    python3 -m venv venv

    # 3. Activate the virtual environment
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows (PowerShell):
    # venv\Scripts\Activate.ps1

    # 4. Upgrade pip and install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt

Once this finishes, your environment is ready for DB setup and application execution.

---

## Database Setup & Migrations

Before the API can work with books, the database schema must exist. Instead of manually creating tables, this project uses Alembic migrations so that the schema is versioned and consistent across machines.

The high-level steps are:

1. Ensure that the PostgreSQL user and database exist.
2. Run Alembic migrations to apply the schema changes.
3. (Optional) Seed the database with fixture data.

Once you understand why this is necessary, you can use commands like the following to set up the database:

    # 1. Create the database user and database using psql (example; adapt to your environment)
    # This assumes you have a 'postgres' superuser or equivalent.
    psql -h 127.0.0.1 -U postgres -c "CREATE USER app_user WITH PASSWORD 'bsd0030';"
    psql -h 127.0.0.1 -U postgres -c "CREATE DATABASE app_db OWNER app_user;"

    # 2. Apply all Alembic migrations from the project root
    alembic upgrade head

    # 3. (Optional) Load fixture data from dbfixtures.sql for development/testing
    psql -h "$APP_DB_HOST" -U "$APP_DB_USER" -d "$APP_DB_NAME" -f dbfixtures.sql

After these steps, your `books` table should exist with the appropriate columns (`id`, `title`, `author`, `year`, `isbn`, `created_at`, `updated_at`, `status`), and you can start interacting with the API.

---

## Running the Application

To serve requests, you need to start the Flask application. The project uses the application factory pattern, which allows easy switching of configuration classes, but also provides a simple entry point for development execution.

Key points:

- `create_app(config_class=DevConfig)` in `app.py` constructs and configures the Flask app.
- A global `app` instance is created at the bottom of `app.py` for convenience.
- When you run `python app.py`, Flask’s built-in development server starts on port 5000.

With that in mind, and assuming your virtual environment is active and DB is configured, you can run:

    # From the project root, with venv activated
    python app.py

By default, the app will listen on:

    http://127.0.0.1:5000

Useful endpoints to verify that the app is running correctly:

- `GET /health` – App + DB health check.
- `GET /books/` – List of books.
- `GET /swagger.json` – Raw OpenAPI schema.
- `GET /docs` – Swagger UI (interactive docs).

---

## API Usage & Examples

Before sending HTTP requests, it is crucial to know how the API expects data and how it reports errors. This allows you to construct correct payloads and interpret responses programmatically.

General rules:

- All book-related endpoints live under `/books`.
- JSON requests must use header: `Content-Type: application/json`.
- The allowed fields are: `title`, `author`, `year`, `isbn`.
- Validation in `books.routes`:
  - Rejects non-JSON or non-object payloads.
  - Rejects unknown fields.
  - Requires all fields for `POST` and `PUT`.
  - Requires at least one field for `PATCH`.
  - Checks types (`year` as integer, others as strings).
- Errors return JSON structured like:

      {
        "error": "Bad Request",
        "message": "Field 'year' must be an integer",
        "code": 400
      }

The examples below use `curl` because it is ubiquitous and easy to script. You can translate these into Postman collections, HTTPie commands, or any other HTTP client.

Assume the app is running at `http://127.0.0.1:5000`.

### Health Check

The health endpoint confirms two things: the app is running and basic DB connectivity works. This is commonly used for monitoring and readiness/liveness probes.

    curl -i http://127.0.0.1:5000/health

A successful response looks like:

    {
      "status": "ok",
      "database": "ok"
    }

If the database cannot be reached, `"database"` will be `"error"`.

### List All Books

Listing books is a simple way to verify that the DB is populated and that the repository layer is functioning.

    curl -i http://127.0.0.1:5000/books/

Example response (truncated):

    [
      {
        "id": 1,
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "year": 2008,
        "isbn": "9780132350884"
      }
    ]

### Retrieve a Single Book

Fetching a book by ID allows you to check a specific record and validate that individual retrieval works as expected.

    curl -i http://127.0.0.1:5000/books/1

If the book exists, you get a JSON object. If not, you receive a 404 error:

    {
      "error": "Not Found",
      "message": "Book not found",
      "code": 404
    }

### Create a New Book (POST)

Creating books demonstrates how request validation works and how new records are persisted. All fields are required here.

    curl -i -X POST http://127.0.0.1:5000/books/ \
      -H "Content-Type: application/json" \
      -d '{
        "title": "Domain-Driven Design",
        "author": "Eric Evans",
        "year": 2003,
        "isbn": "9780321125217"
      }'

On success, you should receive:

- HTTP status `201 Created`.
- A JSON body containing the created book including its `id`.

If you omit a required field or use an incorrect type, you will receive a 400 error with a specific message describing the problem.

### Replace an Existing Book (PUT)

Using PUT shows how to **replace** an existing resource entirely. This requires sending all fields, not just the ones you want to change.

    curl -i -X PUT http://127.0.0.1:5000/books/1 \
      -H "Content-Type: application/json" \
      -d '{
        "title": "Domain-Driven Design (Updated Edition)",
        "author": "Eric Evans",
        "year": 2003,
        "isbn": "9780321125217"
      }'

If the target book does not exist, the response uses the same 404 error shape as the GET endpoint:

    {
      "error": "Not Found",
      "message": "Book not found",
      "code": 404
    }

### Partially Update a Book (PATCH)

`PATCH` is ideal when you only want to adjust a subset of fields (for example, correcting a typo in the title). At least one valid field must be provided.

    curl -i -X PATCH http://127.0.0.1:5000/books/1 \
      -H "Content-Type: application/json" \
      -d '{
        "year": 2004
      }'

If you send an empty JSON object (`{}`), the API explicitly rejects it with:

    {
      "error": "Bad Request",
      "message": "No fields to update",
      "code": 400
    }

### Delete a Book

Deletion completes the CRUD lifecycle and is often used in cleanup or administrative flows. The endpoint returns `204 No Content` to indicate success without returning a body.

    curl -i -X DELETE http://127.0.0.1:5000/books/1

If the specified book does not exist, you receive a 404 error with `"Book not found"`.

### Swagger / OpenAPI Documentation

The project also embeds its own OpenAPI schema and Swagger UI to help you and other developers explore the API interactively and generate client code.

- To obtain the raw schema as JSON (useful for tooling or generating clients):

      curl -i http://127.0.0.1:5000/swagger.json

- To open the interactive Docs UI in a browser, navigate to:

      http://127.0.0.1:5000/docs

Swagger UI is loaded from a CDN and points to `/swagger.json` as the API definition.

---

## Testing

Before pushing changes or deploying, you should run the test suite to confirm that existing behavior remains correct. Tests also serve as living documentation for expected application behavior.

The repository uses **pytest**, and tests reside in the `tests/` directory:

- `test_app.py`: focuses on the Flask app behavior and specific routes or handlers.
- `test_functional_app.py`: may perform more end-to-end checks, exercising multiple layers at once.

To run the tests, ensure your virtual environment is activated, any required test configuration is in place (e.g., test DB), and run pytest from the project root:

    # Run the full test suite
    pytest

    # Run tests in quiet mode
    pytest -q

    # Run only tests matching a substring (useful when focusing on a specific area)
    pytest -k "functional"

If you need an isolated test database, you can extend or adjust `TestConfig` in `config.py` to point to a different DB (e.g., using `APP_TEST_DB_NAME`). Set the appropriate environment variables before invoking `pytest`.

---

## Contributing

A clear contribution workflow reduces friction and ensures that changes are easy to review, test, and merge. The following steps outline a typical Git-based contribution process:

1. **Fork** the repository to your own account (if you do not have write access).
2. **Create a feature branch** from the main branch, using descriptive names like `feature/add-book-search` or `fix/year-validation`.
3. **Implement changes** while preserving the separation of concerns:
   - HTTP/API logic in `books/routes.py`.
   - Data-access logic in `books/repository.py`.
   - Schema changes via new Alembic migrations in `migrations/versions`.
   - Model updates in `books/models.py` when columns change.
4. **Write or update tests** in `tests/` that cover your new behavior or bug fix.
5. **Run the test suite** locally and ensure all tests pass.
6. **Submit a Pull Request (PR)** explaining:
   - What you changed and why.
   - Any breaking changes or migration requirements.
   - How reviewers can reproduce and verify your change.

To support that workflow, you will typically run Git commands similar to these (after making your edits and ensuring they work):

    # Create and switch to a new feature branch
    git checkout -b feature/add-new-endpoint

    # Stage and commit changes with a meaningful message
    git add .
    git commit -m "Add filtering options to books list endpoint"

    # Push your branch to your fork
    git push origin feature/add-new-endpoint

Then you can open a PR from `feature/add-new-endpoint` into the main project branch using your Git hosting platform (e.g., GitHub, GitLab).

For code style, try to:

- Use clear, descriptive names for functions and variables.
- Keep functions small and focused.
- Add docstrings for public functions and modules when behavior is not obvious.
- Follow any existing style or formatting conventions in the repo (e.g., if using `black` or `flake8`, run them before committing).

---

## License

This project is licensed under the BSD 2-Clause License. See the LICENSE file for details.

---

## Contact & References

Having a defined contact point and list of references makes it easier for users and contributors to get help and understand the technologies under the hood.

You can customize the following template:

- **Maintainer:** Victor Bilouro `<python@bilouro.com>`  
- **Issues & Support:** Use the repository’s “Issues” tab for bug reports, feature requests, and questions.

Useful documentation for the technologies used:

- Flask: https://flask.palletsprojects.com/  
- SQLAlchemy ORM: https://docs.sqlalchemy.org/  
- Alembic migrations: https://alembic.sqlalchemy.org/  
- pytest: https://docs.pytest.org/  
- OpenAPI Specification: https://www.openapis.org/  
- Swagger UI: https://swagger.io/tools/swagger-ui/  

By following this README and its reasoning for each command and structure, you should be able to:

1. Set up the environment and database reliably.
2. Run and explore the Books API locally.
3. Extend the codebase in a maintainable way.
4. Contribute changes with confidence, backed by automated tests.
