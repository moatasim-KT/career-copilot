from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from app.models.feedback import JobRecommendationFeedback
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate, JobRecommendationFeedbackCreate
from app.services.job_recommendation_service import JobRecommendationService
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db_session():
	session = MagicMock(spec=Session)
	session.query.return_value.filter.return_value.first.return_value = None
	session.query.return_value.filter.return_value.all.return_value = []
	return session


@pytest.fixture
def job_recommendation_service(mock_db_session):
	with (
		patch("app.services.recommendation_engine.RecommendationEngine") as MockRecommendationEngine,
		patch("app.services.llm_service.get_llm_service") as MockLLMService,
	):
		MockRecommendationEngine.return_value.calculate_match_score.return_value = 0.8
		MockLLMService.return_value.generate_response.return_value = "{}"
		return JobRecommendationService(db=mock_db_session)


@pytest.fixture
def mock_user():
	user = MagicMock(spec=User)
	user.id = 1
	user.username = "testuser"
	user.email = "test@example.com"
	user.skills = ["Python", "FastAPI"]
	user.preferred_locations = ["Remote"]
	user.experience_level = "mid"
	user.profile = {
		"skills": ["Python"],
		"experience_level": "mid",
		"locations": ["Remote"],
		"career_goals": [],
		"preferences": {},
		"salary_expectations": {},
	}
	return user


@pytest.fixture
def mock_job_create_data():
	return JobCreate(
		company="TestCo",
		title="Software Engineer",
		location="Remote",
		description="Develop software",
		salary_min=80000,
		salary_max=120000,
		source="adzuna",
		application_url="http://example.com/job",
		remote_option="remote",
		tech_stack=["Python", "FastAPI"],
	)


@pytest.fixture
def mock_job(mock_job_create_data):
	job = MagicMock(spec=Job)
	job.id = 1
	job.user_id = 1
	job.created_at = datetime.now(timezone.utc)
	job.updated_at = datetime.now(timezone.utc)
	job.status = "not_applied"
	job.match_score = 0.9
	for key, value in mock_job_create_data.model_dump().items():
		setattr(job, key, value)
	return job


@pytest.fixture
def mock_feedback_create_data():
	return JobRecommendationFeedbackCreate(job_id=1, is_helpful=True, comment="Great job!")


@pytest.fixture
def mock_feedback(mock_feedback_create_data):
	feedback = MagicMock(spec=JobRecommendationFeedback)
	feedback.id = 1
	feedback.user_id = 1
	feedback.job_id = mock_feedback_create_data.job_id
	feedback.is_helpful = mock_feedback_create_data.is_helpful
	feedback.comment = mock_feedback_create_data.comment
	feedback.created_at = datetime.now(timezone.utc)
	return feedback


class TestJobRecommendationService:
	@pytest.mark.asyncio
	async def test_generate_recommendations_success(self, job_recommendation_service, mock_db_session, mock_user, mock_job):
		mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_job]
		job_recommendation_service.recommendation_engine.calculate_match_score.return_value = 0.8

		recommendations = await job_recommendation_service.generate_recommendations(mock_user.id)

		assert len(recommendations) == 1
		assert recommendations[0]["job_id"] == mock_job.id
		assert recommendations[0]["match_score"] == 0.8

	@pytest.mark.asyncio
	async def test_process_feedback_success(self, job_recommendation_service, mock_db_session, mock_user, mock_job, mock_feedback_create_data):
		mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_job, None]  # User, Job, then no existing feedback
		job_recommendation_service.db.add.return_value = None
		job_recommendation_service.db.commit.return_value = None
		job_recommendation_service.db.refresh.return_value = None

		feedback = job_recommendation_service.process_feedback(mock_user.id, mock_feedback_create_data)

		assert feedback.user_id == mock_user.id
		assert feedback.job_id == mock_feedback_create_data.job_id
		job_recommendation_service.db.add.assert_called_once()
		job_recommendation_service.db.commit.assert_called_once()

	@pytest.mark.asyncio
	async def test_normalize_job_data_success(self, job_recommendation_service, mock_job_create_data):
		normalized_job = job_recommendation_service.normalize_job_data(mock_job_create_data.model_dump(), "test_source")

		assert normalized_job.company == "TestCo"
		assert normalized_job.title == "Software Engineer"

	@pytest.mark.asyncio
	async def test_parse_job_description_success(self, job_recommendation_service):
		job_url = "http://example.com/job_desc"
		description_text = "Python developer needed. Skills: Python, FastAPI."

		with (
			patch.object(job_recommendation_service, "_scrape_job_description", return_value=description_text),
			patch.object(
				job_recommendation_service, "_parse_with_llm", return_value={"tech_stack": ["Python", "FastAPI"], "experience_level": "mid"}
			),
			patch("app.utils.redis_client.redis_client") as mock_redis,
		):
			mock_redis.get.return_value = None
			mock_redis.set.return_value = True

			parsed_data = await job_recommendation_service.parse_job_description(job_url=job_url)

			assert "tech_stack" in parsed_data
			assert "Python" in parsed_data["tech_stack"]

	@pytest.mark.asyncio
	async def test_generate_enhanced_recommendation_success(self, job_recommendation_service, mock_db_session, mock_user, mock_job):
		mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
		job_recommendation_service.calculate_enhanced_skill_score = MagicMock(return_value=(0.9, {"score": 0.9, "reason": "skill"}))
		job_recommendation_service.calculate_enhanced_experience_score = MagicMock(return_value=(0.8, {"score": 0.8, "reason": "exp"}))
		job_recommendation_service.calculate_enhanced_location_score = MagicMock(return_value=(0.7, {"score": 0.7, "reason": "loc"}))
		job_recommendation_service.calculate_market_timing_score = MagicMock(return_value=(0.95, {"score": 0.95, "reason": "timing"}))
		job_recommendation_service.calculate_salary_alignment_score = MagicMock(return_value=(0.85, {"score": 0.85, "reason": "salary"}))
		job_recommendation_service.calculate_company_preference_score = MagicMock(return_value=(0.75, {"score": 0.75, "reason": "company"}))
		job_recommendation_service.calculate_career_growth_potential_score = MagicMock(return_value=(0.8, {"score": 0.8, "reason": "growth"}))

		with patch("app.core.cache.job_recommendation_cache") as mock_cache:
			mock_cache.get.return_value = None
			mock_cache.set.return_value = True

			recommendation = await job_recommendation_service.generate_enhanced_recommendation(mock_db_session, mock_user.id, mock_job)

			assert "overall_score" in recommendation
			assert recommendation["overall_score"] > 0
			mock_cache.set.assert_called_once()

	@pytest.mark.asyncio
	async def test_get_personalized_recommendations_success(self, job_recommendation_service, mock_db_session, mock_user, mock_job):
		mock_db_session.query.return_value.filter.return_value.subquery.return_value = MagicMock()
		mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_job]
		job_recommendation_service.generate_enhanced_recommendation = MagicMock(
			return_value={"overall_score": 0.8, "confidence": 0.9, "score_breakdown": {"market_timing": {"score": 0.9}}}
		)

		with patch("app.core.cache.job_recommendation_cache") as mock_cache:
			mock_cache.get_recommendations.return_value = None
			mock_cache.set_recommendations.return_value = True

			recommendations = await job_recommendation_service.get_personalized_recommendations(mock_db_session, mock_user.id)

			assert len(recommendations) == 1
			assert recommendations[0]["overall_score"] == 0.8
			mock_cache.set_recommendations.assert_called_once()
			assert recommendations[0]["overall_score"] == 0.8
			mock_cache.set_recommendations.assert_called_once()
