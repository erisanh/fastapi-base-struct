"""
Custom exceptions for the application
"""

# Database connection exceptions
from exceptions.db_connection import ConnectionError, DatabaseError

# Repository exceptions
from exceptions.repository import (
    DuplicateError,
    IntegrityError,
    NotFoundError,
    OperationError,
    RepositoryError,
    ValidationError,
)

__all__ = [
    # Database connection
    "DatabaseError",
    "ConnectionError",
    # Repository
    "RepositoryError",
    "NotFoundError",
    "ValidationError",
    "IntegrityError",
    "DuplicateError",
    "OperationError",
]
