"""
AngelList (Wellfound) job board scraper using GraphQL API.
Free API with excellent startup job coverage and equity data.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings
from app.schemas.job import JobCreate
from app.services.language_processor import get_language_processor

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings
from app.services.language_processor import get_language_processor

from .base_scraper import BaseScraper, JobData


class AngelListScraper(BaseScraper):
	"""AngelList/Wellfound job board scraper using GraphQL API."""

	# API endpoints
	GRAPHQL_ENDPOINT = "https://api.wellfound.com/graphql"
	REST_ENDPOINT = "https://api.angel.co/1/"

	def __init__(self, api_key: Optional[str] = None):
		"""
		Initialize AngelList scraper.

		Args:
		    api_key: Optional API key (increases rate limits)
		"""
		super().__init__(
			source_name="AngelList",
			base_url="https://wellfound.com",
			rate_limit_per_minute=80,  # 5000/hour = ~83/min
		)

		settings = get_settings()
		self.api_key = api_key or getattr(settings, "angellist_api_key", None)
		self.language_processor = get_language_processor()

		# Setup HTTP client
		headers = {}
		if self.api_key:
			headers["Authorization"] = f"Bearer {self.api_key}"

		self.client = httpx.AsyncClient(headers=headers, timeout=30.0)

	async def search_jobs(self, query: str = "software engineer", location: str = "", filters: Optional[Dict] = None) -> List[JobData]:
		"""
		Search for jobs using GraphQL API.

		Args:
		    query: Search query (job title, keywords)
		    location: Location filter (optional)
		    filters: Additional filters (remote, experience, etc.)

		Returns:
		    List of JobData objects
		"""
		await self.rate_limiter.wait_if_needed()

		# Build GraphQL query
		graphql_query = """
        query SearchJobs($query: String!, $limit: Int!) {
          jobs(
            query: $query
            limit: $limit
            filter: { remote: true }
          ) {
            edges {
              node {
                id
                title
                description
                descriptionHtml
                locationName
                remote
                company {
                  name
                  slug
                  logoUrl
                  size
                  markets
                  stage
                  totalRaised
                  techStack
                }
                salaryMin
                salaryMax
                currency
                equityMin
                equityMax
                equityType
                experienceLevel
                jobType
                applicationUrl
                postedAt
              }
            }
          }
        }
        """

		variables = {"query": query, "limit": 50}

		try:
			response = await self.client.post(self.GRAPHQL_ENDPOINT, json={"query": graphql_query, "variables": variables})

			if response.status_code == 200:
				data = response.json()
				return self._parse_graphql_response(data)
			else:
				self.logger.error(f"AngelList API error: {response.status_code}")
				return []

		except Exception as e:
			self.logger.error(f"Error searching AngelList jobs: {e}")
			return []

	def _parse_graphql_response(self, data: Dict) -> List[JobData]:
		"""Parse GraphQL response into JobData objects."""
		jobs = []

		try:
			edges = data.get("data", {}).get("jobs", {}).get("edges", [])

			for edge in edges:
				node = edge.get("node", {})
				job_data = self._parse_job_node(node)
				if job_data:
					jobs.append(job_data)

		except Exception as e:
			self.logger.error(f"Error parsing AngelList response: {e}")

		return jobs

	def _parse_job_node(self, node: Dict) -> Optional[JobData]:
		"""Parse single job node from GraphQL response."""
		try:
			company = node.get("company", {})

			# Extract salary range
			salary_range = None
			if node.get("salaryMin") and node.get("salaryMax"):
				currency = node.get("currency", "USD")
				salary_range = f"{currency} {node['salaryMin']:,}-{node['salaryMax']:,}"

			# Extract equity range
			equity_range = None
			if node.get("equityMin") is not None and node.get("equityMax") is not None:
				equity_type = node.get("equityType", "percentage")
				equity_range = self.language_processor.format_equity_range({"min": node["equityMin"], "max": node["equityMax"], "type": equity_type})

			# Detect language
			description = node.get("description", "")
			job_language = self.language_processor.detect_language(description)

			# Map experience level
			experience_level = self.language_processor.map_experience_level(node.get("experienceLevel", ""), "AngelList")

			# Normalize tech stack
			tech_stack = self.language_processor.normalize_tech_stack(company.get("techStack", []))

			# Map funding stage
			funding_stage = self.language_processor.map_funding_stage(company.get("stage", ""))

			# Build JobData
			job_data = JobData(
				title=node.get("title", ""),
				company=company.get("name", ""),
				location=node.get("locationName", "Remote"),
				description=description,
				description_html=node.get("descriptionHtml"),
				url=node.get("applicationUrl", f"https://wellfound.com/jobs/{node['id']}"),
				salary_range=salary_range,
				employment_type=self._map_job_type(node.get("jobType", "")),
				posted_date=self._parse_date(node.get("postedAt")),
				remote_ok=node.get("remote", False),
				source="AngelList",
				# Phase 3.3 new fields
				experience_level=experience_level,
				equity_range=equity_range,
				tech_stack=tech_stack,
				funding_stage=funding_stage,
				total_funding=company.get("totalRaised"),  # Already in cents
				job_language=job_language,
				company_size=company.get("size"),
				# Store raw data for reference
				raw_data={
					"job_id": node.get("id"),
					"company_slug": company.get("slug"),
					"company_logo": company.get("logoUrl"),
					"markets": company.get("markets", []),
				},
			)

			return job_data

		except Exception as e:
			self.logger.error(f"Error parsing job node: {e}")
			return None

	def _map_job_type(self, job_type: str) -> str:
		"""Map AngelList job type to standard format."""
		type_map = {
			"full_time": "Full-time",
			"part_time": "Part-time",
			"contract": "Contract",
			"internship": "Internship",
			"temporary": "Temporary",
		}
		return type_map.get(job_type.lower(), "Full-time")

	def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
		"""Parse ISO date string."""
		if not date_str:
			return None

		try:
			return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
		except:
			return None

	async def get_job_details(self, job_id: str) -> Optional[JobData]:
		"""
		Get detailed job information by ID.

		Args:
		    job_id: AngelList job ID

		Returns:
		    JobData object or None
		"""
		await self.rate_limiter.wait_if_needed()

		graphql_query = """
        query GetJob($id: ID!) {
          job(id: $id) {
            id
            title
            description
            descriptionHtml
            locationName
            remote
            company {
              name
              slug
              logoUrl
              size
              markets
              stage
              totalRaised
              lastFunding {
                amount
                round
                date
              }
              investors
              techStack
            }
            salaryMin
            salaryMax
            currency
            equityMin
            equityMax
            equityType
            experienceLevel
            jobType
            applicationUrl
            postedAt
          }
        }
        """

		try:
			response = await self.client.post(self.GRAPHQL_ENDPOINT, json={"query": graphql_query, "variables": {"id": job_id}})

			if response.status_code == 200:
				data = response.json()
				node = data.get("data", {}).get("job", {})
				if node:
					job_data = self._parse_job_node(node)
					# Add investor data if available
					if job_data and "investors" in node.get("company", {}):
						job_data.raw_data["investors"] = node["company"]["investors"]
					return job_data

			return None

		except Exception as e:
			self.logger.error(f"Error getting job details: {e}")
			return None

	async def close(self):
		"""Close HTTP client."""
		await self.client.aclose()

	async def __aenter__(self):
		"""Async context manager entry."""
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		"""Async context manager exit."""
		await self.close()


# For testing
async def test_angellist_scraper():
	"""Test AngelList scraper."""
	async with AngelListScraper() as scraper:
		print("Testing AngelList scraper...")

		# Search for jobs
		jobs = await scraper.search_jobs(query="python developer", location="remote")

		print(f"\nFound {len(jobs)} jobs")

		if jobs:
			print("\nFirst job:")
			job = jobs[0]
			print(f"Title: {job.title}")
			print(f"Company: {job.company}")
			print(f"Location: {job.location}")
			print(f"Salary: {job.salary_range}")
			print(f"Equity: {job.equity_range}")
			print(f"Experience: {job.experience_level}")
			print(f"Tech Stack: {job.tech_stack}")
			print(f"Funding: {job.funding_stage}")
			print(f"Language: {job.job_language}")


if __name__ == "__main__":
	asyncio.run(test_angellist_scraper())
