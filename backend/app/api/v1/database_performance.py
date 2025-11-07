"""
from ...core.database_optimization import get_optimization_service
db_optimizer = get_optimization_service()

Consolidated Database Performance and Optimization API Endpoints
Comprehensive database performance monitoring, optimization, and management.

This module consolidates functionality from:
- database_performance.py (database performance monitoring and optimization)
- database_optimization.py (database optimization management)
"""

from datetime import datetime, timezone
from typing import Dict, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...core.logging import get_logger

logger = get_logger(__name__)
# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(prefix="/database-performance", tags=["Database Performance"])


# Response Models
class BaseResponse(BaseModel):
	"""Base response model."""

	success: bool
	message: str
	data: Optional[Dict[str, Any]] = None


class OptimizationResponse(BaseModel):
	"""Response model for optimization operations."""

	status: str
	message: str
	results: Dict[str, Any]


class DatabaseStatsResponse(BaseModel):
	"""Response model for database statistics."""

	status: str
	stats: Dict[str, Any]
	collected_at: str


# Performance Monitoring Endpoints


@router.get("/metrics", response_model=BaseResponse)
async def get_performance_metrics(
	hours: int = Query(default=1, ge=1, le=168, description="Hours of metrics to retrieve"), current_user=Depends(get_current_user)
):
	"""
	Get database performance metrics for the specified time period.

	Args:
	    hours: Number of hours of metrics to retrieve (1-168)
	    current_user: Current authenticated user

	Returns:
	    Performance metrics including query statistics and connection pool info
	"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		# Try to use database optimization service if available
		try:
			from ...core.database_optimization import get_optimization_service

			optimization_service = get_optimization_service()
			metrics = optimization_service.optimize_performance()
		except ImportError:
			# Fallback to basic metrics
			metrics = {
				"period_hours": hours,
				"query_count": 0,
				"average_response_time": 0.0,
				"connection_pool": {"active_connections": 0, "idle_connections": 0},
				"note": "Database performance optimizer not available - showing placeholder data",
			}

		return BaseResponse(success=True, message=f"Performance metrics retrieved for last {hours} hours", data=metrics)

	except Exception as e:
		logger.error(f"Failed to retrieve metrics: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {e!s}")


@router.get("/slow-queries", response_model=BaseResponse)
async def get_slow_query_analysis(
	hours: int = Query(default=24, ge=1, le=168, description="Hours to analyze"),
	min_occurrences: int = Query(default=2, ge=1, description="Minimum query occurrences"),
	current_user=Depends(get_current_user),
):
	"""
	Analyze slow queries and provide optimization suggestions.

	Args:
	    hours: Number of hours to analyze
	    min_occurrences: Minimum number of query occurrences to include
	    current_user: Current authenticated user

	Returns:
	    Slow query analysis with optimization suggestions
	"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		# Try to use database optimization service if available
		try:
			from ...core.database_optimization import get_optimization_service

			optimization_service = get_optimization_service()
			analysis = optimization_service.optimize_performance()

			# Convert to serializable format
			analysis_data = []
			for query_analysis in analysis:
				analysis_data.append(
					{
						"query_pattern": query_analysis.query_pattern,
						"avg_execution_time": float(query_analysis.avg_execution_time),
						"max_execution_time": float(query_analysis.max_execution_time),
						"min_execution_time": float(query_analysis.min_execution_time),
						"execution_count": query_analysis.execution_count,
						"total_time": float(query_analysis.total_time),
						"suggestions": query_analysis.suggestions,
						"affected_tables": query_analysis.affected_tables,
					}
				)
		except ImportError:
			# Fallback analysis
			analysis_data = []
			logger.info("Database performance optimizer not available - no slow query analysis")

		return BaseResponse(
			success=True,
			message=f"Analyzed {len(analysis_data)} slow query patterns",
			data={"analysis_period_hours": hours, "min_occurrences": min_occurrences, "slow_queries": analysis_data},
		)

	except Exception as e:
		logger.error(f"Failed to analyze slow queries: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to analyze slow queries: {e!s}")


