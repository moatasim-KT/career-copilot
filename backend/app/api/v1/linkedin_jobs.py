from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...services.job_scraping_service import JobScrapingService

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
		jobs = await JobScrapingService(db=None).scrape_jobs(request.keywords, request.location)
		return jobs
	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to scrape LinkedIn jobs: {e}")


@router.post("/api/v1/linkedin/jobs/description")
async def get_linkedin_job_description(request: LinkedInJobDetailRequest) -> Dict[str, str]:
	"""Fetch detailed description for a given LinkedIn job URL."""
	try:
		description = await JobScrapingService(db=None).scrape_job_description(request.job_url)
		return {"description": description}
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch job description: {e}")
