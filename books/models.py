from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from typing import Optional


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    isbn: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)

    created_at: Mapped[Optional["datetime"]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )
    updated_at: Mapped[Optional["datetime"]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="active",
    )