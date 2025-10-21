"""
Database performance monitoring and optimization API endpoints.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db_session
from ...core.database_performance import get_db_performance_optimizer, DatabasePerformanceOptimizer
from ...core.auth import get_current_user
from ...models.database_models import User
from ...models.api_models import BaseResponse

router = APIRouter(prefix="/database-performance", tags=["Database Performance"])


@router.get("/metrics", response_model=BaseResponse)
async def get_performance_metrics(
    hours: int = Query(default=1, ge=1, le=168, description="Hours of metrics to retrieve"),
    current_user: User = Depends(get_current_user),
    db_optimizer: DatabasePerformanceOptimizer = Depends(get_db_performance_optimizer)
):
    """
    Get database performance metrics for the specified time period.
    
    Args:
        hours: Number of hours of metrics to retrieve (1-168)
        current_user: Current authenticated user
        db_optimizer: Database performance optimizer instance
        
    Returns:
        Performance metrics including query statistics and connection pool info
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        metrics = await db_optimizer.get_performance_metrics(hours=hours)
        
        return BaseResponse(
            success=True,
            message=f"Performance metrics retrieved for last {hours} hours",
            data=metrics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/slow-queries", response_model=BaseResponse)
async def get_slow_query_analysis(
    hours: int = Query(default=24, ge=1, le=168, description="Hours to analyze"),
    min_occurrences: int = Query(default=2, ge=1, description="Minimum query occurrences"),
    current_user: User = Depends(get_current_user),
    db_optimizer: DatabasePerformanceOptimizer = Depends(get_db_performance_optimizer)
):
    """
    Analyze slow queries and provide optimization suggestions.
    
    Args:
        hours: Number of hours to analyze
        min_occurrences: Minimum number of query occurrences to include
        current_user: Current authenticated user
        db_optimizer: Database performance optimizer instance
        
    Returns:
        Slow query analysis with optimization suggestions
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        analysis = await db_optimizer.analyze_slow_queries(
            hours=hours, 
            min_occurrences=min_occurrences
        )
        
        # Convert to serializable format
        analysis_data = []
        for query_analysis in analysis:
            analysis_data.append({
                "query_pattern": query_analysis.query_pattern,
                "avg_execution_time": float(query_analysis.avg_execution_time),
                "max_execution_time": float(query_analysis.max_execution_time),
                "min_execution_time": float(query_analysis.min_execution_time),
                "execution_count": query_analysis.execution_count,
                "total_time": float(query_analysis.total_time),
                "suggestions": query_analysis.suggestions,
                "affected_tables": query_analysis.affected_tables
            })
        
        return BaseResponse(
            success=True,
            message=f"Analyzed {len(analysis_data)} slow query patterns",
            data={
                "analysis_period_hours": hours,
                "min_occurrences": min_occurrences,
                "slow_queries": analysis_data
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze slow queries: {str(e)}")


@router.post("/optimize-query", response_model=BaseResponse)
async def optimize_query(
    query: str,
    current_user: User = Depends(get_current_user),
    db_optimizer: DatabasePerformanceOptimizer = Depends(get_db_performance_optimizer)
):
    """
    Analyze a specific query and provide optimization suggestions.
    
    Args:
        query: SQL query to analyze
        current_user: Current authenticated user
        db_optimizer: Database performance optimizer instance
        
    Returns:
        Query optimization analysis and suggestions
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not query or len(query.strip()) < 10:
        raise HTTPException(status_code=400, detail="Valid SQL query required")
    
    try:
        optimization = await db_optimizer.optimize_query(query)
        
        return BaseResponse(
            success=True,
            message="Query optimization analysis completed",
            data=optimization
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to optimize query: {str(e)}")


@router.get("/index-recommendations", response_model=BaseResponse)
async def get_index_recommendations(
    current_user: User = Depends(get_current_user),
    db_optimizer: DatabasePerformanceOptimizer = Depends(get_db_performance_optimizer)
):
    """
    Get recommended database indexes based on query analysis.
    
    Args:
        current_user: Current authenticated user
        db_optimizer: Database performance optimizer instance
        
    Returns:
        List of recommended index creation statements
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        recommendations = await db_optimizer.create_recommended_indexes()
        
        return BaseResponse(
            success=True,
            message=f"Generated {len(recommendations)} index recommendations",
            data={
                "recommendations": recommendations,
                "note": "Review these recommendations before applying to production"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.get("/health", response_model=BaseResponse)
async def get_database_health(
    current_user: User = Depends(get_current_user),
    db_optimizer: DatabasePerformanceOptimizer = Depends(get_db_performance_optimizer)
):
    """
    Get database health status including connection pools and replicas.
    
    Args:
        current_user: Current authenticated user
        db_optimizer: Database performance optimizer instance
        
    Returns:
        Database health status
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        health_status = await db_optimizer.health_check()
        
        return BaseResponse(
            success=True,
            message="Database health check completed",
            data=health_status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/analyze-table/{table_name}", response_model=BaseResponse)
async def analyze_table_performance(
    table_name: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Analyze performance statistics for a specific table.
    
    Args:
        table_name: Name of the table to analyze
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Table performance analysis
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate table name to prevent SQL injection
    allowed_tables = [
        'users', 'contract_analyses', 'audit_logs', 'api_keys', 
        'user_settings', 'user_notification_preferences', 
        'docusign_envelopes', 'email_delivery_statuses'
    ]
    
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail="Invalid table name")
    
    try:
        from sqlalchemy import text
        
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
            column_stats.append({
                "column_name": row.attname,
                "n_distinct": row.n_distinct,
                "correlation": float(row.correlation) if row.correlation else None,
                "has_common_values": bool(row.most_common_vals)
            })
        
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
            indexes.append({
                "name": row.indexname,
                "definition": row.indexdef,
                "size": row.index_size
            })
        
        return BaseResponse(
            success=True,
            message=f"Table analysis completed for {table_name}",
            data={
                "table_name": table_name,
                "size_info": {
                    "total_size": size_info.total_size if size_info else "unknown",
                    "table_size": size_info.table_size if size_info else "unknown",
                    "index_size": size_info.index_size if size_info else "unknown",
                    "estimated_rows": size_info.estimated_rows if size_info else 0
                },
                "column_statistics": column_stats,
                "indexes": indexes
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Table analysis failed: {str(e)}")


@router.post("/vacuum/{table_name}", response_model=BaseResponse)
async def vacuum_table(
    table_name: str,
    analyze: bool = Query(default=True, description="Run ANALYZE after VACUUM"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
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
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate table name
    allowed_tables = [
        'users', 'contract_analyses', 'audit_logs', 'api_keys', 
        'user_settings', 'user_notification_preferences', 
        'docusign_envelopes', 'email_delivery_statuses'
    ]
    
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail="Invalid table name")
    
    try:
        from sqlalchemy import text
        
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
                "completed_at": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VACUUM operation failed: {str(e)}")


@router.get("/connection-pools", response_model=BaseResponse)
async def get_connection_pool_status(
    current_user: User = Depends(get_current_user),
    db_optimizer: DatabasePerformanceOptimizer = Depends(get_db_performance_optimizer)
):
    """
    Get detailed connection pool status for all database engines.
    
    Args:
        current_user: Current authenticated user
        db_optimizer: Database performance optimizer instance
        
    Returns:
        Connection pool status for write and read engines
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        pool_status = {}
        
        # Write engine pool status
        if db_optimizer.write_engine:
            pool = db_optimizer.write_engine.pool
            pool_status["write_engine"] = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "total_connections": pool.size() + pool.overflow(),
                "utilization_percent": (pool.checkedout() / (pool.size() + pool.overflow())) * 100 if (pool.size() + pool.overflow()) > 0 else 0
            }
        
        # Read replica pool status
        for name, engine in db_optimizer.read_engines.items():
            pool = engine.pool
            pool_status[name] = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "total_connections": pool.size() + pool.overflow(),
                "utilization_percent": (pool.checkedout() / (pool.size() + pool.overflow())) * 100 if (pool.size() + pool.overflow()) > 0 else 0
            }
        
        return BaseResponse(
            success=True,
            message="Connection pool status retrieved",
            data={
                "pools": pool_status,
                "read_replicas_enabled": db_optimizer.read_replica_enabled,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pool status: {str(e)}")