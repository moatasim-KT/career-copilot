"""
Unified Analytics Tasks Module
Consolidates analytics task scheduling and execution functionality
"""

from typing import Dict, Any
import traceback
from datetime import datetime, timedelta, timezone

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.core.logging import get_logger
from app.services.cache_service import get_cache_service
from app.services.analytics_service import analytics_service

logger = get_logger(__name__)
cache_service = get_cache_service()


# ============================================================================
# CORE ANALYTICS TASKS (from original analytics_tasks.py)
# ============================================================================


@celery_app.task(name="app.tasks.analytics_tasks.cleanup_expired_tasks")
def cleanup_expired_tasks():
	"""
	Clean up expired Celery task results and cache entries
	"""
	try:
		cleaned_cache_entries = 0

		# Clean up expired cache entries
		if cache_service.enabled:
			# Get cache statistics before cleanup
			stats_before = cache_service.get_cache_stats()

			# Clean up old LLM responses (older than 7 days)
			cutoff_timestamp = (datetime.now(timezone.utc) - timedelta(days=7)).timestamp()

			# This is a simplified cleanup - in production you might want more sophisticated logic
			patterns_to_clean = ["llm_response:*", "resume_parsing:*", "job_description:*", "interview_questions:*", "interview_feedback:*"]

			for pattern in patterns_to_clean:
				try:
					deleted = cache_service.delete_pattern(pattern)
					cleaned_cache_entries += deleted
				except Exception as e:
					logger.error(f"Error cleaning cache pattern {pattern}: {e}")

			# Get cache statistics after cleanup
			stats_after = cache_service.get_cache_stats()

			logger.info(f"Cache cleanup completed: {cleaned_cache_entries} entries removed")
			logger.info(f"Memory usage: {stats_before.get('used_memory', 'unknown')} -> {stats_after.get('used_memory', 'unknown')}")

		return {"status": "success", "cleaned_cache_entries": cleaned_cache_entries, "message": "Cleanup completed successfully"}

	except Exception as e:
		logger.error(f"Error in cleanup task: {e}")
		logger.error(f"Traceback: {traceback.format_exc()}")
		return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.analytics_tasks.generate_user_analytics")
def generate_user_analytics(user_id: int) -> Dict[str, Any]:
	"""
	Generate comprehensive analytics for a specific user

	Args:
	    user_id: ID of the user to generate analytics for

	Returns:
	    Dictionary with analytics results
	"""
	db = next(get_db())

	try:
		from app.models.user import User
		from app.models.job import Job
		from app.models.application import Application
		from app.models.content_generation import ContentGeneration
		from app.models.resume_upload import ResumeUpload
		from sqlalchemy import func

		# Get user
		user = db.query(User).filter(User.id == user_id).first()
		if not user:
			raise ValueError(f"User {user_id} not found")

		# Calculate various metrics
		analytics = {}

		# Job metrics
		total_jobs = db.query(func.count(Job.id)).filter(Job.user_id == user_id).scalar()
		analytics["total_jobs"] = total_jobs

		# Application metrics
		total_applications = db.query(func.count(Application.id)).filter(Application.user_id == user_id).scalar()
		analytics["total_applications"] = total_applications

		# Application status breakdown
		status_breakdown = (
			db.query(Application.status, func.count(Application.id)).filter(Application.user_id == user_id).group_by(Application.status).all()
		)

		analytics["application_status_breakdown"] = {status: count for status, count in status_breakdown}

		# Content generation metrics
		content_generated = db.query(func.count(ContentGeneration.id)).filter(ContentGeneration.user_id == user_id).scalar()
		analytics["content_generated"] = content_generated

		# Resume uploads
		resume_uploads = db.query(func.count(ResumeUpload.id)).filter(ResumeUpload.user_id == user_id).scalar()
		analytics["resume_uploads"] = resume_uploads

		# Activity timeline (last 30 days)
		thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

		recent_jobs = db.query(func.count(Job.id)).filter(Job.user_id == user_id, Job.created_at >= thirty_days_ago).scalar()

		recent_applications = (
			db.query(func.count(Application.id)).filter(Application.user_id == user_id, Application.created_at >= thirty_days_ago).scalar()
		)

		analytics["recent_activity"] = {"jobs_added": recent_jobs, "applications_submitted": recent_applications}

		# Success rates
		if total_applications > 0:
			interviews = (
				db.query(func.count(Application.id))
				.filter(Application.user_id == user_id, Application.status.in_(["interview", "offer", "accepted"]))
				.scalar()
			)

			offers = (
				db.query(func.count(Application.id)).filter(Application.user_id == user_id, Application.status.in_(["offer", "accepted"])).scalar()
			)

			analytics["success_rates"] = {
				"interview_rate": (interviews / total_applications) * 100,
				"offer_rate": (offers / total_applications) * 100,
			}
		else:
			analytics["success_rates"] = {"interview_rate": 0, "offer_rate": 0}

		# Cache the analytics
		cache_key = f"user_analytics:{user_id}"
		cache_service.set(cache_key, analytics, ttl=3600)  # Cache for 1 hour

		logger.info(f"Generated analytics for user {user_id}")

		return {"status": "success", "user_id": user_id, "analytics": analytics, "generated_at": datetime.now(timezone.utc).isoformat()}

	except Exception as e:
		logger.error(f"Error generating analytics for user {user_id}: {e}")
		logger.error(f"Traceback: {traceback.format_exc()}")
		raise

	finally:
		db.close()


