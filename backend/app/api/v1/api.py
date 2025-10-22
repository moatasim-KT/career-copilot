"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1 import auth, jobs, documents, applications, profile, job_ingestion, notifications, analytics, document_templates, templates, recommendations, enhanced_recommendations, skill_gap_analysis, skill_gap, health, tasks, skill_matching, email, briefings, goals, cache, export, offline, document_suggestions, data_security, document_versions, feedback, saved_searches, dashboard_layouts, backup, oauth

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include OAuth authentication routes
api_router.include_router(oauth.router, tags=["oauth"])

# Include job management routes
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

# Include document management routes
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# Include application management routes
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])

# Include profile management routes
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])

# Include job ingestion routes
api_router.include_router(job_ingestion.router, prefix="/job-ingestion", tags=["job-ingestion"])

# Include notification routes
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Include analytics routes
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# Include document template routes (legacy)
api_router.include_router(document_templates.router, prefix="/document-templates", tags=["document-templates"])

# Include new template system routes
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])

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

# Include document suggestion routes
api_router.include_router(document_suggestions.router, prefix="/document-suggestions", tags=["document-suggestions"])

# Include data security routes
api_router.include_router(data_security.router, prefix="/data-security", tags=["data-security"])

# Include document versioning routes
api_router.include_router(document_versions.router, prefix="/document-versions", tags=["document-versions"])

# Include feedback and onboarding routes
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback", "onboarding", "help"])

# Include saved searches routes
api_router.include_router(saved_searches.router, prefix="/saved-searches", tags=["saved-searches"])

# Include dashboard layout routes
api_router.include_router(dashboard_layouts.router, prefix="/dashboard/layouts", tags=["dashboard"])

# Include backup and recovery routes
api_router.include_router(backup.router, prefix="/backup", tags=["backup", "recovery"])