"""
Consolidated and Optimized Database Management System.

This module provides a comprehensive, unified database management system with a focus
on performance, reliability, and ease of use. It includes:
- Synchronous and asynchronous connection and session management.
- Optimized connection pooling for both SQLite and PostgreSQL.
- Read replica support for distributing read-heavy workloads.
- Query performance monitoring with slow query detection.
- Centralized database initialization and health checks.
- Backward compatibility for existing application code.
"""

import asyncio
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Base class for all SQLAlchemy models
Base = declarative_base()


class DatabaseManager:
	"""Manages all database connections, sessions, and performance optimizations."""

	def __init__(self):
		self.settings = get_settings()
		self.database_url = self.settings.database_url
		self.sync_engine = None
		self.async_engine = None
		self.read_engines: Dict[str, Any] = {}
		self.read_replica_enabled = False
		self.sync_session_factory = None
		self.async_session_factory = None
		self.pool_settings = self._get_optimal_pool_settings()
		self.last_health_check = None
		self.health_status = {"status": "unknown"}
		self._initialize_engines()
		logger.info("DatabaseManager initialized")

	def _get_optimal_pool_settings(self) -> Dict[str, Any]:
		try:
			import psutil

			cpu_count = psutil.cpu_count()
		except ImportError:
			cpu_count = 4

		base_pool_size = max(5, min(20, cpu_count * 2))
		max_overflow = min(30, base_pool_size * 2)

		return {
			"pool_size": base_pool_size,
			"max_overflow": max_overflow,
			"pool_pre_ping": True,
			"pool_recycle": 3600,  # 1 hour
			"pool_timeout": 30,
		}

	def _initialize_engines(self):
		if not self.database_url:
			logger.error("FATAL: No database URL configured.")
			return

		# Base engine args for both sync and async
		base_engine_args = {"echo": self.settings.debug, "future": True}

		# Prepare URLs
		# If DATABASE_URL already has async drivers, convert them for appropriate engines
		if "postgresql://" in self.database_url:
			async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
		elif "sqlite:///" in self.database_url and "aiosqlite" not in self.database_url:
			async_url = self.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
		else:
			async_url = self.database_url
		# For sync engine, use standard drivers
		sync_url = self.database_url.replace("postgresql+asyncpg://", "postgresql://").replace("sqlite+aiosqlite:///", "sqlite:///")

		# Sync engine args (with poolclass)
		sync_engine_args = base_engine_args.copy()
		if "sqlite" in sync_url:
			sync_engine_args.update(
				{
					"poolclass": StaticPool,
					"connect_args": {"check_same_thread": False, "timeout": 20},
				}
			)
		else:
			sync_engine_args.update({"poolclass": QueuePool, **self.pool_settings})

		# Async engine args (without poolclass - async engines use their own pool management)
		async_engine_args = base_engine_args.copy()
		if "sqlite" in async_url:
			async_engine_args.update(
				{
					"connect_args": {"check_same_thread": False, "timeout": 20},
				}
			)
		else:
			# For async PostgreSQL, pass pool settings without poolclass
			async_pool_settings = {k: v for k, v in self.pool_settings.items() if k != "poolclass"}
			async_engine_args.update(async_pool_settings)

		# Create main write engine (async)
		logger.debug(f"Creating async engine with URL: {async_url}")
		self.async_engine = create_async_engine(async_url, **async_engine_args)
		self.async_session_factory = async_sessionmaker(self.async_engine, class_=AsyncSession, expire_on_commit=False)

		# Create sync engine for specific tasks if needed
		logger.debug(f"Creating sync engine with URL: {sync_url}")
		self.sync_engine = create_engine(sync_url, **sync_engine_args)
		self.sync_session_factory = sessionmaker(self.sync_engine, expire_on_commit=False)

		self._setup_performance_monitoring(self.sync_engine, "write")
		self._initialize_read_replicas()
		logger.info(f"Database engines initialized for {async_url.split('://')[0]}.")

	def _initialize_read_replicas(self):
		read_replica_urls = getattr(self.settings, "read_replica_urls", [])
		if not read_replica_urls:
			logger.info("No read replicas configured.")
			return

		for i, replica_url in enumerate(read_replica_urls):
			try:
				# For async engines, filter out poolclass from settings
				async_pool_settings = {k: v for k, v in self.pool_settings.items() if k != "poolclass"}
				engine = create_async_engine(replica_url, **async_pool_settings)
				self.read_engines[f"replica_{i}"] = engine
				self._setup_performance_monitoring(engine.sync_engine, f"read_replica_{i}")
			except Exception as e:
				logger.error(f"Failed to initialize read replica {i}: {e}")

		if self.read_engines:
			self.read_replica_enabled = True
			logger.info(f"Initialized {len(self.read_engines)} read replicas.")

	def _setup_performance_monitoring(self, engine, engine_type: str):
		@event.listens_for(engine, "before_cursor_execute")
		def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
			context._query_start_time = time.time()

		@event.listens_for(engine, "after_cursor_execute")
		def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
			total = time.time() - context._query_start_time
			if total > 1.0:
				logger.warning(f"Slow query on {engine_type} engine ({total:.2f}s): {statement[:200]}...")

	def _get_read_engine(self):
		if self.read_replica_enabled and self.read_engines:
			# Simple round-robin for load balancing
			replica_name = list(self.read_engines.keys())[int(time.time()) % len(self.read_engines)]
			return self.read_engines[replica_name]
		return self.async_engine

	@asynccontextmanager
	async def get_session(self, read_only: bool = False) -> AsyncGenerator[AsyncSession, None]:
		engine = self._get_read_engine() if read_only else self.async_engine
		session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
		async with session_factory() as session:
			try:
				yield session
				await session.commit()
			except Exception:
				await session.rollback()
				raise
			finally:
				await session.close()

	@contextmanager
	def get_sync_session(self) -> Generator[Session, None, None]:
		if not self.sync_session_factory:
			raise RuntimeError("Sync session factory not initialized.")
		session = self.sync_session_factory()
		try:
			yield session
			session.commit()
		except Exception:
			session.rollback()
			raise
		finally:
			session.close()

	async def init_database(self):
		async with self.async_engine.begin() as conn:
			await conn.run_sync(Base.metadata.create_all)
		logger.info("Database initialization completed.")

	async def check_connection(self) -> bool:
		try:
			async with self.get_session() as session:
				await session.execute(text("SELECT 1"))
			return True
		except Exception as e:
			logger.error(f"Database connection check failed: {e}")
			return False

	async def close(self):
		if self.async_engine:
			await self.async_engine.dispose()
		if self.sync_engine:
			self.sync_engine.dispose()
		for engine in self.read_engines.values():
			await engine.dispose()
		logger.info("All database connections closed.")

	def get_health_status(self) -> Dict[str, Any]:
		"""Synchronous database health probe used by health endpoints.

		Returns a lightweight dict with status and basic details without
		requiring an event loop, so it can be called from sync contexts.
		"""
		start = time.time()
		url_lc = (self.database_url or "").lower()
		if "postgres" in url_lc:
			backend = "postgresql"
		elif "sqlite" in url_lc:
			backend = "sqlite"
		else:
			backend = "unknown"

		try:
			if self.sync_engine is None:
				raise RuntimeError("Sync engine not initialized")

			with self.get_sync_session() as session:
				session.execute(text("SELECT 1"))

			latency_ms = (time.time() - start) * 1000.0
			self.health_status = {
				"status": "healthy",
				"backend": backend,
				"response_time_ms": latency_ms,
			}
			self.last_health_check = time.time()
			return self.health_status

		except Exception as e:  # pragma: no cover - defensive runtime path
			latency_ms = (time.time() - start) * 1000.0
			logger.error(f"Database health probe failed: {e}")
			return {
				"status": "unhealthy",
				"backend": backend,
				"error": str(e),
				"response_time_ms": latency_ms,
			}


