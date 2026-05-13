"""Data-access layer for the books domain.

The engine is built lazily from Flask's `current_app.config` so tests can
override `SQLALCHEMY_DATABASE_URI` (e.g. to point at an in-memory SQLite).
"""
from typing import Any, Dict, List, Optional

from flask import current_app
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from books.exceptions import BookNotFoundError, DuplicateISBNError
from books.models import Book
from config import BaseConfig

# ---------------------------------------------------------------------------
# Lazy engine / session factory
# ---------------------------------------------------------------------------

_engine = None
_sessionmaker: Optional[sessionmaker] = None


def _resolve_database_uri() -> str:
    try:
        return current_app.config["SQLALCHEMY_DATABASE_URI"]
    except RuntimeError:
        # No app context (e.g. CLI utilities) — fall back to BaseConfig.
        return BaseConfig.SQLALCHEMY_DATABASE_URI


def _build_engine(url: str):
    """Create an engine. SQLite (used by tests) needs a static pool so the
    same in-memory database is visible across sessions."""
    if url.startswith("sqlite"):
        return create_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url, future=True, pool_pre_ping=True)


def get_engine():
    global _engine
    if _engine is None:
        _engine = _build_engine(_resolve_database_uri())
    return _engine


def get_sessionmaker() -> sessionmaker:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            future=True,
        )
    return _sessionmaker


def dispose_engine() -> None:
    """Reset module-level state. Tests call this between configurations."""
    global _engine, _sessionmaker
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _sessionmaker = None


def _session() -> Session:
    return get_sessionmaker()()


def _book_to_dict(book: Book) -> Dict[str, Any]:
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "status": book.status,
    }


# ---------------------------------------------------------------------------
# Repository API. Mutating functions raise typed domain errors so the HTTP
# layer can map them to status codes without touching SQLAlchemy.
# ---------------------------------------------------------------------------

def list_books() -> List[Dict[str, Any]]:
    with _session() as session:
        stmt = select(Book).order_by(Book.id)
        books = session.scalars(stmt).all()
        return [_book_to_dict(b) for b in books]


def get_book(book_id: int) -> Optional[Dict[str, Any]]:
    with _session() as session:
        book = session.get(Book, book_id)
        return _book_to_dict(book) if book else None


def create_book(data: Dict[str, Any]) -> Dict[str, Any]:
    with _session() as session:
        book = Book(
            title=data["title"],
            author=data["author"],
            year=data["year"],
            isbn=data["isbn"],
        )
        session.add(book)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise DuplicateISBNError() from exc
        session.refresh(book)
        return _book_to_dict(book)


def replace_book(book_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    with _session() as session:
        book = session.get(Book, book_id)
        if book is None:
            return None

        book.title = data["title"]
        book.author = data["author"]
        book.year = data["year"]
        book.isbn = data["isbn"]

        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise DuplicateISBNError() from exc
        session.refresh(book)
        return _book_to_dict(book)


def update_book(book_id: int, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not fields:
        return None

    with _session() as session:
        book = session.get(Book, book_id)
        if book is None:
            return None

        for key, value in fields.items():
            setattr(book, key, value)

        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise DuplicateISBNError() from exc
        session.refresh(book)
        return _book_to_dict(book)


def delete_book(book_id: int) -> bool:
    with _session() as session:
        book = session.get(Book, book_id)
        if book is None:
            return False

        session.delete(book)
        session.commit()
        return True
