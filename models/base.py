"""Base models and mixins for the application"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all ORM models"""
    __abstract__ = True


class UUIDMixin:
    """Mixin for UUID primary key"""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier",
    )


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Creation timestamp",
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp",
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality
    
    Required for BaseRepository.remove() to work correctly.
    """
    
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Soft delete timestamp",
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        comment="Active status",
    )


class TableBase(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Recommended Base class for all models.
    
    Includes:
    - UUID primary key
    - Timestamps (created_at, updated_at)
    - Soft delete support (deleted_at, is_active)
    """
    __abstract__ = True