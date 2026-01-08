"""Base repository with common utilities for CRUD operations"""

import logging
from datetime import datetime
from typing import Any, Generic, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError as SQLAlchemyIntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.repository import (
    DuplicateError,
    IntegrityError,
    NotFoundError,
    OperationError,
    ValidationError,
)
from models.base import Base
from repositories.query_builder import get_count, get_filter, query_builder
from utils.string_case import decamelize

logger = logging.getLogger(__name__)


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository class with common database operations
    
    Provides common patterns for CRUD operations that can be inherited
    by specific repository classes. Supports soft deletes, advanced filtering,
    pagination, and batch operations.
    
    Attributes:
        session: SQLAlchemy async session
        model_class: SQLAlchamy model class (e.g., User, Workspace)
        model_name: Human-readable name of the model
        
    Usage:
    >>> class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    ...     def __init__(self, session: AsyncSession):
    ...         super().__init__(session, User)

    """
    
    session: AsyncSession
    model_class: type[ModelType]
    model_name: str
    
    def __init__(self, session: AsyncSession, model_class: type[ModelType]):
        """Initialize repository with session and model class
        
        Args:
            session: SQLAlchemy async session
            model_class: SQLAlchemy model class
        """
        self.session = session
        self.model_class = model_class
        self.model_name = model_class.__name__
    
    # ==================== Basic CRUD Operations ====================
    
    async def get_by_id(self, id: Any) -> ModelType | None:
        """Get entity by ID (excluding soft-deleted records)
        
        Args:
            id: Entity primary key
            
        Returns:
            Model instance or None if not found
            
        Raises:
            ValidationError: If id format is invalid
        """
        try:
            result = await self.session.get(self.model_class, id)
            
            # Check if soft-deleted
            if result and hasattr(result, "deleted_at") and getattr(result, "deleted_at") is not None:
                logger.debug(f"{self.model_name} with id={id} is soft-deleted")
                return None
            
            if result:
                logger.debug(f"Found {self.model_name} with id={id}")
            else:
                logger.debug(f"{self.model_name} not found with id={id}")
                
            return result
        except Exception as e:
            logger.error(f"Error getting {self.model_name} by id {id}: {e}")
            raise ValidationError("id", f"Invalid ID format: {e}")
    
    async def get_by_id_including_soft_deleted(self, id: Any) -> ModelType | None:
        """Get entity by ID (including soft-deleted records)
        
        Args:
            id: Entity primary key
            
        Returns:
            Model instance or None if not found
            
        Raises:
            ValidationError: If id format is invalid
        """
        try:
            result = await self.session.get(self.model_class, id)
            
            if result:
                logger.debug(f"Found {self.model_name} with id={id}")
            else:
                logger.debug(f"{self.model_name} not found with id={id}")
                
            return result
        except Exception as e:
            logger.error(f"Error getting {self.model_name} by id {id}: {e}")
            raise ValidationError("id", f"Invalid ID format: {e}")
    
    async def get_by_id_or_raise(self, id: Any) -> ModelType:
        """Get entity by ID or raise NotFoundError if not found
        
        Args:
            id: Entity primary key
            
        Returns:
            Model instance
            
        Raises:
            NotFoundError: If entity not found or soft-deleted
            ValidationError: If id format is invalid
        """
        result = await self.get_by_id(id)
        if result is None:
            raise NotFoundError(self.model_name, id)
        return result
    
    async def get_one_by(
        self,
        filter: dict = {},
        include_soft_deleted: bool = False
    ) -> ModelType | None:
        """Get a single record by filter criteria
        
        Args:
            filter: Filter conditions dictionary
            include_soft_deleted: Whether to include soft-deleted records
            
        Returns:
            Model instance or None if not found
        """
        try:
            filters = [get_filter(self.model_class, filter)]
            
            # Exclude soft-deleted unless specified
            if not include_soft_deleted and hasattr(self.model_class, "deleted_at"):
                filters.append(self.model_class.deleted_at.is_(None))
            
            stmt = select(self.model_class).filter(and_(*filters))
            result = await self.session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error in get_one_by for {self.model_name}: {e}")
            raise OperationError("get_one_by", e)
    
    async def get_one_by_or_raise(
        self,
        filter: dict = {},
        include_soft_deleted: bool = False
    ) -> ModelType:
        """Get a single record by filter or raise NotFoundError
        
        Args:
            filter: Filter conditions dictionary
            include_soft_deleted: Whether to include soft-deleted records
            
        Returns:
            Model instance
            
        Raises:
            NotFoundError: If no record matches the filter
        """
        result = await self.get_one_by(filter, include_soft_deleted)
        if result is None:
            raise NotFoundError(self.model_name, f"filter={filter}")
        return result
    
    async def get_multi(
        self,
        filter_param: dict | None = None,
        include_soft_deleted: bool = False
    ) -> list[ModelType]:
        """Get multiple records with filtering, ordering, and pagination
        
        Args:
            filter_param: Dictionary with filter, order_by, include, join, skip, limit
            include_soft_deleted: Whether to include soft-deleted records
            
        Returns:
            List of model instances
        """
        if filter_param is None:
            filter_param = {}
        
        try:
            query = query_builder(
                model=self.model_class,
                filter=filter_param.get("filter"),
                order_by=filter_param.get("order_by"),
                include=filter_param.get("include"),
                join=filter_param.get("join"),
            )
            
            # Exclude soft-deleted unless specified
            if not include_soft_deleted and hasattr(self.model_class, "deleted_at"):
                query = query.filter(self.model_class.deleted_at.is_(None))
            
            # Apply pagination
            skip = filter_param.get("skip", 0)
            limit = filter_param.get("limit", 100)
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error in get_multi for {self.model_name}: {e}")
            raise OperationError("get_multi", e)
    
    async def get_multi_with_count(
        self,
        filter_param: dict | None = None,
        include_soft_deleted: bool = False
    ) -> dict[str, Any]:
        """Get multiple records with total count
        
        Args:
            filter_param: Dictionary with filter, order_by, include, join, skip, limit
            include_soft_deleted: Whether to include soft-deleted records
            
        Returns:
            Dictionary with 'total' count and 'results' list
        """
        if filter_param is None:
            filter_param = {}
        
        try:
            # Build base query
            query = query_builder(
                model=self.model_class,
                filter=filter_param.get("filter"),
                order_by=filter_param.get("order_by"),
                include=filter_param.get("include"),
                join=filter_param.get("join"),
            )
            
            # Exclude soft-deleted unless specified
            if not include_soft_deleted and hasattr(self.model_class, "deleted_at"):
                query = query.filter(self.model_class.deleted_at.is_(None))
            
            # Count total before pagination
            count_query = get_count(query)
            total_result = await self.session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Apply pagination
            skip = filter_param.get("skip", 0)
            limit = filter_param.get("limit", 100)
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            results = list(result.scalars().all())
            
            logger.debug(f"get_multi_with_count for {self.model_name}: total={total}, returned={len(results)}")
            
            return {
                "total": total,
                "results": results,
            }
        except Exception as e:
            logger.error(f"Error in get_multi_with_count for {self.model_name}: {e}")
            raise OperationError("get_multi_with_count", e)
    
    async def exists(self, id: Any) -> bool:
        """Check if entity exists by ID (excluding soft-deleted)
        
        Args:
            id: Entity primary key
            
        Returns:
            True if entity exists and is not soft-deleted, False otherwise
        """
        result = await self.get_by_id(id)
        return result is not None
    
    async def count(
        self,
        filter: dict | None = None,
        include_soft_deleted: bool = False
    ) -> int:
        """Count total entities matching the filter
        
        Args:
            filter: Optional filter conditions
            include_soft_deleted: Whether to include soft-deleted records
            
        Returns:
            Total count
        """
        try:
            stmt = select(func.count()).select_from(self.model_class)
            
            # Apply filters
            filters = []
            if filter:
                filters.append(get_filter(self.model_class, filter))
            
            if not include_soft_deleted and hasattr(self.model_class, "deleted_at"):
                filters.append(self.model_class.deleted_at.is_(None))
            
            if filters:
                stmt = stmt.filter(and_(*filters))
            
            result = await self.session.execute(stmt)
            count = result.scalar()
            
            logger.debug(f"Total {self.model_name} count: {count}")
            return count or 0
        except Exception as e:
            logger.error(f"Error counting {self.model_name}: {e}")
            raise OperationError("count", e)
    
    # ==================== Create Operations ====================
    
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record
        
        Args:
            obj_in: Pydantic schema for creation
            
        Returns:
            The newly created model instance
            
        Raises:
            IntegrityError: If integrity constraints fail
            DuplicateError: If duplicate key violation occurs
            OperationError: If creation fails for other reasons
        """
        try:
            # Convert Pydantic model to dict and transform keys to snake_case
            obj_in_data = decamelize(jsonable_encoder(obj_in))
            
            # Convert ISO datetime strings to Python datetime objects
            for field in ["created_at", "updated_at", "deleted_at", "expires_at"]:
                if field in obj_in_data and isinstance(obj_in_data[field], str):
                    try:
                        obj_in_data[field] = datetime.fromisoformat(
                            obj_in_data[field].replace('Z', '+00:00')
                        )
                    except ValueError:
                        pass
            
            db_obj = self.model_class(**obj_in_data)
            
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            
            self._log_operation("create", f"id={getattr(db_obj, 'id', 'unknown')}")
            return db_obj
            
        except SQLAlchemyIntegrityError as e:
            await self.session.rollback()
            error_detail = str(e.orig) if hasattr(e, 'orig') else str(e)
            
            # Check for duplicate key violation
            if "unique" in error_detail.lower() or "duplicate" in error_detail.lower():
                logger.error(f"Duplicate key error creating {self.model_name}: {error_detail}")
                raise DuplicateError(self.model_name, "unknown_field", "unknown_value")
            
            logger.error(f"Integrity error creating {self.model_name}: {error_detail}")
            raise IntegrityError("database constraint", error_detail)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating {self.model_name}: {e}")
            raise OperationError("create", e)
    
    async def save(self, model_obj: ModelType) -> ModelType:
        """Save (persist) a model object to the database
        
        Args:
            model_obj: The model instance to save
            
        Returns:
            The saved model instance
        """
        try:
            self.session.add(model_obj)
            await self.session.commit()
            await self.session.refresh(model_obj)
            
            self._log_operation("save", f"id={getattr(model_obj, 'id', 'unknown')}")
            return model_obj
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error saving {self.model_name}: {e}")
            raise OperationError("save", e)
    
    # ==================== Update Operations ====================
    
    async def update(
        self,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, dict[str, Any]]
    ) -> ModelType:
        """Perform a full update on an existing record
        
        Args:
            db_obj: The existing database record
            obj_in: Update payload (Pydantic schema or dict)
            
        Returns:
            The updated model instance
        """
        try:
            obj_data = jsonable_encoder(db_obj)
            
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_defaults=True)
            
            update_data = decamelize(update_data)
            
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            
            # Update timestamp if available
            if hasattr(db_obj, "updated_at"):
                db_obj.updated_at = datetime.now()
            
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            
            self._log_operation("update", f"id={getattr(db_obj, 'id', 'unknown')}")
            return db_obj
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating {self.model_name}: {e}")
            raise OperationError("update", e)
    
    async def patch(
        self,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, dict[str, Any]]
    ) -> ModelType:
        """Perform a partial update (patch) on an existing record
        
        Args:
            db_obj: The existing database record
            obj_in: Partial update payload (Pydantic schema or dict)
            
        Returns:
            The patched model instance
        """
        try:
            obj_data = jsonable_encoder(db_obj)
            
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            
            update_data = decamelize(update_data)
            
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            
            # Update timestamp if available
            if hasattr(db_obj, "updated_at"):
                db_obj.updated_at = datetime.now()
            
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            
            self._log_operation("patch", f"id={getattr(db_obj, 'id', 'unknown')}")
            return db_obj
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error patching {self.model_name}: {e}")
            raise OperationError("patch", e)
    
    async def update_one_by(
        self,
        filter: dict,
        obj_in: Union[UpdateSchemaType, dict[str, Any]]
    ) -> ModelType | None:
        """Find a single record by filter and update it
        
        Args:
            filter: Filter conditions
            obj_in: Update payload
            
        Returns:
            Updated model instance or None if not found
        """
        model = await self.get_one_by(filter)
        if model is None:
            return None
        
        return await self.update(db_obj=model, obj_in=obj_in)
    
    # ==================== Delete Operations ====================
    
    async def delete(self, instance: ModelType) -> bool:
        """Hard-delete an entity instance from the database
        
        Args:
            instance: Model instance to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            OperationError: If deletion fails
        """
        try:
            await self.session.delete(instance)
            await self.session.commit()
            
            self._log_operation("delete", f"id={getattr(instance, 'id', 'unknown')}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting {self.model_name}: {e}")
            raise OperationError("delete", e)
    
    async def delete_by_id(self, id: Any) -> bool:
        """Hard-delete an entity by ID
        
        Args:
            id: Entity primary key
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If entity not found
            OperationError: If deletion fails
        """
        instance = await self.get_by_id_or_raise(id)
        return await self.delete(instance)
    
    async def remove(self, id: Any) -> ModelType:
        """Soft-delete a record by setting deleted_at timestamp
        
        Args:
            id: Entity primary key
            
        Returns:
            The soft-deleted model instance
            
        Raises:
            NotFoundError: If entity not found
            OperationError: If the model doesn't support soft delete
        """
        db_obj = await self.get_by_id_or_raise(id)
        
        if not hasattr(db_obj, "deleted_at"):
            raise OperationError(
                "remove",
                Exception(f"{self.model_name} does not support soft delete")
            )
        
        try:
            db_obj.deleted_at = datetime.now()
            
            if hasattr(db_obj, "is_active"):
                db_obj.is_active = False
            
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            
            self._log_operation("remove", f"id={id}")
            return db_obj
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error soft-deleting {self.model_name}: {e}")
            raise OperationError("remove", e)
    
    # ==================== Utility Operations ====================
    
    async def refresh(self, instance: ModelType) -> ModelType:
        """Refresh the instance from database
        
        Useful after commit to get updated timestamps, etc.
        
        Args:
            instance: Model instance to refresh
            
        Returns:
            Refreshed model instance
        """
        await self.session.refresh(instance)
        logger.debug(f"Refreshed {self.model_name} instance")
        return instance
    
    async def clone(
        self,
        model_obj: ModelType,
        modify: dict[str, Any] = {}
    ) -> ModelType:
        """Clone an existing record with optional modifications
        
        Args:
            model_obj: The existing record to clone
            modify: Additional fields to override in the clone
            
        Returns:
            The cloned model instance
            
        Raises:
            IntegrityError: If cloning violates constraints
        """
        try:
            # Get object data
            obj_data = jsonable_encoder(model_obj)
            
            # Remove primary key and auto-generated fields
            fields_to_remove = ["id", "created_at", "updated_at"]
            for field in fields_to_remove:
                obj_data.pop(field, None)
            
            # Apply modifications
            obj_data.update(modify)
            
            # Create new instance
            clone_obj = self.model_class(**obj_data)
            
            self.session.add(clone_obj)
            await self.session.commit()
            await self.session.refresh(clone_obj)
            
            self._log_operation("clone", f"cloned to id={getattr(clone_obj, 'id', 'unknown')}")
            return clone_obj
            
        except SQLAlchemyIntegrityError as e:
            await self.session.rollback()
            error_detail = str(e.orig) if hasattr(e, 'orig') else str(e)
            logger.error(f"Integrity error cloning {self.model_name}: {error_detail}")
            raise IntegrityError("database constraint", error_detail)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error cloning {self.model_name}: {e}")
            raise OperationError("clone", e)
    
    # ==================== Batch Operations ====================
    
    async def batch_insert_with_mappings(
        self,
        mappings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Perform batch insert using raw dictionary mappings
        
        Args:
            mappings: List of dictionaries mapping column names to values
            
        Returns:
            The inserted mappings
            
        Raises:
            OperationError: If batch insert fails
        """
        try:
            await self.session.execute(
                self.model_class.__table__.insert().values(mappings)
            )
            await self.session.commit()
            
            self._log_operation("batch_insert", f"inserted {len(mappings)} records")
            return mappings
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Batch insert failed for {self.model_name}: {e}")
            raise OperationError("batch_insert", e)
    
    async def batch_insert_with_objects(
        self,
        objects: list[ModelType]
    ) -> list[dict[str, Any]]:
        """Perform batch insert of model instances
        
        Args:
            objects: List of model instances to insert
            
        Returns:
            The inserted objects as dictionaries
            
        Raises:
            OperationError: If batch insert fails
        """
        try:
            mappings = [jsonable_encoder(obj) for obj in objects]
            return await self.batch_insert_with_mappings(mappings)
            
        except Exception as e:
            logger.error(f"Batch insert with objects failed for {self.model_name}: {e}")
            raise OperationError("batch_insert_with_objects", e)
    
    # ==================== Private Helper Methods ====================
    
    def _log_operation(self, operation: str, details: str = "") -> None:
        """Log repository operation
        
        Args:
            operation: Operation name (e.g., "create", "update", "delete")
            details: Additional details to log
        """
        msg = f"{self.model_name}.{operation}"
        if details:
            msg += f" - {details}"
        logger.info(msg)
