"""
Database performance optimization and monitoring module.
Provides query optimization, connection pooling, read replicas, and performance monitoring.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from collections import defaultdict
import statistics

import asyncpg
from sqlalchemy import text, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import Select

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class QueryPerformanceMetric:
    """Query performance metric data."""
    query_hash: str
    query_text: str
    execution_time: float
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    parameters: Optional[Dict] = None
    row_count: Optional[int] = None
    connection_id: Optional[str] = None


@dataclass
class ConnectionPoolMetrics:
    """Connection pool performance metrics."""
    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    invalid: int
    total_connections: int
    active_connections: int
    idle_connections: int
    avg_connection_time: float
    max_connection_time: float
    connection_errors: int


@dataclass
class SlowQueryAnalysis:
    """Slow query analysis result."""
    query_pattern: str
    avg_execution_time: float
    max_execution_time: float
    min_execution_time: float
    execution_count: int
    total_time: float
    suggestions: List[str] = field(default_factory=list)
    affected_tables: List[str] = field(default_factory=list)


class DatabasePerformanceOptimizer:
    """Database performance optimization and monitoring."""
    
    def __init__(self):
        self.query_metrics: List[QueryPerformanceMetric] = []
        self.slow_query_threshold = 1.0  # seconds
        self.max_metrics_history = 10000
        self.connection_metrics = ConnectionPoolMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0)
        
        # Query pattern cache for analysis
        self.query_patterns = defaultdict(list)
        self.optimization_cache = {}
        
        # Read replica configuration
        self.read_engines = {}
        self.write_engine = None
        self.read_replica_enabled = False
        
        # Performance monitoring
        self.monitoring_enabled = True
        self.last_cleanup = datetime.utcnow()
        self.cleanup_interval = timedelta(hours=1)
    
    async def initialize_engines(self):
        """Initialize database engines with performance optimization."""
        if not settings.database_url:
            logger.warning("No database URL configured")
            return
        
        # Configure optimal connection pool settings
        pool_settings = self._get_optimal_pool_settings()
        
        # Create write engine (primary database)
        self.write_engine = create_async_engine(
            settings.database_url,
            **pool_settings,
            echo=settings.api_debug,
            future=True,
            # Performance optimizations
            connect_args=(
                {
                    "command_timeout": 60,
                    "server_settings": {
                        "application_name": "contract_analyzer_write",
                        "jit": "off",
                        "shared_preload_libraries": "pg_stat_statements",
                        "track_activity_query_size": "2048",
                        "log_min_duration_statement": "1000",
                    }
                } if settings.database_url.startswith("postgresql") else {
                    "check_same_thread": False,
                    "timeout": 60
                }
            )
        )
        
        # Set up query monitoring for write engine
        self._setup_query_monitoring(self.write_engine, "write")
        
        # Initialize read replicas if configured
        await self._initialize_read_replicas()
        
        logger.info("Database engines initialized with performance optimization")
    
    def _get_optimal_pool_settings(self) -> Dict[str, Any]:
        """Calculate optimal connection pool settings based on system resources."""
        try:
            import psutil
            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
        except ImportError:
            cpu_count = 4
            memory_gb = 8
        
        # Calculate optimal pool size based on resources
        # Rule of thumb: 2-4 connections per CPU core for mixed workloads
        base_pool_size = max(5, min(20, cpu_count * 3))
        max_overflow = min(30, base_pool_size * 2)
        
        # Adjust based on available memory
        if memory_gb < 4:
            base_pool_size = max(3, base_pool_size // 2)
            max_overflow = max(5, max_overflow // 2)
        elif memory_gb > 16:
            base_pool_size = min(30, base_pool_size + 5)
            max_overflow = min(50, max_overflow + 10)
        
        return {
            "poolclass": QueuePool,
            "pool_size": base_pool_size,
            "max_overflow": max_overflow,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # Recycle connections every hour
            "pool_timeout": 30,
            "pool_reset_on_return": "commit",
        }
    
    async def _initialize_read_replicas(self):
        """Initialize read replica connections if configured."""
        read_replica_urls = getattr(settings, 'read_replica_urls', [])
        
        if not read_replica_urls:
            logger.info("No read replicas configured")
            return
        
        pool_settings = self._get_optimal_pool_settings()
        # Reduce pool size for read replicas
        pool_settings["pool_size"] = max(3, pool_settings["pool_size"] // 2)
        pool_settings["max_overflow"] = max(5, pool_settings["max_overflow"] // 2)
        
        for i, replica_url in enumerate(read_replica_urls):
            try:
                engine = create_async_engine(
                    replica_url,
                    **pool_settings,
                    echo=settings.api_debug,
                    connect_args=(
                        {
                            "command_timeout": 60,
                            "server_settings": {
                                "application_name": f"contract_analyzer_read_{i}",
                                "default_transaction_isolation": "read committed",
                                "statement_timeout": "30s",
                            }
                        } if settings.database_url.startswith("postgresql") else {
                            "check_same_thread": False,
                            "timeout": 60
                        }
                    )
                )
                
                # Test connection
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                
                self.read_engines[f"replica_{i}"] = engine
                self._setup_query_monitoring(engine, f"read_replica_{i}")
                
                logger.info(f"Read replica {i} initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize read replica {i}: {e}")
        
        if self.read_engines:
            self.read_replica_enabled = True
            logger.info(f"Initialized {len(self.read_engines)} read replicas")
    
    def _setup_query_monitoring(self, engine: Any, engine_type: str):
        """Set up query performance monitoring for an engine."""
        
        @event.listens_for(engine.sync_engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            context._engine_type = engine_type
        
        @event.listens_for(engine.sync_engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if not self.monitoring_enabled:
                return
            
            execution_time = time.time() - context._query_start_time
            
            # Create query hash for pattern matching
            query_hash = self._create_query_hash(statement)
            
            # Record metric
            metric = QueryPerformanceMetric(
                query_hash=query_hash,
                query_text=statement[:500] + "..." if len(statement) > 500 else statement,
                execution_time=execution_time,
                timestamp=datetime.utcnow(),
                success=True,
                parameters=parameters if isinstance(parameters, dict) else None,
                row_count=cursor.rowcount if hasattr(cursor, 'rowcount') else None,
                connection_id=getattr(context, '_engine_type', 'unknown')
            )
            
            self._record_query_metric(metric)
            
            # Analyze slow queries
            if execution_time > self.slow_query_threshold:
                self._analyze_slow_query(statement, execution_time, parameters)
        
        @event.listens_for(engine.sync_engine, "handle_error")
        def receive_handle_error(exception_context):
            if not self.monitoring_enabled:
                return
            
            # Record failed query
            metric = QueryPerformanceMetric(
                query_hash="error",
                query_text=str(exception_context.statement)[:500] if exception_context.statement else "unknown",
                execution_time=0.0,
                timestamp=datetime.utcnow(),
                success=False,
                error=str(exception_context.original_exception),
                connection_id=engine_type
            )
            
            self._record_query_metric(metric)
    
    def _create_query_hash(self, query: str) -> str:
        """Create a hash for query pattern matching."""
        import hashlib
        import re
        
        # Normalize query for pattern matching
        normalized = re.sub(r'\b\d+\b', '?', query.lower())  # Replace numbers with ?
        normalized = re.sub(r"'[^']*'", "'?'", normalized)   # Replace string literals
        normalized = re.sub(r'\s+', ' ', normalized)         # Normalize whitespace
        
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _record_query_metric(self, metric: QueryPerformanceMetric):
        """Record a query performance metric."""
        self.query_metrics.append(metric)
        
        # Add to pattern cache for analysis
        self.query_patterns[metric.query_hash].append(metric)
        
        # Cleanup old metrics periodically
        if len(self.query_metrics) > self.max_metrics_history:
            self.query_metrics = self.query_metrics[-self.max_metrics_history//2:]
        
        # Periodic cleanup
        if datetime.utcnow() - self.last_cleanup > self.cleanup_interval:
            asyncio.create_task(self._cleanup_old_metrics())
    
    def _analyze_slow_query(self, query: str, execution_time: float, parameters: Any):
        """Analyze slow query and provide optimization suggestions."""
        suggestions = []
        query_lower = query.lower().strip()
        
        # Common performance issues detection
        if "select *" in query_lower:
            suggestions.append("Avoid SELECT * - specify only needed columns")
        
        if "order by" in query_lower and "limit" not in query_lower:
            suggestions.append("Consider adding LIMIT when using ORDER BY")
        
        if "like '%" in query_lower or 'like "%' in query_lower:
            suggestions.append("Leading wildcards in LIKE can be slow - consider full-text search or trigram indexes")
        
        if query_lower.count("join") > 3:
            suggestions.append("Multiple JOINs detected - verify indexes on join columns")
        
        if "group by" in query_lower and "having" not in query_lower:
            suggestions.append("Consider using WHERE instead of HAVING when possible")
        
        if "distinct" in query_lower:
            suggestions.append("DISTINCT can be expensive - consider if it's necessary")
        
        if "subquery" in query_lower or "(" in query_lower:
            suggestions.append("Consider rewriting subqueries as JOINs for better performance")
        
        # Check for missing indexes (basic heuristics)
        if "where" in query_lower:
            where_clause = query_lower.split("where")[1].split("order by")[0].split("group by")[0]
            if "=" in where_clause or "in (" in where_clause:
                suggestions.append("Ensure indexes exist on WHERE clause columns")
        
        if suggestions:
            logger.warning(
                f"Slow query detected ({execution_time:.2f}s): {query[:100]}... "
                f"Suggestions: {'; '.join(suggestions)}"
            )
    
    async def _cleanup_old_metrics(self):
        """Clean up old performance metrics."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Remove old metrics
        self.query_metrics = [
            m for m in self.query_metrics 
            if m.timestamp > cutoff_time
        ]
        
        # Clean up pattern cache
        for pattern_hash in list(self.query_patterns.keys()):
            self.query_patterns[pattern_hash] = [
                m for m in self.query_patterns[pattern_hash]
                if m.timestamp > cutoff_time
            ]
            
            if not self.query_patterns[pattern_hash]:
                del self.query_patterns[pattern_hash]
        
        self.last_cleanup = datetime.utcnow()
        logger.debug("Cleaned up old performance metrics")
    
    @asynccontextmanager
    async def get_session(self, read_only: bool = False) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with read/write routing."""
        engine = self._get_engine(read_only)
        
        if not engine:
            raise RuntimeError("No database engine available")
        
        from sqlalchemy.ext.asyncio import async_sessionmaker
        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def _get_engine(self, read_only: bool = False):
        """Get appropriate engine based on read/write requirements."""
        if read_only and self.read_replica_enabled and self.read_engines:
            # Round-robin selection of read replicas
            replica_names = list(self.read_engines.keys())
            selected_replica = replica_names[int(time.time()) % len(replica_names)]
            return self.read_engines[selected_replica]
        
        return self.write_engine
    
    async def get_performance_metrics(self, hours: int = 1) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.query_metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"status": "no_recent_data", "hours": hours}
        
        # Calculate basic statistics
        execution_times = [m.execution_time for m in recent_metrics if m.success]
        successful_queries = [m for m in recent_metrics if m.success]
        failed_queries = [m for m in recent_metrics if not m.success]
        
        # Query performance analysis
        query_performance = {}
        if execution_times:
            query_performance = {
                "total_queries": len(recent_metrics),
                "successful_queries": len(successful_queries),
                "failed_queries": len(failed_queries),
                "success_rate": len(successful_queries) / len(recent_metrics) * 100,
                "avg_execution_time": statistics.mean(execution_times),
                "median_execution_time": statistics.median(execution_times),
                "p95_execution_time": statistics.quantiles(execution_times, n=20)[18] if len(execution_times) > 20 else max(execution_times),
                "p99_execution_time": statistics.quantiles(execution_times, n=100)[98] if len(execution_times) > 100 else max(execution_times),
                "min_execution_time": min(execution_times),
                "max_execution_time": max(execution_times),
                "slow_queries": len([t for t in execution_times if t > self.slow_query_threshold])
            }
        
        # Connection pool metrics
        pool_metrics = {}
        if self.write_engine:
            pool = self.write_engine.pool
            pool_metrics = {
                "write_pool": {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid()
                }
            }
            
            # Add read replica pool metrics
            for name, engine in self.read_engines.items():
                pool = engine.pool
                pool_metrics[name] = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid()
                }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "query_performance": query_performance,
            "connection_pools": pool_metrics,
            "read_replicas_enabled": self.read_replica_enabled,
            "read_replica_count": len(self.read_engines),
            "monitoring_enabled": self.monitoring_enabled
        }
    
    async def analyze_slow_queries(self, hours: int = 24, min_occurrences: int = 2) -> List[SlowQueryAnalysis]:
        """Analyze slow query patterns and provide optimization suggestions."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Group queries by pattern
        pattern_analysis = {}
        
        for pattern_hash, metrics in self.query_patterns.items():
            recent_metrics = [m for m in metrics if m.timestamp > cutoff_time and m.success]
            
            if len(recent_metrics) < min_occurrences:
                continue
            
            execution_times = [m.execution_time for m in recent_metrics]
            avg_time = statistics.mean(execution_times)
            
            # Only analyze patterns with significant execution time
            if avg_time > self.slow_query_threshold:
                pattern_analysis[pattern_hash] = SlowQueryAnalysis(
                    query_pattern=recent_metrics[0].query_text,
                    avg_execution_time=avg_time,
                    max_execution_time=max(execution_times),
                    min_execution_time=min(execution_times),
                    execution_count=len(recent_metrics),
                    total_time=sum(execution_times),
                    suggestions=self._generate_optimization_suggestions(recent_metrics[0].query_text),
                    affected_tables=self._extract_table_names(recent_metrics[0].query_text)
                )
        
        # Sort by total time impact
        return sorted(
            pattern_analysis.values(),
            key=lambda x: x.total_time,
            reverse=True
        )
    
    def _generate_optimization_suggestions(self, query: str) -> List[str]:
        """Generate optimization suggestions for a query."""
        suggestions = []
        query_lower = query.lower()
        
        # Index suggestions
        if "where" in query_lower:
            suggestions.append("Ensure proper indexes on WHERE clause columns")
        
        if "join" in query_lower:
            suggestions.append("Verify indexes on JOIN columns")
        
        if "order by" in query_lower:
            suggestions.append("Consider composite index for ORDER BY columns")
        
        # Query structure suggestions
        if "select *" in query_lower:
            suggestions.append("Select only required columns instead of *")
        
        if "like '%" in query_lower:
            suggestions.append("Consider full-text search or trigram indexes for pattern matching")
        
        if "distinct" in query_lower:
            suggestions.append("Evaluate if DISTINCT is necessary")
        
        if query_lower.count("join") > 2:
            suggestions.append("Consider denormalization for frequently joined tables")
        
        return suggestions
    
    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from query (basic implementation)."""
        import re
        
        # Simple regex to find table names after FROM and JOIN
        pattern = r'\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, query.lower())
        
        return list(set(matches))
    
    async def optimize_query(self, query: str) -> Dict[str, Any]:
        """Analyze and suggest optimizations for a specific query."""
        suggestions = self._generate_optimization_suggestions(query)
        affected_tables = self._extract_table_names(query)
        
        # Check if we have historical data for this query pattern
        query_hash = self._create_query_hash(query)
        historical_metrics = self.query_patterns.get(query_hash, [])
        
        performance_history = {}
        if historical_metrics:
            execution_times = [m.execution_time for m in historical_metrics if m.success]
            if execution_times:
                performance_history = {
                    "avg_execution_time": statistics.mean(execution_times),
                    "execution_count": len(execution_times),
                    "last_executed": max(m.timestamp for m in historical_metrics).isoformat()
                }
        
        return {
            "query_hash": query_hash,
            "suggestions": suggestions,
            "affected_tables": affected_tables,
            "performance_history": performance_history,
            "optimization_priority": "high" if any("index" in s.lower() for s in suggestions) else "medium"
        }
    
    async def create_recommended_indexes(self) -> List[str]:
        """Generate SQL statements for recommended indexes based on query analysis."""
        slow_queries = await self.analyze_slow_queries(hours=24, min_occurrences=1)
        
        index_recommendations = []
        
        for analysis in slow_queries:
            if analysis.avg_execution_time > self.slow_query_threshold * 2:  # Focus on very slow queries
                for table in analysis.affected_tables:
                    # Basic index recommendations
                    if "where" in analysis.query_pattern.lower():
                        index_recommendations.append(
                            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_{table}_performance "
                            f"ON {table} USING btree (created_at, status);"
                        )
                    
                    if "order by" in analysis.query_pattern.lower():
                        index_recommendations.append(
                            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_{table}_ordering "
                            f"ON {table} USING btree (created_at DESC);"
                        )
        
        return list(set(index_recommendations))  # Remove duplicates
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "write_engine": False,
            "read_replicas": {},
            "connection_pools": {},
            "performance_monitoring": self.monitoring_enabled
        }
        
        # Check write engine
        if self.write_engine:
            try:
                async with self.get_session() as session:
                    await session.execute(text("SELECT 1"))
                health_status["write_engine"] = True
            except Exception as e:
                logger.error(f"Write engine health check failed: {e}")
        
        # Check read replicas
        for name, engine in self.read_engines.items():
            try:
                session_maker = async_sessionmaker(engine, class_=AsyncSession)
                async with session_maker() as session:
                    await session.execute(text("SELECT 1"))
                health_status["read_replicas"][name] = True
            except Exception as e:
                logger.error(f"Read replica {name} health check failed: {e}")
                health_status["read_replicas"][name] = False
        
        return health_status
    
    async def close(self):
        """Close all database connections."""
        if self.write_engine:
            await self.write_engine.dispose()
        
        for engine in self.read_engines.values():
            await engine.dispose()
        
        logger.info("Database performance optimizer closed")


# Global instance
db_performance_optimizer = DatabasePerformanceOptimizer()


async def get_db_performance_optimizer() -> DatabasePerformanceOptimizer:
    """Get the global database performance optimizer instance."""
    if not db_performance_optimizer.write_engine:
        await db_performance_optimizer.initialize_engines()
    return db_performance_optimizer