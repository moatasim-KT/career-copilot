import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.job import Job
from app.services.recommendation_engine import RecommendationEngine
from app.services.adaptive_recommendation_engine import AdaptiveRecommendationEngine
from datetime import datetime, timedelta

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_user():
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        skills=["Python", "FastAPI", "SQL"],
        preferred_locations=["remote", "New York"],
        experience_level="mid"
    )
    return user

@pytest.fixture
def mock_job_not_applied():
    job = Job(
        id=101,
        user_id=1,
        company="TechCorp",
        title="Python Developer",
        location="Remote",
        description="Develop backend services with Python and FastAPI.",
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
        status="not_applied"
    )
    return job

@pytest.fixture
def mock_job_applied():
    job = Job(
        id=102,
        user_id=1,
        company="OtherCo",
        title="Data Scientist",
        location="San Francisco",
        description="Analyze data and build models.",
        tech_stack=["Python", "Machine Learning", "SQL"],
        status="applied"
    )
    return job

@pytest.fixture
def mock_job_low_match():
    job = Job(
        id=103,
        user_id=1,
        company="Startup",
        title="Frontend Engineer",
        location="Remote",
        description="Build UIs with React.",
        tech_stack=["JavaScript", "React"],
        status="not_applied"
    )
    return job

@pytest.fixture
def recommendation_engine(mock_db):
    return RecommendationEngine(mock_db)

@pytest.fixture
def adaptive_recommendation_engine(mock_db):
    return AdaptiveRecommendationEngine(mock_db)


class TestRecommendationEngine:
    def test_calculate_match_score_high(self, recommendation_engine, mock_user, mock_job_not_applied):
        score = recommendation_engine.calculate_match_score(mock_user, mock_job_not_applied)
        assert score >= 60 # Expect a high score for a good match

    def test_calculate_match_score_low(self, recommendation_engine, mock_user, mock_job_low_match):
        score = recommendation_engine.calculate_match_score(mock_user, mock_job_low_match)
        assert score < 50 # Expect a low score for a poor match

    def test_get_recommendations_filters_applied_jobs(self, recommendation_engine, mock_db, mock_user, mock_job_not_applied, mock_job_applied):
        # Mock the query to return only not_applied jobs
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_job_not_applied]
        recommendations = recommendation_engine.get_recommendations(mock_user)
        assert len(recommendations) == 1
        assert recommendations[0]["job"].id == mock_job_not_applied.id

    def test_get_recommendations_sorts_by_score(self, recommendation_engine, mock_db, mock_user, mock_job_not_applied, mock_job_low_match):
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_job_not_applied, mock_job_low_match]
        recommendations = recommendation_engine.get_recommendations(mock_user, limit=2)
        assert len(recommendations) == 2
        assert recommendations[0]["score"] > recommendations[1]["score"]
        assert recommendations[0]["job"].id == mock_job_not_applied.id


class TestAdaptiveRecommendationEngine:
    def test_get_user_algorithm_variant(self, adaptive_recommendation_engine, mock_user):
        # Test with active A/B test
        with patch.object(adaptive_recommendation_engine, 'ab_test_configs', {
            "test_ab": {"active": True, "traffic_split": 0.5, "variant_a": {}, "variant_b": {}}
        }):
            # Mock hashlib to control variant assignment
            with patch('app.services.adaptive_recommendation_engine.hashlib.md5') as mock_md5:
                mock_md5.return_value.hexdigest.return_value = "1234567890abcdef1234567890abcdef" # Hash value for variant A
                variant_a = adaptive_recommendation_engine.get_user_algorithm_variant(mock_user.id, "test_ab")
                assert variant_a == "variant_a"

                mock_md5.return_value.hexdigest.return_value = "fedcba0987654321fedcba0987654321" # Hash value for variant B
                variant_b = adaptive_recommendation_engine.get_user_algorithm_variant(mock_user.id, "test_ab")
                assert variant_b == "variant_b"

    def test_get_algorithm_weights_default(self, adaptive_recommendation_engine, mock_user):
        # Ensure no A/B tests are active for this test
        with patch.object(adaptive_recommendation_engine, 'ab_test_configs', {}):
            weights = adaptive_recommendation_engine.get_algorithm_weights(mock_user.id)
            assert weights == adaptive_recommendation_engine.default_weights

    def test_get_algorithm_weights_ab_test_active(self, adaptive_recommendation_engine, mock_user, mocker):
        # Test A/B test active
        mocker.patch.object(adaptive_recommendation_engine, 'ab_test_configs', {
            "test_ab": {"active": True, "traffic_split": 0.5, 
                        "variant_a": {"skill_matching": 10, "location_matching": 10, "experience_matching": 80},
                        "variant_b": {"skill_matching": 80, "location_matching": 10, "experience_matching": 10}}
        })
        mocker.patch('app.services.adaptive_recommendation_engine.hashlib.md5', return_value=mocker.MagicMock(hexdigest=mocker.MagicMock(return_value="fedcba0987654321fedcba0987654321"))) # Variant B
        weights = adaptive_recommendation_engine.get_algorithm_weights(mock_user.id)
        assert weights == {"skill_matching": 80, "location_matching": 10, "experience_matching": 10}

    def test_calculate_match_score_adaptive(self, adaptive_recommendation_engine, mock_user, mock_job_not_applied):
        weights = {"skill_matching": 100, "location_matching": 0, "experience_matching": 0}
        score = adaptive_recommendation_engine.calculate_match_score_adaptive(mock_user, mock_job_not_applied, weights)
        assert score > 0

    def test_get_recommendations_adaptive(self, adaptive_recommendation_engine, mock_db, mock_user, mock_job_not_applied, mock_job_low_match):
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_job_not_applied, mock_job_low_match]
        recommendations = adaptive_recommendation_engine.get_recommendations_adaptive(mock_user, limit=2)
        assert len(recommendations) == 2
        assert recommendations[0]["score"] > recommendations[1]["score"]
        assert recommendations[0]["job"].id == mock_job_not_applied.id

    def test_update_algorithm_weights(self, adaptive_recommendation_engine):
        new_weights = {"skill_matching": 40, "location_matching": 30, "experience_matching": 30}
        adaptive_recommendation_engine.update_algorithm_weights(new_weights)
        assert adaptive_recommendation_engine.default_weights == new_weights

    def test_start_ab_test(self, adaptive_recommendation_engine):
        adaptive_recommendation_engine.start_ab_test(
            "new_test",
            {"skill_matching": 10, "location_matching": 10, "experience_matching": 80},
            {"skill_matching": 80, "location_matching": 10, "experience_matching": 10},
            0.7
        )
        assert "new_test" in adaptive_recommendation_engine.ab_test_configs
        assert adaptive_recommendation_engine.ab_test_configs["new_test"]["active"] is True

    def test_stop_ab_test(self, adaptive_recommendation_engine):
        adaptive_recommendation_engine.start_ab_test(
            "test_to_stop",
            {"skill_matching": 10, "location_matching": 10, "experience_matching": 80},
            {"skill_matching": 80, "location_matching": 10, "experience_matching": 10},
            0.7
        )
        adaptive_recommendation_engine.stop_ab_test("test_to_stop")
        assert adaptive_recommendation_engine.ab_test_configs["test_to_stop"]["active"] is False

    def test_get_ab_test_results(self, adaptive_recommendation_engine, mock_db, mock_user):
        # Mock feedback data
        mock_feedback = MagicMock()
        mock_feedback.user_id = mock_user.id
        mock_feedback.is_helpful = True
        mock_feedback.created_at = datetime.utcnow() - timedelta(days=1)

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_feedback]

        with patch.object(adaptive_recommendation_engine, 'ab_test_configs', {
            "test_ab": {"active": True, "traffic_split": 0.5, 
                        "variant_a": {"skill_matching": 10, "location_matching": 10, "experience_matching": 80},
                        "variant_b": {"skill_matching": 80, "location_matching": 10, "experience_matching": 10}}
        }):
            # Mock hashlib to control variant assignment for feedback
            with patch('app.services.adaptive_recommendation_engine.hashlib.md5') as mock_md5:
                mock_md5.return_value.hexdigest.return_value = "fedcba0987654321fedcba0987654321" # Variant B
                results = adaptive_recommendation_engine.get_ab_test_results("test_ab")
                assert results["variant_b"]["metrics"]["total"] == 1
                assert results["variant_b"]["metrics"]["satisfaction_rate"] == 1.0