@celery_app.task(name="app.tasks.analytics_tasks.generate_system_analytics")
def generate_system_analytics() -> Dict[str, Any]:
	"""
	Generate system-wide analytics and health metrics

	Returns:
	    Dictionary with system analytics
	"""
	db = next(get_db())

	try:
		from app.models.user import User
		from app.models.job import Job
		from app.models.application import Application
		from app.models.content_generation import ContentGeneration
		from app.models.resume_upload import ResumeUpload
		from sqlalchemy import func

		analytics = {}

		# User metrics
		total_users = db.query(func.count(User.id)).scalar()
		active_users = (
			db.query(func.count(User.id)).filter(User.last_login >= datetime.now(timezone.utc) - timedelta(days=30)).scalar()
			if hasattr(User, "last_login")
			else total_users
		)

		analytics["users"] = {"total": total_users, "active_30_days": active_users}

		# Job metrics
		total_jobs = db.query(func.count(Job.id)).scalar()
		jobs_last_week = db.query(func.count(Job.id)).filter(Job.created_at >= datetime.now(timezone.utc) - timedelta(days=7)).scalar()

		analytics["jobs"] = {"total": total_jobs, "added_last_week": jobs_last_week}

		# Application metrics
		total_applications = db.query(func.count(Application.id)).scalar()
		applications_last_week = (
			db.query(func.count(Application.id)).filter(Application.created_at >= datetime.now(timezone.utc) - timedelta(days=7)).scalar()
		)

		analytics["applications"] = {"total": total_applications, "submitted_last_week": applications_last_week}

		# Content generation metrics
		total_content = db.query(func.count(ContentGeneration.id)).scalar()
		content_last_week = (
			db.query(func.count(ContentGeneration.id)).filter(ContentGeneration.created_at >= datetime.now(timezone.utc) - timedelta(days=7)).scalar()
		)

		analytics["content_generation"] = {"total": total_content, "generated_last_week": content_last_week}

		# Resume processing metrics
		total_resumes = db.query(func.count(ResumeUpload.id)).scalar()
		successful_parses = db.query(func.count(ResumeUpload.id)).filter(ResumeUpload.parsing_status == "completed").scalar()

		analytics["resume_processing"] = {
			"total_uploads": total_resumes,
			"successful_parses": successful_parses,
			"success_rate": (successful_parses / total_resumes * 100) if total_resumes > 0 else 0,
		}

		# Cache statistics
		if cache_service.enabled:
			cache_stats = cache_service.get_cache_stats()
			analytics["cache"] = cache_stats

		# System health
		analytics["system_health"] = {
			"database_connected": True,  # If we got this far, DB is connected
			"cache_enabled": cache_service.enabled,
			"generated_at": datetime.now(timezone.utc).isoformat(),
		}

		# Cache the system analytics
		cache_service.set("system_analytics", analytics, ttl=1800)  # Cache for 30 minutes

		logger.info("Generated system analytics")

		return {"status": "success", "analytics": analytics}

	except Exception as e:
		logger.error(f"Error generating system analytics: {e}")
		logger.error(f"Traceback: {traceback.format_exc()}")
		raise

	finally:
		db.close()


