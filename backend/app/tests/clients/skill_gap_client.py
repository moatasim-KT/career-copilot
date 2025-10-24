"""Test client for skill gap analysis API."""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from httpx import Response

from ...core.config import get_settings

settings = get_settings()


class SkillGapAPIClient:
    """Client for interacting with the skill gap analysis API endpoints."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        """Initialize the API client."""
        self.base_url = base_url or f"http://localhost:{settings.api_port}/api/v1"
        self.timeout = timeout

    async def analyze_skill_gap(self, 
        user_id: int, 
        job_id: Optional[int] = None,
        role_title: Optional[str] = None
    ) -> Response:
        """
        Get skill gap analysis for a user against a job or role.
        
        Args:
            user_id: User ID to analyze
            job_id: Optional job ID to compare against
            role_title: Optional role title to compare against
            
        Returns:
            Response with skill gap analysis
        """
        params = {"user_id": user_id}
        if job_id:
            params["job_id"] = job_id
        if role_title:
            params["role_title"] = role_title

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(
                f"{self.base_url}/skills/gap-analysis",
                params=params
            )

    async def get_skill_recommendations(self, user_id: int) -> Response:
        """Get personalized skill recommendations for a user."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(
                f"{self.base_url}/skills/recommendations",
                params={"user_id": user_id}
            )

    async def validate_skill_match(self, 
        user_skills: List[str],
        required_skills: List[str]
    ) -> Response:
        """Validate skill matching accuracy."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(
                f"{self.base_url}/skills/validate-match",
                json={
                    "user_skills": user_skills,
                    "required_skills": required_skills
                }
            )

    async def benchmark_response_time(self, iterations: int = 10) -> Dict[str, float]:
        """
        Benchmark API response times.
        
        Args:
            iterations: Number of requests to make
            
        Returns:
            Dictionary with min, max, and average response times
        """
        response_times = []
        
        # Test user data
        test_user_id = 1
        test_skills = ["Python", "SQL", "Docker"]
        required_skills = ["Python", "FastAPI", "PostgreSQL", "Docker"]
        
        for _ in range(iterations):
            start_time = asyncio.get_event_loop().time()
            
            # Make concurrent requests to different endpoints
            responses = await asyncio.gather(
                self.analyze_skill_gap(test_user_id),
                self.get_skill_recommendations(test_user_id),
                self.validate_skill_match(test_skills, required_skills)
            )
            
            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            
            # Check if all requests were successful
            if all(r.status_code == 200 for r in responses):
                response_times.append(response_time)
        
        if not response_times:
            raise RuntimeError("All benchmark requests failed")
            
        return {
            "min_ms": min(response_times) * 1000,
            "max_ms": max(response_times) * 1000,
            "avg_ms": (sum(response_times) / len(response_times)) * 1000
        }        }