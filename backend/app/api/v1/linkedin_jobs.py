from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...services.job_service import JobManagementSystem

router = APIRouter(tags=["linkedin-jobs"])


class LinkedInJobSearchRequest(BaseModel):
	keywords: str
	location: str


class LinkedInJobDetailRequest(BaseModel):
	job_url: str


@router.post("/api/v1/linkedin/jobs/scrape")
async def scrape_linkedin_jobs(request: LinkedInJobSearchRequest) -> List[Dict[str, Any]]:
	"""Trigger LinkedIn job scraping based on keywords and location."""
	try:
		jobs = await JobManagementSystem(db=None).scrape_jobs(request.keywords, request.location)
		return jobs
	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to scrape LinkedIn jobs: {e}")


@router.post("/api/v1/linkedin/jobs/details")
async def scrape_linkedin_job_description(request: LinkedInJobDetailRequest) -> Dict[str, Any]:
	"""Scrape detailed job description from a specific LinkedIn job URL."""
	try:
		description = await JobManagementSystem(db=None).scrape_job_description(request.job_url)
		return {"description": description}
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch job description: {e}")
