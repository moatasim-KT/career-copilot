"""
Database optimization service for query analysis and performance improvements.
"""

import asyncio
import hashlib
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from ..core.database import get_db_session
from ..core.logging import get_logger
from ..repositories.base_repository import BaseRepository

logger = get_logger(__name__)


@dataclass
class QueryOptimizationResult:
    """Result of query optimization analysis."""
    original_query: str
    optimized_query: Optional[str]
    suggestions: List[str]
    estimated_improvement: Optional[float]
    complexity_score: int
    affected_tables: List[str]
    recommended_indexes: List[str]


@dataclass
class TableAnalysisResult:
    """Result of table performance analysis."""
    table_name: str
    row_count: int
    table_size_mb: float
    index_size_mb: float
    fragmentation_percent: float
    most_expensive_queries: List[str]
    recommended_optimizations: List[str]


class DatabaseOptimizationService:
    """Service for database performance optimization and analysis."""
    
    def __init__(self):
        self.query_cache = {}
        self.optimization_cache = {}
        self.table_stats_cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def analyze_query_performance(
        self, 
        query: str, 
        session: AsyncSession
    ) -> QueryOptimizationResult:
        """
        Analyze query performance and provide optimization suggestions.
        
        Args:
            query: SQL query to analyze
            session: Database session
            
        Returns:
            Query optimization analysis result
        """
        query_hash = self._hash_query(query)
        
        # Check cache first
        if query_hash in self.optimization_cache:
            cached_result, timestamp = self.optimization_cache[query_hash]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_result
        
        try:
            # Analyze query structure
            suggestions = self._analyze_query_structure(query)
            affected_tables = self._extract_table_names(query)
            complexity_score = self._calculate_complexity_score(query)
            
            # Get execution plan
            execution_plan = await self._get_execution_plan(query, session)
            
            # Analyze execution plan for optimization opportunities
            plan_suggestions = self._analyze_execution_plan(execution_plan)
            suggestions.extend(plan_suggestions)
            
            # Generate recommended indexes
            recommended_indexes = await self._generate_index_recommendations(
                query, affected_tables, session
            )
            
            # Attempt to optimize query
            optimized_query = self._optimize_query_structure(query)
            
            result = QueryOptimizationResult(
                original_query=query,
                optimized_query=optimized_query,
                suggestions=list(set(suggestions)),  # Remove duplicates
                estimated_improvement=None,  # Would need benchmarking
                complexity_score=complexity_score,
                affected_tables=affected_tables,
                recommended_indexes=recommended_indexes
            )
            
            # Cache result
            self.optimization_cache[query_hash] = (result, datetime.utcnow())
            
            return result
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return QueryOptimizationResult(
                original_query=query,
                optimized_query=None,
                suggestions=[f"Analysis failed: {str(e)}"],
                estimated_improvement=None,
                complexity_score=0,
                affected_tables=[],
                recommended_indexes=[]
            )
    
    async def analyze_table_performance(
        self, 
        table_name: str, 
        session: AsyncSession
    ) -> TableAnalysisResult:
        """
        Analyze table performance and provide optimization recommendations.
        
        Args:
            table_name: Name of the table to analyze
            session: Database session
            
        Returns:
            Table analysis result
        """
        cache_key = f"table_{table_name}"
        
        # Check cache
        if cache_key in self.table_stats_cache:
            cached_result, timestamp = self.table_stats_cache[cache_key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_result
        
        try:
            # Get table statistics
            stats = await self._get_table_statistics(table_name, session)
            
            # Analyze table structure
            recommendations = await self._analyze_table_structure(table_name, session)
            
            # Get most expensive queries for this table
            expensive_queries = await self._get_expensive_queries_for_table(
                table_name, session
            )
            
            result = TableAnalysisResult(
                table_name=table_name,
                row_count=stats.get('row_count', 0),
                table_size_mb=stats.get('table_size_mb', 0.0),
                index_size_mb=stats.get('index_size_mb', 0.0),
                fragmentation_percent=stats.get('fragmentation_percent', 0.0),
                most_expensive_queries=expensive_queries,
                recommended_optimizations=recommendations
            )
            
            # Cache result
            self.table_stats_cache[cache_key] = (result, datetime.utcnow())
            
            return result
            
        except Exception as e:
            logger.error(f"Table analysis failed for {table_name}: {e}")
            return TableAnalysisResult(
                table_name=table_name,
                row_count=0,
                table_size_mb=0.0,
                index_size_mb=0.0,
                fragmentation_percent=0.0,
                most_expensive_queries=[],
                recommended_optimizations=[f"Analysis failed: {str(e)}"]
            )
    
    async def optimize_repository_queries(
        self, 
        repository: BaseRepository, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze and optimize queries used by a repository.
        
        Args:
            repository: Repository instance to optimize
            session: Database session
            
        Returns:
            Optimization results and recommendations
        """
        table_name = repository.model.__tablename__
        
        # Analyze the table
        table_analysis = await self.analyze_table_performance(table_name, session)
        
        # Get common query patterns for this repository
        common_queries = self._get_repository_query_patterns(repository)
        
        query_optimizations = []
        for query in common_queries:
            optimization = await self.analyze_query_performance(query, session)
            query_optimizations.append(optimization)
        
        # Generate repository-specific recommendations
        repo_recommendations = self._generate_repository_recommendations(
            repository, table_analysis, query_optimizations
        )
        
        return {
            "table_analysis": table_analysis,
            "query_optimizations": query_optimizations,
            "repository_recommendations": repo_recommendations,
            "optimization_priority": self._calculate_optimization_priority(
                table_analysis, query_optimizations
            )
        }
    
    def _hash_query(self, query: str) -> str:
        """Create a hash for query caching."""
        normalized = re.sub(r'\s+', ' ', query.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _analyze_query_structure(self, query: str) -> List[str]:
        """Analyze query structure for common performance issues."""
        suggestions = []
        query_lower = query.lower()
        
        # Check for SELECT *
        if "select *" in query_lower:
            suggestions.append("Avoid SELECT * - specify only needed columns")
        
        # Check for missing LIMIT with ORDER BY
        if "order by" in query_lower and "limit" not in query_lower:
            suggestions.append("Consider adding LIMIT clause with ORDER BY")
        
        # Check for leading wildcards in LIKE
        if re.search(r"like\s+['\"]%", query_lower):
            suggestions.append("Leading wildcards in LIKE are slow - consider full-text search")
        
        # Check for multiple JOINs
        join_count = query_lower.count("join")
        if join_count > 3:
            suggestions.append(f"Query has {join_count} JOINs - verify indexes on join columns")
        
        # Check for subqueries
        if "(" in query and "select" in query_lower:
            subquery_count = query_lower.count("select") - 1
            if subquery_count > 0:
                suggestions.append("Consider rewriting subqueries as JOINs when possible")
        
        # Check for DISTINCT
        if "distinct" in query_lower:
            suggestions.append("DISTINCT can be expensive - verify if it's necessary")
        
        # Check for functions in WHERE clause
        if re.search(r"where.*\w+\s*\(", query_lower):
            suggestions.append("Functions in WHERE clause prevent index usage")
        
        # Check for OR conditions
        if " or " in query_lower:
            suggestions.append("OR conditions can be slow - consider UNION or separate queries")
        
        return suggestions
    
    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from query."""
        # Simple regex to find table names after FROM and JOIN
        pattern = r'\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, query.lower())
        return list(set(matches))
    
    def _calculate_complexity_score(self, query: str) -> int:
        """Calculate query complexity score (1-10)."""
        score = 1
        query_lower = query.lower()
        
        # Add points for various complexity factors
        score += query_lower.count("join")
        score += query_lower.count("subquery") * 2
        score += query_lower.count("union") * 2
        score += query_lower.count("group by")
        score += query_lower.count("order by")
        score += query_lower.count("having")
        score += len(re.findall(r"case\s+when", query_lower)) * 2
        
        return min(score, 10)
    
    async def _get_execution_plan(
        self, 
        query: str, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get query execution plan."""
        try:
            # Use EXPLAIN (ANALYZE, BUFFERS) for detailed plan
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
            result = await session.execute(text(explain_query))
            plan_data = result.fetchone()
            
            if plan_data and plan_data[0]:
                return plan_data[0][0] if isinstance(plan_data[0], list) else plan_data[0]
            
            return {}
            
        except Exception as e:
            logger.warning(f"Could not get execution plan: {e}")
            return {}
    
    def _analyze_execution_plan(self, plan: Dict[str, Any]) -> List[str]:
        """Analyze execution plan for optimization opportunities."""
        suggestions = []
        
        if not plan:
            return suggestions
        
        try:
            # Look for expensive operations
            if "Plan" in plan:
                self._analyze_plan_node(plan["Plan"], suggestions)
            
        except Exception as e:
            logger.warning(f"Execution plan analysis failed: {e}")
        
        return suggestions
    
    def _analyze_plan_node(self, node: Dict[str, Any], suggestions: List[str]):
        """Recursively analyze execution plan nodes."""
        node_type = node.get("Node Type", "")
        
        # Check for sequential scans
        if node_type == "Seq Scan":
            suggestions.append(f"Sequential scan detected on {node.get('Relation Name', 'unknown table')} - consider adding index")
        
        # Check for expensive sorts
        if node_type == "Sort" and node.get("Actual Total Time", 0) > 100:
            suggestions.append("Expensive sort operation - consider adding index for ORDER BY")
        
        # Check for hash joins without indexes
        if node_type == "Hash Join":
            suggestions.append("Hash join detected - verify indexes on join columns")
        
        # Check for nested loops with high cost
        if node_type == "Nested Loop" and node.get("Total Cost", 0) > 1000:
            suggestions.append("Expensive nested loop - consider rewriting query or adding indexes")
        
        # Recursively analyze child nodes
        for child in node.get("Plans", []):
            self._analyze_plan_node(child, suggestions)
    
    async def _generate_index_recommendations(
        self, 
        query: str, 
        tables: List[str], 
        session: AsyncSession
    ) -> List[str]:
        """Generate index recommendations based on query analysis."""
        recommendations = []
        
        try:
            # Analyze WHERE clauses for index opportunities
            where_columns = self._extract_where_columns(query)
            
            for table in tables:
                # Check existing indexes
                existing_indexes = await self._get_existing_indexes(table, session)
                
                for column in where_columns.get(table, []):
                    if not self._column_has_index(column, existing_indexes):
                        recommendations.append(
                            f"CREATE INDEX CONCURRENTLY idx_{table}_{column} ON {table} ({column});"
                        )
            
            # Analyze JOIN conditions
            join_conditions = self._extract_join_conditions(query)
            for table, columns in join_conditions.items():
                existing_indexes = await self._get_existing_indexes(table, session)
                
                for column in columns:
                    if not self._column_has_index(column, existing_indexes):
                        recommendations.append(
                            f"CREATE INDEX CONCURRENTLY idx_{table}_{column}_join ON {table} ({column});"
                        )
        
        except Exception as e:
            logger.warning(f"Index recommendation generation failed: {e}")
        
        return recommendations
    
    def _extract_where_columns(self, query: str) -> Dict[str, List[str]]:
        """Extract columns used in WHERE clauses by table."""
        # Simplified extraction - would need more sophisticated parsing for production
        where_columns = {}
        
        # Basic regex to find WHERE conditions
        where_pattern = r"where\s+(\w+)\.(\w+)\s*[=<>!]"
        matches = re.findall(where_pattern, query.lower())
        
        for table, column in matches:
            if table not in where_columns:
                where_columns[table] = []
            where_columns[table].append(column)
        
        return where_columns
    
    def _extract_join_conditions(self, query: str) -> Dict[str, List[str]]:
        """Extract columns used in JOIN conditions by table."""
        join_columns = {}
        
        # Basic regex to find JOIN conditions
        join_pattern = r"join\s+(\w+)\s+.*?on\s+\w+\.(\w+)\s*=\s*\w+\.(\w+)"
        matches = re.findall(join_pattern, query.lower())
        
        for table, col1, col2 in matches:
            if table not in join_columns:
                join_columns[table] = []
            join_columns[table].extend([col1, col2])
        
        return join_columns
    
    async def _get_existing_indexes(
        self, 
        table_name: str, 
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get existing indexes for a table."""
        try:
            query = text("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = :table_name
            """)
            
            result = await session.execute(query, {"table_name": table_name})
            return [{"name": row[0], "definition": row[1]} for row in result]
            
        except Exception as e:
            logger.warning(f"Could not get indexes for {table_name}: {e}")
            return []
    
    def _column_has_index(self, column: str, indexes: List[Dict[str, Any]]) -> bool:
        """Check if column has an index."""
        for index in indexes:
            if column in index["definition"].lower():
                return True
        return False
    
    def _optimize_query_structure(self, query: str) -> Optional[str]:
        """Attempt to optimize query structure."""
        optimized = query
        
        # Replace SELECT * with specific columns (placeholder)
        if "select *" in query.lower():
            # This would need table schema information to be properly implemented
            optimized = query.replace("SELECT *", "SELECT /* specify columns */")
        
        # Add LIMIT to ORDER BY queries without it
        if "order by" in query.lower() and "limit" not in query.lower():
            optimized += " LIMIT 1000"
        
        return optimized if optimized != query else None
    
    async def _get_table_statistics(
        self, 
        table_name: str, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get comprehensive table statistics."""
        try:
            stats_query = text("""
                SELECT 
                    (SELECT reltuples::bigint FROM pg_class WHERE relname = :table_name) as row_count,
                    pg_size_pretty(pg_total_relation_size(:table_name)) as total_size,
                    pg_size_pretty(pg_relation_size(:table_name)) as table_size,
                    pg_size_pretty(pg_total_relation_size(:table_name) - pg_relation_size(:table_name)) as index_size,
                    (pg_relation_size(:table_name) / 1024.0 / 1024.0) as table_size_mb,
                    ((pg_total_relation_size(:table_name) - pg_relation_size(:table_name)) / 1024.0 / 1024.0) as index_size_mb
            """)
            
            result = await session.execute(stats_query, {"table_name": table_name})
            row = result.fetchone()
            
            if row:
                return {
                    "row_count": row[0] or 0,
                    "total_size": row[1],
                    "table_size": row[2],
                    "index_size": row[3],
                    "table_size_mb": float(row[4] or 0),
                    "index_size_mb": float(row[5] or 0),
                    "fragmentation_percent": 0.0  # Would need more complex calculation
                }
            
            return {}
            
        except Exception as e:
            logger.warning(f"Could not get table statistics for {table_name}: {e}")
            return {}
    
    async def _analyze_table_structure(
        self, 
        table_name: str, 
        session: AsyncSession
    ) -> List[str]:
        """Analyze table structure for optimization opportunities."""
        recommendations = []
        
        try:
            # Get column statistics
            stats_query = text("""
                SELECT attname, n_distinct, correlation
                FROM pg_stats 
                WHERE tablename = :table_name
                ORDER BY n_distinct DESC NULLS LAST
            """)
            
            result = await session.execute(stats_query, {"table_name": table_name})
            
            for row in result:
                column_name, n_distinct, correlation = row
                
                # Recommend indexes for high-cardinality columns
                if n_distinct and n_distinct > 100:
                    recommendations.append(
                        f"Consider index on high-cardinality column: {column_name}"
                    )
                
                # Recommend clustering for highly correlated columns
                if correlation and abs(correlation) > 0.8:
                    recommendations.append(
                        f"Consider clustering on correlated column: {column_name}"
                    )
        
        except Exception as e:
            logger.warning(f"Table structure analysis failed for {table_name}: {e}")
        
        return recommendations
    
    async def _get_expensive_queries_for_table(
        self, 
        table_name: str, 
        session: AsyncSession
    ) -> List[str]:
        """Get most expensive queries for a table from pg_stat_statements."""
        try:
            # This requires pg_stat_statements extension
            query = text("""
                SELECT query, mean_time, calls
                FROM pg_stat_statements 
                WHERE query ILIKE :pattern
                ORDER BY mean_time DESC
                LIMIT 5
            """)
            
            result = await session.execute(
                query, 
                {"pattern": f"%{table_name}%"}
            )
            
            return [row[0] for row in result]
            
        except Exception as e:
            logger.warning(f"Could not get expensive queries for {table_name}: {e}")
            return []
    
    def _get_repository_query_patterns(
        self, 
        repository: BaseRepository
    ) -> List[str]:
        """Get common query patterns for a repository."""
        # This would analyze the repository methods to extract common queries
        # For now, return some common patterns
        table_name = repository.model.__tablename__
        
        return [
            f"SELECT * FROM {table_name} WHERE id = ?",
            f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT 20",
            f"SELECT COUNT(*) FROM {table_name}",
            f"SELECT * FROM {table_name} WHERE user_id = ? ORDER BY created_at DESC"
        ]
    
    def _generate_repository_recommendations(
        self,
        repository: BaseRepository,
        table_analysis: TableAnalysisResult,
        query_optimizations: List[QueryOptimizationResult]
    ) -> List[str]:
        """Generate repository-specific optimization recommendations."""
        recommendations = []
        
        # Analyze table size
        if table_analysis.table_size_mb > 1000:  # > 1GB
            recommendations.append("Large table detected - consider partitioning")
        
        # Analyze index usage
        if table_analysis.index_size_mb > table_analysis.table_size_mb * 0.5:
            recommendations.append("High index overhead - review index necessity")
        
        # Analyze query complexity
        avg_complexity = sum(q.complexity_score for q in query_optimizations) / len(query_optimizations) if query_optimizations else 0
        
        if avg_complexity > 6:
            recommendations.append("High query complexity - consider query optimization")
        
        return recommendations
    
    def _calculate_optimization_priority(
        self,
        table_analysis: TableAnalysisResult,
        query_optimizations: List[QueryOptimizationResult]
    ) -> str:
        """Calculate optimization priority based on analysis results."""
        priority_score = 0
        
        # Table size factor
        if table_analysis.table_size_mb > 1000:
            priority_score += 3
        elif table_analysis.table_size_mb > 100:
            priority_score += 2
        elif table_analysis.table_size_mb > 10:
            priority_score += 1
        
        # Query complexity factor
        if query_optimizations:
            avg_complexity = sum(q.complexity_score for q in query_optimizations) / len(query_optimizations)
            if avg_complexity > 7:
                priority_score += 3
            elif avg_complexity > 5:
                priority_score += 2
            elif avg_complexity > 3:
                priority_score += 1
        
        # Number of optimization suggestions
        total_suggestions = sum(len(q.suggestions) for q in query_optimizations)
        if total_suggestions > 10:
            priority_score += 2
        elif total_suggestions > 5:
            priority_score += 1
        
        if priority_score >= 6:
            return "high"
        elif priority_score >= 3:
            return "medium"
        else:
            return "low"


# Global service instance
database_optimization_service = DatabaseOptimizationService()


def get_database_optimization_service() -> DatabaseOptimizationService:
    """Get the database optimization service instance."""
    return database_optimization_service