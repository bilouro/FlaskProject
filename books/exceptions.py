"""Domain-level exceptions raised by the repository.

These keep SQLAlchemy concerns out of the HTTP layer. The error handlers in
`app.py` translate them to HTTP responses with the standard envelope.
"""


class DomainError(Exception):
    """Base for application-level errors that map to HTTP responses."""

    status_code: int = 500
    message: str = "Internal Server Error"

    def __init__(self, message: str = None) -> None:
        super().__init__(message or self.message)
        if message:
            self.message = message


class BookNotFoundError(DomainError):
    status_code = 404
    message = "Book not found"


class DuplicateISBNError(DomainError):
    status_code = 409
    message = "A book with this ISBN already exists"
