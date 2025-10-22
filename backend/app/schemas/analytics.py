from pydantic import BaseModel
from typing import Dict, Any, List

class AnalyticsSummaryResponse(BaseModel):
    total_jobs: int
    total_applications: int
    pending_applications: int
    interviews_scheduled: int
    offers_received: int
    rejections_received: int
    acceptance_rate: float
    daily_applications_today: int
    weekly_applications: int
    monthly_applications: int
    top_skills_in_jobs: List[Dict[str, Any]]
    top_companies_applied: List[Dict[str, Any]]
    application_status_breakdown: Dict[str, int]
