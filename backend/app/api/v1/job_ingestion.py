"""Job ingestion API endpoints built on consolidated services."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.tasks import job_ingestion_tasks

from ...services.job_service import JobManagementSystem

logger = logging.getLogger(__name__)
# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter()


@router.post("/ingest", response_model=Dict[str, Any])
async def trigger_job_ingestion(
	background_tasks: BackgroundTasks,
	max_jobs: int = 50,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
	"""Queue ingestion for the current user via Celery."""
	try:
		logger.info("Queuing job ingestion for user %s", current_user.id)
		background_tasks.add_task(
			job_ingestion_tasks.ingest_jobs_for_user.delay,
			current_user.id,
			max_jobs,
		)
		return {
			"message": "Job ingestion started",
			"user_id": current_user.id,
			"max_jobs": max_jobs,
			"status": "queued",
		}
	except Exception as exc:  # pragma: no cover - defensive
		logger.exception("Failed to queue job ingestion for user %s", current_user.id)
		raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/ingest/immediate", response_model=Dict[str, Any])
async def immediate_job_ingestion(
	max_jobs: int = 25,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
	"""Run ingestion synchronously for the current user."""
	try:
		service = JobIngestionService(db)
		return await service.ingest_jobs_for_user(current_user.id, max_jobs)
	except Exception as exc:  # pragma: no cover - defensive
		logger.exception("Immediate job ingestion failed for user %s", current_user.id)
		raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/stats", response_model=Dict[str, Any])
async def get_ingestion_stats(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
	"""Return ingestion statistics for the current user."""
	try:
		service = JobIngestionService(db)
		return service.get_ingestion_stats(current_user.id)
	except Exception as exc:  # pragma: no cover - defensive
		logger.exception("Failed to fetch ingestion stats for user %s", current_user.id)
		raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/test", response_model=Dict[str, Any])
async def test_job_ingestion(
	keywords: str = "python, developer",
	location: str = "remote",
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
	"""Perform a dry-run across external sources with the provided query."""
	try:
		service = JobIngestionService(db)
		return await service.test_job_ingestion(keywords, location)
	except Exception as exc:  # pragma: no cover - defensive
		logger.exception("Job ingestion test failed for user %s", current_user.id)
		raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/admin/ingest-all", response_model=Dict[str, Any])
async def trigger_ingestion_for_all_users(
	background_tasks: BackgroundTasks,
	max_jobs_per_user: int = 50,
	user_ids: Optional[List[int]] = None,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
	"""Queue ingestion for multiple users (admin helper)."""
	# Check admin permission (basic RBAC - assumes is_admin field exists on User model)
	if not getattr(current_user, "is_admin", False):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required for bulk job ingestion")

	try:
		logger.info("Queuing ingestion for %s users", "selected" if user_ids else "all active")
		background_tasks.add_task(
			job_ingestion_tasks.ingest_jobs.delay,
			user_ids,
			max_jobs_per_user,
		)
		return {
			"message": "Job ingestion started",
			"max_jobs_per_user": max_jobs_per_user,
			"user_ids": user_ids,
			"status": "queued",
		}
	except Exception as exc:  # pragma: no cover - defensive
		logger.exception("Failed to queue bulk ingestion")
		raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/test-all-sources", response_model=Dict[str, Any])
async def test_all_sources(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
	"""Verify external sources respond with data."""
	try:
		service = JobIngestionService(db)
		return await service.test_all_sources()
	except Exception as exc:  # pragma: no cover - defensive
		logger.exception("All sources test failed for user %s", current_user.id)
		raise HTTPException(status_code=500, detail=str(exc)) from exc
