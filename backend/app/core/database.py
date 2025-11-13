"""
Consolidated and Optimized Database Management System.

This module provides a comprehensive, unified database management system with a focus
on performance, reliability, and ease of use. It includes:
- Synchronous and asynchronous connection and session management.
- Optimized connection pooling for PostgreSQL.
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
		# Engines are initialized lazily to avoid creating loop-bound async resources
		# at import time. Callers should invoke init_db() or explicitly call
		# _initialize_engines() (synchronously) during application startup to
		# ensure engines are created on the correct event loop.
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
		# Enforce PostgreSQL-only usage across the codebase to avoid sqlite
		# related event-loop/driver inconsistencies in async contexts.
		if "postgresql://" in self.database_url or "postgresql+" in self.database_url:
			async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://").replace("postgresql+psycopg://", "postgresql+asyncpg://")
			# For sync engine, use the regular (blocking) postgres driver URL
			sync_url = async_url.replace("postgresql+asyncpg://", "postgresql://")
		else:
			raise RuntimeError(
				"Unsupported DATABASE_URL. This deployment requires PostgreSQL. Please set DATABASE_URL to a Postgres connection string."
			)

		# Sync engine args (with poolclass)
		sync_engine_args = base_engine_args.copy()
		# Use QueuePool for Postgres sync engine
		sync_engine_args.update({"poolclass": QueuePool, **self.pool_settings})

		# Async engine args (without poolclass - async engines use their own pool management)
		async_engine_args = base_engine_args.copy()
		# For async PostgreSQL, pass pool settings without poolclass
		async_pool_settings = {k: v for k, v in self.pool_settings.items() if k != "poolclass"}
		async_engine_args.update(async_pool_settings)

		# Create sync engine for specific tasks first to ensure the sync
		# engine uses a blocking DBAPI (psycopg) and not the asyncpg-backed
		# sync shim. This avoids mixing asyncpg connections into the sync
		# pool which can cause cross-event-loop errors.
		logger.debug(f"Creating sync engine with URL: {sync_url}")
		self.sync_engine = create_engine(sync_url, **sync_engine_args)
		self.sync_session_factory = sessionmaker(self.sync_engine, expire_on_commit=False)

		# Create main write engine (async) on the active event loop
		logger.debug(f"Creating async engine with URL: {async_url}")
		try:
			self.async_engine = create_async_engine(async_url, **async_engine_args)
			self.async_session_factory = async_sessionmaker(self.async_engine, class_=AsyncSession, expire_on_commit=False)
		except Exception as e:  # pragma: no cover - defensive fallback when async driver is missing
			logger.error(f"Failed to create async engine ({async_url}): {e}")
			self.async_engine = None
			self.async_session_factory = None

		self._setup_performance_monitoring(self.sync_engine, "write")
		self._initialize_read_replicas()
		logger.info(f"Database engines initialized for {async_url.split('://')[0]}.")

	def _initialize_sync_engine(self):
		"""Initialize only the synchronous (blocking) engine and session factory.

		This is useful for startup paths that need the DB schema (create_all)
		but must avoid creating loop-bound async resources until an active
		event loop is available (e.g., test harnesses using TestClient).
		"""
		if not self.database_url:
			logger.error("FATAL: No database URL configured for sync engine initialization.")
			return

		base_engine_args = {"echo": self.settings.debug, "future": True}

		if "postgresql://" in self.database_url or "postgresql+" in self.database_url:
			# Use blocking psycopg URL for sync engine
			sync_url = self.database_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg://", "postgresql://")

		else:
			raise RuntimeError("Unsupported DATABASE_URL for sync engine initialization.")

		sync_engine_args = base_engine_args.copy()
		sync_engine_args.update({"poolclass": QueuePool, **self.pool_settings})

		logger.debug(f"Creating sync-only engine with URL: {sync_url}")
		self.sync_engine = create_engine(sync_url, **sync_engine_args)
		self.sync_session_factory = sessionmaker(self.sync_engine, expire_on_commit=False)
		self._setup_performance_monitoring(self.sync_engine, "write")
		logger.info("Synchronous database engine initialized (sync-only).")

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

	# Ensure engines are initialized synchronously (safe to call at startup)
	if manager.sync_engine is None:
		try:
			# Initialize only the sync engine at startup. Do not create the
			# async engine here: creating the async engine at module import
			# or during process startup risks binding it to an event loop
			# that differs from the one used by request handlers under
			# TestClient/anyio, causing cross-event-loop runtime errors.
			manager._initialize_sync_engine()
		except Exception as exc:  # pragma: no cover - defensive logging
			logger.error("Failed to initialize sync database engine during init_db: %s", exc)

	# Import models to register mappings, then create tables using the sync engine
	try:
		import importlib

		importlib.import_module("app.models")  # Ensure model metadata is registered
	except Exception as exc:  # pragma: no cover - defensive logging
		logger.warning("Failed to import app.models during init_db: %s", exc)

	if manager.sync_engine is None:
		raise RuntimeError("Database sync engine is not initialized after initialization attempt")

	# Create DB schema using synchronous engine (safer during sync startup code paths)
	Base.metadata.create_all(bind=manager.sync_engine)

	# Update legacy compatibility globals now that sync engine is ready.
	# Note: async engine is intentionally left uninitialized here so it
	# will be created lazily on the active request event loop when the
	# FastAPI dependency `get_db()` is first invoked.
	_setup_legacy_compatibility()

	logger.info("Database schema ensured via init_db()")


# Backward compatibility for FastAPI dependency injection


async def get_db() -> AsyncGenerator[AsyncSession, None]:
	db_manager = get_db_manager()
	# First try to ensure a long-lived async engine exists bound to the
	# current event loop. Creating the global async engine here ensures
	# subsequent DB work (connections/futures) are attached to the same
	# loop used by request handlers and avoids "Future attached to a
	# different loop" errors that appear when engines are created on
	# other loops (e.g. TestClient internals).
	if db_manager.async_engine is None:
		logger.debug("get_db: async_engine is None; attempting to initialize global engines on current loop")
		try:
			# This will create both sync and async engines; async engine will
			# be bound to the currently running event loop.
			db_manager._initialize_engines()
			if db_manager.async_engine is not None:
				try:
					await db_manager.init_database()
				except Exception:
					logger.exception("Failed to run async init_database after creating engines; continuing and letting request proceed if possible")
			# Update legacy compatibility now that factories exist
			_setup_legacy_compatibility()
		except Exception as exc:  # pragma: no cover - defensive fallback
			logger.exception("Failed to initialize global async engine inside get_db(): %s", exc)
			# If global initialization failed, fall back to creating a
			# request-scoped temporary async engine so the request can still
			# proceed. This is rare but preserves functionality in constrained
			# testing environments.
			# Build async URL similar to manager._initialize_engines logic
			db_url = db_manager.database_url
			if not db_url:
				raise RuntimeError("No DATABASE_URL configured")

			if "postgresql+asyncpg://" in db_url or "postgresql://" in db_url:
				async_url = db_url.replace("postgresql://", "postgresql+asyncpg://").replace("postgresql+psycopg://", "postgresql+asyncpg://")
				raise RuntimeError("Unsupported DATABASE_URL. This deployment requires PostgreSQL.")

			async_pool_settings = {k: v for k, v in db_manager.pool_settings.items() if k != "poolclass"}
			try:
				temp_engine = create_async_engine(async_url, echo=db_manager.settings.debug, future=True, **async_pool_settings)
				temp_session_factory = async_sessionmaker(temp_engine, class_=AsyncSession, expire_on_commit=False)
			except Exception as exc:  # pragma: no cover - surface creation failure
				logger.exception("Failed to create temporary async engine as fallback: %s", exc)
				raise

			try:
				async with temp_session_factory() as session:
					yield session
			finally:
				try:
					await temp_engine.dispose()
				except Exception as dispose_exc:
					logger.exception("Failed to dispose temporary async engine: %s", dispose_exc)

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
