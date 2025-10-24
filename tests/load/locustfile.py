"""
Locust load testing configuration for Career Copilot.
Test scenarios focusing on API endpoints and common user flows.
"""

from typing import Dict, Any
import json
import random
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.clients import HttpSession

class CareerCopilotUser(HttpUser):
    """
    Simulated user for load testing Career Copilot.
    Implements realistic user behavior patterns.
    """
    
    # Wait time between tasks (2-5 seconds)
    wait_time = between(2, 5)
    
    def on_start(self):
        """Initialize user session."""
        # Login and store authentication token
        self.token = self._login()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def _login(self) -> str:
        """Perform user login and return token."""
        credentials = {
            "email": f"loadtest_user_{random.randint(1, 1000)}@test.com",
            "password": "LoadTest123!"
        }
        
        with self.client.post(
            "/api/v1/auth/login",
            json=credentials,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                return response.json()["token"]
            response.failure(f"Login failed: {response.status_code}")
            return ""
    
    @task(3)
    def view_job_recommendations(self):
        """Get personalized job recommendations."""
        with self.client.get(
            "/api/v1/recommendations/jobs",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get recommendations: {response.status_code}")
    
    @task(2)
    def search_jobs(self):
        """Search for jobs with random criteria."""
        search_terms = [
            "software engineer",
            "data scientist",
            "product manager",
            "devops engineer",
            "full stack developer"
        ]
        
        params = {
            "query": random.choice(search_terms),
            "location": random.choice(["remote", "San Francisco", "New York", "London"]),
            "page": random.randint(1, 5),
            "limit": 10
        }
        
        with self.client.get(
            "/api/v1/jobs/search",
            params=params,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Job search failed: {response.status_code}")
    
    @task(2)
    def analyze_resume(self):
        """Submit resume for analysis."""
        sample_resume = {
            "content": "Professional software engineer with 5 years of experience...",
            "format": "text"
        }
        
        with self.client.post(
            "/api/v1/analysis/resume",
            json=sample_resume,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Resume analysis failed: {response.status_code}")
    
    @task(1)
    def get_skill_insights(self):
        """Get skill gap analysis and market insights."""
        with self.client.get(
            "/api/v1/insights/skills",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Skill insights failed: {response.status_code}")
    
    @task(1)
    def update_preferences(self):
        """Update user preferences."""
        preferences = {
            "job_types": random.sample(["full-time", "contract", "remote"], 2),
            "locations": random.sample(["San Francisco", "New York", "Remote"], 2),
            "salary_range": {
                "min": random.randint(80000, 120000),
                "max": random.randint(130000, 200000)
            }
        }
        
        with self.client.put(
            "/api/v1/users/preferences",
            json=preferences,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Update preferences failed: {response.status_code}")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test environment."""
    print("Starting load test...")
    print(f"Target host: {environment.host}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Clean up after test."""
    print("\nLoad test completed")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failed requests: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Requests per second: {environment.stats.total.current_rps:.2f}")