"""
Database health monitoring for E2E testing.

This module provides comprehensive database health checking functionality
for PostgreSQL and ChromaDB, including connectivity, performance monitoring,
and response time validation.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool

from .base import ServiceHealthTestBase
from .utils import TestDataGenerator


class DatabaseHealthChecker(ServiceHealthTestBase):
    """
    Database health checker for E2E testing.
    
    Checks PostgreSQL connectivity and performance, ChromaDB accessibility,
    and implements database response time monitoring.
    """
    
    def __init__(self, database_url: str = None, backend_url: str = "http://localhost:8000", 
                 performance_thresholds: Dict[str, float] = None):
        """
        Initialize database health checker.
        
        Args:
            database_url: Database connection URL (defaults to SQLite for testing)
            backend_url: Backend service URL for health endpoints
            performance_thresholds: Performance thresholds for monitoring
        """
        super().__init__()
        self.database_url = database_url or "sqlite:///./data/career_copilot.db"
        self.backend_url = backend_url.rstrip('/')
        
        # Default performance thresholds
        self.performance_thresholds = performance_thresholds or {
            "connection_time_warning_ms": 100,
            "connection_time_critical_ms": 500,
            "query_time_warning_ms": 200,
            "query_time_critical_ms": 1000,
            "pool_usage_warning": 70.0,  # percentage
            "pool_usage_critical": 90.0,  # percentage
        }
        
        self.engine = None
        
    async def setup(self):
        """Set up database health test environment."""
        await super().setup()
        self.logger.info(f"Database health checker initialized for {self.database_url}")
        
        # Create database engine for direct testing
        try:
            if "sqlite" in self.database_url:
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False}
                )
            else:
                self.engine = create_engine(self.database_url)
            self.logger.debug("Database engine created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create database engine: {e}")
            
    async def run_test(self) -> Dict[str, Any]:
        """
        Execute database health check test.
        
        Returns:
            Dictionary containing database health check results and status.
        """
        self.logger.info("Starting database health check")
        
        # Check PostgreSQL connectivity and performance
        postgres_health = await self._check_postgresql_health()
        self.add_health_result(
            "postgresql_connectivity", 
            postgres_health["healthy"], 
            postgres_health["response_time"],
            postgres_health.get("details", {})
        )
        
        # Check ChromaDB accessibility
        chromadb_health = await self._check_chromadb_health()
        self.add_health_result(
            "chromadb_accessibility",
            chromadb_health["healthy"],
            chromadb_health["response_time"], 
            chromadb_health.get("details", {})
        )
        
        # Check database response time monitoring
        response_time_health = await self._check_response_time_monitoring()
        self.add_health_result(
            "response_time_monitoring",
            response_time_health["healthy"],
            response_time_health["response_time"],
            response_time_health.get("details", {})
        )
        
        # Determine overall status
        unhealthy_services = self.get_unhealthy_services()
        overall_status = "passed" if not unhealthy_services else "failed"
        
        return {
            "test_name": "database_health_check",
            "status": overall_status,
            "message": f"Database health check completed. Unhealthy services: {len(unhealthy_services)}",
            "health_results": self.health_results,
            "unhealthy_services": unhealthy_services,
            "total_checks": len(self.health_results)
        }
    
    async def _check_postgresql_health(self) -> Dict[str, Any]:
        """
        Check PostgreSQL connectivity and performance.
        
        Returns:
            Dictionary with PostgreSQL health status, response time, and details.
        """
        start_time = time.time()
        
        try:
            # Test basic connectivity
            connection_start = time.time()
            
            if self.engine:
                # Direct database connection test
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1 as test_value"))
                    test_value = result.fetchone()[0]
                    
                    if test_value != 1:
                        raise Exception("Database query returned unexpected result")
                        
                connection_time = (time.time() - connection_start) * 1000
                
                # Test additional queries for performance monitoring
                performance_results = await self._test_database_performance()
                
                # Check connection pool status if available
                pool_info = self._get_pool_info()
                
                # Evaluate performance status
                status = "healthy"
                warnings = []
                
                if connection_time > self.performance_thresholds["connection_time_critical_ms"]:
                    status = "unhealthy"
                    warnings.append(f"Critical connection time: {connection_time:.1f}ms")
                elif connection_time > self.performance_thresholds["connection_time_warning_ms"]:
                    status = "degraded"
                    warnings.append(f"Slow connection time: {connection_time:.1f}ms")
                
                # Check query performance
                avg_query_time = performance_results.get("average_query_time_ms", 0)
                if avg_query_time > self.performance_thresholds["query_time_critical_ms"]:
                    status = "unhealthy"
                    warnings.append(f"Critical query performance: {avg_query_time:.1f}ms")
                elif avg_query_time > self.performance_thresholds["query_time_warning_ms"]:
                    if status == "healthy":
                        status = "degraded"
                    warnings.append(f"Slow query performance: {avg_query_time:.1f}ms")
                
                response_time = (time.time() - start_time) * 1000
                
                return {
                    "healthy": status != "unhealthy",
                    "response_time": response_time,
                    "details": {
                        "status": status,
                        "connection_time_ms": connection_time,
                        "database_type": "postgresql" if "postgresql" in self.database_url else "sqlite",
                        "performance": performance_results,
                        "pool_info": pool_info,
                        "warnings": warnings if warnings else None,
                        "database_url_type": self.database_url.split("://")[0] if "://" in self.database_url else "unknown"
                    }
                }
            else:
                # Fallback to backend health endpoint
                return await self._check_database_via_backend()
                
        except SQLAlchemyError as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"SQLAlchemy error: {str(e)}",
                    "error_type": "database_connection_error"
                }
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"Database connectivity check failed: {str(e)}",
                    "error_type": "general_error"
                }
            }
    
    async def _test_database_performance(self) -> Dict[str, Any]:
        """
        Test database performance with various queries.
        
        Returns:
            Dictionary with performance metrics.
        """
        if not self.engine:
            return {"error": "No database engine available"}
        
        try:
            performance_metrics = {
                "queries": [],
                "average_query_time_ms": 0,
                "total_queries": 0
            }
            
            # Test queries based on database type
            if "sqlite" in self.database_url:
                test_queries = [
                    ("Simple SELECT", "SELECT 1"),
                    ("Table info", "SELECT name FROM sqlite_master WHERE type='table' LIMIT 5"),
                    ("System info", "PRAGMA database_list"),
                ]
            else:
                # PostgreSQL queries
                test_queries = [
                    ("Simple SELECT", "SELECT 1"),
                    ("Table scan", "SELECT count(*) FROM information_schema.tables"),
                    ("System info", "SELECT version()"),
                ]
            
            total_time = 0
            
            with self.engine.connect() as conn:
                for query_name, query in test_queries:
                    query_start = time.time()
                    try:
                        result = conn.execute(text(query))
                        # Fetch results to ensure query completes
                        if result.returns_rows:
                            result.fetchall()
                        query_time = (time.time() - query_start) * 1000
                        
                        performance_metrics["queries"].append({
                            "name": query_name,
                            "execution_time_ms": query_time,
                            "status": "success"
                        })
                        
                        total_time += query_time
                        
                    except Exception as e:
                        query_time = (time.time() - query_start) * 1000
                        performance_metrics["queries"].append({
                            "name": query_name,
                            "execution_time_ms": query_time,
                            "status": "failed",
                            "error": str(e)
                        })
            
            performance_metrics["total_queries"] = len(test_queries)
            performance_metrics["average_query_time_ms"] = total_time / len(test_queries) if test_queries else 0
            
            return performance_metrics
            
        except Exception as e:
            return {
                "error": f"Performance test failed: {str(e)}",
                "queries": [],
                "average_query_time_ms": 0,
                "total_queries": 0
            }
    
    def _get_pool_info(self) -> Dict[str, Any]:
        """
        Get database connection pool information.
        
        Returns:
            Dictionary with pool statistics.
        """
        if not self.engine or not hasattr(self.engine, 'pool'):
            return {"available": False, "message": "No pool information available"}
        
        try:
            pool = self.engine.pool
            
            # Get pool statistics
            pool_info = {
                "available": True,
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }
            
            # Calculate utilization if max size is available
            if hasattr(pool, '_max_overflow') and hasattr(pool, '_pool_size'):
                max_connections = pool._pool_size + pool._max_overflow
                current_connections = pool.size()
                pool_info["max_connections"] = max_connections
                pool_info["utilization_percent"] = (current_connections / max_connections * 100) if max_connections > 0 else 0
            
            return pool_info
            
        except Exception as e:
            return {
                "available": False,
                "error": f"Failed to get pool info: {str(e)}"
            }
    
    async def _check_database_via_backend(self) -> Dict[str, Any]:
        """
        Check database health via backend health endpoint.
        
        Returns:
            Dictionary with database health status from backend.
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backend_url}/api/v1/health/db")
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    health_data = response.json()
                    db_status = health_data.get("status", "unknown")
                    
                    return {
                        "healthy": db_status == "healthy",
                        "response_time": response_time,
                        "details": {
                            "status_code": response.status_code,
                            "backend_response": health_data,
                            "method": "backend_endpoint"
                        }
                    }
                else:
                    return {
                        "healthy": False,
                        "response_time": response_time,
                        "details": {
                            "status_code": response.status_code,
                            "error": f"Backend health endpoint returned {response.status_code}",
                            "method": "backend_endpoint"
                        }
                    }
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"Backend database health check failed: {str(e)}",
                    "method": "backend_endpoint"
                }
            }
    
    async def _check_chromadb_health(self) -> Dict[str, Any]:
        """
        Check ChromaDB accessibility and performance.
        
        Returns:
            Dictionary with ChromaDB health status and details.
        """
        start_time = time.time()
        
        try:
            # Try to check ChromaDB via backend health endpoint first
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self.backend_url}/health/database")
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    health_data = response.json()
                    
                    # Extract ChromaDB specific information
                    chromadb_info = health_data.get("details", {}).get("chromadb", {})
                    
                    if chromadb_info:
                        chromadb_healthy = chromadb_info.get("healthy", False)
                        chromadb_status = chromadb_info.get("status", "unknown")
                        
                        return {
                            "healthy": chromadb_healthy,
                            "response_time": response_time,
                            "details": {
                                "status": chromadb_status,
                                "chromadb_info": chromadb_info,
                                "method": "backend_health_endpoint",
                                "backend_status_code": response.status_code
                            }
                        }
                    else:
                        # ChromaDB info not available in response, try alternative check
                        return await self._check_chromadb_alternative()
                else:
                    return {
                        "healthy": False,
                        "response_time": response_time,
                        "details": {
                            "error": f"Backend database health endpoint returned {response.status_code}",
                            "status_code": response.status_code,
                            "method": "backend_health_endpoint"
                        }
                    }
                    
        except httpx.TimeoutException:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": "ChromaDB health check timed out",
                    "method": "backend_health_endpoint"
                }
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"ChromaDB health check failed: {str(e)}",
                    "method": "backend_health_endpoint"
                }
            }
    
    async def _check_chromadb_alternative(self) -> Dict[str, Any]:
        """
        Alternative ChromaDB health check method.
        
        Returns:
            Dictionary with ChromaDB health status.
        """
        start_time = time.time()
        
        try:
            # Try to import and test ChromaDB directly
            import chromadb
            from chromadb.config import Settings
            import os
            
            # Use default ChromaDB path
            chroma_path = os.path.join(os.getcwd(), "data", "chroma")
            
            # Test ChromaDB connectivity
            client = chromadb.PersistentClient(
                path=chroma_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )
            
            # Test basic operations
            collections = client.list_collections()
            collection_count = len(collections)
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "healthy": True,
                "response_time": response_time,
                "details": {
                    "status": "healthy",
                    "collections_count": collection_count,
                    "chroma_path": chroma_path,
                    "method": "direct_connection"
                }
            }
            
        except ImportError:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": "ChromaDB not available - import failed",
                    "method": "direct_connection"
                }
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"ChromaDB direct connection failed: {str(e)}",
                    "method": "direct_connection"
                }
            }
    
    async def _check_response_time_monitoring(self) -> Dict[str, Any]:
        """
        Check database response time monitoring capabilities.
        
        Returns:
            Dictionary with response time monitoring status.
        """
        start_time = time.time()
        
        try:
            # Perform multiple database operations to test response times
            response_times = []
            operations = []
            
            if self.engine:
                # Test multiple operations and measure response times
                test_operations = [
                    ("connection_test", "SELECT 1"),
                    ("simple_query", "SELECT 1 as test"),
                ]
                
                # Add database-specific queries
                if "sqlite" in self.database_url:
                    test_operations.append(("metadata_query", "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1"))
                else:
                    test_operations.append(("metadata_query", "SELECT table_name FROM information_schema.tables LIMIT 1"))
                
                for op_name, query in test_operations:
                    op_start = time.time()
                    try:
                        with self.engine.connect() as conn:
                            result = conn.execute(text(query))
                            if result.returns_rows:
                                result.fetchall()
                        
                        op_time = (time.time() - op_start) * 1000
                        response_times.append(op_time)
                        operations.append({
                            "operation": op_name,
                            "response_time_ms": op_time,
                            "status": "success"
                        })
                        
                    except Exception as e:
                        op_time = (time.time() - op_start) * 1000
                        operations.append({
                            "operation": op_name,
                            "response_time_ms": op_time,
                            "status": "failed",
                            "error": str(e)
                        })
            
            # Calculate response time statistics
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
            else:
                avg_response_time = max_response_time = min_response_time = 0
            
            # Evaluate response time performance
            status = "healthy"
            warnings = []
            
            if avg_response_time > self.performance_thresholds["query_time_critical_ms"]:
                status = "unhealthy"
                warnings.append(f"Critical average response time: {avg_response_time:.1f}ms")
            elif avg_response_time > self.performance_thresholds["query_time_warning_ms"]:
                status = "degraded"
                warnings.append(f"Slow average response time: {avg_response_time:.1f}ms")
            
            if max_response_time > self.performance_thresholds["query_time_critical_ms"] * 2:
                status = "unhealthy"
                warnings.append(f"Critical max response time: {max_response_time:.1f}ms")
            
            total_response_time = (time.time() - start_time) * 1000
            
            return {
                "healthy": status != "unhealthy",
                "response_time": total_response_time,
                "details": {
                    "status": status,
                    "monitoring_available": True,
                    "statistics": {
                        "average_response_time_ms": avg_response_time,
                        "max_response_time_ms": max_response_time,
                        "min_response_time_ms": min_response_time,
                        "total_operations": len(operations),
                        "successful_operations": len([op for op in operations if op["status"] == "success"])
                    },
                    "operations": operations,
                    "warnings": warnings if warnings else None,
                    "thresholds": self.performance_thresholds
                }
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"Response time monitoring failed: {str(e)}",
                    "monitoring_available": False
                }
            }
    
    async def check_comprehensive_database_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive database health check including all components.
        
        Returns:
            Dictionary with complete database health assessment.
        """
        self.logger.info("Running comprehensive database health check")
        
        # Run all health checks concurrently
        postgres_task = asyncio.create_task(self._check_postgresql_health())
        chromadb_task = asyncio.create_task(self._check_chromadb_health())
        response_time_task = asyncio.create_task(self._check_response_time_monitoring())
        
        # Wait for all checks to complete
        postgres_result, chromadb_result, response_time_result = await asyncio.gather(
            postgres_task, chromadb_task, response_time_task, return_exceptions=True
        )
        
        # Process results and handle exceptions
        results = {}
        
        if isinstance(postgres_result, Exception):
            results["postgresql"] = {
                "healthy": False,
                "error": str(postgres_result),
                "response_time": 0
            }
        else:
            results["postgresql"] = postgres_result
        
        if isinstance(chromadb_result, Exception):
            results["chromadb"] = {
                "healthy": False,
                "error": str(chromadb_result),
                "response_time": 0
            }
        else:
            results["chromadb"] = chromadb_result
        
        if isinstance(response_time_result, Exception):
            results["response_time_monitoring"] = {
                "healthy": False,
                "error": str(response_time_result),
                "response_time": 0
            }
        else:
            results["response_time_monitoring"] = response_time_result
        
        # Calculate overall health status
        healthy_components = sum(1 for result in results.values() if result.get("healthy", False))
        total_components = len(results)
        overall_healthy = healthy_components == total_components
        
        return {
            "overall_healthy": overall_healthy,
            "healthy_components": healthy_components,
            "total_components": total_components,
            "success_rate": (healthy_components / total_components * 100) if total_components > 0 else 0,
            "components": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_health_summary(self) -> str:
        """
        Get a brief summary of database health check results.
        
        Returns:
            String summary of database health status.
        """
        total_checks = len(self.health_results)
        healthy_checks = len([r for r in self.health_results.values() if r["healthy"]])
        
        return (
            f"Database Health: {healthy_checks}/{total_checks} checks passed. "
            f"Components: {', '.join(self.health_results.keys())}"
        )