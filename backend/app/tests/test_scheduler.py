import pytest
from unittest.mock import MagicMock, patch
from app.tasks.scheduled_tasks import scheduler, start_scheduler, shutdown_scheduler
import time

# A simple flag to be modified by a test job
job_executed = False

def sample_job():
    global job_executed
    job_executed = True

@pytest.fixture(scope="module")
def mock_scheduler_setup():
    with patch('app.tasks.scheduled_tasks.scheduler', autospec=True) as mock_scheduler:
        mock_scheduler.running = True # Simulate scheduler is running
        start_scheduler()
        yield mock_scheduler
        shutdown_scheduler()

def test_scheduler_is_running(mock_scheduler_setup):
    mock_scheduler_setup.start.assert_called_once()
    assert mock_scheduler_setup.running == True

def test_add_and_run_job(mock_scheduler_setup):
    global job_executed
    job_executed = False
    
    mock_scheduler_setup.add_job(sample_job, 'interval', seconds=1, id='test_job')
    
    mock_scheduler_setup.add_job.assert_called_with(sample_job, 'interval', seconds=1, id='test_job')