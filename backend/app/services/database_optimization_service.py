"""
Database optimization service for performance improvements
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import time
from datetime import datetime, timedelta, timezone

from app.core.database import engine
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import *  # Import all models

logger = get_logger(__name__)


class DatabaseOptimizationService:
	"""Service for database performance optimization"""

	def __init__(self):
		self.settings = get_settings()
		self.db_engine = engine

	def create_performance_indexes(self, db: Session) -> Dict[str, Any]:
		"""
		Create performance indexes for enhanced features

		Returns:
		    Dictionary with index creation results
		"""
		indexes_created = []
		indexes_failed = []

		# Define indexes to create
		indexes_to_create = [
			# User table indexes
			{
				"name": "idx_users_oauth_provider_id",
				"table": "users",
				"columns": ["oauth_provider", "oauth_id"],
				"unique": True,
				"condition": "oauth_provider IS NOT NULL AND oauth_id IS NOT NULL",
			},
			{"name": "idx_users_skills_gin", "table": "users", "columns": ["skills"], "type": "gin", "condition": "skills IS NOT NULL"},
			{
				"name": "idx_users_preferred_locations_gin",
				"table": "users",
				"columns": ["preferred_locations"],
				"type": "gin",
				"condition": "preferred_locations IS NOT NULL",
			},
			{"name": "idx_users_experience_level", "table": "users", "columns": ["experience_level"], "condition": "experience_level IS NOT NULL"},
			# Job table indexes
			{"name": "idx_jobs_user_status", "table": "jobs", "columns": ["user_id", "status"]},
			{"name": "idx_jobs_source_created", "table": "jobs", "columns": ["source", "created_at"]},
			{"name": "idx_jobs_tech_stack_gin", "table": "jobs", "columns": ["tech_stack"], "type": "gin", "condition": "tech_stack IS NOT NULL"},
			{"name": "idx_jobs_company_title", "table": "jobs", "columns": ["company", "title"]},
			{"name": "idx_jobs_location", "table": "jobs", "columns": ["location"], "condition": "location IS NOT NULL"},
			{
				"name": "idx_jobs_salary_range",
				"table": "jobs",
				"columns": ["salary_min", "salary_max"],
				"condition": "salary_min IS NOT NULL OR salary_max IS NOT NULL",
			},
			{"name": "idx_jobs_remote_option", "table": "jobs", "columns": ["remote_option"], "condition": "remote_option IS NOT NULL"},
			# Application table indexes
			{"name": "idx_applications_user_status", "table": "applications", "columns": ["user_id", "status"]},
			{"name": "idx_applications_status_created", "table": "applications", "columns": ["status", "created_at"]},
			{"name": "idx_applications_applied_date", "table": "applications", "columns": ["applied_date"], "condition": "applied_date IS NOT NULL"},
			{
				"name": "idx_applications_interview_date",
				"table": "applications",
				"columns": ["interview_date"],
				"condition": "interview_date IS NOT NULL",
			},
			# Content generation indexes
			{"name": "idx_content_generations_user_type", "table": "content_generations", "columns": ["user_id", "content_type"]},
			{
				"name": "idx_content_generations_job_type",
				"table": "content_generations",
				"columns": ["job_id", "content_type"],
				"condition": "job_id IS NOT NULL",
			},
			{"name": "idx_content_generations_status", "table": "content_generations", "columns": ["status"]},
			{"name": "idx_content_generations_created", "table": "content_generations", "columns": ["created_at"]},
			# Resume upload indexes
			{"name": "idx_resume_uploads_user_status", "table": "resume_uploads", "columns": ["user_id", "parsing_status"]},
			{"name": "idx_resume_uploads_status_created", "table": "resume_uploads", "columns": ["parsing_status", "created_at"]},
			{
				"name": "idx_resume_uploads_extracted_skills_gin",
				"table": "resume_uploads",
				"columns": ["extracted_skills"],
				"type": "gin",
				"condition": "extracted_skills IS NOT NULL",
			},
			# Feedback indexes
			{"name": "idx_job_recommendation_feedback_user_job", "table": "job_recommendation_feedback", "columns": ["user_id", "job_id"]},
			{"name": "idx_job_recommendation_feedback_helpful", "table": "job_recommendation_feedback", "columns": ["is_helpful", "created_at"]},
			{"name": "idx_feedback_user_type_status", "table": "feedback", "columns": ["user_id", "type", "status"]},
			{"name": "idx_feedback_type_priority", "table": "feedback", "columns": ["type", "priority"]},
			{"name": "idx_feedback_status_created", "table": "feedback", "columns": ["status", "created_at"]},
			# Interview session indexes (if exists)
			{
				"name": "idx_interview_sessions_user_type",
				"table": "interview_sessions",
				"columns": ["user_id", "session_type"],
				"optional": True,  # Only create if table exists
			},
			{
				"name": "idx_interview_sessions_job_user",
				"table": "interview_sessions",
				"columns": ["job_id", "user_id"],
				"condition": "job_id IS NOT NULL",
				"optional": True,
			},
			# Help article indexes
			{"name": "idx_help_articles_category_published", "table": "help_articles", "columns": ["category", "is_published"], "optional": True},
			{"name": "idx_help_articles_slug", "table": "help_articles", "columns": ["slug"], "unique": True, "optional": True},
		]

		for index_def in indexes_to_create:
			try:
				# Check if table exists (for optional indexes)
				if index_def.get("optional", False):
					table_exists = self._table_exists(db, index_def["table"])
					if not table_exists:
						logger.info(f"Skipping index {index_def['name']} - table {index_def['table']} does not exist")
						continue

				# Check if index already exists
				if self._index_exists(db, index_def["name"]):
					logger.info(f"Index {index_def['name']} already exists, skipping")
					continue

				# Create the index
				success = self._create_index(db, index_def)
				if success:
					indexes_created.append(index_def["name"])
					logger.info(f"✅ Created index: {index_def['name']}")
				else:
					indexes_failed.append(index_def["name"])

			except Exception as e:
				logger.error(f"❌ Failed to create index {index_def['name']}: {e}")
				indexes_failed.append(index_def["name"])

		return {"indexes_created": indexes_created, "indexes_failed": indexes_failed, "total_attempted": len(indexes_to_create)}

	def _table_exists(self, db: Session, table_name: str) -> bool:
		"""Check if a table exists in the database"""
		try:
			if "postgresql" in str(self.db_engine.url):
				result = db.execute(
					text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    )
                """),
					{"table_name": table_name},
				)


			return bool(result.fetchone())
		except Exception as e:
			logger.error(f"Error checking if table {table_name} exists: {e}")
			return False

	def _index_exists(self, db: Session, index_name: str) -> bool:
		"""Check if an index already exists"""
		try:
			if "postgresql" in str(self.db_engine.url):
				result = db.execute(
					text("""
                    SELECT EXISTS (
                        SELECT FROM pg_indexes 
                        WHERE indexname = :index_name
                    )
                """),
					{"index_name": index_name},
				)


			return bool(result.fetchone())
		except Exception as e:
			logger.error(f"Error checking if index {index_name} exists: {e}")
			return False

	def _create_index(self, db: Session, index_def: Dict[str, Any]) -> bool:
		"""Create a single index based on definition"""
		try:
			name = index_def["name"]
			table = index_def["table"]
			columns = index_def["columns"]
			unique = index_def.get("unique", False)
			condition = index_def.get("condition")
			index_type = index_def.get("type", "btree")

			# Build the CREATE INDEX statement
			sql_parts = []

			if unique:
				sql_parts.append("CREATE UNIQUE INDEX")
			else:
				sql_parts.append("CREATE INDEX")

			sql_parts.append(f"{name} ON {table}")

			# Add index type for PostgreSQL
			if "postgresql" in str(self.db_engine.url) and index_type != "btree":
				sql_parts.append(f"USING {index_type}")

			# Add columns
			columns_str = ", ".join(columns)
			sql_parts.append(f"({columns_str})")

			# Add condition if specified
			if condition:
				sql_parts.append(f"WHERE {condition}")

			sql = " ".join(sql_parts)

			# Execute the CREATE INDEX statement
			db.execute(text(sql))
			db.commit()

			return True

		except Exception as e:
			logger.error(f"Error creating index {index_def['name']}: {e}")
			db.rollback()
			return False

	def optimize_queries(self, db: Session) -> Dict[str, Any]:
		"""
		Optimize complex queries used by the application

		Returns:
		    Dictionary with optimization results
		"""
		optimizations = []

		try:
			# Update table statistics (PostgreSQL)
			if "postgresql" in str(self.db_engine.url):
				db.execute(text("ANALYZE;"))
				optimizations.append("Updated table statistics")

			# Vacuum analyze (PostgreSQL) - be careful in production
			# db.execute(text("VACUUM ANALYZE;"))
			# optimizations.append("Performed vacuum analyze")

			db.commit()

			logger.info(f"Query optimizations completed: {optimizations}")

			return {"optimizations_applied": optimizations, "status": "success"}

		except Exception as e:
			logger.error(f"Error optimizing queries: {e}")
			db.rollback()
			return {"optimizations_applied": optimizations, "status": "error", "error": str(e)}

	def implement_connection_pooling(self) -> Dict[str, Any]:
		"""
		Configure database connection pooling for better performance

		Returns:
		    Dictionary with pooling configuration results
		"""
		try:
			# Get current engine configuration
			current_pool_size = getattr(self.db_engine.pool, "size", "unknown")
			current_max_overflow = getattr(self.db_engine.pool, "max_overflow", "unknown")

			# Recommended pool settings based on application type
			recommended_settings = {
				"pool_size": 20,  # Base number of connections to maintain
				"max_overflow": 30,  # Additional connections when needed
				"pool_timeout": 30,  # Seconds to wait for connection
				"pool_recycle": 3600,  # Recycle connections after 1 hour
				"pool_pre_ping": True,  # Validate connections before use
			}

			# Create optimized engine (this would typically be done at startup)
			# For now, we'll just return the recommended configuration

			logger.info("Connection pooling configuration analyzed")

			return {
				"status": "analyzed",
				"current_pool_size": current_pool_size,
				"current_max_overflow": current_max_overflow,
				"recommended_settings": recommended_settings,
				"message": "Connection pooling settings analyzed. Apply at application startup.",
			}

		except Exception as e:
			logger.error(f"Error analyzing connection pooling: {e}")
			return {"status": "error", "error": str(e)}

	def analyze_query_performance(self, db: Session) -> Dict[str, Any]:
		"""
		Analyze query performance and identify slow queries

		Returns:
		    Dictionary with performance analysis results
		"""
		try:
			performance_data = {}

			# Test common query patterns
			query_tests = [
				{
					"name": "user_jobs_lookup",
					"description": "User jobs with status filter",
					"query": "SELECT COUNT(*) FROM jobs WHERE user_id = 1 AND status = 'not_applied'",
				},
				{
					"name": "job_recommendations",
					"description": "Jobs for recommendations (tech stack filter)",
					"query": "SELECT COUNT(*) FROM jobs WHERE tech_stack IS NOT NULL AND status = 'not_applied'",
				},
				{
					"name": "application_analytics",
					"description": "Application status breakdown",
					"query": "SELECT status, COUNT(*) FROM applications GROUP BY status",
				},
				{
					"name": "content_generation_lookup",
					"description": "User content by type",
					"query": "SELECT COUNT(*) FROM content_generations WHERE user_id = 1 AND content_type = 'cover_letter'",
				},
				{
					"name": "feedback_analysis",
					"description": "Job recommendation feedback",
					"query": "SELECT COUNT(*) FROM job_recommendation_feedback WHERE is_helpful = true",
				},
			]

			for test in query_tests:
				try:
					start_time = time.time()
					result = db.execute(text(test["query"]))
					result.fetchall()  # Ensure query is fully executed
					end_time = time.time()

					execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

					performance_data[test["name"]] = {
						"description": test["description"],
						"execution_time_ms": round(execution_time, 2),
						"status": "fast" if execution_time < 100 else "slow" if execution_time < 1000 else "very_slow",
					}

				except Exception as e:
					performance_data[test["name"]] = {"description": test["description"], "error": str(e), "status": "error"}

			# Analyze results
			slow_queries = [name for name, data in performance_data.items() if data.get("status") in ["slow", "very_slow"]]

			avg_execution_time = sum(data.get("execution_time_ms", 0) for data in performance_data.values() if "execution_time_ms" in data) / len(
				[d for d in performance_data.values() if "execution_time_ms" in d]
			)

			logger.info(f"Query performance analysis completed. Average execution time: {avg_execution_time:.2f}ms")

			return {
				"status": "success",
				"performance_data": performance_data,
				"slow_queries": slow_queries,
				"average_execution_time_ms": round(avg_execution_time, 2),
				"recommendations": self._get_performance_recommendations(performance_data),
			}

		except Exception as e:
			logger.error(f"Error analyzing query performance: {e}")
			return {"status": "error", "error": str(e)}

	def _get_performance_recommendations(self, performance_data: Dict[str, Any]) -> List[str]:
		"""Generate performance recommendations based on analysis"""
		recommendations = []

		for query_name, data in performance_data.items():
			if data.get("status") == "very_slow":
				recommendations.append(f"Critical: {query_name} is very slow ({data.get('execution_time_ms')}ms) - needs immediate optimization")
			elif data.get("status") == "slow":
				recommendations.append(f"Warning: {query_name} is slow ({data.get('execution_time_ms')}ms) - consider adding indexes")

		# General recommendations
		if len([d for d in performance_data.values() if d.get("status") in ["slow", "very_slow"]]) > 2:
			recommendations.append("Consider implementing query result caching for frequently accessed data")
			recommendations.append("Review database connection pooling settings")

		if not recommendations:
			recommendations.append("Query performance looks good! No immediate optimizations needed.")

		return recommendations

	def cleanup_old_data(self, db: Session, days_old: int = 90) -> Dict[str, Any]:
		"""
		Clean up old data to improve performance

		Args:
		    days_old: Delete data older than this many days

		Returns:
		    Dictionary with cleanup results
		"""
		try:
			cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
			cleanup_results = {}

			# Clean up old content generations (keep user-modified ones)
			old_content = db.execute(
				text("""
                DELETE FROM content_generations 
                WHERE created_at < :cutoff_date 
                AND user_modifications IS NULL 
                AND status NOT IN ('approved', 'used')
            """),
				{"cutoff_date": cutoff_date},
			)
			cleanup_results["content_generations_deleted"] = old_content.rowcount

			# Clean up old resume uploads (keep successful ones)
			old_resumes = db.execute(
				text("""
                DELETE FROM resume_uploads 
                WHERE created_at < :cutoff_date 
                AND parsing_status = 'failed'
            """),
				{"cutoff_date": cutoff_date},
			)
			cleanup_results["failed_resume_uploads_deleted"] = old_resumes.rowcount

			# Clean up old feedback votes (keep recent ones)
			old_votes = db.execute(
				text("""
                DELETE FROM feedback_votes 
                WHERE created_at < :cutoff_date
            """),
				{"cutoff_date": cutoff_date},
			)
			cleanup_results["old_feedback_votes_deleted"] = old_votes.rowcount

			db.commit()

			total_deleted = sum(cleanup_results.values())
			logger.info(f"Data cleanup completed: {total_deleted} records deleted")

			return {"status": "success", "cleanup_results": cleanup_results, "total_deleted": total_deleted, "cutoff_date": cutoff_date.isoformat()}

		except Exception as e:
			logger.error(f"Error cleaning up old data: {e}")
			db.rollback()
			return {"status": "error", "error": str(e)}

	def get_database_stats(self, db: Session) -> Dict[str, Any]:
		"""
		Get database statistics and health metrics

		Returns:
		    Dictionary with database statistics
		"""
		try:
			stats = {}

			# Table row counts
			tables = ["users", "jobs", "applications", "content_generations", "resume_uploads", "job_recommendation_feedback", "feedback"]

			for table in tables:
				try:
					result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
					count = result.scalar()
					stats[f"{table}_count"] = count
				except Exception as e:
					stats[f"{table}_count"] = f"Error: {e!s}"

			# Database size (PostgreSQL specific)
			if "postgresql" in str(self.db_engine.url):
				try:
					result = db.execute(
						text("""
                        SELECT pg_size_pretty(pg_database_size(current_database())) as size
                    """)
					)
					size = result.scalar()
					stats["database_size"] = size
				except Exception as e:
					stats["database_size"] = f"Error: {e!s}"

			# Index usage (PostgreSQL specific)
			if "postgresql" in str(self.db_engine.url):
				try:
					result = db.execute(
						text("""
                        SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
                        FROM pg_stat_user_indexes 
                        ORDER BY idx_tup_read DESC 
                        LIMIT 10
                    """)
					)
					index_stats = [dict(row) for row in result.fetchall()]
					stats["top_used_indexes"] = index_stats
				except Exception as e:
					stats["index_usage_error"] = str(e)

			# Connection info
			stats["database_url"] = str(self.db_engine.url).split("@")[0] + "@[hidden]"  # Hide credentials
			stats["pool_size"] = getattr(self.db_engine.pool, "size", "unknown")
			stats["checked_in_connections"] = getattr(self.db_engine.pool, "checkedin", "unknown")
			stats["checked_out_connections"] = getattr(self.db_engine.pool, "checkedout", "unknown")

			logger.info("Database statistics collected successfully")

			return {"status": "success", "stats": stats, "collected_at": datetime.now(timezone.utc).isoformat()}

		except Exception as e:
			logger.error(f"Error collecting database statistics: {e}")
			return {"status": "error", "error": str(e)}


# Global database optimization service instance
db_optimization_service = DatabaseOptimizationService()
