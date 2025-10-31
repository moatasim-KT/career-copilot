"""
Optimized database configuration with connection pooling and performance settings
"""

from sqlalchemy import create_engine, event
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.orm import sessionmaker
import time

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_optimized_engine():
	"""Create an optimized database engine with connection pooling"""
	settings = get_settings()
	database_url = settings.database_url

	# Base engine arguments
	engine_args = {
		"echo": settings.debug,  # Log SQL queries in debug mode
		"future": True,  # Use SQLAlchemy 2.0 style
	}

	# Configure based on database type
	if database_url.startswith("sqlite"):
		# SQLite-specific optimizations
		engine_args.update(
			{
				"poolclass": StaticPool,
				"connect_args": {
					"check_same_thread": False,
					"timeout": 20,
					# SQLite performance pragmas
					"isolation_level": None,  # Enable autocommit mode
				},
				"pool_pre_ping": True,
			}
		)

		# Create engine
		engine = create_engine(database_url, **engine_args)

		# Add SQLite-specific optimizations
		@event.listens_for(engine, "connect")
		def set_sqlite_pragma(dbapi_connection, connection_record):
			"""Set SQLite performance pragmas"""
			cursor = dbapi_connection.cursor()

			# Performance optimizations
			cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
			cursor.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL, safer than OFF
			cursor.execute("PRAGMA cache_size=10000")  # 10MB cache
			cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
			cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O

			# Foreign key support
			cursor.execute("PRAGMA foreign_keys=ON")

			cursor.close()

			logger.debug("SQLite performance pragmas applied")

	elif "postgresql" in database_url:
		# PostgreSQL-specific optimizations
		engine_args.update(
			{
				"poolclass": QueuePool,
				"pool_size": 20,  # Base number of connections
				"max_overflow": 30,  # Additional connections when needed
				"pool_timeout": 30,  # Seconds to wait for connection
				"pool_recycle": 3600,  # Recycle connections after 1 hour
				"pool_pre_ping": True,  # Validate connections before use
				"connect_args": {
					"connect_timeout": 10,
					"application_name": "career_copilot",
					# PostgreSQL-specific optimizations
					"options": "-c default_transaction_isolation=read_committed",
				},
			}
		)

		# Create engine
		engine = create_engine(database_url, **engine_args)

		# Add PostgreSQL-specific optimizations
		@event.listens_for(engine, "connect")
		def set_postgresql_settings(dbapi_connection, connection_record):
			"""Set PostgreSQL performance settings"""
			with dbapi_connection.cursor() as cursor:
				# Set session-level optimizations
				cursor.execute("SET statement_timeout = '30s'")  # Prevent long-running queries
				cursor.execute("SET lock_timeout = '10s'")  # Prevent lock waits
				cursor.execute("SET idle_in_transaction_session_timeout = '5min'")

				logger.debug("PostgreSQL performance settings applied")

	else:
		# Generic database configuration
		engine_args.update(
			{
				"poolclass": QueuePool,
				"pool_size": 10,
				"max_overflow": 20,
				"pool_timeout": 30,
				"pool_recycle": 3600,
				"pool_pre_ping": True,
			}
		)

		engine = create_engine(database_url, **engine_args)

	# Add general performance monitoring
	@event.listens_for(engine, "before_cursor_execute")
	def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
		"""Log slow queries"""
		context._query_start_time = time.time()

	@event.listens_for(engine, "after_cursor_execute")
	def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
		"""Log slow queries"""
		total = time.time() - context._query_start_time
		if total > 1.0:  # Log queries taking more than 1 second
			logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")

	logger.info(f"✅ Optimized database engine created for {database_url.split('://')[0]}")

	return engine


def create_optimized_session_factory(engine):
	"""Create an optimized session factory"""
	return sessionmaker(
		bind=engine,
		autocommit=False,
		autoflush=False,  # Manual flush for better control
		expire_on_commit=False,  # Keep objects usable after commit
	)


