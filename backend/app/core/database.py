"""
Enhanced database management with connection pooling, query optimization, and performance monitoring.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from dataclasses import dataclass

import asyncpg
import chromadb
from chromadb.config import Settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy import text, event
from sqlalchemy.engine import Engine

from .config import get_settings
from .logging import get_logger
from ..models.database_models import Base

logger = get_logger(__name__)


@dataclass
class QueryMetrics:
    """Query performance metrics."""
    query: str
    execution_time: float
    timestamp: datetime
    success: bool
    error: Optional[str] = None


class DatabaseManager:
	"""Enhanced database manager with connection pooling and async operations."""

	def __init__(self):
		self.engine = None
		self.async_session = None
		self.chroma_client = None
		self.connection_pool = None
		self._initialized = False
		
		# Performance monitoring
		self.query_metrics = []
		self.slow_query_threshold = 1.0  # seconds
		self.connection_stats = {
			"total_connections": 0,
			"active_connections": 0,
			"failed_connections": 0,
			"avg_connection_time": 0.0
		}
		
		# Query optimization
		self.query_cache = {}
		self.cache_hit_rate = 0.0
		self.optimization_suggestions = []

	async def initialize(self):
		"""Initialize database connections and pools with performance optimization."""
		if self._initialized:
			return

		try:
			# Get configuration values
			settings = get_settings()
			database_url = settings.database_url or f"sqlite+aiosqlite:///./data/contract_analyzer.db"
			api_debug = settings.api_debug
			
			# Initialize database connection pool with optimized settings
			if database_url:
				# Determine optimal pool size based on system resources
				try:
					import psutil
					cpu_count = psutil.cpu_count()
					memory_gb = psutil.virtual_memory().total / (1024**3)
					
					# Calculate optimal pool size based on system resources
					optimal_pool_size = min(20, max(5, cpu_count * 2))
					optimal_max_overflow = min(30, optimal_pool_size * 2)
					
					# Adjust for available memory
					if memory_gb < 4:
						optimal_pool_size = max(3, optimal_pool_size // 2)
						optimal_max_overflow = max(5, optimal_max_overflow // 2)
				except ImportError:
					# Fallback if psutil is not available
					optimal_pool_size = 10
					optimal_max_overflow = 20
				
				# Configure engine based on database type
				if database_url.startswith(("postgresql", "postgres")):
					# PostgreSQL-specific configuration with enhanced connection management
					self.engine = create_async_engine(
						database_url,
						pool_size=optimal_pool_size,
						max_overflow=optimal_max_overflow,
						pool_pre_ping=True,
						pool_recycle=3600,  # Recycle connections every hour
						pool_timeout=30,
						pool_reset_on_return='commit',
						echo=api_debug,
						connect_args={
							"command_timeout": 60,
							"server_settings": {
								"application_name": "contract_analyzer",
								"jit": "off",
							}
						}
					)
				else:
					# SQLite configuration with connection pooling
					self.engine = create_async_engine(
						database_url,
						echo=api_debug,
						poolclass=StaticPool,
						connect_args={
							"check_same_thread": False,
							"timeout": 60
						}
					)
				
				# Set up query performance monitoring
				self._setup_query_monitoring()
				
				# Set up connection pool monitoring
				self._setup_connection_pool_monitoring()
				
				self.async_session = async_sessionmaker(
					self.engine, 
					class_=AsyncSession, 
					expire_on_commit=False
				)
				
				# Auto-run migrations on startup
				await self._auto_migrate_database()
				
				# Create database indexes for performance
				await self._create_performance_indexes()

			# Initialize ChromaDB with connection pooling
			chroma_persist_directory = settings.chroma_persist_directory
			self.chroma_client = chromadb.PersistentClient(
				path=chroma_persist_directory, 
				settings=Settings(allow_reset=True, anonymized_telemetry=False, is_persistent=True)
			)

			# Initialize Redis connection pool
			enable_redis = settings.enable_redis_caching
			if enable_redis:
				import redis.asyncio as redis

				redis_host = settings.redis_host
				redis_port = settings.redis_port
				redis_db = settings.redis_db
				redis_password = settings.redis_password
				
				self.redis_pool = redis.ConnectionPool(
					host=redis_host,
					port=redis_port,
					db=redis_db,
					password=redis_password,
					max_connections=20,
					socket_timeout=30,
					socket_connect_timeout=10,
					retry_on_timeout=True,
				)
				self.redis_client = redis.Redis(connection_pool=self.redis_pool)

			self._initialized = True
			logger.info("Database manager initialized successfully")

		except Exception as e:
			logger.error(f"Failed to initialize database manager: {e}")
			raise

	@asynccontextmanager
	async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
		"""Get async database session with proper cleanup."""
		if not self.async_session:
			raise RuntimeError("Database not initialized")

		async with self.async_session() as session:
			try:
				yield session
				await session.commit()
			except Exception:
				await session.rollback()
				raise
			finally:
				await session.close()

	async def get_chroma_collection(self, collection_name: str = None):
		"""Get ChromaDB collection with error handling."""
		if not self.chroma_client:
			raise RuntimeError("ChromaDB not initialized")

		collection_name = collection_name or settings.chroma_collection_name
		try:
			return self.chroma_client.get_collection(collection_name)
		except Exception:
			# Create collection if it doesn't exist
			return self.chroma_client.create_collection(collection_name)

	async def cache_get(self, key: str) -> Optional[Any]:
		"""Get value from Redis cache."""
		if not hasattr(self, "redis_client"):
			return None

		try:
			value = await self.redis_client.get(key)
			return value.decode("utf-8") if value else None
		except Exception as e:
			logger.warning(f"Cache get failed for key {key}: {e}")
			return None

	async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
		"""Set value in Redis cache with TTL."""
		if not hasattr(self, "redis_client"):
			return False

		try:
			await self.redis_client.setex(key, ttl, str(value))
			return True
		except Exception as e:
			logger.warning(f"Cache set failed for key {key}: {e}")
			return False

	async def cache_delete(self, key: str) -> bool:
		"""Delete value from Redis cache."""
		if not hasattr(self, "redis_client"):
			return False

		try:
			await self.redis_client.delete(key)
			return True
		except Exception as e:
			logger.warning(f"Cache delete failed for key {key}: {e}")
			return False

	async def health_check(self) -> Dict[str, Any]:
		"""Enhanced database health status check with migration info."""
		health_status = {
			"database": False, 
			"chromadb": False, 
			"redis": False, 
			"migrations": {},
			"connection_pool": {},
			"performance": {},
			"timestamp": datetime.utcnow().isoformat()
		}

		# Check main database with migration status
		if self.async_session:
			try:
				async with self.get_session() as session:
					await session.execute(text("SELECT 1"))
					health_status["database"] = True
				
				# Get migration status
				from .migrations import get_database_migrator
				migrator = await get_database_migrator()
				migration_health = await migrator.get_database_health()
				health_status["migrations"] = migration_health.get("migrations", {})
				
				# Get detailed connection pool stats
				if self.engine and hasattr(self.engine, 'pool'):
					pool = self.engine.pool
					try:
						# Handle different pool types (StaticPool vs QueuePool)
						pool_type = type(pool).__name__
						if pool_type == "StaticPool":
							# StaticPool (SQLite) - single connection
							pool_size = 1
							checked_in = 0
							checked_out = 1 if self.connection_stats["active_connections"] > 0 else 0
							overflow = 0
							invalid = 0
						elif hasattr(pool, 'size'):
							# QueuePool and other pool types
							pool_size = pool.size()
							checked_in = pool.checkedin()
							checked_out = pool.checkedout()
							overflow = pool.overflow()
							invalid = pool.invalid()
						else:
							# Fallback for unknown pool types
							pool_size = 1
							checked_in = 0
							checked_out = 0
							overflow = 0
							invalid = 0
						
						health_status["connection_pool"] = {
							"pool_type": pool_type,
							"pool_size": pool_size,
							"checked_in": checked_in,
							"checked_out": checked_out,
							"overflow": overflow,
							"invalid": invalid,
							"total_connections": self.connection_stats["total_connections"],
							"active_connections": self.connection_stats["active_connections"],
							"failed_connections": self.connection_stats["failed_connections"],
							"avg_connection_time": self.connection_stats["avg_connection_time"],
							"pool_utilization": (checked_out / pool_size * 100) if pool_size > 0 else 0
						}
					except Exception as e:
						health_status["connection_pool"] = {
							"error": f"Pool stats error: {e}",
							"pool_type": type(pool).__name__ if hasattr(self.engine, 'pool') else "unknown"
						}
				
				# Get performance metrics
				health_status["performance"] = await self.get_performance_metrics()
				
			except Exception as e:
				logger.error(f"Database health check failed: {e}")
				health_status["database_error"] = str(e)

		# Check ChromaDB
		if self.chroma_client:
			try:
				collections = self.chroma_client.list_collections()
				health_status["chromadb"] = True
				health_status["chromadb_collections"] = len(collections)
			except Exception as e:
				logger.error(f"ChromaDB health check failed: {e}")
				health_status["chromadb_error"] = str(e)

		# Check Redis
		if hasattr(self, "redis_client"):
			try:
				await self.redis_client.ping()
				health_status["redis"] = True
			except Exception as e:
				logger.error(f"Redis health check failed: {e}")
				health_status["redis_error"] = str(e)

		return health_status

	def _setup_query_monitoring(self):
		"""Set up query performance monitoring."""
		@event.listens_for(Engine, "before_cursor_execute")
		def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
			context._query_start_time = time.time()

		@event.listens_for(Engine, "after_cursor_execute")
		def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
			total = time.time() - context._query_start_time
			
			# Record query metrics
			query_metric = QueryMetrics(
				query=statement[:100] + "..." if len(statement) > 100 else statement,
				execution_time=total,
				timestamp=datetime.utcnow(),
				success=True
			)
			self.query_metrics.append(query_metric)
			
			# Keep only last 1000 queries
			if len(self.query_metrics) > 1000:
				self.query_metrics = self.query_metrics[-1000:]
			
			# Log slow queries
			if total > self.slow_query_threshold:
				logger.warning(f"Slow query detected ({total:.2f}s): {statement[:200]}")
				self._analyze_slow_query(statement, total)
	
	def _setup_connection_pool_monitoring(self):
		"""Set up connection pool event monitoring."""
		if not self.engine:
			return
		
		@event.listens_for(self.engine.pool, "connect")
		def on_connect(dbapi_conn, connection_record):
			self.connection_stats["total_connections"] += 1
			connection_record.info['connect_time'] = time.time()
		
		@event.listens_for(self.engine.pool, "checkout")
		def on_checkout(dbapi_conn, connection_record, connection_proxy):
			self.connection_stats["active_connections"] += 1
			if 'connect_time' in connection_record.info:
				connect_time = time.time() - connection_record.info['connect_time']
				# Update average connection time
				current_avg = self.connection_stats["avg_connection_time"]
				total_conns = self.connection_stats["total_connections"]
				if total_conns > 0:
					self.connection_stats["avg_connection_time"] = (
						(current_avg * (total_conns - 1) + connect_time) / total_conns
					)
		
		@event.listens_for(self.engine.pool, "checkin")
		def on_checkin(dbapi_conn, connection_record):
			if self.connection_stats["active_connections"] > 0:
				self.connection_stats["active_connections"] -= 1
		
		@event.listens_for(self.engine.pool, "invalidate")
		def on_invalidate(dbapi_conn, connection_record, exception):
			self.connection_stats["failed_connections"] += 1
			logger.warning(f"Database connection invalidated: {exception}")
	
	async def _auto_migrate_database(self):
		"""Automatically run database migrations on startup."""
		try:
			from .migrations import auto_migrate_on_startup
			
			logger.info("🔄 Running auto-migration check...")
			success = await auto_migrate_on_startup()
			
			if success:
				logger.info("✅ Auto-migration completed successfully")
			else:
				logger.warning("⚠️  Auto-migration failed or not needed")
				
		except Exception as e:
			logger.error(f"❌ Auto-migration error: {e}")
			# Don't fail initialization if migration fails
			pass

	def _analyze_slow_query(self, query: str, execution_time: float):
		"""Analyze slow queries and provide optimization suggestions."""
		suggestions = []
		
		# Check for common performance issues
		query_lower = query.lower()
		
		if "select *" in query_lower:
			suggestions.append("Consider selecting specific columns instead of *")
		
		if "order by" in query_lower and "limit" not in query_lower:
			suggestions.append("Consider adding LIMIT clause when using ORDER BY")
		
		if "like '%" in query_lower:
			suggestions.append("Leading wildcards in LIKE queries can be slow - consider full-text search")
		
		if query_lower.count("join") > 3:
			suggestions.append("Multiple JOINs detected - consider query optimization")
		
		if suggestions:
			self.optimization_suggestions.append({
				"query": query[:200],
				"execution_time": execution_time,
				"suggestions": suggestions,
				"timestamp": datetime.utcnow()
			})

	async def _create_performance_indexes(self):
		"""Create database indexes for better performance."""
		if not self.engine:
			return
		
		# Define indexes with their corresponding tables
		index_definitions = [
			# Contract analysis indexes
			("contracts", "CREATE INDEX IF NOT EXISTS idx_contracts_created_at ON contracts(created_at)"),
			("contracts", "CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)"),
			("contracts", "CREATE INDEX IF NOT EXISTS idx_contracts_user_id ON contracts(user_id)"),
			("contract_analyses", "CREATE INDEX IF NOT EXISTS idx_contract_analyses_contract_id ON contract_analyses(contract_id)"),
			("contract_analyses", "CREATE INDEX IF NOT EXISTS idx_contract_analyses_analysis_type ON contract_analyses(analysis_type)"),
			("audit_logs", "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)"),
			("audit_logs", "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)"),
			("users", "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"),
			("users", "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"),
		]
		
		try:
			async with self.engine.begin() as conn:
				# Check which tables exist first using run_sync
				def get_table_names(sync_conn):
					from sqlalchemy import inspect
					inspector = inspect(sync_conn)
					return inspector.get_table_names()
				
				existing_tables = await conn.run_sync(get_table_names)
				
				created_indexes = 0
				skipped_indexes = 0
				
				for table_name, query in index_definitions:
					if table_name in existing_tables:
						try:
							await conn.execute(text(query))
							created_indexes += 1
						except Exception as e:
							logger.debug(f"Index creation skipped for {table_name}: {e}")
							skipped_indexes += 1
					else:
						logger.debug(f"Table {table_name} does not exist, skipping index creation")
						skipped_indexes += 1
				
				if created_indexes > 0:
					logger.info(f"Performance indexes created: {created_indexes} created, {skipped_indexes} skipped")
				else:
					logger.debug("No performance indexes created - tables may not exist yet")
					
		except Exception as e:
			logger.warning(f"Failed to create performance indexes: {e}")

	async def get_performance_metrics(self) -> Dict[str, Any]:
		"""Get database performance metrics."""
		if not self.query_metrics:
			return {"status": "no_queries"}
		
		recent_queries = [q for q in self.query_metrics 
						 if q.timestamp > datetime.utcnow() - timedelta(hours=1)]
		
		if not recent_queries:
			return {"status": "no_recent_queries"}
		
		execution_times = [q.execution_time for q in recent_queries]
		successful_queries = [q for q in recent_queries if q.success]
		
		# Handle connection pool stats safely
		connection_pool_stats = {"pool_type": "unknown"}
		if self.engine and hasattr(self.engine, 'pool'):
			pool = self.engine.pool
			try:
				pool_type = type(pool).__name__
				if pool_type == "StaticPool":
					# StaticPool (SQLite) - single connection
					connection_pool_stats = {
						"pool_type": "StaticPool",
						"pool_size": 1,
						"checked_in": 0,
						"checked_out": 1 if self.connection_stats["active_connections"] > 0 else 0,
						"overflow": 0,
						"invalid": 0
					}
				elif hasattr(pool, 'size'):
					# QueuePool and other pool types
					connection_pool_stats = {
						"pool_type": pool_type,
						"pool_size": pool.size(),
						"checked_in": pool.checkedin(),
						"checked_out": pool.checkedout(),
						"overflow": pool.overflow(),
						"invalid": pool.invalid()
					}
				else:
					# Fallback for unknown pool types
					connection_pool_stats = {
						"pool_type": pool_type,
						"pool_size": 1,
						"checked_in": 0,
						"checked_out": 0,
						"overflow": 0,
						"invalid": 0
					}
			except Exception as e:
				connection_pool_stats = {
					"pool_type": type(pool).__name__ if hasattr(pool, '__name__') else "unknown",
					"error": str(e)
				}
		
		return {
			"query_performance": {
				"total_queries": len(recent_queries),
				"successful_queries": len(successful_queries),
				"failed_queries": len(recent_queries) - len(successful_queries),
				"avg_execution_time": sum(execution_times) / len(execution_times),
				"min_execution_time": min(execution_times),
				"max_execution_time": max(execution_times),
				"slow_queries": len([t for t in execution_times if t > self.slow_query_threshold])
			},
			"connection_pool": connection_pool_stats,
			"optimization_suggestions": len(self.optimization_suggestions)
		}

	async def optimize_queries(self) -> Dict[str, Any]:
		"""Analyze and optimize database queries."""
		optimization_results = {
			"analyzed_queries": len(self.query_metrics),
			"optimizations_applied": 0,
			"performance_improvements": {}
		}
		
		# Analyze recent slow queries
		recent_slow_queries = [
			q for q in self.query_metrics 
			if q.execution_time > self.slow_query_threshold and 
			q.timestamp > datetime.utcnow() - timedelta(hours=24)
		]
		
		if recent_slow_queries:
			# Group similar queries
			query_groups = {}
			for query in recent_slow_queries:
				# Simple grouping by query pattern
				pattern = query.query.split()[0] if query.query.split() else "unknown"
				if pattern not in query_groups:
					query_groups[pattern] = []
				query_groups[pattern].append(query)
			
			# Generate optimization recommendations
			for pattern, queries in query_groups.items():
				avg_time = sum(q.execution_time for q in queries) / len(queries)
				if avg_time > self.slow_query_threshold * 2:
					optimization_results["optimizations_applied"] += 1
		
		return optimization_results

	async def monitor_connection_health(self) -> Dict[str, Any]:
		"""Monitor connection health and detect issues."""
		health_report = {
			"healthy": True,
			"issues": [],
			"recommendations": [],
			"connection_stats": self.connection_stats.copy(),
			"timestamp": datetime.utcnow().isoformat()
		}
		
		try:
			if self.engine and hasattr(self.engine, 'pool'):
				pool = self.engine.pool
				
				# Handle different pool types
				try:
					pool_type = type(pool).__name__
					if pool_type == "StaticPool":
						# StaticPool (SQLite) - different monitoring approach
						health_report["pool_type"] = "StaticPool (SQLite)"
						if self.connection_stats["active_connections"] > 5:
							health_report["issues"].append("High concurrent connection usage for SQLite")
							health_report["recommendations"].append("Consider connection pooling optimization")
					elif hasattr(pool, 'size'):
						# QueuePool and other pool types
						pool_size = pool.size()
						checked_out = pool.checkedout()
						utilization = (checked_out / pool_size * 100) if pool_size > 0 else 0
						
						if utilization > 80:
							health_report["healthy"] = False
							health_report["issues"].append(f"High pool utilization: {utilization:.1f}%")
							health_report["recommendations"].append("Consider increasing pool size")
						
						# Check for connection leaks
						if checked_out > pool_size * 0.9:
							health_report["issues"].append("Possible connection leak detected")
							health_report["recommendations"].append("Review connection usage patterns")
					else:
						# Unknown pool type
						health_report["pool_type"] = f"Unknown ({pool_type})"
				
				except Exception as pool_error:
					health_report["issues"].append(f"Pool monitoring error: {pool_error}")
				
				# Check for failed connections
				failure_rate = (
					self.connection_stats["failed_connections"] / 
					max(1, self.connection_stats["total_connections"]) * 100
				)
				
				if failure_rate > 5:
					health_report["healthy"] = False
					health_report["issues"].append(f"High connection failure rate: {failure_rate:.1f}%")
					health_report["recommendations"].append("Check database connectivity and configuration")
				
				# Check average connection time
				if self.connection_stats["avg_connection_time"] > 5.0:
					health_report["issues"].append("Slow connection establishment")
					health_report["recommendations"].append("Check network latency and database performance")
			
		except Exception as e:
			health_report["issues"].append(f"Health monitoring error: {e}")
		
		return health_report
	
	async def optimize_connection_pool(self) -> Dict[str, Any]:
		"""Optimize connection pool settings based on usage patterns."""
		optimization_results = {
			"optimizations_applied": [],
			"recommendations": [],
			"current_settings": {},
			"suggested_settings": {}
		}
		
		try:
			if self.engine and hasattr(self.engine, 'pool'):
				pool = self.engine.pool
				
				# Handle different pool types
				pool_type = type(pool).__name__
				if pool_type == "StaticPool":
					# StaticPool (SQLite)
					optimization_results["current_settings"] = {
						"pool_type": "StaticPool",
						"pool_size": 1,
						"note": "SQLite uses StaticPool - single connection"
					}
					
					# SQLite-specific recommendations
					if self.connection_stats["active_connections"] > 3:
						optimization_results["recommendations"].append("High concurrent usage for SQLite - consider PostgreSQL for production")
				elif hasattr(pool, 'size'):
					# Regular connection pool (QueuePool, etc.)
					pool_size = pool.size()
					checked_out = pool.checkedout()
					
					optimization_results["current_settings"] = {
						"pool_type": pool_type,
						"pool_size": pool_size,
						"max_overflow": getattr(pool, '_max_overflow', 0),
						"timeout": getattr(pool, '_timeout', 30)
					}
					
					# Analyze usage patterns
					avg_utilization = (checked_out / pool_size * 100) if pool_size > 0 else 0
					
					# Suggest optimizations
					if avg_utilization < 20:
						optimization_results["recommendations"].append("Pool size could be reduced")
						optimization_results["suggested_settings"]["pool_size"] = max(3, pool_size - 2)
					elif avg_utilization > 80:
						optimization_results["recommendations"].append("Pool size should be increased")
						optimization_results["suggested_settings"]["pool_size"] = pool_size + 5
				else:
					# Unknown pool type
					optimization_results["current_settings"] = {
						"pool_type": pool_type,
						"pool_size": "unknown",
						"note": f"Unknown pool type: {pool_type}"
					}
				
				# Check connection timeout
				if self.connection_stats["avg_connection_time"] > 2.0:
					optimization_results["recommendations"].append("Consider increasing connection timeout")
					optimization_results["suggested_settings"]["timeout"] = 60
			
		except Exception as e:
			optimization_results["error"] = str(e)
		
		return optimization_results

	async def close(self):
		"""Close all database connections."""
		if self.engine:
			await self.engine.dispose()

		if hasattr(self, "redis_pool"):
			await self.redis_pool.disconnect()

		self._initialized = False
		logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


async def get_database_manager() -> DatabaseManager:
	"""Get the global database manager instance."""
	if not db_manager._initialized:
		await db_manager.initialize()
	return db_manager


@asynccontextmanager
async def get_db_session():
	"""Dependency for getting database session."""
	manager = await get_database_manager()
	async with manager.get_session() as session:
		yield session


@asynccontextmanager
async def get_chroma_collection(collection_name: str = None):
	"""Dependency for getting ChromaDB collection."""
	manager = await get_database_manager()
	collection = await manager.get_chroma_collection(collection_name)
	yield collection


# Compatibility exports for legacy code
async def get_db():
	"""Legacy compatibility function for getting database session."""
	async with get_db_session() as session:
		yield session


# Export engine for direct access
async def get_engine():
	"""Get database engine."""
	manager = await get_database_manager()
	return manager.engine


# Synchronous engine access (for compatibility)
engine = None


async def initialize_engine():
	"""Initialize and return engine."""
	global engine
	manager = await get_database_manager()
	engine = manager.engine
	return engine