@celery_app.task(name="app.tasks.analytics_tasks.optimize_database")
def optimize_database():
	"""
	Perform database optimization tasks
	"""
	db = next(get_db())

	try:
		optimizations_performed = []

		# Analyze table statistics (PostgreSQL specific)
		try:
			db.execute("ANALYZE;")
			optimizations_performed.append("Table statistics updated")
		except Exception as e:
			logger.warning(f"Could not run ANALYZE: {e}")

		# Clean up old sessions or temporary data
		# This is database-specific and should be customized

		# Vacuum (PostgreSQL) or optimize (MySQL) - be careful with this in production
		# db.execute("VACUUM;")  # Uncomment if using PostgreSQL and want to vacuum

		db.commit()

		logger.info(f"Database optimization completed: {optimizations_performed}")

		return {"status": "success", "optimizations": optimizations_performed, "completed_at": datetime.now(timezone.utc).isoformat()}

	except Exception as e:
		logger.error(f"Error optimizing database: {e}")
		return {"status": "error", "message": str(e)}

	finally:
		db.close()


@celery_app.task(bind=True, name="app.tasks.analytics_tasks.generate_batch_analytics")
def generate_batch_analytics(self, user_ids: list) -> Dict[str, Any]:
	"""
	Generate analytics for multiple users in batch

	Args:
	    user_ids: List of user IDs to generate analytics for

	Returns:
	    Dictionary with batch analytics results
	"""
	try:
		total_users = len(user_ids)
		processed = 0
		successful = 0
		failed = 0

		for i, user_id in enumerate(user_ids):
			try:
				# Update progress
				self.update_state(
					state="PROGRESS",
					meta={
						"current": i + 1,
						"total": total_users,
						"status": f"Processing user {i + 1} of {total_users}",
						"successful": successful,
						"failed": failed,
					},
				)

				# Generate analytics for this user
				result = generate_user_analytics.delay(user_id)

				# Wait for result (with timeout)
				try:
					result.get(timeout=60)  # 1 minute timeout per user
					successful += 1
				except Exception as e:
					logger.error(f"Batch analytics failed for user {user_id}: {e}")
					failed += 1

				processed += 1

			except Exception as e:
				logger.error(f"Error in batch processing user {user_id}: {e}")
				failed += 1
				processed += 1

		self.update_state(
			state="SUCCESS",
			meta={"current": total_users, "total": total_users, "status": "Batch analytics completed", "successful": successful, "failed": failed},
		)

		logger.info(f"Batch analytics completed: {successful} successful, {failed} failed")

		return {"status": "success", "total": total_users, "processed": processed, "successful": successful, "failed": failed}

	except Exception as e:
		logger.error(f"Error in batch analytics generation: {e}")

		self.update_state(state="FAILURE", meta={"status": f"Batch processing failed: {e!s}"})

		raise


# ============================================================================
# SCHEDULED ANALYTICS COLLECTION TASKS (from analytics_collection_tasks.py)
# ============================================================================


