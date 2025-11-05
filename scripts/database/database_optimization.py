#!/usr/bin/env python3
"""
Database Query Optimization and Index Management
Implements database performance optimization, index analysis, and query tuning
Requirements: 7.1, 7.2, 7.4
"""

import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.config import get_settings  # type: ignore[import-untyped]
from sqlalchemy import MetaData, inspect, text
from sqlalchemy.engine import Engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceMetric:
	"""Query performance metric data structure"""

	query_name: str
	query_sql: str
	execution_time: float
	rows_returned: int
	rows_examined: int
	index_used: bool
	optimization_score: float
	recommendations: list[str]


@dataclass
class IndexAnalysis:
	"""Database index analysis results"""

	table_name: str
	existing_indexes: list[dict[str, Any]]
	missing_indexes: list[dict[str, Any]]
	unused_indexes: list[dict[str, Any]]
	duplicate_indexes: list[dict[str, Any]]
	optimization_potential: float


class DatabaseOptimizer:
	"""Database optimization and performance tuning"""

	def __init__(self, engine: Engine | None = None):
		self.engine = engine or globals()["engine"]
		self.settings = get_settings()
		self.metadata = MetaData()
		self.inspector = inspect(self.engine)
		self.query_metrics: list[QueryPerformanceMetric] = []
		self.index_analyses: list[IndexAnalysis] = []

	def analyze_query_performance(self, queries: list[tuple[str, str]]) -> list[QueryPerformanceMetric]:
		"""Analyze performance of specific queries"""
		logger.info(f"Analyzing performance of {len(queries)} queries")

		metrics = []

		for query_name, query_sql in queries:
			logger.debug(f"Analyzing query: {query_name}")

			# Execute query multiple times to get average performance
			execution_times = []
			rows_returned = 0

			for _ in range(3):  # 3 iterations for average
				start_time = time.time()

				try:
					with self.engine.connect() as conn:
						result = conn.execute(text(query_sql))
						rows = result.fetchall()
						rows_returned = len(rows)

					end_time = time.time()
					execution_times.append(end_time - start_time)

				except Exception as e:
					logger.error(f"Query {query_name} failed: {e}")
					execution_times.append(float("inf"))

			# Calculate average execution time
			valid_times = [t for t in execution_times if t != float("inf")]
			avg_execution_time = sum(valid_times) / len(valid_times) if valid_times else float("inf")

			# Analyze query for optimization opportunities
			recommendations = self._analyze_query_for_optimization(query_sql, avg_execution_time)

			# Calculate optimization score (0-100, higher is better)
			optimization_score = self._calculate_query_optimization_score(avg_execution_time, rows_returned, recommendations)

			metric = QueryPerformanceMetric(
				query_name=query_name,
				query_sql=query_sql,
				execution_time=avg_execution_time,
				rows_returned=rows_returned,
				rows_examined=rows_returned,  # Simplified for this implementation
				index_used=self._query_uses_index(query_sql),
				optimization_score=optimization_score,
				recommendations=recommendations,
			)

			metrics.append(metric)

			logger.info(f"Query {query_name}: {avg_execution_time:.4f}s, Score: {optimization_score:.1f}")

		self.query_metrics = metrics
		return metrics

	def _analyze_query_for_optimization(self, query_sql: str, execution_time: float) -> list[str]:
		"""Analyze query and suggest optimizations"""
		recommendations = []

		query_lower = query_sql.lower()

		# Check for common performance issues
		if execution_time > 0.1:
			recommendations.append("Query execution time exceeds 100ms threshold")

		if "select *" in query_lower:
			recommendations.append("Avoid SELECT * - specify only needed columns")

		if "order by" in query_lower and "limit" not in query_lower:
			recommendations.append("Consider adding LIMIT to ORDER BY queries")

		if query_lower.count("join") > 2:
			recommendations.append("Complex joins detected - consider query restructuring")

		if "where" not in query_lower and ("update" in query_lower or "delete" in query_lower):
			recommendations.append("UPDATE/DELETE without WHERE clause detected")

		if "group by" in query_lower and "having" not in query_lower:
			recommendations.append("Consider using HAVING clause with GROUP BY for filtering")

		# Check for potential index usage
		if "where" in query_lower:
			# Extract WHERE conditions (simplified)
			where_part = query_lower.split("where")[1].split("order by")[0].split("group by")[0]
			if "=" in where_part or "in" in where_part:
				recommendations.append("Ensure indexes exist for WHERE clause columns")

		return recommendations

	def _calculate_query_optimization_score(self, execution_time: float, rows_returned: int, recommendations: list[str]) -> float:
		"""Calculate optimization score for a query (0-100)"""
		score = 100.0

		# Deduct points for slow execution
		if execution_time > 0.001:  # 1ms
			score -= min(30, (execution_time - 0.001) * 1000)

		# Deduct points for each recommendation
		score -= len(recommendations) * 5

		# Bonus for fast queries
		if execution_time < 0.01:  # 10ms
			score += 10

		return max(0.0, min(100.0, score))

	def _query_uses_index(self, query_sql: str) -> bool:
		"""Check if query likely uses an index (simplified heuristic)"""
		query_lower = query_sql.lower()

		# Simple heuristics for index usage
		has_where_with_equality = "where" in query_lower and "=" in query_lower
		has_primary_key_lookup = "id =" in query_lower
		has_indexed_column = any(col in query_lower for col in ["user_id", "email", "created_at"])

		return has_where_with_equality or has_primary_key_lookup or has_indexed_column

	def analyze_table_indexes(self, table_name: str) -> IndexAnalysis:
		"""Analyze indexes for a specific table"""
		logger.info(f"Analyzing indexes for table: {table_name}")

		existing_indexes: list[dict[str, Any]] = []
		missing_indexes: list[dict[str, Any]] = []
		unused_indexes: list[dict[str, Any]] = []
		duplicate_indexes: list[dict[str, Any]] = []

		try:
			# Get existing indexes
			if self.inspector.has_table(table_name):
				indexes = self.inspector.get_indexes(table_name)
				columns = self.inspector.get_columns(table_name)

				for index in indexes:
					existing_indexes.append(
						{
							"name": index["name"],
							"columns": index["column_names"],
							"unique": index["unique"],
							"type": "btree",  # Default assumption
						}
					)

			# Suggest missing indexes based on table and common patterns
			# Note: columns type from SQLAlchemy inspector is complex, using type ignore
			suggested_indexes = self._suggest_indexes_for_table(table_name, columns)  # type: ignore[arg-type]

			# Check which suggested indexes are missing
			existing_column_sets = set()
			for idx in existing_indexes:
				columns_list = idx.get("columns", [])
				if isinstance(columns_list, list):
					column_set = tuple(sorted(columns_list))
					existing_column_sets.add(column_set)

			for suggestion in suggested_indexes:
				column_set = tuple(sorted(suggestion["columns"]))
				if column_set not in existing_column_sets:
					missing_indexes.append(suggestion)  # Detect duplicate indexes (simplified)
			column_sets: dict[tuple[str, ...], dict[str, Any]] = {}
			for idx in existing_indexes:
				columns_list = idx.get("columns", [])
				if isinstance(columns_list, list):
					column_set = tuple(sorted(columns_list))
					if column_set in column_sets:
						duplicate_indexes.append({"duplicate_of": column_sets[column_set], "index": idx})
					else:
						column_sets[column_set] = idx  # Calculate optimization potential
			optimization_potential = self._calculate_index_optimization_potential(existing_indexes, missing_indexes, duplicate_indexes)

		except Exception as e:
			logger.error(f"Index analysis failed for table {table_name}: {e}")
			optimization_potential = 0.0

		analysis = IndexAnalysis(
			table_name=table_name,
			existing_indexes=existing_indexes,
			missing_indexes=missing_indexes,
			unused_indexes=unused_indexes,
			duplicate_indexes=duplicate_indexes,
			optimization_potential=optimization_potential,
		)

		logger.info(
			f"Table {table_name}: {len(existing_indexes)} existing, {len(missing_indexes)} missing, {len(duplicate_indexes)} duplicate indexes"
		)

		return analysis

	def _suggest_indexes_for_table(self, table_name: str, columns: list[dict[str, Any]]) -> list[dict[str, Any]]:
		"""Suggest indexes for a table based on common patterns"""
		suggestions = []
		column_names = [col["name"] for col in columns]

		# Common index patterns by table
		if table_name == "users":
			suggestions.extend(
				[
					{"columns": ["email"], "reason": "User authentication and lookups"},
					{"columns": ["created_at"], "reason": "User registration tracking"},
					{"columns": ["updated_at"], "reason": "Recent activity queries"},
				]
			)

		elif table_name == "jobs":
			suggestions.extend(
				[
					{"columns": ["user_id"], "reason": "User job lookups"},
					{"columns": ["status"], "reason": "Job status filtering"},
					{"columns": ["created_at"], "reason": "Date-based sorting"},
					{"columns": ["user_id", "status"], "reason": "Combined user and status queries"},
					{"columns": ["user_id", "created_at"], "reason": "User jobs by date"},
					{"columns": ["company"], "reason": "Company-based searches"},
					{"columns": ["location"], "reason": "Location-based searches"},
				]
			)

		elif table_name == "analytics":
			suggestions.extend(
				[
					{"columns": ["user_id"], "reason": "User analytics lookups"},
					{"columns": ["period"], "reason": "Time-based analytics queries"},
					{"columns": ["user_id", "period"], "reason": "User analytics by period"},
					{"columns": ["generated_at"], "reason": "Analytics generation tracking"},
				]
			)

		# Filter suggestions to only include columns that exist
		valid_suggestions = []
		for suggestion in suggestions:
			if all(col in column_names for col in suggestion["columns"]):
				valid_suggestions.append(suggestion)

		return valid_suggestions

	def _calculate_index_optimization_potential(self, existing: list[Any], missing: list[Any], duplicates: list[Any]) -> float:
		"""Calculate optimization potential (0-100)"""
		potential = 0.0  # Points for missing indexes
		potential += len(missing) * 20

		# Points for duplicate indexes (can be removed)
		potential += len(duplicates) * 10

		# Cap at 100
		return min(100.0, potential)

	def generate_index_creation_sql(self, analysis: IndexAnalysis) -> list[str]:
		"""Generate SQL statements to create missing indexes"""
		sql_statements = []

		for missing_index in analysis.missing_indexes:
			columns_str = ", ".join(missing_index["columns"])
			index_name = f"idx_{analysis.table_name}_{'_'.join(missing_index['columns'])}"

			sql = f"CREATE INDEX {index_name} ON {analysis.table_name} ({columns_str});"
			sql_statements.append(sql)

		return sql_statements

	def benchmark_common_queries(self) -> list[QueryPerformanceMetric]:
		"""Benchmark common application queries"""
		logger.info("Benchmarking common application queries")

		common_queries = [
			# User queries
			("user_by_email", "SELECT * FROM users WHERE email = 'test@example.com'"),
			("user_count", "SELECT COUNT(*) FROM users"),
			("recent_users", "SELECT * FROM users ORDER BY created_at DESC LIMIT 10"),
			# Job queries
			("user_jobs", "SELECT * FROM jobs WHERE user_id = 1 ORDER BY created_at DESC LIMIT 20"),
			("available_jobs", "SELECT * FROM jobs WHERE status = 'not_applied' LIMIT 50"),
			("job_count_by_status", "SELECT status, COUNT(*) FROM jobs GROUP BY status"),
			("jobs_by_company", "SELECT * FROM jobs WHERE company LIKE '%Tech%' LIMIT 10"),
			# Analytics queries
			("user_analytics", "SELECT * FROM analytics WHERE user_id = 1 ORDER BY period DESC LIMIT 5"),
			("analytics_summary", "SELECT COUNT(*) as total_records, MAX(generated_at) as latest FROM analytics"),
			# Complex queries
			(
				"user_job_summary",
				"""
                SELECT u.email, COUNT(j.id) as job_count,
                       COUNT(CASE WHEN j.status = 'applied' THEN 1 END) as applied_count
                FROM users u
                LEFT JOIN jobs j ON u.id = j.user_id
                GROUP BY u.id, u.email
                ORDER BY job_count DESC
                LIMIT 10
            """,
			),
			(
				"recent_activity",
				"""
                SELECT 'job' as type, created_at, user_id FROM jobs
                WHERE created_at > datetime('now', '-7 days')
                UNION ALL
                SELECT 'analytics' as type, generated_at as created_at, user_id FROM analytics
                WHERE generated_at > datetime('now', '-7 days')
                ORDER BY created_at DESC
                LIMIT 20
            """,
			),
		]

		return self.analyze_query_performance(common_queries)

	def optimize_database_configuration(self) -> dict[str, Any]:
		"""Analyze and suggest database configuration optimizations"""
		logger.info("Analyzing database configuration")

		optimizations = {
			"connection_pool": {
				"current_pool_size": getattr(self.engine.pool, "size", "unknown"),
				"current_max_overflow": getattr(self.engine.pool, "max_overflow", "unknown"),
				"recommendations": [],
			},
			"query_cache": {
				"enabled": False,  # SQLite doesn't have query cache
				"recommendations": ["Consider implementing application-level caching with Redis"],
			},
			"indexes": {"total_tables_analyzed": 0, "total_missing_indexes": 0, "total_duplicate_indexes": 0, "recommendations": []},
		}

		# Analyze connection pool
		if hasattr(self.engine.pool, "size"):
			pool_size = self.engine.pool.size()
			pool_recommendations: list[str] = optimizations["connection_pool"]["recommendations"]  # type: ignore[assignment]
			if pool_size < 5:
				pool_recommendations.append("Consider increasing connection pool size for better concurrency")
			elif pool_size > 20:
				pool_recommendations.append("Connection pool size may be too large, consider reducing to save memory")

		# Analyze all tables
		tables = ["users", "jobs", "analytics"]
		total_missing = 0
		total_duplicate = 0

		for table_name in tables:
			if self.inspector.has_table(table_name):
				analysis = self.analyze_table_indexes(table_name)
				self.index_analyses.append(analysis)
				total_missing += len(analysis.missing_indexes)
				total_duplicate += len(analysis.duplicate_indexes)

		optimizations["indexes"]["total_tables_analyzed"] = len(self.index_analyses)
		optimizations["indexes"]["total_missing_indexes"] = total_missing
		optimizations["indexes"]["total_duplicate_indexes"] = total_duplicate

		index_recommendations: list[str] = optimizations["indexes"]["recommendations"]  # type: ignore[assignment]
		if total_missing > 0:
			index_recommendations.append(f"Add {total_missing} missing indexes to improve query performance")

		if total_duplicate > 0:
			index_recommendations.append(f"Remove {total_duplicate} duplicate indexes to save storage space")

		return optimizations

	def run_comprehensive_optimization_analysis(self) -> dict[str, Any]:
		"""Run comprehensive database optimization analysis"""
		logger.info("Starting comprehensive database optimization analysis")

		start_time = time.time()

		# 1. Benchmark common queries
		logger.info("1. Benchmarking common queries...")
		query_metrics = self.benchmark_common_queries()

		# 2. Analyze database configuration
		logger.info("2. Analyzing database configuration...")
		config_analysis = self.optimize_database_configuration()

		# 3. Generate optimization recommendations
		logger.info("3. Generating optimization recommendations...")
		recommendations = self._generate_optimization_recommendations()

		# 4. Calculate overall optimization score
		optimization_score = self._calculate_overall_optimization_score()

		end_time = time.time()
		analysis_duration = end_time - start_time

		# Generate comprehensive report
		report = {
			"summary": {
				"analysis_duration": analysis_duration,
				"queries_analyzed": len(query_metrics),
				"tables_analyzed": len(self.index_analyses),
				"optimization_score": optimization_score,
				"total_recommendations": len(recommendations),
				"critical_issues": len([r for r in recommendations if r.get("priority") == "high"]),
			},
			"query_performance": [asdict(metric) for metric in query_metrics],
			"index_analysis": [asdict(analysis) for analysis in self.index_analyses],
			"configuration_analysis": config_analysis,
			"optimization_recommendations": recommendations,
			"sql_statements": self._generate_all_optimization_sql(),
			"timestamp": datetime.utcnow().isoformat(),
		}

		# Log summary
		logger.info("=" * 60)
		logger.info("DATABASE OPTIMIZATION ANALYSIS COMPLETE")
		logger.info("=" * 60)
		logger.info(f"Analysis Duration: {analysis_duration:.2f}s")
		logger.info(f"Optimization Score: {optimization_score:.1f}/100")
		logger.info(f"Queries Analyzed: {len(query_metrics)}")
		logger.info(f"Tables Analyzed: {len(self.index_analyses)}")
		logger.info(f"Recommendations: {len(recommendations)}")

		return report

	def _generate_optimization_recommendations(self) -> list[dict[str, Any]]:
		"""Generate comprehensive optimization recommendations"""
		recommendations = []

		# Query performance recommendations
		slow_queries = [m for m in self.query_metrics if m.execution_time > 0.1]
		if slow_queries:
			recommendations.append(
				{
					"category": "query_performance",
					"priority": "high",
					"title": f"{len(slow_queries)} Slow Queries Detected",
					"description": f"Queries taking longer than 100ms: {', '.join([q.query_name for q in slow_queries])}",
					"recommendation": "Optimize slow queries by adding indexes, rewriting queries, or implementing caching",
					"impact": "Improved response times and reduced database load",
				}
			)

		# Index recommendations
		total_missing_indexes = sum(len(a.missing_indexes) for a in self.index_analyses)
		if total_missing_indexes > 0:
			recommendations.append(
				{
					"category": "indexing",
					"priority": "high",
					"title": f"{total_missing_indexes} Missing Indexes",
					"description": "Critical indexes are missing for optimal query performance",
					"recommendation": "Create missing indexes using the provided SQL statements",
					"impact": "Significantly faster query execution and better scalability",
				}
			)

		# Duplicate index recommendations
		total_duplicate_indexes = sum(len(a.duplicate_indexes) for a in self.index_analyses)
		if total_duplicate_indexes > 0:
			recommendations.append(
				{
					"category": "indexing",
					"priority": "medium",
					"title": f"{total_duplicate_indexes} Duplicate Indexes",
					"description": "Duplicate indexes are wasting storage space and slowing down writes",
					"recommendation": "Remove duplicate indexes to improve write performance and reduce storage",
					"impact": "Reduced storage usage and faster write operations",
				}
			)

		# Query optimization recommendations
		queries_with_recommendations = [m for m in self.query_metrics if m.recommendations]
		if queries_with_recommendations:
			recommendations.append(
				{
					"category": "query_optimization",
					"priority": "medium",
					"title": "Query Structure Improvements",
					"description": f"{len(queries_with_recommendations)} queries can be optimized",
					"recommendation": "Review and optimize query structures based on specific recommendations",
					"impact": "Better query performance and reduced resource usage",
				}
			)

		# General recommendations
		recommendations.extend(
			[
				{
					"category": "monitoring",
					"priority": "medium",
					"title": "Database Performance Monitoring",
					"description": "Implement continuous database performance monitoring",
					"recommendation": "Set up query performance monitoring and alerting for slow queries",
					"impact": "Proactive identification and resolution of performance issues",
				},
				{
					"category": "maintenance",
					"priority": "low",
					"title": "Regular Database Maintenance",
					"description": "Implement regular database maintenance procedures",
					"recommendation": "Schedule regular VACUUM, ANALYZE, and index maintenance operations",
					"impact": "Consistent database performance over time",
				},
			]
		)

		return recommendations

	def _calculate_overall_optimization_score(self) -> float:
		"""Calculate overall database optimization score (0-100)"""
		score = 100.0

		# Deduct points for slow queries
		slow_queries = [m for m in self.query_metrics if m.execution_time > 0.1]
		score -= len(slow_queries) * 10

		# Deduct points for missing indexes
		total_missing_indexes = sum(len(a.missing_indexes) for a in self.index_analyses)
		score -= total_missing_indexes * 5

		# Deduct points for duplicate indexes
		total_duplicate_indexes = sum(len(a.duplicate_indexes) for a in self.index_analyses)
		score -= total_duplicate_indexes * 3

		# Deduct points for queries with many recommendations
		queries_with_many_recommendations = [m for m in self.query_metrics if len(m.recommendations) > 3]
		score -= len(queries_with_many_recommendations) * 5

		return max(0.0, score)

	def _generate_all_optimization_sql(self) -> dict[str, list[str]]:
		"""Generate all SQL statements for optimization"""
		sql_statements: dict[str, list[str]] = {"create_indexes": [], "drop_duplicate_indexes": [], "analyze_tables": []}

		# Generate index creation SQL
		for analysis in self.index_analyses:
			sql_statements["create_indexes"].extend(self.generate_index_creation_sql(analysis))

		# Generate table analysis SQL
		for analysis in self.index_analyses:
			sql_statements["analyze_tables"].append(f"ANALYZE {analysis.table_name};")

		return sql_statements

	def save_report(self, report: dict[str, Any], filename: str | None = None) -> str:
		"""Save optimization report to file

		Args:
			report: Dictionary containing optimization report data
			filename: Optional filename. If not provided, auto-generates timestamp-based name.
				Path components are stripped for security (prevents path traversal).

		Returns:
			Full path to the saved report file
		"""
		from pathlib import Path

		if filename is None:
			timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
			filename = f"database_optimization_report_{timestamp}.json"

		# Security: Sanitize filename to prevent path traversal attacks (CWE-22)
		# Extract only the filename component, removing any directory paths
		safe_filename = Path(filename).name

		# Additional validation: ensure filename doesn't contain path separators
		if not safe_filename or ".." in safe_filename or "/" in safe_filename or "\\" in safe_filename:
			raise ValueError(f"Invalid filename: {filename}")

		# Ensure write operations stay within current working directory
		output_path = Path.cwd() / safe_filename

	# Verify the resolved path is within the current directory
	if not output_path.resolve().is_relative_to(Path.cwd().resolve()):
		raise ValueError(f"Path traversal attempt detected: {filename}")

	# Path validation complete - safe to write file
	# deepcode ignore PT: Path is validated above via is_relative_to() check
	with open(output_path, "w") as f:
		json.dump(report, f, indent=2, default=str)

	logger.info(f"Database optimization report saved to: {output_path}")
	return str(output_path)


