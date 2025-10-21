import pytest
from unittest.mock import MagicMock, patch
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.scheduler import start_scheduler, shutdown_scheduler, scheduler, settings
from app.tasks.job_ingestion_tasks import ingest_jobs_enhanced
from app.tasks.notification_tasks import send_morning_briefings, send_evening_summaries
from app.tasks.recommendation_tasks import generate_daily_recommendations

@pytest.fixture(autouse=True)
def mock_scheduler_components():
    with (
        patch('app.scheduler.BackgroundScheduler') as mock_bg_scheduler,
        patch('app.scheduler.SQLAlchemyJobStore') as mock_job_store,
        patch('app.scheduler.ThreadPoolExecutor') as mock_thread_pool,
        patch('app.scheduler.ProcessPoolExecutor') as mock_process_pool,
        patch('app.scheduler.get_settings') as mock_get_settings,
        patch('app.scheduler.ingest_jobs_enhanced.delay') as mock_ingest_delay,
        patch('app.scheduler.generate_daily_recommendations.delay') as mock_generate_delay,
        patch('app.scheduler.send_morning_briefings.delay') as mock_morning_delay,
        patch('app.scheduler.send_evening_summaries.delay') as mock_evening_delay,
    ):

        # Configure mock settings
        mock_settings_instance = MagicMock()
        mock_settings_instance.enable_scheduler = True
        mock_settings_instance.database_url = "sqlite:///test.db"
        mock_get_settings.return_value = mock_settings_instance
        settings.enable_scheduler = True # Ensure module-level settings is updated

        # Configure mock scheduler instance
        mock_scheduler_instance = MagicMock(spec=BackgroundScheduler)
        mock_scheduler_instance.running = False # Default to not running
        mock_bg_scheduler.return_value = mock_scheduler_instance

        yield mock_scheduler_instance, mock_ingest_delay, mock_generate_delay, mock_morning_delay, mock_evening_delay


def test_scheduler_starts_when_enabled(mock_scheduler_components):
    mock_scheduler_instance, _, _, _, _ = mock_scheduler_components
    
    settings.enable_scheduler = True # Ensure settings is enabled
    start_scheduler()
    
    mock_scheduler_instance.start.assert_called_once()
    mock_scheduler_instance.add_job.assert_called()
    assert mock_scheduler_instance.add_job.call_count == 4

def test_scheduler_does_not_start_when_disabled(mock_scheduler_components):
    mock_scheduler_instance, _, _, _, _ = mock_scheduler_components
    
    settings.enable_scheduler = False # Ensure settings is disabled
    start_scheduler()
    
    mock_scheduler_instance.start.assert_not_called()
    mock_scheduler_instance.add_job.assert_not_called()

def test_scheduler_shuts_down_when_running(mock_scheduler_components):
    mock_scheduler_instance, _, _, _, _ = mock_scheduler_components
    
    mock_scheduler_instance.running = True # Simulate scheduler is running
    shutdown_scheduler()
    
    mock_scheduler_instance.shutdown.assert_called_once()

def test_scheduler_does_not_shut_down_when_not_running(mock_scheduler_components):
    mock_scheduler_instance, _, _, _, _ = mock_scheduler_components
    
    mock_scheduler_instance.running = False # Simulate scheduler is not running
    shutdown_scheduler()
    
    mock_scheduler_instance.shutdown.assert_not_called()

def test_scheduled_tasks_are_registered(mock_scheduler_components):
    mock_scheduler_instance, mock_ingest_delay, mock_generate_delay, mock_morning_delay, mock_evening_delay = mock_scheduler_components
    
    settings.enable_scheduler = True
    start_scheduler()
    
    # Verify add_job calls for each task
    mock_scheduler_instance.add_job.assert_any_call(
        mock_ingest_delay,
        CronTrigger(hour=4, minute=0),
        id="ingest_jobs_enhanced",
        name="Nightly Job Ingestion (Celery)",
        replace_existing=True
    )
    mock_scheduler_instance.add_job.assert_any_call(
        mock_generate_delay,
        CronTrigger(hour=7, minute=30),
        id="generate_daily_recommendations",
        name="Daily Recommendation Generation (Celery)",
        replace_existing=True
    )
    mock_scheduler_instance.add_job.assert_any_call(
        mock_morning_delay,
        CronTrigger(hour=8, minute=0),
        id="send_morning_briefings",
        name="Morning Job Briefings (Celery)",
        replace_existing=True
    )
    mock_scheduler_instance.add_job.assert_any_call(
        mock_evening_delay,
        CronTrigger(hour=20, minute=0),
        id="send_evening_summaries",
        name="Evening Progress Summaries (Celery)",
        replace_existing=True
    )
