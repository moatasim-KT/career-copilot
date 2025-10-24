"""
Database health monitoring implementation.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, Optional

import chromadb
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import get_settings
from ...core.database import engine, get_db
from ...core.logging import get_logger
from ...services.chroma_service import get_chroma_client
from .base import BaseHealthChecker, HealthCheckResult, HealthStatus

logger = get_logger(__name__)
settings = get_settings()


class DatabaseHealthMonitor(BaseHealthChecker):
    """Database health monitoring implementation."""

    def __init__(self) -> None:
        super().__init__()

    def __init__(self):
        """Initialize database health monitor."""
        self.performance_thresholds = {
            "query_time_warning_ms": 100,
            "query_time_critical_ms": 500,
            "connection_warning_ms": 50,
            "connection_critical_ms": 200,
            "pool_usage_warning": 0.7,
            "pool_usage_critical": 0.9,
        }

    async def check_health(self) -> HealthCheckResult:
        """Perform comprehensive database health check."""
        start_time = time.time()

        try:
            # Check PostgreSQL health
            pg_health = await self._check_postgresql()
            if not pg_health["healthy"]:
                return self._create_unhealthy_result(
                    message="PostgreSQL health check failed",
                    response_time_ms=(time.time() - start_time) * 1000,
                    error=pg_health.get("error"),
                )

            # Check ChromaDB health
            chroma_health = await self._check_chromadb()
            if not chroma_health["healthy"]:
                return self._create_unhealthy_result(
                    message="ChromaDB health check failed",
                    response_time_ms=(time.time() - start_time) * 1000,
                    error=chroma_health.get("error"),
                )

            # Check overall database performance
            performance = await self._check_performance()
            status = HealthStatus.HEALTHY
            if performance.get("warnings"):
                status = HealthStatus.DEGRADED
            if performance.get("critical"):
                status = HealthStatus.UNHEALTHY

            return HealthCheckResult(
                status=status,
                message="Database health check completed",
                timestamp=datetime.utcnow(),
                response_time_ms=(time.time() - start_time) * 1000,
                details={
                    "postgresql": pg_health,
                    "chromadb": chroma_health,
                    "performance": performance,
                },
            )

        except Exception as e:
            logger.error(f"Database health check failed: {e!s}")
            return self._create_unhealthy_result(
                message="Database health check failed",
                response_time_ms=(time.time() - start_time) * 1000,
                error=f"{e!s}",
            )

    async def _check_postgresql(self) -> Dict[str, Any]:
        """Check PostgreSQL connectivity and status."""
        try:
            # Test basic connectivity
            conn_start = time.time()
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                conn_time = (time.time() - conn_start) * 1000

            # Check connection pool
            pool_info = engine.pool.status()
            total_connections = pool_info.max_size
            used_connections = pool_info.size
            pool_usage = (
                used_connections / total_connections if total_connections > 0 else 0
            )

            # Evaluate status
            status = "healthy"
            warnings = []

            if conn_time > self.performance_thresholds["connection_critical_ms"]:
                status = "unhealthy"
                warnings.append(f"Critical connection time: {conn_time:.1f}ms")
            elif conn_time > self.performance_thresholds["connection_warning_ms"]:
                status = "degraded"
                warnings.append(f"Slow connection time: {conn_time:.1f}ms")

            if pool_usage > self.performance_thresholds["pool_usage_critical"]:
                status = "unhealthy"
                warnings.append(f"Critical pool usage: {pool_usage*100:.1f}%")
            elif pool_usage > self.performance_thresholds["pool_usage_warning"]:
                if status == "healthy":
                    status = "degraded"
                warnings.append(f"High pool usage: {pool_usage*100:.1f}%")

            return {
                "healthy": status != "unhealthy",
                "status": status,
                "connection_time_ms": conn_time,
                "pool_usage": pool_usage,
                "total_connections": total_connections,
                "used_connections": used_connections,
                "warnings": warnings if warnings else None,
            }

        except Exception as e:
            return {"healthy": False, "error": f"PostgreSQL check failed: {e!s}"}

    async def _check_chromadb(self) -> Dict[str, Any]:
        """Check ChromaDB accessibility."""
        try:
            client = await get_chroma_client()
            collections = client.list_collections()

            # Check basic operations
            test_collection = client.create_collection(
                name=f"health_check_{int(time.time())}"
            )

            # Add and query a test document
            test_doc = {"test": "health_check"}
            test_collection.add(
                embeddings=[[0.1] * 128],  # Simple test embedding
                documents=[str(test_doc)],
                ids=["health_check"],
            )

            query_start = time.time()
            results = test_collection.query(query_embeddings=[[0.1] * 128], n_results=1)
            query_time = (time.time() - query_start) * 1000

            # Cleanup
            client.delete_collection(f"health_check_{int(time.time())}")

            status = "healthy"
            warnings = []

            # Check query performance
            if query_time > self.performance_thresholds["query_time_critical_ms"]:
                status = "unhealthy"
                warnings.append(f"Critical query time: {query_time:.1f}ms")
            elif query_time > self.performance_thresholds["query_time_warning_ms"]:
                status = "degraded"
                warnings.append(f"Slow query time: {query_time:.1f}ms")

            return {
                "healthy": status != "unhealthy",
                "status": status,
                "query_time_ms": query_time,
                "collections_count": len(collections),
                "warnings": warnings if warnings else None,
            }

        except Exception as e:
            return {"healthy": False, "error": f"ChromaDB check failed: {e!s}"}

    async def _check_performance(self) -> Dict[str, Any]:
        """Check database response time monitoring."""
        try:
            performance_metrics = {"queries": [], "warnings": [], "critical": []}

            async with engine.connect() as conn:
                # Test queries
                test_queries = [
                    ("Simple SELECT", "SELECT 1"),
                    ("Table scan", "SELECT count(*) FROM information_schema.tables"),
                    (
                        "Complex join",
                        """
                        SELECT t1.table_name, t2.column_name 
                        FROM information_schema.tables t1 
                        JOIN information_schema.columns t2 
                        ON t1.table_name = t2.table_name 
                        LIMIT 10
                    """,
                    ),
                ]

                for query_name, query in test_queries:
                    start_time = time.time()
                    await conn.execute(text(query))
                    query_time = (time.time() - start_time) * 1000

                    metrics = {"query": query_name, "execution_time_ms": query_time}

                    if (
                        query_time
                        > self.performance_thresholds["query_time_critical_ms"]
                    ):
                        performance_metrics["critical"].append(
                            f"{query_name}: {query_time:.1f}ms"
                        )
                    elif (
                        query_time
                        > self.performance_thresholds["query_time_warning_ms"]
                    ):
                        performance_metrics["warnings"].append(
                            f"{query_name}: {query_time:.1f}ms"
                        )

                    performance_metrics["queries"].append(metrics)

            return performance_metrics

        except Exception as e:
            return {
                "error": f"Performance check failed: {e!s}",
                "queries": [],
                "warnings": [],
                "critical": [f"Check failed: {e!s}"],
            }
