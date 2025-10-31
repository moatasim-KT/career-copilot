"""
Enhanced Celery tasks for recommendation generation and caching system
"""

import logging
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.cache_service import get_recommendation_cache_service

recommendation_cache_service = get_recommendation_cache_service()
from app.celery import celery_app

# Configure logging
logger = logging.getLogger(__name__)


@celery_app.task(name="generate_daily_recommendations", bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 60})
def generate_daily_recommendations(self):
	"""
	Enhanced daily recommendation generation task (7:30 AM)
	- Generates personalized recommendations for all active users
	- Implements intelligent caching and performance tracking
	- Provides detailed metrics and error handling
	"""
	db = next(get_db())
	task_start_time = datetime.now()

	try:
		from app.models.user import User
		from app.models.analytics import Analytics

		# Get all active users
		users = db.query(User).filter(User.is_active == True).all()
		logger.info(f"Starting daily recommendation generation for {len(users)} users")

		results = {
			"total_users": len(users),
			"successful_generations": 0,
			"failed_generations": 0,
			"cache_hits": 0,
			"cache_misses": 0,
			"performance_metrics": {},
			"errors": [],
			"execution_time_seconds": 0,
		}

		for user in users:
			user_start_time = datetime.now()

			try:
				# Check if user has recent activity (jobs added in last 7 days)
				from app.models.job import Job

				recent_jobs = db.query(Job).filter(Job.user_id == user.id, Job.created_at >= datetime.now() - timedelta(days=7)).count()

				# Generate recommendations with enhanced parameters
				recommendations = recommendation_cache_service.generate_and_cache_recommendations(
					db, user.id, force_refresh=True, include_performance_data=True
				)

				if recommendations:
					results["successful_generations"] += 1

					# Track generation metrics
					generation_time = (datetime.now() - user_start_time).total_seconds()

					# Store detailed metrics
					metrics_data = {
						"user_id": user.id,
						"recommendations_count": len(recommendations),
						"generation_time_seconds": generation_time,
						"recent_jobs_count": recent_jobs,
						"average_score": sum(r.get("overall_score", 0) for r in recommendations) / len(recommendations) if recommendations else 0,
						"high_quality_count": len([r for r in recommendations if r.get("overall_score", 0) >= 0.7]),
						"generated_at": datetime.now().isoformat(),
					}

					# Save generation metrics
					analytics = Analytics(user_id=user.id, type="recommendation_generation_metrics", data=metrics_data)
					db.add(analytics)

					logger.info(f"Generated {len(recommendations)} recommendations for user {user.id} in {generation_time:.2f}s")

				else:
					results["failed_generations"] += 1
					logger.warning(f"No recommendations generated for user {user.id}")

			except Exception as e:
				results["failed_generations"] += 1
				error_msg = f"Failed to generate recommendations for user {user.id}: {e!s}"
				results["errors"].append(error_msg)
				logger.error(error_msg)

				# Track failed generation
				error_data = {"user_id": user.id, "error": str(e), "error_type": type(e).__name__, "timestamp": datetime.now().isoformat()}

				analytics = Analytics(user_id=user.id, type="recommendation_generation_error", data=error_data)
				db.add(analytics)

		# Calculate overall performance metrics
		total_time = (datetime.now() - task_start_time).total_seconds()
		results["execution_time_seconds"] = total_time
		results["average_time_per_user"] = total_time / len(users) if users else 0
		results["success_rate"] = results["successful_generations"] / len(users) if users else 0

		# Store task-level metrics
		task_metrics = Analytics(
			user_id=None,  # System-level metric
			type="daily_recommendation_task_metrics",
			data=results,
		)
		db.add(task_metrics)
		db.commit()

		logger.info(f"Daily recommendation generation completed: {results['successful_generations']}/{len(users)} successful in {total_time:.2f}s")

		return results

	except Exception as e:
		logger.error(f"Critical error in daily recommendation generation: {e!s}")
		raise self.retry(countdown=60, max_retries=3)
	finally:
		db.close()


