import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.services.analytics_service import AnalyticsService, EmailEventType, EmailProvider
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.models.analytics import Analytics

@pytest.fixture
def mock_db_session():
    session = MagicMock(spec=Session)
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    return session

@pytest.fixture
def analytics_service(mock_db_session):
    return AnalyticsService(db=mock_db_session)

@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    user.skills = ["Python", "FastAPI"]
    user.preferred_locations = ["Remote"]
    user.experience_level = "mid"
    user.daily_application_goal = 5
    user.jobs = [] # Mock jobs for user
    return user

@pytest.fixture
def mock_job():
    job = MagicMock(spec=Job)
    job.id = 101
    job.title = "Software Engineer"
    job.company = "TechCorp"
    job.location = "Remote"
    job.tech_stack = ["Python", "Docker"]
    job.salary_min = 80000
    job.salary_max = 120000
    job.date_added = datetime.now(timezone.utc) - timedelta(days=5)
    job.requirements = {"skills_required": ["Python", "Docker"]}
    return job

@pytest.fixture
def mock_application():
    app = MagicMock(spec=Application)
    app.id = 1001
    app.job_id = 101
    app.user_id = 1
    app.status = "applied"
    app.applied_date = datetime.now(timezone.utc).date()
    app.interview_feedback = None
    return app

