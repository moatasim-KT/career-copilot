"""
Consolidated database management system.

This module provides comprehensive database functionality including:
- Connection management and pooling
- Session handling (sync and async)
- Database initialization
- Health checks and monitoring
- Query execution utilities
"""

import asyncio
import logging
import time
from contextlib import contextmanager, asynccontextmanager
from typing import Any, Dict, List, Optional, Union, AsyncGenerator, Generator

import asyncpg
from sqlalchemy import create_engine, text, MetaData, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Base class for models
Base = declarative_base()


class DatabaseManager:
    """
    Comprehensive database manager handling connections, sessions, and operations.
    
    Provides both synchronous and asynchronous database operations with
    connection pooling, health monitoring, and performance optimization.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.database_url = self.settings.database_url
        
        # Engines
        self.sync_engine = None
        self.async_engine = None
        
        # Session factories
        self.sync_session_factory = None
        self.async_session_factory = None
        
        # Connection pool settings
        self.pool_settings = self._get_optimal_pool_settings()
        
        # Health monitoring
        self.last_health_check = None
        self.health_status = {"status": "unknown"}
        
        # Initialize engines
        self._initialize_engines()
        
        logger.info("DatabaseManager initialized")
    
    def _get_optimal_pool_settings(self) -> Dict[str, Any]:
        """Calculate optimal connection pool settings."""
        try:
            import psutil
            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
        except ImportError:
            cpu_count = 4
            memory_gb = 8
        
        # Calculate pool size based on resources
        base_pool_size = max(5, min(20, cpu_count * 2))
        max_overflow = min(30, base_pool_size * 2)
        
        # Adjust based on memory
        if memory_gb < 4:
            base_pool_size = max(3, base_pool_size // 2)
            max_overflow = max(5, max_overflow // 2)
        elif memory_gb > 16:
            base_pool_size = min(25, base_pool_size + 5)
            max_overflow = min(40, max_overflow + 10)
        
        return {
            "pool_size": base_pool_size,
            "max_overflow": max_overflow,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # 1 hour
            "pool_timeout": 30,
            "pool_reset_on_return": "commit",
        }
    
    def _initialize_engines(self):
        """Initialize database engines with optimization."""
        if not self.database_url:
            logger.warning("No database URL configured")
            return
        
        # Common engine arguments
        engine_args = {
            "echo": self.settings.debug if hasattr(self.settings, 'debug') else False,
            "future": True,
        }
        
        # Database-specific configuration
        if self.database_url.startswith("sqlite"):
            # SQLite configuration
            engine_args.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 20,
                    "isolation_level": None,  # Enable autocommit
                },
                "pool_pre_ping": True,
            })
        else:
            # PostgreSQL/other databases
            engine_args.update({
                "poolclass": QueuePool,
                **self.pool_settings,
                "connect_args": {
                    "connect_timeout": 10,
                    "application_name": "career_copilot",
                    "options": "-c default_transaction_isolation=read_committed"
                } if "postgresql" in self.database_url else {}
            })
        
        # Create synchronous engine
        self.sync_engine = create_engine(self.database_url, **engine_args)
        
        # Create asynchronous engine
        async_url = self.database_url
        if async_url.startswith("postgresql://"):
            async_url = async_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif async_url.startswith("sqlite:///"):
            async_url = async_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        
        self.async_engine = create_async_engine(async_url, **engine_args)
        
        # Create session factories
        self.sync_session_factory = sessionmaker(
            bind=self.sync_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        self.async_session_factory = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        # Set up performance monitoring
        self._setup_performance_monitoring()
        
        # Set up database-specific optimizations
        self._setup_database_optimizations()
        
        logger.info(f"Database engines initialized for {self.database_url.split('://')[0]}")
    
    def _setup_performance_monitoring(self):
        """Set up query performance monitoring."""
        
        @event.listens_for(self.sync_engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(self.sync_engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            if total > 1.0:  # Log slow queries
                logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")
    
    def _setup_database_optimizations(self):
        """Set up database-specific optimizations."""
        
        if self.database_url.startswith("sqlite"):
            @event.listens_for(self.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                # Performance optimizations
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.execute("PRAGMA mmap_size=268435456")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
                logger.debug("SQLite performance pragmas applied")
        
        elif "postgresql" in self.database_url:
            @event.listens_for(self.sync_engine, "connect")
            def set_postgresql_settings(dbapi_connection, connection_record):
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout = '30s'")
                    cursor.execute("SET lock_timeout = '10s'")
                    cursor.execute("SET idle_in_transaction_session_timeout = '5min'")
                logger.debug("PostgreSQL performance settings applied")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get synchronous database session with automatic cleanup.
        
        Usage:
            with db_manager.get_session() as session:
                result = session.execute(text("SELECT 1"))
        """
        session = self.sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get asynchronous database session with automatic cleanup.
        
        Usage:
            async with db_manager.get_async_session() as session:
                result = await session.execute(text("SELECT 1"))
        """
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    def get_connection(self):
        """
        Get raw database connection.
        
        Returns:
            Database connection from the connection pool
        """
        if not self.sync_engine:
            raise RuntimeError("Database engine not initialized")
        
        return self.sync_engine.connect()
    
    async def get_async_connection(self):
        """
        Get raw asynchronous database connection.
        
        Returns:
            Async database connection from the connection pool
        """
        if not self.async_engine:
            raise RuntimeError("Async database engine not initialized")
        
        return self.async_engine.connect()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a SQL query synchronously.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        with self.get_session() as session:
            if params:
                result = session.execute(text(query), params)
            else:
                result = session.execute(text(query))
            
            # Handle different result types
            if result.returns_rows:
                return result.fetchall()
            else:
                return result.rowcount
    
    async def execute_async_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a SQL query asynchronously.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        async with self.get_async_session() as session:
            if params:
                result = await session.execute(text(query), params)
            else:
                result = await session.execute(text(query))
            
            # Handle different result types
            if result.returns_rows:
                return result.fetchall()
            else:
                return result.rowcount
    
    def init_database(self) -> bool:
        """
        Initialize database tables and extensions.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Create extensions for PostgreSQL
            if "postgresql" in self.database_url:
                self._create_postgresql_extensions()
            
            # Create all tables
            Base.metadata.create_all(bind=self.sync_engine)
            
            logger.info("Database initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    async def init_database_async(self) -> bool:
        """
        Initialize database tables and extensions asynchronously.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Create extensions for PostgreSQL
            if "postgresql" in self.database_url:
                await self._create_postgresql_extensions_async()
            
            # Create all tables
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Async database initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Async database initialization failed: {e}")
            return False
    
    def _create_postgresql_extensions(self):
        """Create PostgreSQL extensions."""
        with self.get_connection() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\""))
            conn.execute(text("SET timezone = 'UTC'"))
            conn.commit()
            logger.debug("PostgreSQL extensions created")
    
    async def _create_postgresql_extensions_async(self):
        """Create PostgreSQL extensions asynchronously."""
        async with self.get_async_connection() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\""))
            await conn.execute(text("SET timezone = 'UTC'"))
            await conn.commit()
            logger.debug("PostgreSQL extensions created (async)")
    
    def check_connection(self) -> bool:
        """
        Check if database connection is working.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    async def check_connection_async(self) -> bool:
        """
        Check if async database connection is working.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with self.get_async_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Async database connection check failed: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive database health status.
        
        Returns:
            Dictionary containing health information
        """
        try:
            start_time = time.time()
            
            # Test connection
            connection_ok = self.check_connection()
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Get pool statistics
            pool_stats = {}
            if self.sync_engine and hasattr(self.sync_engine, 'pool'):
                pool = self.sync_engine.pool
                pool_stats = {
                    "size": getattr(pool, 'size', lambda: 'unknown')(),
                    "checked_in": getattr(pool, 'checkedin', lambda: 'unknown')(),
                    "checked_out": getattr(pool, 'checkedout', lambda: 'unknown')(),
                    "overflow": getattr(pool, 'overflow', lambda: 'unknown')(),
                    "invalid": getattr(pool, 'invalid', lambda: 'unknown')(),
                }
            
            health_status = {
                "status": "healthy" if connection_ok else "unhealthy",
                "response_time_ms": round(response_time, 2),
                "database_type": self.database_url.split("://")[0] if self.database_url else "unknown",
                "pool_stats": pool_stats,
                "engines": {
                    "sync_engine": self.sync_engine is not None,
                    "async_engine": self.async_engine is not None,
                },
                "timestamp": time.time()
            }
            
            self.last_health_check = time.time()
            self.health_status = health_status
            
            return health_status
            
        except Exception as e:
            error_status = {
                "status": "error",
                "error": str(e),
                "database_type": self.database_url.split("://")[0] if self.database_url else "unknown",
                "timestamp": time.time()
            }
            
            self.health_status = error_status
            return error_status
    
    async def get_health_status_async(self) -> Dict[str, Any]:
        """
        Get comprehensive database health status asynchronously.
        
        Returns:
            Dictionary containing health information
        """
        try:
            start_time = time.time()
            
            # Test async connection
            connection_ok = await self.check_connection_async()
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Get pool statistics
            pool_stats = {}
            if self.async_engine and hasattr(self.async_engine, 'pool'):
                pool = self.async_engine.pool
                pool_stats = {
                    "size": getattr(pool, 'size', lambda: 'unknown')(),
                    "checked_in": getattr(pool, 'checkedin', lambda: 'unknown')(),
                    "checked_out": getattr(pool, 'checkedout', lambda: 'unknown')(),
                    "overflow": getattr(pool, 'overflow', lambda: 'unknown')(),
                    "invalid": getattr(pool, 'invalid', lambda: 'unknown')(),
                }
            
            health_status = {
                "status": "healthy" if connection_ok else "unhealthy",
                "response_time_ms": round(response_time, 2),
                "database_type": self.database_url.split("://")[0] if self.database_url else "unknown",
                "pool_stats": pool_stats,
                "engines": {
                    "sync_engine": self.sync_engine is not None,
                    "async_engine": self.async_engine is not None,
                },
                "timestamp": time.time()
            }
            
            self.last_health_check = time.time()
            self.health_status = health_status
            
            return health_status
            
        except Exception as e:
            error_status = {
                "status": "error",
                "error": str(e),
                "database_type": self.database_url.split("://")[0] if self.database_url else "unknown",
                "timestamp": time.time()
            }
            
            self.health_status = error_status
            return error_status
    
    def close(self):
        """Close all database connections."""
        if self.sync_engine:
            self.sync_engine.dispose()
            logger.debug("Sync engine disposed")
        
        if self.async_engine:
            # Note: async engine disposal should be done in async context
            # This is a fallback for sync cleanup
            try:
                asyncio.create_task(self.async_engine.dispose())
            except RuntimeError:
                # If no event loop is running, we can't dispose async engine
                logger.warning("Could not dispose async engine - no event loop running")
        
        logger.info("DatabaseManager closed")
    
    async def close_async(self):
        """Close all database connections asynchronously."""
        if self.async_engine:
            await self.async_engine.dispose()
            logger.debug("Async engine disposed")
        
        if self.sync_engine:
            self.sync_engine.dispose()
            logger.debug("Sync engine disposed")
        
        logger.info("DatabaseManager closed (async)")


# Global database manager instance
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_database_manager_async() -> DatabaseManager:
    """
    Get the global database manager instance (async version).
    
    Returns:
        DatabaseManager instance
    """
    return get_database_manager()


# Backward compatibility functions
def get_db():
    """
    Database session dependency for FastAPI.
    
    Yields:
        Database session
    """
    db_manager = get_database_manager()
    with db_manager.get_session() as session:
        yield session


async def get_db_async():
    """
    Async database session dependency for FastAPI.
    
    Yields:
        Async database session
    """
    db_manager = get_database_manager()
    async with db_manager.get_async_session() as session:
        yield session


def init_db():
    """Initialize database tables (backward compatibility)."""
    db_manager = get_database_manager()
    return db_manager.init_database()


async def create_tables():
    """Create all tables asynchronously (backward compatibility)."""
    db_manager = get_database_manager()
    return await db_manager.init_database_async()


# Legacy compatibility
SessionLocal = None
AsyncSessionLocal = None
engine = None


def _setup_legacy_compatibility():
    """Set up legacy compatibility objects."""
    global SessionLocal, AsyncSessionLocal, engine
    
    db_manager = get_database_manager()
    if db_manager.sync_engine:
        engine = db_manager.sync_engine
        SessionLocal = db_manager.sync_session_factory
        AsyncSessionLocal = db_manager.async_session_factory


# Initialize legacy compatibility on import
_setup_legacy_compatibility()