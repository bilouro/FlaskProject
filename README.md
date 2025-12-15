# Flask Example Microservice

This is a simple example project using **Flask** to expose a small REST microservice for managing books (in memory, no database).

It includes:

- A minimal Flask application (`app.py`)
- REST endpoints for:
  - `GET /books` – list books
  - `GET /books/<id>` – get a single book
  - `POST /books` – create a new book
  - `PUT /books/<id>` – replace a book
  - `PATCH /books/<id>` – partially update a book
  - `DELETE /books/<id>` – remove a book
- Basic unit tests in `tests/test_app.py` using `unittest`

---

## Requirements

- **Python** 3.9.6
- **virtualenv** (or `python -m venv`)

Installed Python packages used by the project:

- `Flask`
- (Optional, dev) `pytest` or any other tool you want, but the sample uses only the standard `unittest` module.

---

## Setting up the environment

### 1. Clone or copy the project

Place the project files in a folder, for example:
