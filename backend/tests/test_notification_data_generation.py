"""
Tests for Notification Service Data Generation
Tests the real database query implementations for morning briefing and evening updates.
"""

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.services.notification_service import UnifiedNotificationService


@pytest.fixture
def sample_user(db: Session):
	"""Create a sample user for testing."""
	user = User(
		email="test@example.com",
		username="testuser",
		full_name="Test User",
		hashed_password="hashed_password",
	)
	db.add(user)
	db.commit()
	db.refresh(user)
	return user


@pytest.fixture
def sample_jobs(db: Session, sample_user):
	"""Create sample jobs for testing."""
	# Job from yesterday
	yesterday_job = Job(
		user_id=sample_user.id,
		title="Backend Engineer",
		company="Tech Corp",
		location="Remote",
		created_at=datetime.utcnow() - timedelta(hours=12),
	)

	# Job from 2 days ago
	old_job = Job(
		user_id=sample_user.id,
		title="Frontend Developer",
		company="Web Co",
		location="New York",
		created_at=datetime.utcnow() - timedelta(days=2),
	)

	# Job from today
	today_job = Job(
		user_id=sample_user.id,
		title="Full Stack Engineer",
		company="Startup Inc",
		location="San Francisco",
		created_at=datetime.utcnow() - timedelta(hours=2),
	)

	db.add_all([yesterday_job, old_job, today_job])
	db.commit()
	return [yesterday_job, old_job, today_job]


@pytest.fixture
def sample_applications(db: Session, sample_user, sample_jobs):
	"""Create sample applications for testing."""
	today = date.today()

	# Application with upcoming follow-up
	app_with_followup = Application(
		user_id=sample_user.id,
		job_id=sample_jobs[0].id,
		status="applied",
		applied_date=today - timedelta(days=3),
		follow_up_date=today + timedelta(days=2),
	)

	# Application with past follow-up
	app_past_followup = Application(
		user_id=sample_user.id,
		job_id=sample_jobs[1].id,
		status="applied",
		applied_date=today - timedelta(days=10),
		follow_up_date=today - timedelta(days=5),
	)

	# Application with scheduled interview
	app_with_interview = Application(
		user_id=sample_user.id,
		job_id=sample_jobs[2].id,
		status="interview",
		applied_date=today - timedelta(days=5),
		interview_date=datetime.utcnow() + timedelta(days=3),
	)

	# Application submitted today
	app_today = Application(
		user_id=sample_user.id,
		job_id=sample_jobs[0].id,
		status="applied",
		applied_date=today,
	)

	# Application with response today
	app_response_today = Application(
		user_id=sample_user.id,
		job_id=sample_jobs[1].id,
		status="interview",
		applied_date=today - timedelta(days=7),
		response_date=today,
	)

	db.add_all([app_with_followup, app_past_followup, app_with_interview, app_today, app_response_today])
	db.commit()
	return [app_with_followup, app_past_followup, app_with_interview, app_today, app_response_today]