# Connection health check
def check_database_health(engine) -> dict:
	"""Check database connection health"""
	try:
		with engine.connect() as conn:
			start_time = time.time()

			# Simple health check query
			if "sqlite" in str(engine.url):
				result = conn.execute("SELECT 1")
			elif "postgresql" in str(engine.url):
				result = conn.execute("SELECT 1")
			else:
				result = conn.execute("SELECT 1")

			result.fetchone()
			response_time = (time.time() - start_time) * 1000  # Convert to ms

			# Get pool statistics
			pool = engine.pool
			pool_stats = {
				"size": getattr(pool, "size", "unknown"),
				"checked_in": getattr(pool, "checkedin", "unknown"),
				"checked_out": getattr(pool, "checkedout", "unknown"),
				"overflow": getattr(pool, "overflow", "unknown"),
				"invalid": getattr(pool, "invalid", "unknown"),
			}

			return {
				"status": "healthy",
				"response_time_ms": round(response_time, 2),
				"database_type": str(engine.url).split("://")[0],
				"pool_stats": pool_stats,
			}

	except Exception as e:
		logger.error(f"Database health check failed: {e}")
		return {"status": "unhealthy", "error": str(e), "database_type": str(engine.url).split("://")[0] if engine else "unknown"}


# Database maintenance utilities
def optimize_database_maintenance(engine):
	"""Perform database maintenance operations"""
	try:
		with engine.connect() as conn:
			if "sqlite" in str(engine.url):
				# SQLite maintenance
				conn.execute("PRAGMA optimize")
				conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
				logger.info("SQLite maintenance completed")

			elif "postgresql" in str(engine.url):
				# PostgreSQL maintenance (be careful in production)
				conn.execute("ANALYZE")
				logger.info("PostgreSQL statistics updated")

		return {"status": "success", "message": "Database maintenance completed"}

	except Exception as e:
		logger.error(f"Database maintenance failed: {e}")
		return {"status": "error", "error": str(e)}


# Query performance monitoring
class QueryPerformanceMonitor:
	"""Monitor and log query performance"""

	def __init__(self, slow_query_threshold: float = 1.0):
		self.slow_query_threshold = slow_query_threshold
		self.query_stats = {}

	def log_query(self, statement: str, execution_time: float):
		"""Log query execution time"""
		# Normalize query for statistics
		normalized_query = self._normalize_query(statement)

		if normalized_query not in self.query_stats:
			self.query_stats[normalized_query] = {"count": 0, "total_time": 0, "max_time": 0, "min_time": float("inf")}

		stats = self.query_stats[normalized_query]
		stats["count"] += 1
		stats["total_time"] += execution_time
		stats["max_time"] = max(stats["max_time"], execution_time)
		stats["min_time"] = min(stats["min_time"], execution_time)

		# Log slow queries
		if execution_time > self.slow_query_threshold:
			logger.warning(f"Slow query: {execution_time:.2f}s - {statement[:200]}...")

	def _normalize_query(self, statement: str) -> str:
		"""Normalize query for statistics grouping"""
		# Simple normalization - replace parameters with placeholders
		import re

		normalized = re.sub(r"\b\d+\b", "?", statement)
		normalized = re.sub(r"'[^']*'", "'?'", normalized)
		return normalized[:100]  # Truncate for storage

	def get_stats(self) -> dict:
		"""Get query performance statistics"""
		stats_summary = {}

		for query, stats in self.query_stats.items():
			avg_time = stats["total_time"] / stats["count"]
			stats_summary[query] = {
				"count": stats["count"],
				"avg_time": round(avg_time, 3),
				"max_time": round(stats["max_time"], 3),
				"min_time": round(stats["min_time"], 3),
				"total_time": round(stats["total_time"], 3),
			}

		return stats_summary


# Global query performance monitor
query_monitor = QueryPerformanceMonitor()