def main() -> None:
	"""Main function to run database optimization"""
	import argparse

	parser = argparse.ArgumentParser(description="Database Optimization Suite")
	parser.add_argument("--output", help="Output report file")
	parser.add_argument("--apply-optimizations", action="store_true", help="Apply recommended optimizations (USE WITH CAUTION)")
	parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

	args = parser.parse_args()

	if args.verbose:
		logging.getLogger().setLevel(logging.DEBUG)

	# Initialize optimizer
	optimizer = DatabaseOptimizer()

	try:
		# Run comprehensive analysis
		report = optimizer.run_comprehensive_optimization_analysis()

		# Save report
		report_file = optimizer.save_report(report, args.output)

		# Apply optimizations if requested
		if args.apply_optimizations:
			logger.warning("Applying database optimizations...")
			sql_statements = report["sql_statements"]["create_indexes"]

			with optimizer.engine.connect() as conn:
				for sql in sql_statements:
					try:
						logger.info(f"Executing: {sql}")
						conn.execute(text(sql))
						conn.commit()
					except Exception as e:
						logger.error(f"Failed to execute {sql}: {e}")

		# Print summary
		print("\n" + "=" * 80)
		print("DATABASE OPTIMIZATION SUMMARY")
		print("=" * 80)
		print(f"Optimization Score: {report['summary']['optimization_score']:.1f}/100")
		print(f"Queries Analyzed: {report['summary']['queries_analyzed']}")
		print(f"Tables Analyzed: {report['summary']['tables_analyzed']}")
		print(f"Recommendations: {report['summary']['total_recommendations']}")
		print(f"Critical Issues: {report['summary']['critical_issues']}")
		print(f"Report saved to: {report_file}")

		# Exit with appropriate code
		if report["summary"]["optimization_score"] >= 80:
			print("\n✅ Database is well optimized!")
			sys.exit(0)
		else:
			print("\n⚠️  Database optimization recommended")
			sys.exit(1)

	except Exception as e:
		logger.error(f"Database optimization failed: {e}")
		sys.exit(1)


if __name__ == "__main__":
	main()
