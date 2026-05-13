"""Pydantic v2 schemas for the books domain.

Input schemas (`BookCreate`/`BookReplace`/`BookPatch`) reject unknown fields
and enforce strict type checks. The output schema (`BookOut`) types the
response payload, including the server-managed `status`, `created_at`, and
`updated_at` fields.
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


_TITLE = Annotated[str, Field(min_length=1, max_length=255)]
_AUTHOR = Annotated[str, Field(min_length=1, max_length=255)]
_ISBN = Annotated[str, Field(min_length=1, max_length=32)]
_YEAR = Annotated[int, Field(ge=-3000, le=9999)]


class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class BookCreate(_StrictBase):
    title: _TITLE
    author: _AUTHOR
    year: _YEAR
    isbn: _ISBN


class BookReplace(BookCreate):
    """PUT shares the create contract — full replacement."""


class BookPatch(_StrictBase):
    title: Optional[_TITLE] = None
    author: Optional[_AUTHOR] = None
    year: Optional[_YEAR] = None
    isbn: Optional[_ISBN] = None
    status: Optional[Annotated[str, Field(min_length=1, max_length=32)]] = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "BookPatch":
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field must be provided")
        return self


class BookOut(BaseModel):
    """Response payload. Accepts dict or ORM instance (`from_attributes`)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    year: int
    isbn: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
