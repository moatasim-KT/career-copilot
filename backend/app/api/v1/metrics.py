"""
Metrics API endpoint for Prometheus scraping.
"""

from fastapi import APIRouter, Response
from app.middleware.metrics_middleware import get_metrics, get_metrics_content_type

router = APIRouter()


@router.get("/metrics", include_in_schema=False)
async def metrics():
	"""
	Prometheus metrics endpoint.
	Returns metrics in Prometheus text format.
	"""
	return Response(content=get_metrics(), media_type=get_metrics_content_type())