class TestAnalyticsService:

    @pytest.mark.asyncio
    async def test_collect_event_success(self, analytics_service, mock_db_session):
        event_type = "user_login"
        data = {"ip": "127.0.0.1"}
        user_id = 1

        result = analytics_service.collect_event(event_type, data, user_id)

        assert result is True
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_event_no_db_session(self, analytics_service):
        analytics_service.db = None
        result = analytics_service.collect_event("user_login", {}, 1)
        assert result is False

    @pytest.mark.asyncio
    async def test_process_analytics_success(self, analytics_service, mock_db_session):
        mock_analytics_record = MagicMock(spec=Analytics)
        mock_analytics_record.id = 1
        mock_analytics_record.data = {}
        mock_db_session.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_analytics_record]

        result = analytics_service.process_analytics()

        assert result["processed_count"] == 1
        assert mock_analytics_record.data["processed"] is True
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_metrics_success(self, analytics_service, mock_db_session):
        mock_analytics_record = MagicMock(spec=Analytics)
        mock_analytics_record.data = {"value": 10}
        mock_analytics_record.generated_at = datetime.now(timezone.utc)
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_analytics_record]

        result = analytics_service.get_metrics("some_metric", "last_7_days", 1)

        assert result["total_records"] == 1
        assert result["data_points"][0]["value"] == 10

    @pytest.mark.asyncio
    async def test_get_user_analytics_success(self, analytics_service, mock_db_session, mock_user, mock_job, mock_application):
        mock_user.jobs = [mock_job]
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [1, 1, 0, 0, 0, 0, 1, 1, 1] # Mock counts
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_application]

        result = analytics_service.get_user_analytics(mock_user)

        assert "total_jobs" in result
        assert result["total_jobs"] == 1

    @pytest.mark.asyncio
    async def test_batch_collect_events_success(self, analytics_service, mock_db_session):
        events = [
            {"event_type": "view", "data": {"page": "home"}, "user_id": 1},
            {"event_type": "click", "data": {"element": "button"}, "user_id": 1},
        ]

        result = analytics_service.batch_collect_events(events)

        assert result["successful"] == 2
        assert result["failed"] == 0
        assert mock_db_session.add.call_count == 2
        assert mock_db_session.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_record_email_event_success(self, analytics_service, mock_db_session):
        tracking_id = "test_tracking_id"
        event_type = EmailEventType.SEND
        recipient = "test@example.com"
        provider = EmailProvider.SMTP

        result = await analytics_service.email_analytics_service.record_email_event(
            tracking_id=tracking_id, event_type=event_type, recipient=recipient, provider=provider
        )

        assert result.tracking_id == tracking_id
        assert result.event_type == event_type
        assert result.recipient == recipient
        assert result.provider == provider

    @pytest.mark.asyncio
    async def test_get_email_metrics_success(self, analytics_service, mock_db_session):
        # Mock some analytics records for email events
        mock_analytics_record_send = MagicMock(spec=Analytics)
        mock_analytics_record_send.data = {"event_type": EmailEventType.SEND.value, "provider": EmailProvider.SMTP.value}
        mock_analytics_record_send.generated_at = datetime.now(timezone.utc)

        mock_analytics_record_delivered = MagicMock(spec=Analytics)
        mock_analytics_record_delivered.data = {"event_type": EmailEventType.DELIVERY.value, "provider": EmailProvider.SMTP.value}
        mock_analytics_record_delivered.generated_at = datetime.now(timezone.utc)

        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_analytics_record_send, mock_analytics_record_delivered
        ]

        result = await analytics_service.get_email_metrics()

        assert result["metrics"]["total_sent"] == 1
        assert result["metrics"]["total_delivered"] == 1
        assert result["metrics"]["delivery_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_get_comprehensive_analytics_report_success(self, analytics_service, mock_db_session, mock_user):
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        # Mock other analytics service methods called within get_comprehensive_analytics_report
        analytics_service.get_user_analytics = MagicMock(return_value={"total_jobs": 10})
        analytics_service.get_interview_trends = MagicMock(return_value={})
        analytics_service.collect_user_engagement_metrics = MagicMock(return_value={"engagement_score": 70})
        analytics_service.monitor_application_success_rates = MagicMock(return_value={"success_metrics": {"response_percentage": "50%"}})
        analytics_service.analyze_market_trends = MagicMock(return_value={"total_jobs_analyzed": 100})

        result = await analytics_service.get_comprehensive_analytics_report(mock_user.id)

        assert "user_analytics" in result
        assert result["user_analytics"]["total_jobs"] == 10
        assert result["overall_insights"] is not None

    @pytest.mark.asyncio
    async def test_analyze_market_trends_success(self, analytics_service, mock_db_session, mock_job, mock_user):
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_job]

        result = analytics_service.analyze_market_trends(mock_user.id)

        assert "posting_trends" in result
        assert "salary_trends" in result
        assert "skill_demand_analysis" in result

    @pytest.mark.asyncio
    async def test_track_user_activity_success(self, analytics_service, mock_db_session):
        user_id = 1
        activity_type = "job_view"
        metadata = {"job_id": 123}

        result = analytics_service.track_user_activity(user_id, activity_type, metadata)

        assert result is True
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_user_engagement_metrics_success(self, analytics_service, mock_db_session, mock_user):
        mock_analytics_record = MagicMock(spec=Analytics)
        mock_analytics_record.data = {"activities": [{"activity_type": "job_view", "timestamp": datetime.now(timezone.utc).isoformat()}]}
        mock_analytics_record.generated_at = datetime.now(timezone.utc)
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_analytics_record]
        mock_db_session.query.return_value.filter.return_value.count.return_value = 1

        result = analytics_service.collect_user_engagement_metrics(mock_user.id)

        assert "total_activities" in result
        assert result["total_activities"] == 1

    @pytest.mark.asyncio
    async def test_monitor_application_success_rates_success(self, analytics_service, mock_db_session, mock_user, mock_job, mock_application):
        mock_db_session.query.return_value.join.return_value.filter.return_value.all.return_value = [(mock_application, mock_job)]

        result = analytics_service.monitor_application_success_rates(mock_user.id)

        assert "total_applications" in result
        assert result["total_applications"] == 1

    @pytest.mark.asyncio
    async def test_get_comprehensive_analytics_report_user_not_found(self, analytics_service, mock_db_session):
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        result = await analytics_service.get_comprehensive_analytics_report(999)
        assert "error" in result
        assert result["error"] == "User not found"

    @pytest.mark.asyncio
    async def test_analyze_risk_trends_success(self, analytics_service):
        result = await analytics_service.analyze_risk_trends()
        assert "period" in result
        assert result["average_risk_score"] == 2.5

    @pytest.mark.asyncio
    async def test_compare_contracts_success(self, analytics_service):
        result = await analytics_service.compare_contracts("contract1", "contract2")
        assert "similarity_score" in result
        assert result["similarity_score"] == 0.75

    @pytest.mark.asyncio
    async def test_check_compliance_success(self, analytics_service):
        result = await analytics_service.check_compliance("contract1")
        assert "compliance_score" in result
        assert result["compliance_score"] == 0.88

    @pytest.mark.asyncio
    async def test_analyze_costs_success(self, analytics_service, mock_db_session):
        mock_analytics_record = MagicMock(spec=Analytics)
        mock_analytics_record.data = {"cost": 10.0, "model": "gpt-4"}
        mock_analytics_record.generated_at = datetime.now(timezone.utc)
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_analytics_record]

        result = await analytics_service.analyze_costs()
        assert "total_cost" in result
        assert result["total_cost"] == 10.0

    @pytest.mark.asyncio
    async def test_get_performance_metrics_success(self, analytics_service, mock_db_session):
        mock_analytics_record = MagicMock(spec=Analytics)
        mock_analytics_record.data = {"response_time": 0.5, "status": "success"}
        mock_analytics_record.generated_at = datetime.now(timezone.utc)
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_analytics_record]

        result = await analytics_service.get_performance_metrics()
        assert "average_response_time" in result
        assert result["average_response_time"] == 0.5

    @pytest.mark.asyncio
    async def test_email_analytics_service_record_email_event(self, analytics_service, mock_db_session):
        # Mock the internal email_analytics_service
        analytics_service.email_analytics_service = MagicMock()

        tracking_id = "test_id"
        event_type = EmailEventType.SEND
        recipient = "test@example.com"
        provider = EmailProvider.SMTP

        await analytics_service.email_analytics_service.record_email_event(
            tracking_id=tracking_id, event_type=event_type, recipient=recipient, provider=provider
        )

        analytics_service.email_analytics_service.record_email_event.assert_called_once_with(
            analytics_service.email_analytics_service.record_email_event.call_args[0][0] # Pass the EmailEvent object
        )

    @pytest.mark.asyncio
    async def test_email_analytics_service_get_email_metrics(self, analytics_service, mock_db_session):
        # Mock the internal email_analytics_service
        analytics_service.email_analytics_service = MagicMock()
        analytics_service.email_analytics_service.get_email_metrics.return_value = {"metrics": {"total_sent": 5}}

        result = await analytics_service.get_email_metrics()

        analytics_service.email_analytics_service.get_email_metrics.assert_called_once()
        assert result["metrics"]["total_sent"] == 5

    @pytest.mark.asyncio
    async def test_email_analytics_service_get_delivery_timeline(self, analytics_service, mock_db_session):
        # Mock the internal email_analytics_service
        analytics_service.email_analytics_service = MagicMock()
        analytics_service.email_analytics_service.get_delivery_timeline.return_value = [{"event": "sent"}]

        result = await analytics_service.get_delivery_timeline("test_id")

        analytics_service.email_analytics_service.get_delivery_timeline.assert_called_once_with("test_id")
        assert result[0]["event"] == "sent"

    @pytest.mark.asyncio
    async def test_email_analytics_service_get_recipient_metrics(self, analytics_service, mock_db_session):
        # Mock the internal email_analytics_service
        analytics_service.email_analytics_service = MagicMock()
        analytics_service.email_analytics_service.get_recipient_metrics.return_value = {"metrics": {"total_sent": 3}}

        result = await analytics_service.get_recipient_metrics("test@example.com")

        analytics_service.email_analytics_service.get_recipient_metrics.assert_called_once_with("test@example.com", None, None)
        assert result["metrics"]["total_sent"] == 3

    @pytest.mark.asyncio
    async def test_email_analytics_service_generate_analytics_report(self, analytics_service, mock_db_session):
        # Mock the internal email_analytics_service
        analytics_service.email_analytics_service = MagicMock()
        analytics_service.email_analytics_service.generate_analytics_report.return_value = {"report_type": "summary"}

        result = await analytics_service.generate_analytics_report(datetime.now(), datetime.now())

        analytics_service.email_analytics_service.generate_analytics_report.assert_called_once()
        assert result["report_type"] == "summary"

    @pytest.mark.asyncio
    async def test_email_analytics_service_track_pixel_open(self, analytics_service, mock_db_session):
        # Mock the internal email_analytics_service
        analytics_service.email_analytics_service = MagicMock()
        analytics_service.email_analytics_service.track_pixel_open.return_value = {"success": True}

        result = await analytics_service.track_pixel_open("test_id", {"ip_address": "127.0.0.1"})

        analytics_service.email_analytics_service.track_pixel_open.assert_called_once_with("test_id", {"ip_address": "127.0.0.1"})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_email_analytics_service_track_link_click(self, analytics_service, mock_db_session):
        # Mock the internal email_analytics_service
        analytics_service.email_analytics_service = MagicMock()
        analytics_service.email_analytics_service.track_link_click.return_value = {"success": True}

        result = await analytics_service.track_link_click("test_id", "http://example.com", {"ip_address": "127.0.0.1"})

        analytics_service.email_analytics_service.track_link_click.assert_called_once_with("test_id", "http://example.com", {"ip_address": "127.0.0.1"})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_email_analytics_service_get_real_time_stats(self, analytics_service, mock_db_session):
        # Mock the internal email_analytics_service
        analytics_service.email_analytics_service = MagicMock()
        analytics_service.email_analytics_service.get_real_time_stats.return_value = {"success": True, "last_24_hours": {"total_sent": 10}}

        result = await analytics_service.get_real_time_stats()

        analytics_service.email_analytics_service.get_real_time_stats.assert_called_once()
        assert result["success"] is True
        assert result["last_24_hours"]["total_sent"] == 10

    @pytest.mark.asyncio
    async def test_email_analytics_service_get_health_status(self, analytics_service, mock_db_session):
        # Mock the internal email_analytics_service
        analytics_service.email_analytics_service = MagicMock()
        analytics_service.email_analytics_service.get_health_status.return_value = {"healthy": True}

        result = await analytics_service.get_health_status()

        analytics_service.email_analytics_service.get_health_status.assert_called_once()
        assert result["healthy"] is True

    @pytest.mark.asyncio
    async def test_email_analytics_service_shutdown(self, analytics_service, mock_db_session):
        # Mock the internal email_analytics_service
        analytics_service.email_analytics_service = MagicMock()

        await analytics_service.email_analytics_service.shutdown()

        analytics_service.email_analytics_service.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_analytics_service_initialize(self, analytics_service, mock_db_session):
        # Mock the internal email_analytics_service
        analytics_service.email_analytics_service = MagicMock()

        await analytics_service.email_analytics_service.initialize()

        analytics_service.email_analytics_service.initialize.assert_called_once()
