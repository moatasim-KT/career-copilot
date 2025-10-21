"""
Celery tasks package
"""

from .monitoring import TaskMonitor
from .job_ingestion_tasks import (
    ingest_jobs_enhanced,
    ingest_jobs_for_user_enhanced,
    test_job_sources,
    get_ingestion_statistics,
    cleanup_old_jobs
)
from .notification_tasks import (
    send_morning_briefings,
    send_evening_summaries,
    check_daily_achievements,
    adaptive_timing_analysis
)
from .analytics_tasks import (
    generate_skill_gap_analysis,
    generate_application_analytics,
    generate_market_analysis,
    cleanup_old_analytics
)

__all__ = [
    "TaskMonitor",
    "ingest_jobs_enhanced",
    "ingest_jobs_for_user_enhanced", 
    "test_job_sources",
    "get_ingestion_statistics",
    "cleanup_old_jobs",
    "send_morning_briefings",
    "send_evening_summaries",
    "check_daily_achievements",
    "adaptive_timing_analysis",
    "generate_skill_gap_analysis",
    "generate_application_analytics",
    "generate_market_analysis",
    "cleanup_old_analytics"
]