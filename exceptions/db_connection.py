"""
Defines custom exceptions for database connection errors.
"""

class DatabaseError(Exception):
    """Base exception for all the database related errors

    Attributes:
        message: str: Description of the error
    """

    message: str

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ConnectionError(DatabaseError):
    """Raised when database connection/pool occur

    Attributes:
        original_error: the underlying exception that cause the connection failure
    """

    original_error: Exception

    def __init__(self, original_error: Exception):
        self.original_error = original_error
        message = f"Database connection error: {str(self.original_error)}"
        super().__init__(message)
