"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1 import (
	analytics,
	applications,
	auth,
	backup,
	briefings,
	cache,
	dashboard_layouts,
	data_security,
	email,
	enhanced_recommendations,
	export,
	feedback,
	goals,
	health,
	jobs,
	notifications,
	oauth,
	offline,
	personalization,
	profile,
	recommendations,
	resume,
	saved_searches,
	skill_gap,
	skill_gap_analysis,
	skill_matching,
	social,
	tasks,
)

api_router = APIRouter()

# Include personalization and behavior tracking routes FIRST (before jobs router)
# This prevents /jobs/available from conflicting with /jobs/{job_id}
api_router.include_router(personalization.router, tags=["personalization"])

# Include social features routes (mentors, connections, sharing)
api_router.include_router(social.router, tags=["social"])

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include OAuth authentication routes
api_router.include_router(oauth.router, tags=["oauth"])

# Include job management routes
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

# Include application management routes
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])

# Include profile management routes
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])

# Include notification routes
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Include analytics routes
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# Include recommendation routes
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])

# Include enhanced recommendation routes
api_router.include_router(enhanced_recommendations.router, prefix="/enhanced-recommendations", tags=["enhanced-recommendations"])

# Include skill gap analysis routes
api_router.include_router(skill_gap_analysis.router, prefix="/skill-gap-analysis", tags=["skill-gap-analysis"])

# Include simple skill gap route
api_router.include_router(skill_gap.router, tags=["skill-gap"])

# Include health check routes
api_router.include_router(health.router, tags=["health"])

# Include task management routes
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# Include skill matching routes
api_router.include_router(skill_matching.router, prefix="/skill-matching", tags=["skill-matching"])

# Include email management routes
api_router.include_router(email.router, prefix="/email", tags=["email"])

# Include briefing management routes
api_router.include_router(briefings.router, prefix="/briefings", tags=["briefings"])

# Include goal management routes
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])

# Include cache management routes
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])

# Include export routes
api_router.include_router(export.router, prefix="/export", tags=["export"])

# Include offline routes
api_router.include_router(offline.router, prefix="/offline", tags=["offline"])

# Include data security routes
api_router.include_router(data_security.router, prefix="/data-security", tags=["data-security"])

# Include feedback and onboarding routes
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback", "onboarding", "help"])

# Include saved searches routes
api_router.include_router(saved_searches.router, prefix="/saved-searches", tags=["saved-searches"])

# Include dashboard layout routes
api_router.include_router(dashboard_layouts.router, prefix="/dashboard/layouts", tags=["dashboard"])

# Include backup and recovery routes
api_router.include_router(backup.router, prefix="/backup", tags=["backup", "recovery"])

# Include resume parsing routes
api_router.include_router(resume.router, prefix="/resume", tags=["resume", "parsing"])

# Include WebSocket management routes
from app.api.v1 import websocket

api_router.include_router(websocket.router, prefix="/websocket", tags=["websocket", "notifications"])

# Include dashboard routes
from app.api.v1 import dashboard

api_router.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard", "real-time"])
