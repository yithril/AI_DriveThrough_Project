"""
Base repository class with common CRUD operations
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from ..core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository class providing common CRUD operations
    """
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record (does not commit - use UnitOfWork)
        
        Args:
            **kwargs: Model attributes
            
        Returns:
            ModelType: Created model instance
            
        Raises:
            IntegrityError: If unique constraint violation
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()  # Flush to get ID but don't commit
        await self.db.refresh(instance)
        return instance
    
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get a record by ID
        
        Args:
            id: Primary key ID
            
        Returns:
            ModelType or None: Model instance if found
        """
        try:
            result = await self.db.execute(
                select(self.model).where(self.model.id == id)
            )
            record = result.scalar_one_or_none()
            return record
        except Exception as e:
            raise
    
    async def get_by_id_with_relations(self, id: int, relations: List[str]) -> Optional[ModelType]:
        """
        Get a record by ID with specified relations loaded
        
        Args:
            id: Primary key ID
            relations: List of relationship names to eager load
            
        Returns:
            ModelType or None: Model instance if found
        """
        query = select(self.model).where(self.model.id == id)
        
        # Add eager loading for specified relations
        for relation in relations:
            if hasattr(self.model, relation):
                query = query.options(selectinload(getattr(self.model, relation)))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all records with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[ModelType]: List of model instances
        """
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def get_all_by_filter(self, filters: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all records matching filters
        
        Args:
            filters: Dictionary of field: value filters
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[ModelType]: List of model instances
        """
        query = select(self.model)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        result = await self.db.execute(
            query.offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        Update a record by ID
        
        Args:
            id: Primary key ID
            **kwargs: Fields to update
            
        Returns:
            ModelType or None: Updated model instance if found
            
        Raises:
            IntegrityError: If unique constraint violation
        """
        # Remove None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not update_data:
            return await self.get_by_id(id)
        
        await self.db.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
        )
        await self.db.flush()  # Flush but don't commit - use UnitOfWork
        
        return await self.get_by_id(id)
    
    async def delete(self, id: int) -> bool:
        """
        Delete a record by ID
        
        Args:
            id: Primary key ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.flush()  # Flush but don't commit - use UnitOfWork
        return result.rowcount > 0
    
    async def exists(self, id: int) -> bool:
        """
        Check if a record exists by ID
        
        Args:
            id: Primary key ID
            
        Returns:
            bool: True if exists, False otherwise
        """
        result = await self.db.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records matching optional filters
        
        Args:
            filters: Optional dictionary of field: value filters
            
        Returns:
            int: Number of matching records
        """
        query = select(self.model.id)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        result = await self.db.execute(query)
        return len(result.scalars().all())
    
    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """
        Get a record by a specific field value
        
        Args:
            field: Field name
            value: Field value
            
        Returns:
            ModelType or None: Model instance if found
        """
        if not hasattr(self.model, field):
            return None
        
        result = await self.db.execute(
            select(self.model).where(getattr(self.model, field) == value)
        )
        return result.scalar_one_or_none()
