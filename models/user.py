import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import TableBase

if TYPE_CHECKING:
    from models.rbac import Role


class User(TableBase):
    """User model
    
    Inherits id, created_at, updated_at, deleted_at, is_active from TableBase
    """
    __tablename__: str = "user"  # Keep singular to match existing FK references or update all FKs

    # core fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address",
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hashed user password",
    )
    
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="User's full name"
    )

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        secondary="user_role", back_populates="users"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
