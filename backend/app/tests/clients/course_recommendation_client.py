"""Test client for course recommendation API."""

import asyncio
import json
from typing import Dict, List, Optional

import httpx
from httpx import Response

from ...core.config import get_settings

settings = get_settings()


class CourseRecommendationAPIClient:
	"""Client for interacting with the course recommendation API endpoints."""

	def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
		"""Initialize the API client."""
		self.base_url = base_url or f"http://localhost:{settings.api_port}/api/v1"
		self.timeout = timeout

	async def get_course_recommendations(self, user_id: int, skill_focus: Optional[List[str]] = None, limit: int = 10) -> Response:
		"""
		Get course recommendations for a user.

		Args:
		    user_id: User ID to get recommendations for
		    skill_focus: Optional list of skills to focus on
		    limit: Maximum number of recommendations to return

		Returns:
		    Response with course recommendations
		"""
		params = {"user_id": user_id, "limit": limit}
		if skill_focus:
			params["skill_focus"] = json.dumps(skill_focus)

		async with httpx.AsyncClient(timeout=self.timeout) as client:
			return await client.get(f"{self.base_url}/courses/recommendations", params=params)

	async def validate_course_relevance(self, user_id: int, course_id: int) -> Response:
		"""Validate course relevance for a user."""
		async with httpx.AsyncClient(timeout=self.timeout) as client:
			return await client.post(f"{self.base_url}/courses/validate-relevance", json={"user_id": user_id, "course_id": course_id})

	async def get_course_completion_stats(self, course_id: int, timeframe_days: int = 30) -> Response:
		"""Get course completion statistics."""
		async with httpx.AsyncClient(timeout=self.timeout) as client:
			return await client.get(f"{self.base_url}/courses/{course_id}/stats", params={"timeframe_days": timeframe_days})

	async def benchmark_recommendations(self, iterations: int = 10, test_user_id: int = 1) -> Dict[str, float]:
		"""
		Benchmark recommendation quality and response times.

		Args:
		    iterations: Number of requests to make
		    test_user_id: User ID to test with

		Returns:
		    Dictionary with quality metrics and response times
		"""
		response_times = []
		relevance_scores = []

		for _ in range(iterations):
			start_time = asyncio.get_event_loop().time()

			# Get recommendations
			response = await self.get_course_recommendations(test_user_id)

			if response.status_code == 200:
				end_time = asyncio.get_event_loop().time()
				response_time = end_time - start_time
				response_times.append(response_time)

				# Check recommendation quality
				recommendations = response.json()
				if recommendations.get("courses"):
					# Validate first recommendation
					course_id = recommendations["courses"][0]["id"]
					relevance = await self.validate_course_relevance(test_user_id, course_id)

		if relevance.status_code == 200:
			relevance_data = relevance.json()
			relevance_scores.append(relevance_data.get("relevance_score", 0))

		if not response_times:
			raise RuntimeError("All benchmark requests failed")

		return {
			"response_times": {
				"min_ms": min(response_times) * 1000,
				"max_ms": max(response_times) * 1000,
				"avg_ms": (sum(response_times) / len(response_times)) * 1000,
			},
			"relevance": {
				"min_score": min(relevance_scores) if relevance_scores else 0,
				"max_score": max(relevance_scores) if relevance_scores else 0,
				"avg_score": (sum(relevance_scores) / len(relevance_scores)) if relevance_scores else 0,
			},
		}