@router.post("/optimize-query", response_model=BaseResponse)
async def optimize_query(query: str, current_user=Depends(get_current_user)):
	"""
	Analyze a specific query and provide optimization suggestions.

	Args:
	    query: SQL query to analyze
	    current_user: Current authenticated user

	Returns:
	    Query optimization analysis and suggestions
	"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	if not query or len(query.strip()) < 10:
		raise HTTPException(status_code=400, detail="Valid SQL query required")

	try:
		# Try to use database optimization service if available
		try:
			from ...core.database_optimization import get_optimization_service

			optimization_service = get_optimization_service()
			optimization = optimization_service.optimize_performance()
		except ImportError:
			# Basic query analysis fallback
			optimization = {
				"original_query": query,
				"suggestions": ["Consider adding appropriate indexes", "Review WHERE clause conditions", "Check for unnecessary JOINs"],
				"estimated_improvement": "Unknown - optimizer not available",
			}

		return BaseResponse(success=True, message="Query optimization analysis completed", data=optimization)

	except Exception as e:
		logger.error(f"Failed to optimize query: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to optimize query: {e!s}")


# Database Optimization Endpoints (consolidated from database_optimization.py)


@router.post("/optimize/indexes", response_model=OptimizationResponse)
async def create_performance_indexes(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Create performance indexes for enhanced features (admin only)"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		# Try to use database optimization service if available
		try:
			from ...services.database_optimization_service import db_optimization_service

			results = db_optimization_service.create_performance_indexes(db)

			return OptimizationResponse(
				status="success", message=f"Index optimization completed. Created {len(results['indexes_created'])} indexes.", results=results
			)
		except ImportError:
			# Fallback index creation
			results = {"indexes_created": [], "note": "Database optimization service not available"}

			return OptimizationResponse(status="success", message="Index optimization service not available", results=results)

	except Exception as e:
		logger.error(f"Error creating performance indexes: {e}")
		raise HTTPException(status_code=500, detail="Error creating performance indexes")


@router.post("/optimize/queries", response_model=OptimizationResponse)
async def optimize_queries(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Optimize database queries (admin only)"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		# Try to use database optimization service if available
		try:
			from ...services.database_optimization_service import db_optimization_service

			results = db_optimization_service.optimize_queries(db)

			return OptimizationResponse(status=results["status"], message="Query optimization completed", results=results)
		except ImportError:
			# Fallback query optimization
			results = {"status": "success", "optimizations_applied": 0, "note": "Database optimization service not available"}

			return OptimizationResponse(status="success", message="Query optimization service not available", results=results)

	except Exception as e:
		logger.error(f"Error optimizing queries: {e}")
		raise HTTPException(status_code=500, detail="Error optimizing queries")


@router.get("/analyze/performance", response_model=OptimizationResponse)
async def analyze_query_performance(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Analyze query performance (admin only)"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		# Try to use database optimization service if available
		try:
			from ...services.database_optimization_service import db_optimization_service

			results = db_optimization_service.analyze_query_performance(db)

			return OptimizationResponse(status=results["status"], message="Query performance analysis completed", results=results)
		except ImportError:
			# Fallback performance analysis
			results = {"status": "success", "analysis": "Performance analysis service not available", "recommendations": []}

			return OptimizationResponse(status="success", message="Performance analysis service not available", results=results)

	except Exception as e:
		logger.error(f"Error analyzing query performance: {e}")
		raise HTTPException(status_code=500, detail="Error analyzing query performance")


@router.get("/connection-pooling", response_model=OptimizationResponse)
async def analyze_connection_pooling(current_user=Depends(get_current_user)):
	"""Analyze connection pooling configuration (admin only)"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		# Try to use database optimization service if available
		try:
			from ...services.database_optimization_service import db_optimization_service

			results = db_optimization_service.implement_connection_pooling()

			return OptimizationResponse(status=results["status"], message="Connection pooling analysis completed", results=results)
		except ImportError:
			# Fallback connection pooling analysis
			results = {"status": "success", "current_pool_size": "unknown", "recommendations": ["Connection pooling service not available"]}

			return OptimizationResponse(status="success", message="Connection pooling service not available", results=results)

	except Exception as e:
		logger.error(f"Error analyzing connection pooling: {e}")
		raise HTTPException(status_code=500, detail="Error analyzing connection pooling")


