"""
Repository-level exceptions for data access operations.
"""

from typing import Any
from uuid import UUID


class RepositoryError(Exception):
    """Base exception for all repository-related errors
    
    Attributes:
        message: Description of the error
    """
    
    message: str
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class NotFoundError(RepositoryError):
    """Raised when a requested entity is not found in the database
    
    Attributes:
        entity_name: Name of the entity type (e.g., "User", "Workspace")
        entity_id: ID of the entity that was not found
    """
    
    entity_name: str
    entity_id: Any
    
    def __init__(self, entity_name: str, entity_id: Any):
        self.entity_name = entity_name
        self.entity_id = entity_id
        message = f"{entity_name} with id={entity_id} not found"
        super().__init__(message)


class ValidationError(RepositoryError):
    """Raised when data validation fails
    
    Attributes:
        field_name: Name of the field that failed validation
        validation_message: Description of the validation failure
    """
    
    field_name: str
    validation_message: str
    
    def __init__(self, field_name: str, validation_message: str):
        self.field_name = field_name
        self.validation_message = validation_message
        message = f"Validation error for '{field_name}': {validation_message}"
        super().__init__(message)


class IntegrityError(RepositoryError):
    """Raised when a database integrity constraint is violated
    
    Attributes:
        constraint: Name or description of the violated constraint
        detail: Additional details about the violation
    """
    
    constraint: str
    detail: str | None
    
    def __init__(self, constraint: str, detail: str | None = None):
        self.constraint = constraint
        self.detail = detail
        message = f"Integrity constraint violation: {constraint}"
        if detail:
            message += f" - {detail}"
        super().__init__(message)


class DuplicateError(IntegrityError):
    """Raised when attempting to create a duplicate record
    
    Attributes:
        entity_name: Name of the entity type
        field_name: Name of the field with duplicate value
        value: The duplicate value
    """
    
    entity_name: str
    field_name: str
    value: Any
    
    def __init__(self, entity_name: str, field_name: str, value: Any):
        self.entity_name = entity_name
        self.field_name = field_name
        self.value = value
        constraint = f"{entity_name}.{field_name}"
        detail = f"Record with {field_name}={value} already exists"
        super().__init__(constraint, detail)


class OperationError(RepositoryError):
    """Raised when a database operation fails
    
    Attributes:
        operation: Name of the operation (e.g., "create", "update", "delete")
        original_error: The underlying exception that caused the failure
    """
    
    operation: str
    original_error: Exception | None
    
    def __init__(self, operation: str, original_error: Exception | None = None):
        self.operation = operation
        self.original_error = original_error
        message = f"Database operation '{operation}' failed"
        if original_error:
            message += f": {str(original_error)}"
        super().__init__(message)
