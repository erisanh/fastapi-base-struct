import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import TableBase

if TYPE_CHECKING:
    from models.user import User


class PermissionGroup(TableBase):
    __tablename__ = "permission_group"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Permission group name",
    )

    permissions: Mapped[list["Permission"]] = relationship(
        back_populates="permission_group"
    )


class TabList(TableBase):
    __tablename__ = "tab_list"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Tab list name",
    )

    permissions: Mapped[list["Permission"]] = relationship(back_populates="tab_list")


class Permission(TableBase):
    __tablename__ = "permission"

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

    roles: Mapped[list["Role"]] = relationship(
        secondary="role_permission", back_populates="permissions"
    )

    permission_group: Mapped["PermissionGroup"] = relationship(
        back_populates="permissions"
    )

    tab_list: Mapped["TabList"] = relationship(back_populates="permissions")


class Role(TableBase):
    __tablename__ = "role"

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

    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permission", back_populates="roles"
    )

    users: Mapped[list["User"]] = relationship(
        secondary="user_role", back_populates="roles"
    )


class RolePermission(TableBase):
    __tablename__ = "role_permission"

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


class UserRole(TableBase):
    __tablename__ = "user_role"

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
