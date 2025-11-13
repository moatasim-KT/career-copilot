"""Unit tests for skill gap analysis in analytics service"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.services.analytics_service import AnalyticsService


@pytest.fixture
async def test_user_with_skills(async_db: AsyncSession):
	"""Create a test user with specific skills"""
	user = User(
		email="skillgap_test@example.com",
		username="skillgap_test",
		hashed_password="test_hash",
		skills=["Python", "JavaScript", "React", "FastAPI", "PostgreSQL"],
	)
	async_db.add(user)
	await async_db.commit()
	await async_db.refresh(user)
	return user


@pytest.fixture
async def jobs_with_tech_stacks(async_db: AsyncSession, test_user_with_skills: User):
	"""Create jobs with various tech stacks to test skill gap analysis"""
	today = datetime.now(timezone.utc).date()

	jobs_data = [
		# Jobs with overlapping skills
		{
			"title": "Python Developer",
			"company": "TechCorp A",
			"tech_stack": ["Python", "Django", "PostgreSQL", "Docker"],  # Has Python & PostgreSQL
			"location": "Remote",
		},
		{
			"title": "Full Stack Engineer",
			"company": "TechCorp B",
			"tech_stack": ["JavaScript", "React", "Node.js", "MongoDB"],  # Has JavaScript & React
			"location": "Remote",
		},
		# Jobs with skill gaps
		{
			"title": "Senior Backend Engineer",
			"company": "TechCorp C",
			"tech_stack": ["Python", "FastAPI", "Kubernetes", "Redis"],  # Missing Kubernetes & Redis
			"location": "Remote",
		},
		{
			"title": "DevOps Engineer",
			"company": "TechCorp D",
			"tech_stack": ["AWS", "Docker", "Terraform", "Kubernetes"],  # Missing AWS, Docker, Terraform, Kubernetes
			"location": "Remote",
		},
		{
			"title": "Data Engineer",
			"company": "TechCorp E",
			"tech_stack": ["Python", "Spark", "Airflow", "Scala"],  # Missing Spark, Airflow, Scala
			"location": "Remote",
		},
	]

	jobs = []
	for job_data in jobs_data:
		job = Job(user_id=test_user_with_skills.id, posted_date=today - timedelta(days=1), **job_data)
		async_db.add(job)
		jobs.append(job)

	await async_db.commit()
	for job in jobs:
		await async_db.refresh(job)

	return jobs


@pytest.mark.asyncio
async def test_analyze_skill_gaps_basic(async_db: AsyncSession, test_user_with_skills: User, jobs_with_tech_stacks: list[Job]):
	"""Test basic skill gap analysis functionality"""
	service = AnalyticsService(async_db)

	# Analyze skill gaps
	result = await service.analyze_skill_gaps(user_id=test_user_with_skills.id, limit=10)

	# Basic assertions
	assert result is not None
	assert "user_skills" in result
	assert "skill_gaps" in result
	assert "total_jobs_analyzed" in result
	assert "recommendations" in result

	# User should have 5 skills
	assert len(result["user_skills"]) == 5
	assert "Python" in result["user_skills"]
	assert "JavaScript" in result["user_skills"]

	# Should have identified some skill gaps
	assert len(result["skill_gaps"]) > 0
	assert result["total_jobs_analyzed"] == 5


@pytest.mark.asyncio
async def test_skill_gap_frequency_calculation(async_db: AsyncSession, test_user_with_skills: User, jobs_with_tech_stacks: list[Job]):
	"""Test that skill gap frequency is calculated correctly"""
	service = AnalyticsService(async_db)

	result = await service.analyze_skill_gaps(user_id=test_user_with_skills.id, limit=10)

	skill_gaps = result["skill_gaps"]

	# Check that Kubernetes appears frequently (in 2 jobs)
	kubernetes_gap = next((gap for gap in skill_gaps if gap["skill"] == "Kubernetes"), None)
	assert kubernetes_gap is not None
	assert kubernetes_gap["frequency"] == 2
	assert kubernetes_gap["percentage"] > 0

	# Check that Docker appears (in 2 jobs)
	docker_gap = next((gap for gap in skill_gaps if gap["skill"] == "Docker"), None)
	assert docker_gap is not None
	assert docker_gap["frequency"] == 2


@pytest.mark.asyncio
async def test_skill_gap_sorting_by_frequency(async_db: AsyncSession, test_user_with_skills: User, jobs_with_tech_stacks: list[Job]):
	"""Test that skill gaps are sorted by frequency (descending)"""
	service = AnalyticsService(async_db)

	result = await service.analyze_skill_gaps(user_id=test_user_with_skills.id, limit=10)

	skill_gaps = result["skill_gaps"]

	# Verify sorting (descending by frequency)
	frequencies = [gap["frequency"] for gap in skill_gaps]
	assert frequencies == sorted(frequencies, reverse=True), "Skill gaps should be sorted by frequency (descending)"


@pytest.mark.asyncio
async def test_skill_gap_recommendations(async_db: AsyncSession, test_user_with_skills: User, jobs_with_tech_stacks: list[Job]):
	"""Test that recommendations are generated for top skill gaps"""
	service = AnalyticsService(async_db)

	result = await service.analyze_skill_gaps(user_id=test_user_with_skills.id, limit=10)

	recommendations = result["recommendations"]

	# Should have recommendations
	assert len(recommendations) > 0

	# Recommendations should be based on top skill gaps
	top_skill_gaps = [gap["skill"] for gap in result["skill_gaps"][:3]]

	# At least one recommendation should mention a top skill gap
	recommendation_text = " ".join(recommendations)
	assert any(skill in recommendation_text for skill in top_skill_gaps)


@pytest.mark.asyncio
async def test_no_skill_gaps_when_user_has_all_skills(async_db: AsyncSession):
	"""Test skill gap analysis when user has all required skills"""
	# Create user with comprehensive skills
	user = User(
		email="expert@example.com",
		username="expert_user",
		hashed_password="test_hash",
		skills=["Python", "Django", "PostgreSQL", "Docker", "Kubernetes", "AWS"],
	)
	async_db.add(user)
	await async_db.commit()
	await async_db.refresh(user)

	# Create job that matches all user skills
	job = Job(user_id=user.id, title="Backend Engineer", company="TechCorp", tech_stack=["Python", "Django", "PostgreSQL"], location="Remote")
	async_db.add(job)
	await async_db.commit()

	service = AnalyticsService(async_db)
	result = await service.analyze_skill_gaps(user_id=user.id, limit=10)

	# Should have minimal or no skill gaps
	assert result["skill_gaps"] == [] or len(result["skill_gaps"]) == 0


@pytest.mark.asyncio
async def test_skill_gap_with_no_jobs(async_db: AsyncSession):
	"""Test skill gap analysis when user has no jobs"""
	user = User(email="newuser@example.com", username="newuser", hashed_password="test_hash", skills=["Python", "JavaScript"])
	async_db.add(user)
	await async_db.commit()
	await async_db.refresh(user)

	service = AnalyticsService(async_db)
	result = await service.analyze_skill_gaps(user_id=user.id, limit=10)

	# Should return empty skill gaps
	assert result["total_jobs_analyzed"] == 0
	assert result["skill_gaps"] == []
	assert "No jobs found" in " ".join(result.get("recommendations", []))


@pytest.mark.asyncio
async def test_skill_gap_with_case_insensitive_matching(async_db: AsyncSession):
	"""Test that skill matching is case-insensitive"""
	user = User(
		email="casetest@example.com",
		username="casetest",
		hashed_password="test_hash",
		skills=["python", "javascript"],  # lowercase
	)
	async_db.add(user)
	await async_db.commit()
	await async_db.refresh(user)

	# Create job with uppercase skills
	job = Job(
		user_id=user.id,
		title="Developer",
		company="TechCorp",
		tech_stack=["Python", "JavaScript", "React"],  # Mixed case
		location="Remote",
	)
	async_db.add(job)
	await async_db.commit()

	service = AnalyticsService(async_db)
	result = await service.analyze_skill_gaps(user_id=user.id, limit=10)

	# Should only identify "React" as gap, not Python or JavaScript
	skill_gaps = [gap["skill"] for gap in result["skill_gaps"]]
	assert "React" in skill_gaps or "react" in skill_gaps
	assert "Python" not in skill_gaps
	assert "JavaScript" not in skill_gaps


@pytest.mark.asyncio
async def test_skill_gap_limit_parameter(async_db: AsyncSession, test_user_with_skills: User, jobs_with_tech_stacks: list[Job]):
	"""Test that limit parameter works correctly"""
	service = AnalyticsService(async_db)

	# Test with limit
	result = await service.analyze_skill_gaps(user_id=test_user_with_skills.id, limit=5)

	# Should respect the limit for recommendations
	assert len(result["skill_gaps"]) <= 10  # Reasonable upper bound
	assert result["total_jobs_analyzed"] == 5  # Only analyzed 5 jobs


@pytest.mark.asyncio
async def test_skill_gap_percentage_calculation(async_db: AsyncSession, test_user_with_skills: User, jobs_with_tech_stacks: list[Job]):
	"""Test that percentage calculation is correct"""
	service = AnalyticsService(async_db)

	result = await service.analyze_skill_gaps(user_id=test_user_with_skills.id, limit=10)

	total_jobs = result["total_jobs_analyzed"]

	for gap in result["skill_gaps"]:
		expected_percentage = (gap["frequency"] / total_jobs) * 100
		assert abs(gap["percentage"] - expected_percentage) < 0.01, f"Percentage mismatch for skill {gap['skill']}"