@celery_app.task(name="collect_daily_analytics")
def collect_daily_analytics():
	"""Daily task to collect analytics data for all active users"""
	logger.info("Starting daily analytics collection")

	db = next(get_db())
	try:
		from app.models.user import User

		# Get all active users
		active_users = db.query(User).filter(User.is_active == True).all()

		results = {"processed_users": 0, "successful_collections": 0, "failed_collections": 0, "errors": []}

		for user in active_users:
			try:
				# Create analytics service instance with database session
				analytics_service_instance = analytics_service.__class__(db=db)

				# Collect user engagement metrics
				engagement_result = analytics_service_instance.collect_user_engagement_metrics(
					user.id,
					days=7,  # Weekly engagement
				)

				# Monitor application success rates
				success_result = analytics_service_instance.monitor_application_success_rates(
					user.id,
					days=30,  # Monthly success monitoring
				)

				# Analyze market trends (only for users with recent activity)
				last_active = user.last_active or user.created_at
				if last_active >= datetime.now(timezone.utc) - timedelta(days=7):
					market_result = analytics_service_instance.analyze_market_trends(
						user.id,
						days=7,  # Weekly market analysis
					)

				results["successful_collections"] += 1
				logger.info(f"Successfully collected analytics for user {user.id}")

			except Exception as e:
				results["failed_collections"] += 1
				error_msg = f"Failed to collect analytics for user {user.id}: {e!s}"
				results["errors"].append(error_msg)
				logger.error(error_msg)

			results["processed_users"] += 1

		logger.info(f"Daily analytics collection completed: {results}")
		return results

	except Exception as e:
		logger.error(f"Daily analytics collection failed: {e}")
		return {"error": str(e)}
	finally:
		db.close()


@celery_app.task(name="generate_weekly_analytics_reports")
def generate_weekly_analytics_reports():
	"""Weekly task to generate comprehensive analytics reports"""
	logger.info("Starting weekly analytics report generation")

	db = next(get_db())
	try:
		from app.models.user import User

		# Get users who have been active in the last week
		cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
		active_users = db.query(User).filter(User.is_active == True, User.last_active >= cutoff_date).all()

		results = {"processed_users": 0, "successful_reports": 0, "failed_reports": 0, "errors": []}

		for user in active_users:
			try:
				# Create analytics service instance with database session
				analytics_service_instance = analytics_service.__class__(db=db)

				# Generate comprehensive analytics report
				report = analytics_service_instance.get_comprehensive_analytics_report(
					user.id,
					days=90,  # 3-month comprehensive report
				)

				if "error" not in report:
					results["successful_reports"] += 1
					logger.info(f"Successfully generated weekly report for user {user.id}")
				else:
					results["failed_reports"] += 1
					results["errors"].append(f"Report generation failed for user {user.id}: {report['error']}")

			except Exception as e:
				results["failed_reports"] += 1
				error_msg = f"Failed to generate report for user {user.id}: {e!s}"
				results["errors"].append(error_msg)
				logger.error(error_msg)

			results["processed_users"] += 1

		logger.info(f"Weekly analytics report generation completed: {results}")
		return results

	except Exception as e:
		logger.error(f"Weekly analytics report generation failed: {e}")
		return {"error": str(e)}
	finally:
		db.close()


@celery_app.task(name="analyze_market_trends_global")
def analyze_market_trends_global():
	"""Daily task to analyze global market trends across all job data"""
	logger.info("Starting global market trends analysis")

	db = next(get_db())
	try:
		# Use a system user ID (0) for global market analysis
		system_user_id = 0

		# Create analytics service instance with database session
		analytics_service_instance = analytics_service.__class__(db=db)

		# Analyze market trends with extended period for better insights
		market_analysis = analytics_service_instance.analyze_market_trends(system_user_id, days=30)

		if "error" not in market_analysis:
			logger.info("Successfully completed global market trends analysis")

			# Extract key insights for logging
			total_jobs = market_analysis.get("total_jobs_analyzed", 0)
			growth_rate = market_analysis.get("growth_metrics", {}).get("growth_rate_percentage", 0)
			top_skills = list(market_analysis.get("skill_demand", {}).get("top_skills", {}).keys())[:5]

			logger.info(f"Market analysis summary: {total_jobs} jobs analyzed, {growth_rate}% growth rate, top skills: {top_skills}")

			return {
				"success": True,
				"total_jobs_analyzed": total_jobs,
				"growth_rate": growth_rate,
				"top_skills": top_skills,
				"analysis_date": market_analysis.get("analysis_date"),
			}
		else:
			logger.error(f"Global market trends analysis failed: {market_analysis['error']}")
			return {"error": market_analysis["error"]}

	except Exception as e:
		logger.error(f"Global market trends analysis failed: {e}")
		return {"error": str(e)}
	finally:
		db.close()


