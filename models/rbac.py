import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func

from models.base import Base
from models.user import User


class PermissionGroup(Base):
    __tablename__ = "permission_group"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique permission group identifier",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Permission group name",
    )

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

    permissions: Mapped[list["Permission"]] = relationship(
        back_populates="permission_group"
    )


class TabList(Base):
    __tablename__ = "tab_list"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique tab list identifier",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Tab list name",
    )

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

    permissions: Mapped[list["Permission"]] = relationship(back_populates="tab_list")


class Permission(Base):
    __tablename__ = "permission"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique permission identifier",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Permission name",
    )

    permission_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permission_group.id"),
        nullable=False,
        comment="Permission group ID",
    )

    tab_list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tab_list.id"),
        nullable=False,
        comment="Tab list ID",
    )

    description: Mapped[str] = mapped_column(
        String(255),
        comment="Permission description",
    )

    resource: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Resource",
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Action",
    )

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

    roles: Mapped[list["Role"]] = relationship(
        secondary="role_permission", back_populates="permissions"
    )

    permission_group: Mapped["PermissionGroup"] = relationship(
        back_populates="permissions"
    )

    tab_list: Mapped["TabList"] = relationship(back_populates="permissions")


class Role(Base):
    __tablename__ = "role"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique role identifier",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Role name",
    )

    description: Mapped[str] = mapped_column(
        String(255),
        comment="Role description",
    )

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

    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permission", back_populates="roles"
    )

    users: Mapped[list["User"]] = relationship(
        secondary="user_role", back_populates="roles"
    )


class RolePermission(Base):
    __tablename__ = "role_permission"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique role permission identifier",
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("role.id"),
        nullable=False,
        comment="Role ID",
    )

    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permission.id"),
        nullable=False,
        comment="Permission ID",
    )

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


class UserRole(Base):
    __tablename__ = "user_role"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique user role identifier",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        comment="User ID",
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("role.id"),
        nullable=False,
        comment="Role ID",
    )

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
