"""Optimized database configuration with connection pooling and monitoring."""

import time

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_optimized_engine():
	"""Create an optimized database engine with connection pooling."""
	settings = get_settings()
	database_url = settings.database_url

	engine_args = {
		"echo": settings.debug,
		"future": True,
	}

	if database_url.startswith("sqlite"):
		engine_args.update(
			{
				"connect_args": {"check_same_thread": False},
				"poolclass": StaticPool if database_url.endswith(":memory:") else QueuePool,
			}
		)
	elif database_url.startswith(("postgresql", "postgres")):
		engine_args.update(
			{
				"poolclass": QueuePool,
				"pool_size": 20,
				"max_overflow": 30,
				"pool_timeout": 30,
				"pool_recycle": 3600,
				"pool_pre_ping": True,
				"connect_args": {
					"connect_timeout": 10,
					"application_name": "career_copilot",
					"options": "-c default_transaction_isolation=read_committed",
				},
			}
		)
	else:
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

	if database_url.startswith(("postgresql", "postgres")):

		@event.listens_for(engine, "connect")
		def set_postgresql_settings(dbapi_connection, connection_record):
			with dbapi_connection.cursor() as cursor:
				cursor.execute("SET statement_timeout = '30s'")
				cursor.execute("SET lock_timeout = '10s'")
				cursor.execute("SET idle_in_transaction_session_timeout = '5min'")
				logger.debug("PostgreSQL performance settings applied")

	@event.listens_for(engine, "before_cursor_execute")
	def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
		context._query_start_time = time.time()

	@event.listens_for(engine, "after_cursor_execute")
	def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
		total = time.time() - context._query_start_time
		if total > 1.0:
			logger.warning("Slow query detected: %.2fs - %s...", total, statement[:100])

	logger.info("✅ Optimized database engine created for %s", database_url.split("://")[0])
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
	"""Check database connection health."""
	try:
		with engine.connect() as conn:
			start_time = time.time()
			conn.execute(text("SELECT 1"))
			response_time = (time.time() - start_time) * 1000

		pool = engine.pool
		pool_stats = {
			"size": getattr(pool, "size", lambda: "unknown")(),
			"checked_in": getattr(pool, "checkedin", lambda: "unknown")(),
			"checked_out": getattr(pool, "checkedout", lambda: "unknown")(),
			"overflow": getattr(pool, "overflow", lambda: "unknown")(),
			"invalid": getattr(pool, "invalid", lambda: "unknown")(),
		}

		return {
			"status": "healthy",
			"response_time_ms": round(response_time, 2),
			"database_type": str(engine.url).split("://")[0],
			"pool_stats": pool_stats,
		}
	except Exception as e:
		logger.error("Database health check failed: %s", e)
		db_type = str(engine.url).split("://")[0] if engine else "unknown"
		return {"status": "unhealthy", "error": str(e), "database_type": db_type}


# Database maintenance utilities
def optimize_database_maintenance(engine):
	"""Perform database maintenance operations."""
	try:
		with engine.connect() as conn:
			db_type = str(engine.url).split("://")[0]
			if db_type.startswith("postgres"):
				conn.execute(text("ANALYZE"))
				logger.info("PostgreSQL statistics updated")
		return {"status": "success", "message": "Database maintenance completed"}
	except Exception as e:
		logger.error("Database maintenance failed: %s", e)
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
