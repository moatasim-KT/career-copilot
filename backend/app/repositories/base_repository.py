"""
Base repository class with common database operations and performance optimizations.
"""

import time
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from sqlalchemy import select, update, delete, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from ..core.database import Base
from ..core.logging import get_logger

logger = get_logger(__name__)
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations and performance optimizations."""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository with model and session.
        
        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session
        self._query_cache = {}
        self._enable_query_logging = True
    
    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record.
        
        Args:
            **kwargs: Field values for the new record
            
        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get record by ID.
        
        Args:
            id: Record UUID
            
        Returns:
            Model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """
        Get record by field value.
        
        Args:
            field_name: Name of the field to filter by
            value: Value to match
            
        Returns:
            Model instance or None if not found
        """
        field = getattr(self.model, field_name)
        result = await self.session.execute(
            select(self.model).where(field == value)
        )
        return result.scalar_one_or_none()
    
    async def list_all(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        List all records with optional pagination and ordering.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Field name to order by
            
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        if order_by:
            order_field = getattr(self.model, order_by, None)
            if order_field is not None:
                query = query.order_by(order_field)
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def list_by_field(
        self, 
        field_name: str, 
        value: Any,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """
        List records by field value.
        
        Args:
            field_name: Name of the field to filter by
            value: Value to match
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of model instances
        """
        field = getattr(self.model, field_name)
        query = select(self.model).where(field == value)
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_by_id(self, id: UUID, **kwargs) -> Optional[ModelType]:
        """
        Update record by ID.
        
        Args:
            id: Record UUID
            **kwargs: Fields to update
            
        Returns:
            Updated model instance or None if not found
        """
        # First check if record exists
        instance = await self.get_by_id(id)
        if not instance:
            return None
        
        # Update the record
        await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
        )
        
        # Refresh and return updated instance
        await self.session.refresh(instance)
        return instance
    
    async def delete_by_id(self, id: UUID) -> bool:
        """
        Delete record by ID.
        
        Args:
            id: Record UUID
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0
    
    async def count(self, **filters) -> int:
        """
        Count records with optional filters.
        
        Args:
            **filters: Field filters
            
        Returns:
            Number of matching records
        """
        query = select(func.count(self.model.id))
        
        for field_name, value in filters.items():
            field = getattr(self.model, field_name, None)
            if field is not None:
                query = query.where(field == value)
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def exists(self, **filters) -> bool:
        """
        Check if record exists with given filters.
        
        Args:
            **filters: Field filters
            
        Returns:
            True if record exists, False otherwise
        """
        count = await self.count(**filters)
        return count > 0
    
    async def bulk_create(self, records: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in bulk.
        
        Args:
            records: List of dictionaries with field values
            
        Returns:
            List of created model instances
        """
        instances = [self.model(**record) for record in records]
        self.session.add_all(instances)
        await self.session.flush()
        
        # Refresh all instances to get generated IDs
        for instance in instances:
            await self.session.refresh(instance)
        
        return instances
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple records in bulk.
        
        Args:
            updates: List of dictionaries with 'id' and update fields
            
        Returns:
            Number of updated records
        """
        total_updated = 0
        
        for update_data in updates:
            record_id = update_data.pop('id')
            result = await self.session.execute(
                update(self.model)
                .where(self.model.id == record_id)
                .values(**update_data)
            )
            total_updated += result.rowcount
        
        return total_updated
    
    async def execute_optimized_query(
        self, 
        query: Select, 
        use_cache: bool = False,
        cache_ttl: int = 300
    ) -> Any:
        """
        Execute query with performance optimizations.
        
        Args:
            query: SQLAlchemy select query
            use_cache: Whether to use query result caching
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            Query result
        """
        start_time = time.time()
        
        try:
            # Execute query
            result = await self.session.execute(query)
            
            # Log slow queries
            execution_time = time.time() - start_time
            if execution_time > 1.0 and self._enable_query_logging:
                logger.warning(
                    f"Slow query detected ({execution_time:.2f}s): {str(query)[:200]}..."
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Query failed after {execution_time:.2f}s: {str(e)[:200]}..."
            )
            raise
    
    async def get_with_relationships(
        self, 
        id: UUID, 
        relationships: List[str] = None
    ) -> Optional[ModelType]:
        """
        Get record by ID with specified relationships loaded.
        
        Args:
            id: Record UUID
            relationships: List of relationship names to load
            
        Returns:
            Model instance with relationships or None if not found
        """
        query = select(self.model).where(self.model.id == id)
        
        if relationships:
            for rel_name in relationships:
                if hasattr(self.model, rel_name):
                    query = query.options(selectinload(getattr(self.model, rel_name)))
        
        result = await self.execute_optimized_query(query)
        return result.scalar_one_or_none()
    
    async def list_with_pagination(
        self,
        page: int = 1,
        page_size: int = 20,
        order_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        relationships: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        List records with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            page_size: Number of records per page
            order_by: Field name to order by
            filters: Dictionary of field filters
            relationships: List of relationship names to load
            
        Returns:
            Dictionary with items, total count, and pagination info
        """
        # Build base query
        query = select(self.model)
        count_query = select(func.count(self.model.id))
        
        # Apply filters
        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    if isinstance(value, list):
                        query = query.where(field.in_(value))
                        count_query = count_query.where(field.in_(value))
                    else:
                        query = query.where(field == value)
                        count_query = count_query.where(field == value)
        
        # Get total count
        total_result = await self.execute_optimized_query(count_query)
        total_count = total_result.scalar()
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            query = query.order_by(order_field)
        
        # Apply relationships
        if relationships:
            for rel_name in relationships:
                if hasattr(self.model, rel_name):
                    query = query.options(selectinload(getattr(self.model, rel_name)))
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.execute_optimized_query(query)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "has_next": page * page_size < total_count,
            "has_prev": page > 1
        }
    
    async def search_text(
        self,
        search_term: str,
        text_fields: List[str],
        limit: Optional[int] = None,
        use_full_text: bool = True
    ) -> List[ModelType]:
        """
        Search records using text fields with full-text search optimization.
        
        Args:
            search_term: Text to search for
            text_fields: List of text field names to search in
            limit: Maximum number of results
            use_full_text: Whether to use PostgreSQL full-text search
            
        Returns:
            List of matching model instances
        """
        if not text_fields or not search_term:
            return []
        
        query = select(self.model)
        
        if use_full_text and hasattr(self.session.bind, 'dialect') and 'postgresql' in str(self.session.bind.dialect):
            # Use PostgreSQL full-text search
            search_conditions = []
            for field_name in text_fields:
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    search_conditions.append(
                        func.to_tsvector('english', field).match(search_term)
                    )
            
            if search_conditions:
                from sqlalchemy import or_
                query = query.where(or_(*search_conditions))
        else:
            # Fallback to ILIKE search
            search_conditions = []
            for field_name in text_fields:
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    search_conditions.append(field.ilike(f"%{search_term}%"))
            
            if search_conditions:
                from sqlalchemy import or_
                query = query.where(or_(*search_conditions))
        
        if limit:
            query = query.limit(limit)
        
        result = await self.execute_optimized_query(query)
        return result.scalars().all()
    
    async def get_statistics(self, group_by_field: str = None) -> Dict[str, Any]:
        """
        Get basic statistics for the model.
        
        Args:
            group_by_field: Field to group statistics by
            
        Returns:
            Dictionary with statistics
        """
        stats = {"total_count": await self.count()}
        
        if group_by_field and hasattr(self.model, group_by_field):
            field = getattr(self.model, group_by_field)
            
            # Group by field statistics
            query = select(field, func.count()).group_by(field)
            result = await self.execute_optimized_query(query)
            
            group_stats = {}
            for row in result:
                group_stats[str(row[0])] = row[1]
            
            stats[f"by_{group_by_field}"] = group_stats
        
        return stats
    
    async def optimize_table(self) -> Dict[str, Any]:
        """
        Perform table optimization operations.
        
        Returns:
            Dictionary with optimization results
        """
        table_name = self.model.__tablename__
        
        try:
            # Analyze table statistics
            await self.session.execute(text(f"ANALYZE {table_name}"))
            
            # Get table size information
            size_query = text("""
                SELECT 
                    pg_size_pretty(pg_total_relation_size(:table_name)) as total_size,
                    pg_size_pretty(pg_relation_size(:table_name)) as table_size,
                    pg_size_pretty(pg_total_relation_size(:table_name) - pg_relation_size(:table_name)) as index_size
            """)
            
            result = await self.session.execute(size_query, {"table_name": table_name})
            size_info = result.fetchone()
            
            return {
                "table_name": table_name,
                "analyzed": True,
                "total_size": size_info[0] if size_info else "unknown",
                "table_size": size_info[1] if size_info else "unknown", 
                "index_size": size_info[2] if size_info else "unknown"
            }
            
        except Exception as e:
            logger.error(f"Table optimization failed for {table_name}: {e}")
            return {
                "table_name": table_name,
                "analyzed": False,
                "error": str(e)
            }