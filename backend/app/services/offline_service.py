"""
Offline functionality and graceful degradation service
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime

from app.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)

cache_service = get_cache_service()


class OfflineService:
	"""Service for handling offline functionality and graceful degradation"""

	def __init__(self):
		self.fallback_data = {}

	def get_with_fallback(self, key: str, fetch_func, fallback_value: Any = None) -> Dict:
		"""Get data with fallback to cache if fetch fails"""
		try:
			# Try to fetch fresh data
			data = fetch_func()

			# Cache successful result
			if data:
				cache_service.set(f"offline:{key}", data, ttl=86400)  # 24 hours

			return {"success": True, "data": data, "source": "live", "timestamp": datetime.now().isoformat()}

		except Exception as e:
			logger.warning(f"Fetch failed for {key}, trying cache: {e}")

			# Try cache
			cached = cache_service.get(f"offline:{key}")
			if cached:
				return {
					"success": True,
					"data": cached,
					"source": "cache",
					"timestamp": datetime.now().isoformat(),
					"warning": "Using cached data due to service unavailability",
				}

			# Use fallback
			return {"success": False, "data": fallback_value, "source": "fallback", "timestamp": datetime.now().isoformat(), "error": str(e)}

	def check_service_availability(self, service_name: str, check_func) -> Dict:
		"""Check if external service is available"""
		try:
			check_func()

			# Cache availability status
			cache_service.set(f"service_status:{service_name}", True, ttl=300)  # 5 min

			return {"service": service_name, "available": True, "checked_at": datetime.now().isoformat()}

		except Exception as e:
			logger.error(f"Service {service_name} unavailable: {e}")

			cache_service.set(f"service_status:{service_name}", False, ttl=60)  # 1 min

			return {"service": service_name, "available": False, "error": str(e), "checked_at": datetime.now().isoformat()}

	def is_service_available(self, service_name: str) -> bool:
		"""Check cached service availability status"""
		status = cache_service.get(f"service_status:{service_name}")
		return status if status is not None else True  # Assume available if unknown

	def get_offline_manifest(self) -> Dict:
		"""Get manifest of data available offline"""
		return {
			"version": "1.0",
			"cached_endpoints": ["/api/v1/jobs", "/api/v1/recommendations", "/api/v1/analytics/summary", "/api/v1/profile"],
			"cache_duration_hours": 24,
			"last_sync": datetime.now().isoformat(),
		}

	def prepare_offline_data(self, user_id: int, db) -> Dict:
		"""Prepare essential data for offline use"""
		from app.models.job import Job
		from app.models.application import Application

		try:
			# Get recent jobs
			jobs = db.query(Job).filter(Job.user_id == user_id).order_by(Job.created_at.desc()).limit(50).all()

			# Get recent applications
			applications = db.query(Application).filter(Application.user_id == user_id).order_by(Application.created_at.desc()).limit(50).all()

			offline_data = {
				"jobs": [{"id": j.id, "title": j.title, "company": j.company, "location": j.location, "status": j.status} for j in jobs],
				"applications": [
					{"id": a.id, "job_id": a.job_id, "status": a.status, "applied_date": a.applied_date.isoformat() if a.applied_date else None}
					for a in applications
				],
				"prepared_at": datetime.now().isoformat(),
			}

			# Cache for offline use
			cache_service.set(f"offline_data:{user_id}", offline_data, ttl=86400)

			return {"success": True, "data": offline_data, "items_cached": len(jobs) + len(applications)}

		except Exception as e:
			logger.error(f"Failed to prepare offline data: {e}")
			return {"success": False, "error": str(e)}

	def get_offline_data(self, user_id: int) -> Optional[Dict]:
		"""Get cached offline data"""
		return cache_service.get(f"offline_data:{user_id}")


offline_service = OfflineService()