@celery_app.task(name="cleanup_old_analytics_data")
def cleanup_old_analytics_data(retention_days: int = 365):
	"""Task to cleanup old analytics data to manage database size"""
	logger.info(f"Starting analytics data cleanup (retention: {retention_days} days)")

	db = next(get_db())
	try:
		from app.models.analytics import Analytics

		cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

		# Count records to be deleted
		old_records_count = db.query(Analytics).filter(Analytics.generated_at < cutoff_date).count()

		if old_records_count > 0:
			# Delete old analytics records
			deleted_count = db.query(Analytics).filter(Analytics.generated_at < cutoff_date).delete()

			db.commit()

			logger.info(f"Cleaned up {deleted_count} old analytics records")
			return {"success": True, "deleted_records": deleted_count, "cutoff_date": cutoff_date.isoformat()}
		else:
			logger.info("No old analytics records found for cleanup")
			return {"success": True, "deleted_records": 0, "message": "No records to cleanup"}

	except Exception as e:
		logger.error(f"Analytics data cleanup failed: {e}")
		db.rollback()
		return {"error": str(e)}
	finally:
		db.close()


@celery_app.task(name="generate_analytics_summary_report")
def generate_analytics_summary_report():
	"""Generate system-wide analytics summary report"""
	logger.info("Starting analytics summary report generation")

	db = next(get_db())
	try:
		from app.models.analytics import Analytics
		from app.models.user import User

		# Get analytics data from the last 30 days
		cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

		# Count analytics records by type
		analytics_counts = (
			db.query(Analytics.type, db.func.count(Analytics.id).label("count"))
			.filter(Analytics.generated_at >= cutoff_date)
			.group_by(Analytics.type)
			.all()
		)

		# Get total active users
		active_users_count = db.query(User).filter(User.is_active == True, User.last_active >= cutoff_date).count()

		# Calculate analytics coverage
		users_with_analytics = db.query(Analytics.user_id).filter(Analytics.generated_at >= cutoff_date).distinct().count()

		coverage_percentage = (users_with_analytics / active_users_count * 100) if active_users_count > 0 else 0

		summary_report = {
			"generated_at": datetime.now(timezone.utc).isoformat(),
			"period_days": 30,
			"active_users": active_users_count,
			"users_with_analytics": users_with_analytics,
			"analytics_coverage_percentage": round(coverage_percentage, 1),
			"analytics_by_type": {row.type: row.count for row in analytics_counts},
			"total_analytics_records": sum(row.count for row in analytics_counts),
		}

		logger.info(f"Analytics summary report generated: {summary_report}")
		return summary_report

	except Exception as e:
		logger.error(f"Analytics summary report generation failed: {e}")
		return {"error": str(e)}
	finally:
		db.close()


# ============================================================================
# CELERY BEAT SCHEDULE CONFIGURATION
# ============================================================================

# Celery beat schedule configuration (add this to your main Celery config)
ANALYTICS_CELERY_BEAT_SCHEDULE = {
	"collect-daily-analytics": {
		"task": "collect_daily_analytics",
		"schedule": 3600.0 * 24,  # Daily at midnight
	},
	"generate-weekly-analytics-reports": {
		"task": "generate_weekly_analytics_reports",
		"schedule": 3600.0 * 24 * 7,  # Weekly on Sunday
	},
	"analyze-market-trends-global": {
		"task": "analyze_market_trends_global",
		"schedule": 3600.0 * 24,  # Daily
	},
	"cleanup-old-analytics-data": {
		"task": "cleanup_old_analytics_data",
		"schedule": 3600.0 * 24 * 7,  # Weekly cleanup
		"kwargs": {"retention_days": 365},
	},
	"generate-analytics-summary-report": {
		"task": "generate_analytics_summary_report",
		"schedule": 3600.0 * 24,  # Daily summary
	},
}
