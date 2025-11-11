"""
Comprehensive tests for advanced search and filtering functionality.
Tests job search, application search, caching, and performance optimizations.
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.application import Application
from app.models.user import User


@pytest.mark.asyncio
class TestJobSearch:
	"""Test advanced job search functionality"""

	async def test_basic_job_search(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test basic job search with query parameter"""
		# Create test jobs
		jobs_data = [
			{"company": "TechCorp", "title": "Python Developer", "description": "Python backend development"},
			{"company": "DataInc", "title": "Data Scientist", "description": "Machine learning and AI"},
			{"company": "WebSoft", "title": "Frontend Developer", "description": "React and TypeScript"},
		]
		
		for job_data in jobs_data:
			job = Job(**job_data, user_id=test_user.id)
			db_session.add(job)
		await db_session.commit()

		# Search for Python
		response = await async_client.get("/api/v1/jobs/search", params={"query": "Python"})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 1
		assert results[0]["title"] == "Python Developer"

	async def test_multi_field_search(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test search across multiple fields (title, company, description)"""
		# Create test job
		job = Job(
			company="TechCorp",
			title="Backend Developer",
			description="Work with Python and Django",
			user_id=test_user.id
		)
		db_session.add(job)
		await db_session.commit()

		# Search by company
		response = await async_client.get("/api/v1/jobs/search", params={"query": "TechCorp"})
		assert response.status_code == 200
		assert len(response.json()) == 1

		# Search by description
		response = await async_client.get("/api/v1/jobs/search", params={"query": "Django"})
		assert response.status_code == 200
		assert len(response.json()) == 1

	async def test_location_filtering(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test location-based filtering"""
		jobs_data = [
			{"company": "CompanyA", "title": "Developer", "location": "San Francisco, CA"},
			{"company": "CompanyB", "title": "Developer", "location": "New York, NY"},
			{"company": "CompanyC", "title": "Developer", "location": "Remote"},
		]
		
		for job_data in jobs_data:
			job = Job(**job_data, user_id=test_user.id)
			db_session.add(job)
		await db_session.commit()

		# Filter by location
		response = await async_client.get("/api/v1/jobs/search", params={"location": "San Francisco"})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 1
		assert "San Francisco" in results[0]["location"]

	async def test_remote_filtering(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test remote job filtering"""
		jobs_data = [
			{"company": "CompanyA", "title": "Developer", "remote_option": "remote"},
			{"company": "CompanyB", "title": "Developer", "remote_option": "hybrid"},
			{"company": "CompanyC", "title": "Developer", "remote_option": "onsite"},
		]
		
		for job_data in jobs_data:
			job = Job(**job_data, user_id=test_user.id)
			db_session.add(job)
		await db_session.commit()

		# Filter remote only
		response = await async_client.get("/api/v1/jobs/search", params={"remote_only": True})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 1
		assert results[0]["remote_option"] == "remote"

	async def test_job_type_filtering(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test job type filtering"""
		jobs_data = [
			{"company": "CompanyA", "title": "Developer", "job_type": "full-time"},
			{"company": "CompanyB", "title": "Developer", "job_type": "part-time"},
			{"company": "CompanyC", "title": "Developer", "job_type": "contract"},
		]
		
		for job_data in jobs_data:
			job = Job(**job_data, user_id=test_user.id)
			db_session.add(job)
		await db_session.commit()

		# Filter by job type
		response = await async_client.get("/api/v1/jobs/search", params={"job_type": "full-time"})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 1
		assert results[0]["job_type"] == "full-time"

	async def test_salary_range_filtering(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test salary range filtering"""
		jobs_data = [
			{"company": "CompanyA", "title": "Junior Dev", "salary_min": 50000, "salary_max": 70000},
			{"company": "CompanyB", "title": "Mid Dev", "salary_min": 80000, "salary_max": 100000},
			{"company": "CompanyC", "title": "Senior Dev", "salary_min": 120000, "salary_max": 150000},
		]
		
		for job_data in jobs_data:
			job = Job(**job_data, user_id=test_user.id)
			db_session.add(job)
		await db_session.commit()

		# Filter by minimum salary
		response = await async_client.get("/api/v1/jobs/search", params={"min_salary": 80000})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 2  # Mid and Senior

		# Filter by maximum salary
		response = await async_client.get("/api/v1/jobs/search", params={"max_salary": 100000})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 2  # Junior and Mid

	async def test_tech_stack_filtering(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test tech stack filtering with multiple values"""
		jobs_data = [
			{"company": "CompanyA", "title": "Backend Dev", "tech_stack": ["Python", "Django", "PostgreSQL"]},
			{"company": "CompanyB", "title": "Frontend Dev", "tech_stack": ["React", "TypeScript", "Node.js"]},
			{"company": "CompanyC", "title": "Full Stack Dev", "tech_stack": ["Python", "React", "PostgreSQL"]},
		]
		
		for job_data in jobs_data:
			job = Job(**job_data, user_id=test_user.id)
			db_session.add(job)
		await db_session.commit()

		# Filter by single tech
		response = await async_client.get("/api/v1/jobs/search", params={"tech_stack": ["Python"]})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 2  # Backend and Full Stack

		# Filter by multiple techs (OR logic)
		response = await async_client.get("/api/v1/jobs/search", params={"tech_stack": ["Python", "React"]})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 3  # All jobs have at least one of these

	async def test_combined_filters(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test combining multiple filters"""
		jobs_data = [
			{
				"company": "TechCorp",
				"title": "Senior Python Developer",
				"location": "San Francisco, CA",
				"remote_option": "remote",
				"job_type": "full-time",
				"salary_min": 120000,
				"salary_max": 150000,
				"tech_stack": ["Python", "Django", "AWS"]
			},
			{
				"company": "DataInc",
				"title": "Junior Python Developer",
				"location": "New York, NY",
				"remote_option": "onsite",
				"job_type": "full-time",
				"salary_min": 60000,
				"salary_max": 80000,
				"tech_stack": ["Python", "Flask"]
			},
		]
		
		for job_data in jobs_data:
			job = Job(**job_data, user_id=test_user.id)
			db_session.add(job)
		await db_session.commit()

		# Combine multiple filters
		response = await async_client.get(
			"/api/v1/jobs/search",
			params={
				"query": "Python",
				"remote_only": True,
				"min_salary": 100000,
				"tech_stack": ["AWS"]
			}
		)
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 1
		assert results[0]["title"] == "Senior Python Developer"

	async def test_pagination(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test search pagination"""
		# Create 25 test jobs
		for i in range(25):
			job = Job(
				company=f"Company{i}",
				title=f"Developer {i}",
				user_id=test_user.id
			)
			db_session.add(job)
		await db_session.commit()

		# First page
		response = await async_client.get("/api/v1/jobs/search", params={"skip": 0, "limit": 10})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 10

		# Second page
		response = await async_client.get("/api/v1/jobs/search", params={"skip": 10, "limit": 10})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 10

		# Third page
		response = await async_client.get("/api/v1/jobs/search", params={"skip": 20, "limit": 10})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 5


@pytest.mark.asyncio
class TestApplicationSearch:
	"""Test advanced application search functionality"""

	async def test_basic_application_search(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test basic application search with query parameter"""
		# Create test job and applications
		job1 = Job(company="TechCorp", title="Python Developer", user_id=test_user.id)
		job2 = Job(company="DataInc", title="Data Scientist", user_id=test_user.id)
		db_session.add_all([job1, job2])
		await db_session.commit()

		app1 = Application(job_id=job1.id, user_id=test_user.id, status="applied", notes="Great opportunity")
		app2 = Application(job_id=job2.id, user_id=test_user.id, status="interview")
		db_session.add_all([app1, app2])
		await db_session.commit()

		# Search by job title
		response = await async_client.get("/api/v1/applications/search", params={"query": "Python"})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 1

		# Search by notes
		response = await async_client.get("/api/v1/applications/search", params={"query": "opportunity"})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 1

	async def test_status_filtering(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test application status filtering"""
		# Create test job
		job = Job(company="TechCorp", title="Developer", user_id=test_user.id)
		db_session.add(job)
		await db_session.commit()

		# Create applications with different statuses
		statuses = ["interested", "applied", "interview", "offer", "rejected"]
		for status in statuses:
			app = Application(job_id=job.id, user_id=test_user.id, status=status)
			db_session.add(app)
		await db_session.commit()

		# Filter by status
		response = await async_client.get("/api/v1/applications/search", params={"status": "applied"})
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 1
		assert results[0]["status"] == "applied"

	async def test_date_range_filtering(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test application date range filtering"""
		# Create test job
		job = Job(company="TechCorp", title="Developer", user_id=test_user.id)
		db_session.add(job)
		await db_session.commit()

		# Create applications with different dates
		today = datetime.now()
		dates = [
			today - timedelta(days=10),
			today - timedelta(days=5),
			today,
		]
		
		for date in dates:
			app = Application(job_id=job.id, user_id=test_user.id, status="applied")
			app.created_at = date
			db_session.add(app)
		await db_session.commit()

		# Filter by date range
		start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
		end_date = today.strftime("%Y-%m-%d")
		
		response = await async_client.get(
			"/api/v1/applications/search",
			params={"start_date": start_date, "end_date": end_date}
		)
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 2  # Last 7 days

	async def test_sorting(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test application sorting by multiple fields"""
		# Create test job
		job = Job(company="TechCorp", title="Developer", user_id=test_user.id)
		db_session.add(job)
		await db_session.commit()

		# Create applications
		for i in range(3):
			app = Application(
				job_id=job.id,
				user_id=test_user.id,
				status=["interested", "applied", "interview"][i]
			)
			db_session.add(app)
		await db_session.commit()

		# Sort by status ascending
		response = await async_client.get(
			"/api/v1/applications/search",
			params={"sort_by": "status", "sort_order": "asc"}
		)
		assert response.status_code == 200
		results = response.json()
		assert results[0]["status"] == "applied"

		# Sort by created_at descending (default)
		response = await async_client.get(
			"/api/v1/applications/search",
			params={"sort_by": "created_at", "sort_order": "desc"}
		)
		assert response.status_code == 200
		results = response.json()
		assert len(results) == 3

	async def test_invalid_sort_field(self, async_client: AsyncClient, test_user: User):
		"""Test error handling for invalid sort field"""
		response = await async_client.get(
			"/api/v1/applications/search",
			params={"sort_by": "invalid_field"}
		)
		assert response.status_code == 400
		assert "Invalid sort_by field" in response.json()["detail"]

	async def test_invalid_date_format(self, async_client: AsyncClient, test_user: User):
		"""Test error handling for invalid date format"""
		response = await async_client.get(
			"/api/v1/applications/search",
			params={"start_date": "invalid-date"}
		)
		assert response.status_code == 400
		assert "Invalid start_date format" in response.json()["detail"]


@pytest.mark.asyncio
class TestSearchCaching:
	"""Test search result caching"""

	async def test_job_search_caching(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test that job search results are cached"""
		# Create test job
		job = Job(company="TechCorp", title="Python Developer", user_id=test_user.id)
		db_session.add(job)
		await db_session.commit()

		# First request (cache miss)
		response1 = await async_client.get("/api/v1/jobs/search", params={"query": "Python", "use_cache": True})
		assert response1.status_code == 200
		results1 = response1.json()

		# Second request (cache hit)
		response2 = await async_client.get("/api/v1/jobs/search", params={"query": "Python", "use_cache": True})
		assert response2.status_code == 200
		results2 = response2.json()

		# Results should be identical
		assert results1 == results2

	async def test_application_search_caching(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test that application search results are cached"""
		# Create test job and application
		job = Job(company="TechCorp", title="Developer", user_id=test_user.id)
		db_session.add(job)
		await db_session.commit()

		app = Application(job_id=job.id, user_id=test_user.id, status="applied")
		db_session.add(app)
		await db_session.commit()

		# First request (cache miss)
		response1 = await async_client.get("/api/v1/applications/search", params={"status": "applied", "use_cache": True})
		assert response1.status_code == 200
		results1 = response1.json()

		# Second request (cache hit)
		response2 = await async_client.get("/api/v1/applications/search", params={"status": "applied", "use_cache": True})
		assert response2.status_code == 200
		results2 = response2.json()

		# Results should be identical
		assert results1 == results2

	async def test_cache_bypass(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test that caching can be bypassed"""
		# Create test job
		job = Job(company="TechCorp", title="Developer", user_id=test_user.id)
		db_session.add(job)
		await db_session.commit()

		# Request with cache disabled
		response = await async_client.get("/api/v1/jobs/search", params={"query": "Developer", "use_cache": False})
		assert response.status_code == 200


@pytest.mark.asyncio
class TestSearchPerformance:
	"""Test search performance with large datasets"""

	async def test_large_dataset_search(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test search performance with 1000+ jobs"""
		# Create 1000 test jobs
		jobs = []
		for i in range(1000):
			job = Job(
				company=f"Company{i}",
				title=f"Developer {i}",
				location=f"City{i % 10}",
				remote_option=["remote", "hybrid", "onsite"][i % 3],
				job_type=["full-time", "part-time", "contract"][i % 3],
				salary_min=50000 + (i * 100),
				salary_max=100000 + (i * 100),
				tech_stack=["Python", "JavaScript", "Java"][i % 3:i % 3 + 1],
				user_id=test_user.id
			)
			jobs.append(job)
		
		db_session.add_all(jobs)
		await db_session.commit()

		# Test search performance
		import time
		start_time = time.time()
		
		response = await async_client.get(
			"/api/v1/jobs/search",
			params={
				"query": "Developer",
				"remote_only": True,
				"min_salary": 80000,
				"limit": 100
			}
		)
		
		end_time = time.time()
		elapsed_time = end_time - start_time

		assert response.status_code == 200
		# Should complete in under 2 seconds (requirement: sub-second for most queries)
		assert elapsed_time < 2.0, f"Search took {elapsed_time:.2f}s, expected < 2.0s"

	async def test_indexed_field_performance(self, async_client: AsyncClient, test_user: User, db_session: AsyncSession):
		"""Test that indexed fields provide fast queries"""
		# Create test jobs
		for i in range(500):
			job = Job(
				company=f"Company{i}",
				title=f"Developer {i}",
				location=f"City{i % 5}",
				user_id=test_user.id
			)
			db_session.add(job)
		await db_session.commit()

		# Test location filter (should use index)
		import time
		start_time = time.time()
		
		response = await async_client.get("/api/v1/jobs/search", params={"location": "City1"})
		
		end_time = time.time()
		elapsed_time = end_time - start_time

		assert response.status_code == 200
		# Should be very fast with index
		assert elapsed_time < 1.0, f"Indexed query took {elapsed_time:.2f}s, expected < 1.0s"