@router.post("/cleanup")
async def cleanup_old_data(days_old: int = 90, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Clean up old data to improve performance (admin only)"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	if days_old < 30:
		raise HTTPException(status_code=400, detail="Cannot delete data newer than 30 days")

	try:
		# Try to use database optimization service if available
		try:
			from ...services.database_optimization_service import db_optimization_service

			results = db_optimization_service.cleanup_old_data(db, days_old)

			return OptimizationResponse(
				status=results["status"], message=f"Data cleanup completed. Deleted {results.get('total_deleted', 0)} records.", results=results
			)
		except ImportError:
			# Fallback cleanup
			results = {"status": "success", "total_deleted": 0, "note": "Database optimization service not available - no cleanup performed"}

			return OptimizationResponse(status="success", message="Data cleanup service not available", results=results)

	except Exception as e:
		logger.error(f"Error cleaning up old data: {e}")
		raise HTTPException(status_code=500, detail="Error cleaning up old data")


@router.get("/stats", response_model=DatabaseStatsResponse)
async def get_database_stats(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get database statistics and health metrics (admin only)"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		# Try to use database optimization service if available
		try:
			from ...services.database_optimization_service import db_optimization_service

			results = db_optimization_service.get_database_stats(db)

			return DatabaseStatsResponse(status=results["status"], stats=results.get("stats", {}), collected_at=results.get("collected_at", ""))
		except ImportError:
			# Fallback database stats
			stats = {"tables": "unknown", "total_size": "unknown", "note": "Database optimization service not available"}

			return DatabaseStatsResponse(status="success", stats=stats, collected_at=datetime.now(timezone.utc).isoformat())

	except Exception as e:
		logger.error(f"Error getting database stats: {e}")
		raise HTTPException(status_code=500, detail="Error retrieving database statistics")


@router.post("/optimize/all", response_model=OptimizationResponse)
async def optimize_all(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Run all database optimizations (admin only)"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		all_results = {}

		# Try to use database optimization service if available
		try:
			from ...services.database_optimization_service import db_optimization_service

			# Create indexes
			logger.info("Creating performance indexes...")
			index_results = db_optimization_service.create_performance_indexes(db)
			all_results["indexes"] = index_results

			# Optimize queries
			logger.info("Optimizing queries...")
			query_results = db_optimization_service.optimize_queries(db)
			all_results["queries"] = query_results

			# Analyze performance
			logger.info("Analyzing performance...")
			perf_results = db_optimization_service.analyze_query_performance(db)
			all_results["performance"] = perf_results

			# Get connection pooling info
			logger.info("Analyzing connection pooling...")
			pool_results = db_optimization_service.implement_connection_pooling()
			all_results["connection_pooling"] = pool_results

			total_indexes_created = len(index_results.get("indexes_created", []))

			return OptimizationResponse(
				status="success", message=f"Complete database optimization finished. Created {total_indexes_created} indexes.", results=all_results
			)
		except ImportError:
			# Fallback optimization
			all_results = {
				"indexes": {"status": "service_not_available"},
				"queries": {"status": "service_not_available"},
				"performance": {"status": "service_not_available"},
				"connection_pooling": {"status": "service_not_available"},
			}

			return OptimizationResponse(status="success", message="Database optimization services not available", results=all_results)

	except Exception as e:
		logger.error(f"Error running complete optimization: {e}")
		raise HTTPException(status_code=500, detail="Error running complete database optimization")


# Additional Performance Monitoring Endpoints


@router.get("/index-recommendations", response_model=BaseResponse)
async def get_index_recommendations(current_user=Depends(get_current_user)):
	"""
	Get recommended database indexes based on query analysis.

	Args:
	    current_user: Current authenticated user

	Returns:
	    List of recommended index creation statements
	"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		# Try to use database optimization service if available
		try:
			from ...core.database_optimization import get_optimization_service

			optimization_service = get_optimization_service()
			recommendations = optimization_service.optimize_performance()
		except ImportError:
			# Fallback recommendations
			recommendations = [
				"CREATE INDEX idx_users_email ON users(email);",
				"CREATE INDEX idx_jobs_created_at ON jobs(created_at);",
				"-- Database performance optimizer not available",
			]

		return BaseResponse(
			success=True,
			message=f"Generated {len(recommendations)} index recommendations",
			data={"recommendations": recommendations, "note": "Review these recommendations before applying to production"},
		)

	except Exception as e:
		logger.error(f"Failed to generate recommendations: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {e!s}")


@router.get("/health", response_model=BaseResponse)
async def get_database_health(current_user=Depends(get_current_user)):
	"""
	Get database health status including connection pools and replicas.

	Args:
	    current_user: Current authenticated user

	Returns:
	    Database health status
	"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		# Try to use database optimization service if available
		try:
			from ...core.database_optimization import get_optimization_service

			optimization_service = get_optimization_service()
			health_status = optimization_service.optimize_performance()
		except ImportError:
			# Fallback health check
			health_status = {"database": "connected", "connection_pool": "unknown", "note": "Database performance optimizer not available"}

		return BaseResponse(success=True, message="Database health check completed", data=health_status)

	except Exception as e:
		logger.error(f"Health check failed: {e}")
		raise HTTPException(status_code=500, detail=f"Health check failed: {e!s}")


@router.post("/analyze-table/{table_name}", response_model=BaseResponse)
async def analyze_table_performance(table_name: str, current_user=Depends(get_current_user), session: AsyncSession = Depends(get_db)):
	"""
	Analyze performance statistics for a specific table.

	Args:
	    table_name: Name of the table to analyze
	    current_user: Current authenticated user
	    session: Database session

	Returns:
	    Table performance analysis
	"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	# Validate table name to prevent SQL injection
	allowed_tables = [
		"users",
		"contract_analyses",
		"audit_logs",
		"api_keys",
		"user_settings",
		"user_notification_preferences",
		"docusign_envelopes",
		"email_delivery_statuses",
	]

	if table_name not in allowed_tables:
		raise HTTPException(status_code=400, detail="Invalid table name")

	try:
		# Get table statistics
		stats_query = text("""
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation,
                most_common_vals,
                most_common_freqs
            FROM pg_stats 
            WHERE tablename = :table_name
            ORDER BY attname
        """)

		result = await session.execute(stats_query, {"table_name": table_name})
		column_stats = []

		for row in result:
			column_stats.append(
				{
					"column_name": row.attname,
					"n_distinct": row.n_distinct,
					"correlation": float(row.correlation) if row.correlation else None,
					"has_common_values": bool(row.most_common_vals),
				}
			)

		# Get table size information
		size_query = text("""
            SELECT 
                pg_size_pretty(pg_total_relation_size(:table_name)) as total_size,
                pg_size_pretty(pg_relation_size(:table_name)) as table_size,
                pg_size_pretty(pg_total_relation_size(:table_name) - pg_relation_size(:table_name)) as index_size,
                (SELECT reltuples::bigint FROM pg_class WHERE relname = :table_name) as estimated_rows
        """)

		size_result = await session.execute(size_query, {"table_name": table_name})
		size_info = size_result.fetchone()

		# Get index information
		index_query = text("""
            SELECT 
                indexname,
                indexdef,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
            FROM pg_indexes 
            WHERE tablename = :table_name
            ORDER BY indexname
        """)

		index_result = await session.execute(index_query, {"table_name": table_name})
		indexes = []

		for row in index_result:
			indexes.append({"name": row.indexname, "definition": row.indexdef, "size": row.index_size})

		return BaseResponse(
			success=True,
			message=f"Table analysis completed for {table_name}",
			data={
				"table_name": table_name,
				"size_info": {
					"total_size": size_info.total_size if size_info else "unknown",
					"table_size": size_info.table_size if size_info else "unknown",
					"index_size": size_info.index_size if size_info else "unknown",
					"estimated_rows": size_info.estimated_rows if size_info else 0,
				},
				"column_statistics": column_stats,
				"indexes": indexes,
			},
		)

	except Exception as e:
		logger.error(f"Table analysis failed: {e}")
		raise HTTPException(status_code=500, detail=f"Table analysis failed: {e!s}")


@router.post("/vacuum/{table_name}", response_model=BaseResponse)
async def vacuum_table(
	table_name: str,
	analyze: bool = Query(default=True, description="Run ANALYZE after VACUUM"),
	current_user=Depends(get_current_user),
	session: AsyncSession = Depends(get_db),
):
	"""
	Perform VACUUM operation on a specific table to reclaim space and update statistics.

	Args:
	    table_name: Name of the table to vacuum
	    analyze: Whether to run ANALYZE after VACUUM
	    current_user: Current authenticated user
	    session: Database session

	Returns:
	    Vacuum operation result
	"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	# Validate table name
	allowed_tables = [
		"users",
		"contract_analyses",
		"audit_logs",
		"api_keys",
		"user_settings",
		"user_notification_preferences",
		"docusign_envelopes",
		"email_delivery_statuses",
	]

	if table_name not in allowed_tables:
		raise HTTPException(status_code=400, detail="Invalid table name")

	try:
		# VACUUM cannot be run inside a transaction, so we need to commit first
		await session.commit()

		# Run VACUUM
		vacuum_command = f"VACUUM {'ANALYZE' if analyze else ''} {table_name}"
		await session.execute(text(vacuum_command))

		return BaseResponse(
			success=True,
			message=f"VACUUM {'ANALYZE' if analyze else ''} completed for {table_name}",
			data={
				"table_name": table_name,
				"operation": "VACUUM ANALYZE" if analyze else "VACUUM",
				"completed_at": datetime.now(timezone.utc).isoformat(),
			},
		)

	except Exception as e:
		logger.error(f"VACUUM operation failed: {e}")
		raise HTTPException(status_code=500, detail=f"VACUUM operation failed: {e!s}")


@router.get("/connection-pools", response_model=BaseResponse)
async def get_connection_pool_status(current_user=Depends(get_current_user)):
	"""
	Get detailed connection pool status for all database engines.

	Args:
	    current_user: Current authenticated user

	Returns:
	    Connection pool status for write and read engines
	"""
	# Check admin access
	if not getattr(current_user, "is_superuser", False) and not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		pool_status = {}

		# Try to get database optimization service if available
		try:
			from ...core.database_optimization import get_optimization_service

			optimization_service = get_optimization_service()

			# Write engine pool status
			if optimization_service.write_engine:
				pool = optimization_service.write_engine.pool
				pool_status["write_engine"] = {
					"size": pool.size(),
					"checked_in": pool.checkedin(),
					"checked_out": pool.checkedout(),
					"overflow": pool.overflow(),
					"invalid": pool.invalid(),
					"total_connections": pool.size() + pool.overflow(),
					"utilization_percent": (pool.checkedout() / (pool.size() + pool.overflow())) * 100 if (pool.size() + pool.overflow()) > 0 else 0,
				}

			# Read replica pool status
			for name, engine in optimization_service.read_engines.items():
				pool = engine.pool
				pool_status[name] = {
					"size": pool.size(),
					"checked_in": pool.checkedin(),
					"checked_out": pool.checkedout(),
					"overflow": pool.overflow(),
					"invalid": pool.invalid(),
					"total_connections": pool.size() + pool.overflow(),
					"utilization_percent": (pool.checkedout() / (pool.size() + pool.overflow())) * 100 if (pool.size() + pool.overflow()) > 0 else 0,
				}
		except ImportError:
			pool_status = {"note": "Database performance optimizer not available", "status": "unknown"}

		return BaseResponse(
			success=True, message="Connection pool status retrieved", data={"pools": pool_status, "timestamp": datetime.now(timezone.utc).isoformat()}
		)

	except Exception as e:
		logger.error(f"Failed to get pool status: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get pool status: {e!s}")