@celery_app.task(name="optimize_recommendation_performance", bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2, "countdown": 120})
def optimize_recommendation_performance(self):
	"""
	Enhanced recommendation performance optimization task
	- Analyzes recommendation effectiveness for all users
	- Identifies performance bottlenecks and optimization opportunities
	- Provides actionable insights for algorithm improvements
	"""
	db = next(get_db())
	task_start_time = datetime.now()

	try:
		from app.models.user import User
		from app.models.analytics import Analytics

		users = db.query(User).filter(User.is_active == True).all()
		logger.info(f"Starting recommendation performance optimization for {len(users)} users")

		optimization_results = {
			"total_users_analyzed": len(users),
			"users_needing_optimization": 0,
			"performance_insights": {},
			"algorithm_recommendations": [],
			"cache_performance": {},
			"execution_time_seconds": 0,
		}

		# Aggregate performance metrics
		all_performance_data = []
		cache_stats = {"hits": 0, "misses": 0, "stale": 0}

		for user in users:
			try:
				# Get comprehensive optimization analysis
				optimization = recommendation_cache_service.optimize_recommendations(db, user.id)
				performance = optimization.get("performance", {})

				# Collect performance data
				all_performance_data.append(
					{
						"user_id": user.id,
						"engagement_rate": performance.get("metrics", {}).get("engagement_rate", 0),
						"application_rate": performance.get("metrics", {}).get("application_rate", 0),
						"click_through_rate": performance.get("metrics", {}).get("click_through_rate", 0),
						"total_recommendations": performance.get("total_recommendations", 0),
						"health_status": optimization.get("overall_health", "unknown"),
					}
				)

				# Count users needing optimization
				if optimization.get("overall_health") == "needs_improvement":
					optimization_results["users_needing_optimization"] += 1

					# Store individual optimization recommendations
					opt_analytics = Analytics(user_id=user.id, type="recommendation_optimization", data=optimization)
					db.add(opt_analytics)

				# Check cache performance
				cached_recs = recommendation_cache_service.get_cached_recommendations(db, user.id, max_age_hours=24)
				if cached_recs:
					cache_stats["hits"] += 1
				else:
					cache_stats["misses"] += 1

			except Exception as e:
				logger.error(f"Failed to optimize recommendations for user {user.id}: {e!s}")

		# Calculate system-wide insights
		if all_performance_data:
			avg_engagement = sum(d["engagement_rate"] for d in all_performance_data) / len(all_performance_data)
			avg_application = sum(d["application_rate"] for d in all_performance_data) / len(all_performance_data)
			avg_ctr = sum(d["click_through_rate"] for d in all_performance_data) / len(all_performance_data)

			optimization_results["performance_insights"] = {
				"average_engagement_rate": round(avg_engagement, 3),
				"average_application_rate": round(avg_application, 3),
				"average_click_through_rate": round(avg_ctr, 3),
				"users_with_good_performance": len([d for d in all_performance_data if d["engagement_rate"] > 0.3]),
				"users_with_poor_performance": len([d for d in all_performance_data if d["engagement_rate"] < 0.1]),
			}

			# Generate algorithm recommendations
			if avg_engagement < 0.2:
				optimization_results["algorithm_recommendations"].append(
					{
						"issue": "Low system-wide engagement",
						"recommendation": "Consider adjusting recommendation algorithm weights",
						"priority": "high",
					}
				)

			if avg_application < 0.1:
				optimization_results["algorithm_recommendations"].append(
					{
						"issue": "Low application conversion",
						"recommendation": "Review job quality filters and user matching criteria",
						"priority": "high",
					}
				)

			# Cache performance analysis
			total_cache_requests = cache_stats["hits"] + cache_stats["misses"]
			cache_hit_rate = cache_stats["hits"] / total_cache_requests if total_cache_requests > 0 else 0

			optimization_results["cache_performance"] = {
				"hit_rate": round(cache_hit_rate, 3),
				"total_requests": total_cache_requests,
				"hits": cache_stats["hits"],
				"misses": cache_stats["misses"],
			}

			if cache_hit_rate < 0.7:
				optimization_results["algorithm_recommendations"].append(
					{"issue": "Low cache hit rate", "recommendation": "Optimize cache invalidation strategy", "priority": "medium"}
				)

		# Calculate execution time
		total_time = (datetime.now() - task_start_time).total_seconds()
		optimization_results["execution_time_seconds"] = total_time

		# Store system-level optimization results
		system_analytics = Analytics(user_id=None, type="system_recommendation_optimization", data=optimization_results)
		db.add(system_analytics)
		db.commit()

		logger.info(
			f"Recommendation optimization completed: {optimization_results['users_needing_optimization']}/{len(users)} users need optimization"
		)

		return optimization_results

	except Exception as e:
		logger.error(f"Critical error in recommendation optimization: {e!s}")
		raise self.retry(countdown=120, max_retries=2)
	finally:
		db.close()


