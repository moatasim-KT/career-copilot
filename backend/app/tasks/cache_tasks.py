"""
Celery tasks for cache management and optimization
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.celery import celery_app
from app.core.cache import analytics_cache, cache_service, job_recommendation_cache
from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def cleanup_expired_cache(self):
	"""Clean up expired cache entries and optimize Redis memory usage"""
	try:
		if not cache_service.is_connected():
			logger.error("Redis not connected - skipping cache cleanup")
			return {"status": "error", "message": "Redis not connected"}

		# Get initial stats
		initial_stats = cache_service.get_cache_stats()
		redis_client = cache_service.redis_client
		initial_info = redis_client.info()

		# Clean up expired keys by pattern
		cleanup_results = {}

		# Clean up old recommendation cache (older than 4 hours)
		old_rec_pattern = "cc:job_recommendations:*"
		old_rec_keys = redis_client.keys(old_rec_pattern)
		expired_rec_count = 0

		for key in old_rec_keys:
			ttl = redis_client.ttl(key)
			if ttl < 3600:  # Less than 1 hour remaining
				redis_client.delete(key)
				expired_rec_count += 1

		cleanup_results["expired_recommendations"] = expired_rec_count

		# Clean up old analytics cache (older than 2 hours)
		old_analytics_pattern = "cc:analytics_*"
		old_analytics_keys = redis_client.keys(old_analytics_pattern)
		expired_analytics_count = 0

		for key in old_analytics_keys:
			ttl = redis_client.ttl(key)
			if ttl < 1800:  # Less than 30 minutes remaining
				redis_client.delete(key)
				expired_analytics_count += 1

		cleanup_results["expired_analytics"] = expired_analytics_count

		# Clean up old profile cache (older than 30 minutes)
		old_profile_pattern = "cc:user_profile*"
		old_profile_keys = redis_client.keys(old_profile_pattern)
		expired_profile_count = 0

		for key in old_profile_keys:
			ttl = redis_client.ttl(key)
			if ttl < 900:  # Less than 15 minutes remaining
				redis_client.delete(key)
				expired_profile_count += 1

		cleanup_results["expired_profiles"] = expired_profile_count

		# Get final stats
		final_info = redis_client.info()
		final_stats = cache_service.get_cache_stats()

		result = {
			"status": "success",
			"cleanup_results": cleanup_results,
			"total_cleaned": sum(cleanup_results.values()),
			"memory_stats": {
				"before": initial_info.get("used_memory_human", "N/A"),
				"after": final_info.get("used_memory_human", "N/A"),
				"freed_keys": initial_info.get("expired_keys", 0) - final_info.get("expired_keys", 0),
			},
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

		logger.info(f"Cache cleanup completed: {result}")
		return result

	except Exception as e:
		logger.error(f"Cache cleanup failed: {e}")
		return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, max_retries=3)
def invalidate_stale_recommendations(self):
	"""Invalidate recommendation cache for users with recent profile updates"""
	try:
		if not cache_service.is_connected():
			logger.error("Redis not connected - skipping recommendation invalidation")
			return {"status": "error", "message": "Redis not connected"}

		# Get users who updated their profiles in the last hour
		cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)

		with next(get_db()) as db:
			updated_users = db.query(User.id).filter(User.updated_at >= cutoff_time).all()

			invalidated_count = 0
			for (user_id,) in updated_users:
				# Invalidate recommendations for this user
				if job_recommendation_cache.invalidate_recommendations(user_id):
					invalidated_count += 1

				# Also invalidate analytics cache as profile changes affect analytics
				analytics_cache.invalidate_user_analytics(user_id)

		result = {
			"status": "success",
			"users_checked": len(updated_users),
			"recommendations_invalidated": invalidated_count,
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

		logger.info(f"Stale recommendation invalidation completed: {result}")
		return result

	except Exception as e:
		logger.error(f"Stale recommendation invalidation failed: {e}")
		return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, max_retries=3)
def warm_up_cache(self, user_ids: list[int] | None = None):
	"""Pre-populate cache with frequently accessed data"""
	try:
		if not cache_service.is_connected():
			logger.error("Redis not connected - skipping cache warm-up")
			return {"status": "error", "message": "Redis not connected"}

		warmed_up = {"profiles": 0, "recommendations": 0, "analytics": 0}

		with next(get_db()) as db:
			# If no specific user IDs provided, get active users
			if not user_ids:
				# Get users who have been active in the last 7 days
				cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
				active_users = db.query(User.id).filter(User.last_active >= cutoff_time).limit(50).all()  # Limit to prevent overwhelming
				user_ids = [user_id for (user_id,) in active_users]

			# Import services here to avoid circular imports
			from app.services.job_recommendation_service import get_job_recommendation_service
			from app.services.profile_service import ProfileService
			from app.services.skill_analysis_service import skill_analysis_service

			for user_id in user_ids:
				try:
					# Warm up profile cache
					profile_service = ProfileService(db)
					profile = profile_service.get_user_profile(user_id)
					if profile:
						warmed_up["profiles"] += 1

					# Warm up recommendations cache
					recommendations = get_job_recommendation_service(db).generate_recommendations_for_user(db, user_id, limit=10)
					if recommendations:
						warmed_up["recommendations"] += 1

					# Warm up skill analysis cache
					skill_analysis = skill_analysis_service.analyze_skill_gap(db, user_id)
					if skill_analysis and "error" not in skill_analysis:
						warmed_up["analytics"] += 1

				except Exception as e:
					logger.warning(f"Failed to warm up cache for user {user_id}: {e}")
					continue

		result = {"status": "success", "users_processed": len(user_ids), "warmed_up": warmed_up, "timestamp": datetime.now(timezone.utc).isoformat()}

		logger.info(f"Cache warm-up completed: {result}")
		return result

	except Exception as e:
		logger.error(f"Cache warm-up failed: {e}")
		return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, max_retries=3)
def generate_cache_performance_report(self):
	"""Generate a comprehensive cache performance report"""
	try:
		if not cache_service.is_connected():
			logger.error("Redis not connected - skipping performance report")
			return {"status": "error", "message": "Redis not connected"}

		# Get application stats
		app_stats = cache_service.get_cache_stats()

		# Get Redis stats
		redis_client = cache_service.redis_client
		redis_info = redis_client.info()

		# Count keys by type
		key_counts = {}
		prefixes = ["cc:user_profile:", "cc:job_recommendations:", "cc:analytics_"]
		for prefix in prefixes:
			keys = redis_client.keys(f"{prefix}*")
			key_counts[prefix.replace("cc:", "").replace(":", "")] = len(keys)

		# Calculate performance metrics
		redis_hits = redis_info.get("keyspace_hits", 0)
		redis_misses = redis_info.get("keyspace_misses", 0)
		redis_total = redis_hits + redis_misses
		redis_hit_rate = (redis_hits / redis_total * 100) if redis_total > 0 else 0

		# Generate recommendations
		recommendations = []

		if app_stats.get("hit_rate", 0) < 70:
			recommendations.append("Application cache hit rate is low - consider increasing TTL values")

		if redis_hit_rate < 80:
			recommendations.append("Redis hit rate is low - consider optimizing cache keys and TTL")

		if redis_info.get("used_memory", 0) > 100 * 1024 * 1024:  # 100MB
			recommendations.append("Redis memory usage is high - consider implementing cache eviction policies")

		if redis_info.get("connected_clients", 0) > 50:
			recommendations.append("High number of Redis connections - consider connection pooling optimization")

		report = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"application_performance": {
				"hit_rate": app_stats.get("hit_rate", 0),
				"total_requests": app_stats.get("total_requests", 0),
				"errors": app_stats.get("errors", 0),
			},
			"redis_performance": {
				"hit_rate": round(redis_hit_rate, 2),
				"ops_per_second": redis_info.get("instantaneous_ops_per_sec", 0),
				"memory_usage": redis_info.get("used_memory_human", "N/A"),
				"connected_clients": redis_info.get("connected_clients", 0),
			},
			"cache_distribution": key_counts,
			"recommendations": recommendations,
			"status": "success",
		}

		logger.info(f"Cache performance report generated: {report}")
		return report

	except Exception as e:
		logger.error(f"Cache performance report generation failed: {e}")
		return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, max_retries=3)
def optimize_cache_memory(self):
	"""Optimize Redis memory usage by cleaning up unnecessary data"""
	try:
		if not cache_service.is_connected():
			logger.error("Redis not connected - skipping memory optimization")
			return {"status": "error", "message": "Redis not connected"}

		redis_client = cache_service.redis_client
		initial_info = redis_client.info()
		initial_memory = initial_info.get("used_memory", 0)

		optimization_results = {}

		# Remove keys with very short TTL (less than 60 seconds)
		all_keys = redis_client.keys("cc:*")
		short_ttl_removed = 0

		for key in all_keys:
			ttl = redis_client.ttl(key)
			if 0 < ttl < 60:  # Expiring soon
				redis_client.delete(key)
				short_ttl_removed += 1

		optimization_results["short_ttl_removed"] = short_ttl_removed

		# Compress large values (if any patterns are identified)
		# This would be implementation-specific based on data patterns

		# Get final memory usage
		final_info = redis_client.info()
		final_memory = final_info.get("used_memory", 0)
		memory_saved = initial_memory - final_memory

		result = {
			"status": "success",
			"optimization_results": optimization_results,
			"memory_stats": {
				"initial_memory": initial_info.get("used_memory_human", "N/A"),
				"final_memory": final_info.get("used_memory_human", "N/A"),
				"memory_saved_bytes": memory_saved,
				"memory_saved_percentage": round((memory_saved / initial_memory * 100), 2) if initial_memory > 0 else 0,
			},
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

		logger.info(f"Cache memory optimization completed: {result}")
		return result

	except Exception as e:
		logger.error(f"Cache memory optimization failed: {e}")
		return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, max_retries=3)
def backup_critical_cache_data(self):
	"""Backup critical cache data to prevent data loss"""
	try:
		if not cache_service.is_connected():
			logger.error("Redis not connected - skipping cache backup")
			return {"status": "error", "message": "Redis not connected"}

		redis_client = cache_service.redis_client
		backup_data = {}

		# Backup user profiles (most critical)
		profile_keys = redis_client.keys("cc:user_profile:*")
		profile_backup = {}

		for key in profile_keys[:100]:  # Limit to prevent memory issues
			try:
				data = redis_client.get(key)
				if data:
					profile_backup[key.decode() if isinstance(key, bytes) else key] = data
			except Exception as e:
				logger.warning(f"Failed to backup key {key}: {e}")

		backup_data["profiles"] = len(profile_backup)

		# Store backup metadata in Redis with longer TTL
		backup_metadata = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"profile_count": len(profile_backup),
			"backup_size": len(str(profile_backup)),
		}

		redis_client.setex(
			"cc:backup:metadata",
			86400 * 7,  # 7 days TTL
			str(backup_metadata),
		)

		result = {"status": "success", "backup_data": backup_data, "backup_metadata": backup_metadata}

		logger.info(f"Cache backup completed: {result}")
		return result

	except Exception as e:
		logger.error(f"Cache backup failed: {e}")
		return {"status": "error", "message": str(e)}
