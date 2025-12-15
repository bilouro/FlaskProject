from typing import Any, Dict, List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

from config import BaseConfig
from books.models import Book

# ---------------------------------------------------------------------------
# SQLAlchemy engine / session
# ---------------------------------------------------------------------------

# Single engine with connection pool, shared by the repository
engine = create_engine(
    BaseConfig.SQLALCHEMY_DATABASE_URI,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


def _book_to_dict(book: Book) -> Dict[str, Any]:
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
    }


# ---------------------------------------------------------------------------
# Repository functions using ORM
# ---------------------------------------------------------------------------

def list_books() -> List[Dict[str, Any]]:
    with SessionLocal() as session:
        stmt = select(Book).order_by(Book.id)
        books = session.scalars(stmt).all()
        return [_book_to_dict(b) for b in books]


def get_book(book_id: int) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        book = session.get(Book, book_id)
        return _book_to_dict(book) if book else None


def create_book(data: Dict[str, Any]) -> Dict[str, Any]:
    with SessionLocal() as session:
        book = Book(
            title=data["title"],
            author=data["author"],
            year=data["year"],
            isbn=data["isbn"],
        )
        session.add(book)
        session.commit()
        session.refresh(book)  # garante que id e demais campos estejam populados
        return _book_to_dict(book)


def replace_book(book_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        book = session.get(Book, book_id)
        if book is None:
            return None

        book.title = data["title"]
        book.author = data["author"]
        book.year = data["year"]
        book.isbn = data["isbn"]

        session.commit()
        session.refresh(book)
        return _book_to_dict(book)


def update_book(book_id: int, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not fields:
        return None

    with SessionLocal() as session:
        book = session.get(Book, book_id)
        if book is None:
            return None

        for key, value in fields.items():
            setattr(book, key, value)

        session.commit()
        session.refresh(book)
        return _book_to_dict(book)


def delete_book(book_id: int) -> bool:
    with SessionLocal() as session:
        book = session.get(Book, book_id)
        if book is None:
            return False

        session.delete(book)
        session.commit()
        return True