@celery_app.task(name="cleanup_old_recommendation_cache", bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2, "countdown": 60})
def cleanup_old_recommendation_cache(self):
	"""
	Enhanced recommendation cache cleanup task
	- Removes stale recommendation cache entries
	- Cleans up old performance metrics and interaction data
	- Maintains optimal database performance
	"""
	db = next(get_db())

	try:
		from app.models.analytics import Analytics

		cleanup_results = {
			"recommendation_cache_deleted": 0,
			"interaction_data_deleted": 0,
			"metrics_data_deleted": 0,
			"error_logs_deleted": 0,
			"total_space_freed": 0,
			"execution_time_seconds": 0,
		}

		task_start_time = datetime.now()

		# Define retention periods for different data types
		cache_retention_days = 7
		interaction_retention_days = 90
		metrics_retention_days = 30
		error_retention_days = 14

		# Clean up old recommendation caches (7 days)
		cache_cutoff = datetime.now() - timedelta(days=cache_retention_days)
		cache_deleted = db.query(Analytics).filter(Analytics.type == "recommendation_cache", Analytics.generated_at < cache_cutoff).delete()
		cleanup_results["recommendation_cache_deleted"] = cache_deleted

		# Clean up old interaction data (90 days)
		interaction_cutoff = datetime.now() - timedelta(days=interaction_retention_days)
		interaction_deleted = (
			db.query(Analytics).filter(Analytics.type == "recommendation_interactions", Analytics.generated_at < interaction_cutoff).delete()
		)
		cleanup_results["interaction_data_deleted"] = interaction_deleted

		# Clean up old metrics data (30 days)
		metrics_cutoff = datetime.now() - timedelta(days=metrics_retention_days)
		metrics_deleted = (
			db.query(Analytics)
			.filter(
				Analytics.type.in_(["recommendation_generation_metrics", "daily_recommendation_task_metrics", "system_recommendation_optimization"]),
				Analytics.generated_at < metrics_cutoff,
			)
			.delete()
		)
		cleanup_results["metrics_data_deleted"] = metrics_deleted

		# Clean up old error logs (14 days)
		error_cutoff = datetime.now() - timedelta(days=error_retention_days)
		error_deleted = (
			db.query(Analytics).filter(Analytics.type == "recommendation_generation_error", Analytics.generated_at < error_cutoff).delete()
		)
		cleanup_results["error_logs_deleted"] = error_deleted

		# Clear memory cache for inactive users
		recommendation_cache_service.cleanup_memory_cache()

		db.commit()

		# Calculate execution time
		cleanup_results["execution_time_seconds"] = (datetime.now() - task_start_time).total_seconds()

		total_deleted = cache_deleted + interaction_deleted + metrics_deleted + error_deleted

		logger.info(f"Cache cleanup completed: {total_deleted} records deleted")

		# Store cleanup metrics
		cleanup_analytics = Analytics(user_id=None, type="recommendation_cache_cleanup_metrics", data=cleanup_results)
		db.add(cleanup_analytics)
		db.commit()

		return cleanup_results

	except Exception as e:
		logger.error(f"Error in recommendation cache cleanup: {e!s}")
		raise self.retry(countdown=60, max_retries=2)
	finally:
		db.close()


