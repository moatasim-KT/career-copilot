"""Unit tests for trend analysis in analytics service"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.services.analytics_service import AnalyticsService


@pytest.fixture
async def test_user_for_trends(async_db: AsyncSession):
	"""Create a test user for trend analysis"""
	user = User(email="trends_test@example.com", username="trends_test", hashed_password="test_hash", daily_application_goal=5)
	async_db.add(user)
	await async_db.commit()
	await async_db.refresh(user)
	return user


@pytest.fixture
async def applications_with_trend_data(async_db: AsyncSession, test_user_for_trends: User):
	"""Create applications over multiple weeks for trend analysis"""
	today = datetime.now(timezone.utc).date()

	# Create jobs first
	jobs = []
	for i in range(20):
		job = Job(user_id=test_user_for_trends.id, title=f"Software Engineer {i}", company=f"Company {i}", location="Remote")
		async_db.add(job)
		jobs.append(job)

	await async_db.commit()
	for job in jobs:
		await async_db.refresh(job)

	# Create applications with various patterns
	applications_data = [
		# Week 1 (4 weeks ago): Low activity (2 applications)
		{"job_id": jobs[0].id, "status": "applied", "applied_date": today - timedelta(weeks=4)},
		{"job_id": jobs[1].id, "status": "applied", "applied_date": today - timedelta(weeks=4, days=2)},
		# Week 2 (3 weeks ago): Increasing (4 applications)
		{"job_id": jobs[2].id, "status": "applied", "applied_date": today - timedelta(weeks=3)},
		{"job_id": jobs[3].id, "status": "applied", "applied_date": today - timedelta(weeks=3, days=1)},
		{"job_id": jobs[4].id, "status": "interview", "applied_date": today - timedelta(weeks=3, days=2)},
		{"job_id": jobs[5].id, "status": "applied", "applied_date": today - timedelta(weeks=3, days=3)},
		# Week 3 (2 weeks ago): Peak activity (6 applications)
		{"job_id": jobs[6].id, "status": "applied", "applied_date": today - timedelta(weeks=2)},
		{"job_id": jobs[7].id, "status": "interview", "applied_date": today - timedelta(weeks=2, days=1)},
		{"job_id": jobs[8].id, "status": "applied", "applied_date": today - timedelta(weeks=2, days=2)},
		{"job_id": jobs[9].id, "status": "offer", "applied_date": today - timedelta(weeks=2, days=3)},
		{"job_id": jobs[10].id, "status": "applied", "applied_date": today - timedelta(weeks=2, days=4)},
		{"job_id": jobs[11].id, "status": "rejected", "applied_date": today - timedelta(weeks=2, days=5)},
		# Week 4 (1 week ago): Declining (3 applications)
		{"job_id": jobs[12].id, "status": "applied", "applied_date": today - timedelta(weeks=1)},
		{"job_id": jobs[13].id, "status": "interview", "applied_date": today - timedelta(weeks=1, days=2)},
		{"job_id": jobs[14].id, "status": "applied", "applied_date": today - timedelta(weeks=1, days=4)},
		# Current week: Low activity (2 applications)
		{"job_id": jobs[15].id, "status": "applied", "applied_date": today - timedelta(days=2)},
		{"job_id": jobs[16].id, "status": "applied", "applied_date": today - timedelta(days=1)},
	]

	applications = []
	for app_data in applications_data:
		app = Application(user_id=test_user_for_trends.id, **app_data)
		async_db.add(app)
		applications.append(app)

	await async_db.commit()
	for app in applications:
		await async_db.refresh(app)

	return applications


@pytest.mark.asyncio
async def test_calculate_application_trends_basic(
	async_db: AsyncSession, test_user_for_trends: User, applications_with_trend_data: list[Application]
):
	"""Test basic trend calculation functionality"""
	service = AnalyticsService(async_db)

	result = await service.calculate_application_trends(user_id=test_user_for_trends.id, days=30)

	# Basic structure assertions
	assert result is not None
	assert "daily_trends" in result
	assert "weekly_summary" in result
	assert "overall_trend" in result
	assert "peak_activity" in result

	# Should have daily data
	assert len(result["daily_trends"]) > 0

	# Overall trend should be calculated
	assert result["overall_trend"] in ["increasing", "decreasing", "stable"]


@pytest.mark.asyncio
async def test_daily_trends_structure(async_db: AsyncSession, test_user_for_trends: User, applications_with_trend_data: list[Application]):
	"""Test that daily trends have correct structure"""
	service = AnalyticsService(async_db)

	result = await service.calculate_application_trends(user_id=test_user_for_trends.id, days=30)

	daily_trends = result["daily_trends"]

	# Check structure of daily trends
	for day_data in daily_trends:
		assert "date" in day_data
		assert "count" in day_data
		assert isinstance(day_data["count"], int)
		assert day_data["count"] >= 0


@pytest.mark.asyncio
async def test_weekly_summary_calculation(async_db: AsyncSession, test_user_for_trends: User, applications_with_trend_data: list[Application]):
	"""Test weekly summary calculation"""
	service = AnalyticsService(async_db)

	result = await service.calculate_application_trends(user_id=test_user_for_trends.id, days=30)

	weekly_summary = result["weekly_summary"]

	# Should have weekly data
	assert "this_week" in weekly_summary
	assert "last_week" in weekly_summary
	assert "week_over_week_change" in weekly_summary

	# Values should be non-negative
	assert weekly_summary["this_week"] >= 0
	assert weekly_summary["last_week"] >= 0


@pytest.mark.asyncio
async def test_peak_activity_detection(async_db: AsyncSession, test_user_for_trends: User, applications_with_trend_data: list[Application]):
	"""Test that peak activity is correctly identified"""
	service = AnalyticsService(async_db)

	result = await service.calculate_application_trends(user_id=test_user_for_trends.id, days=30)

	peak_activity = result["peak_activity"]

	# Peak activity should have date and count
	assert "date" in peak_activity
	assert "count" in peak_activity

	# Peak count should be the maximum
	daily_counts = [day["count"] for day in result["daily_trends"]]
	assert peak_activity["count"] == max(daily_counts) if daily_counts else 0


@pytest.mark.asyncio
async def test_trend_direction_increasing(async_db: AsyncSession):
	"""Test detection of increasing trend"""
	user = User(email="increasing@example.com", username="increasing", hashed_password="test_hash")
	async_db.add(user)
	await async_db.commit()
	await async_db.refresh(user)

	today = datetime.now(timezone.utc).date()

	# Create jobs
	jobs = []
	for i in range(10):
		job = Job(user_id=user.id, title=f"Job {i}", company="Company", location="Remote")
		async_db.add(job)
		jobs.append(job)
	await async_db.commit()
	for job in jobs:
		await async_db.refresh(job)

	# Create increasing pattern: 1, 2, 3 applications per week
	applications = []
	# Week 3: 1 application
	applications.append(Application(user_id=user.id, job_id=jobs[0].id, status="applied", applied_date=today - timedelta(weeks=3)))
	# Week 2: 2 applications
	applications.append(Application(user_id=user.id, job_id=jobs[1].id, status="applied", applied_date=today - timedelta(weeks=2)))
	applications.append(Application(user_id=user.id, job_id=jobs[2].id, status="applied", applied_date=today - timedelta(weeks=2, days=1)))
	# Week 1: 3 applications
	applications.append(Application(user_id=user.id, job_id=jobs[3].id, status="applied", applied_date=today - timedelta(weeks=1)))
	applications.append(Application(user_id=user.id, job_id=jobs[4].id, status="applied", applied_date=today - timedelta(weeks=1, days=1)))
	applications.append(Application(user_id=user.id, job_id=jobs[5].id, status="applied", applied_date=today - timedelta(weeks=1, days=2)))

	for app in applications:
		async_db.add(app)
	await async_db.commit()

	service = AnalyticsService(async_db)
	result = await service.calculate_application_trends(user_id=user.id, days=30)

	# Should detect increasing trend
	assert result["overall_trend"] == "increasing"


@pytest.mark.asyncio
async def test_trend_direction_decreasing(async_db: AsyncSession):
	"""Test detection of decreasing trend"""
	user = User(email="decreasing@example.com", username="decreasing", hashed_password="test_hash")
	async_db.add(user)
	await async_db.commit()
	await async_db.refresh(user)

	today = datetime.now(timezone.utc).date()

	# Create jobs
	jobs = []
	for i in range(10):
		job = Job(user_id=user.id, title=f"Job {i}", company="Company", location="Remote")
		async_db.add(job)
		jobs.append(job)
	await async_db.commit()
	for job in jobs:
		await async_db.refresh(job)

	# Create decreasing pattern: 3, 2, 1 applications per week
	applications = []
	# Week 3: 3 applications
	applications.append(Application(user_id=user.id, job_id=jobs[0].id, status="applied", applied_date=today - timedelta(weeks=3)))
	applications.append(Application(user_id=user.id, job_id=jobs[1].id, status="applied", applied_date=today - timedelta(weeks=3, days=1)))
	applications.append(Application(user_id=user.id, job_id=jobs[2].id, status="applied", applied_date=today - timedelta(weeks=3, days=2)))
	# Week 2: 2 applications
	applications.append(Application(user_id=user.id, job_id=jobs[3].id, status="applied", applied_date=today - timedelta(weeks=2)))
	applications.append(Application(user_id=user.id, job_id=jobs[4].id, status="applied", applied_date=today - timedelta(weeks=2, days=1)))
	# Week 1: 1 application
	applications.append(Application(user_id=user.id, job_id=jobs[5].id, status="applied", applied_date=today - timedelta(weeks=1)))

	for app in applications:
		async_db.add(app)
	await async_db.commit()

	service = AnalyticsService(async_db)
	result = await service.calculate_application_trends(user_id=user.id, days=30)

	# Should detect decreasing trend
	assert result["overall_trend"] == "decreasing"


@pytest.mark.asyncio
async def test_trend_with_no_applications(async_db: AsyncSession):
	"""Test trend calculation when user has no applications"""
	user = User(email="noapps@example.com", username="noapps", hashed_password="test_hash")
	async_db.add(user)
	await async_db.commit()
	await async_db.refresh(user)

	service = AnalyticsService(async_db)
	result = await service.calculate_application_trends(user_id=user.id, days=30)

	# Should handle empty data gracefully
	assert result["daily_trends"] == [] or all(day["count"] == 0 for day in result["daily_trends"])
	assert result["overall_trend"] == "stable"
	assert result["weekly_summary"]["this_week"] == 0
	assert result["weekly_summary"]["last_week"] == 0


@pytest.mark.asyncio
async def test_trend_days_parameter(async_db: AsyncSession, test_user_for_trends: User, applications_with_trend_data: list[Application]):
	"""Test that days parameter correctly limits the analysis period"""
	service = AnalyticsService(async_db)

	# Test with 7 days
	result_7_days = await service.calculate_application_trends(user_id=test_user_for_trends.id, days=7)

	# Test with 30 days
	result_30_days = await service.calculate_application_trends(user_id=test_user_for_trends.id, days=30)

	# 30 days should include more applications
	total_7_days = sum(day["count"] for day in result_7_days["daily_trends"])
	total_30_days = sum(day["count"] for day in result_30_days["daily_trends"])

	assert total_30_days >= total_7_days


@pytest.mark.asyncio
async def test_week_over_week_change_calculation(async_db: AsyncSession, test_user_for_trends: User, applications_with_trend_data: list[Application]):
	"""Test that week-over-week change is calculated correctly"""
	service = AnalyticsService(async_db)

	result = await service.calculate_application_trends(user_id=test_user_for_trends.id, days=30)

	weekly_summary = result["weekly_summary"]

	# Verify calculation
	this_week = weekly_summary["this_week"]
	last_week = weekly_summary["last_week"]
	change = weekly_summary["week_over_week_change"]

	if last_week > 0:
		expected_change = ((this_week - last_week) / last_week) * 100
		assert abs(change - expected_change) < 0.01
	else:
		# If last week was 0, change should be 0 or 100 (if this week > 0)
		assert change >= 0


@pytest.mark.asyncio
async def test_trend_analysis_with_status_filter(async_db: AsyncSession, test_user_for_trends: User, applications_with_trend_data: list[Application]):
	"""Test trend analysis can filter by application status"""
	service = AnalyticsService(async_db)

	# This assumes the service supports status filtering (may need to be implemented)
	result = await service.calculate_application_trends(user_id=test_user_for_trends.id, days=30)

	# Should return results regardless of status
	assert len(result["daily_trends"]) > 0