_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
	global _db_manager
	if _db_manager is None:
		_db_manager = DatabaseManager()
	return _db_manager


# Backward compatibility alias


def get_database_manager() -> DatabaseManager:
	return get_db_manager()


def init_db() -> None:
	"""Legacy-compatible synchronous database bootstrapper."""
	manager = get_db_manager()

	try:
		import importlib

		importlib.import_module("app.models")  # Ensure model metadata is registered
	except Exception as exc:  # pragma: no cover - defensive logging
		logger.warning("Failed to import app.models during init_db: %s", exc)

	if manager.sync_engine is None:
		raise RuntimeError("Database sync engine is not initialized")

	Base.metadata.create_all(bind=manager.sync_engine)
	logger.info("Database schema ensured via init_db()")


# Backward compatibility for FastAPI dependency injection


async def get_db() -> AsyncGenerator[AsyncSession, None]:
	db_manager = get_db_manager()
	async with db_manager.get_session() as session:
		yield session


# Legacy compatibility
SessionLocal = None
AsyncSessionLocal = None
engine = None


def _setup_legacy_compatibility():
	global SessionLocal, AsyncSessionLocal, engine
	db_manager = get_db_manager()
	engine = db_manager.sync_engine
	SessionLocal = db_manager.sync_session_factory
	AsyncSessionLocal = db_manager.async_session_factory


_setup_legacy_compatibility()