class TestMorningBriefingDataGeneration:
	"""Test morning briefing real data generation."""

	@pytest.mark.asyncio
	async def test_morning_briefing_counts_new_jobs(self, db: Session, sample_user, sample_jobs):
		"""Test that morning briefing counts jobs from last 24 hours."""
		service = UnifiedNotificationService(db)

		content = await service._generate_morning_briefing_content(sample_user.id)

		# Should count yesterday's job and today's job (within 24 hours)
		assert content["job_matches"] == 2
		assert "greeting" in content
		assert isinstance(content["job_matches"], int)

	@pytest.mark.asyncio
	async def test_morning_briefing_counts_upcoming_followups(self, db: Session, sample_user, sample_applications):
		"""Test that morning briefing counts applications with upcoming follow-ups."""
		service = UnifiedNotificationService(db)

		content = await service._generate_morning_briefing_content(sample_user.id)

		# Should count only the application with follow-up date in next 3 days
		assert content["applications_due"] == 1
		assert isinstance(content["applications_due"], int)

	@pytest.mark.asyncio
	async def test_morning_briefing_counts_scheduled_interviews(self, db: Session, sample_user, sample_applications):
		"""Test that morning briefing counts scheduled interviews."""
		service = UnifiedNotificationService(db)

		content = await service._generate_morning_briefing_content(sample_user.id)

		# Should count the application with future interview date
		assert content["interviews_scheduled"] == 1
		assert isinstance(content["interviews_scheduled"], int)

	@pytest.mark.asyncio
	async def test_morning_briefing_personalized_greeting(self, db: Session, sample_user):
		"""Test that morning briefing includes time-appropriate greeting."""
		service = UnifiedNotificationService(db)

		content = await service._generate_morning_briefing_content(sample_user.id)

		# Greeting should be based on current time
		assert "greeting" in content
		greeting = content["greeting"]
		hour = datetime.now().hour

		if hour < 12:
			assert "morning" in greeting.lower() or "☀" in greeting
		elif hour < 17:
			assert "afternoon" in greeting.lower() or "👋" in greeting
		else:
			assert "evening" in greeting.lower() or "🌙" in greeting

	@pytest.mark.asyncio
	async def test_morning_briefing_with_no_activity(self, db: Session, sample_user):
		"""Test morning briefing with no recent activity."""
		service = UnifiedNotificationService(db)

		content = await service._generate_morning_briefing_content(sample_user.id)

		# Should return zero counts but still have greeting
		assert content["job_matches"] == 0
		assert content["applications_due"] == 0
		assert content["interviews_scheduled"] == 0
		assert "greeting" in content


class TestEveningUpdateDataGeneration:
	"""Test evening update real data generation."""

	@pytest.mark.asyncio
	async def test_evening_update_counts_new_jobs_today(self, db: Session, sample_user, sample_jobs):
		"""Test that evening update counts jobs added today."""
		service = UnifiedNotificationService(db)

		content = await service._generate_evening_update_content(sample_user.id)

		# Should count only today's job
		assert content["new_jobs"] == 1
		assert isinstance(content["new_jobs"], int)

	@pytest.mark.asyncio
	async def test_evening_update_counts_applications_submitted_today(self, db: Session, sample_user, sample_applications):
		"""Test that evening update counts applications submitted today."""
		service = UnifiedNotificationService(db)

		content = await service._generate_evening_update_content(sample_user.id)

		# Should count the application submitted today
		assert content["applications_submitted"] == 1
		assert isinstance(content["applications_submitted"], int)

	@pytest.mark.asyncio
	async def test_evening_update_counts_responses_received_today(self, db: Session, sample_user, sample_applications):
		"""Test that evening update counts responses received today."""
		service = UnifiedNotificationService(db)

		content = await service._generate_evening_update_content(sample_user.id)

		# Should count the application with response_date = today
		assert content["responses_received"] == 1
		assert isinstance(content["responses_received"], int)

	@pytest.mark.asyncio
	async def test_evening_update_summary_with_activity(self, db: Session, sample_user, sample_jobs, sample_applications):
		"""Test that evening update generates appropriate summary with activity."""
		service = UnifiedNotificationService(db)

		content = await service._generate_evening_update_content(sample_user.id)

		# Summary should mention new jobs and applications
		assert "summary" in content
		summary = content["summary"]
		assert "new matches" in summary.lower() or "applications" in summary.lower()

	@pytest.mark.asyncio
	async def test_evening_update_summary_without_activity(self, db: Session, sample_user):
		"""Test that evening update generates encouraging summary with no activity."""
		service = UnifiedNotificationService(db)

		content = await service._generate_evening_update_content(sample_user.id)

		# Should have encouraging message
		assert "summary" in content
		summary = content["summary"]
		assert "tomorrow" in summary.lower() or "fresh start" in summary.lower()
		assert content["new_jobs"] == 0
		assert content["applications_submitted"] == 0
		assert content["responses_received"] == 0

	@pytest.mark.asyncio
	async def test_evening_update_structure(self, db: Session, sample_user):
		"""Test that evening update has correct structure."""
		service = UnifiedNotificationService(db)

		content = await service._generate_evening_update_content(sample_user.id)

		# Should have all required fields
		assert "summary" in content
		assert "new_jobs" in content
		assert "applications_submitted" in content
		assert "responses_received" in content
		assert isinstance(content["summary"], str)
		assert isinstance(content["new_jobs"], int)
		assert isinstance(content["applications_submitted"], int)
		assert isinstance(content["responses_received"], int)