@celery_app.task(
	name="generate_personalized_recommendations", bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 30}
)
def generate_personalized_recommendations(self, user_id: int, force_refresh: bool = False):
	"""
	Generate personalized recommendations for a specific user
	- Can be triggered on-demand or by user activity
	- Includes real-time personalization based on recent behavior
	- Optimized for individual user experience
	"""
	db = next(get_db())

	try:
		from app.models.user import User
		from app.models.analytics import Analytics

		user = db.query(User).filter(User.id == user_id).first()
		if not user:
			logger.error(f"User {user_id} not found")
			return {"error": "User not found"}

		start_time = datetime.now()

		# Generate personalized recommendations with enhanced context
		recommendations = recommendation_cache_service.get_personalized_recommendations(db, user_id, limit=15)

		# Track personalization metrics
		generation_time = (datetime.now() - start_time).total_seconds()

		personalization_data = {
			"user_id": user_id,
			"recommendations_count": len(recommendations),
			"generation_time_seconds": generation_time,
			"personalization_factors": {"recent_activity": True, "interaction_history": True, "performance_optimization": True},
			"generated_at": datetime.now().isoformat(),
		}

		# Store personalization metrics
		analytics = Analytics(user_id=user_id, type="personalized_recommendation_metrics", data=personalization_data)
		db.add(analytics)
		db.commit()

		logger.info(f"Generated {len(recommendations)} personalized recommendations for user {user_id}")

		return {
			"user_id": user_id,
			"recommendations_count": len(recommendations),
			"generation_time_seconds": generation_time,
			"recommendations": recommendations[:10],  # Return top 10 for API response
		}

	except Exception as e:
		logger.error(f"Error generating personalized recommendations for user {user_id}: {e!s}")
		raise self.retry(countdown=30, max_retries=3)
	finally:
		db.close()


@celery_app.task(name="track_recommendation_performance", bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2, "countdown": 60})
def track_recommendation_performance(self):
	"""
	Track and analyze recommendation system performance
	- Monitors key performance indicators
	- Identifies trends and patterns
	- Provides insights for continuous improvement
	"""
	db = next(get_db())

	try:
		from app.models.user import User
		from app.models.analytics import Analytics

		# Get performance data for the last 7 days
		week_ago = datetime.now() - timedelta(days=7)

		# Aggregate performance metrics
		performance_data = {
			"analysis_period": "7_days",
			"total_recommendations_generated": 0,
			"total_user_interactions": 0,
			"average_generation_time": 0,
			"cache_performance": {},
			"user_engagement_trends": {},
			"algorithm_effectiveness": {},
			"generated_at": datetime.now().isoformat(),
		}

		# Get generation metrics
		generation_metrics = (
			db.query(Analytics).filter(Analytics.type == "recommendation_generation_metrics", Analytics.generated_at >= week_ago).all()
		)

		if generation_metrics:
			total_recs = sum(m.data.get("recommendations_count", 0) for m in generation_metrics)
			total_time = sum(m.data.get("generation_time_seconds", 0) for m in generation_metrics)
			avg_time = total_time / len(generation_metrics) if generation_metrics else 0

			performance_data["total_recommendations_generated"] = total_recs
			performance_data["average_generation_time"] = round(avg_time, 3)

		# Get interaction data
		interaction_data = db.query(Analytics).filter(Analytics.type == "recommendation_interactions", Analytics.generated_at >= week_ago).all()

		total_interactions = 0
		for record in interaction_data:
			interactions = record.data.get("interactions", [])
			total_interactions += len(interactions)

		performance_data["total_user_interactions"] = total_interactions

		# Calculate engagement trends
		active_users = db.query(User).filter(User.is_active == True).count()
		if active_users > 0:
			performance_data["user_engagement_trends"] = {
				"active_users": active_users,
				"interactions_per_user": round(total_interactions / active_users, 2),
				"recommendations_per_user": round(performance_data["total_recommendations_generated"] / active_users, 2),
			}

		# Store performance tracking results
		tracking_analytics = Analytics(user_id=None, type="recommendation_performance_tracking", data=performance_data)
		db.add(tracking_analytics)
		db.commit()

		logger.info(
			f"Recommendation performance tracking completed: {total_interactions} interactions, {performance_data['total_recommendations_generated']} recommendations"
		)

		return performance_data

	except Exception as e:
		logger.error(f"Error in recommendation performance tracking: {e!s}")
		raise self.retry(countdown=60, max_retries=2)
	finally:
		db.close()
