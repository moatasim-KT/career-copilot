"""
ChromaDB Health Check API Endpoints.

This module provides REST API endpoints for monitoring ChromaDB health
and connection pool statistics.
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...core.logging import get_logger
from ...services.chroma_client import get_chroma_client
from ...services.chroma_health_monitor import get_health_monitor

logger = get_logger(__name__)

router = APIRouter(prefix="/chroma", tags=["ChromaDB Health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    details: Dict[str, Any]


class StatsResponse(BaseModel):
    """Statistics response model."""
    connection_pool: Dict[str, Any]
    collections: Dict[str, Any]
    embedding_function: Dict[str, Any]
    persist_directory: str
    timestamp: str


class HealthSummaryResponse(BaseModel):
    """Health summary response model."""
    status: str
    consecutive_failures: int
    monitoring_active: bool
    last_check: str
    uptime_seconds: float
    metrics_summary: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """
    Get comprehensive ChromaDB health status.
    
    Returns detailed health information including:
    - Connection pool status
    - Response times
    - Error rates
    - Collection information
    """
    try:
        chroma_client = await get_chroma_client()
        health_info = await chroma_client.health_check()
        
        return HealthResponse(
            status=health_info["status"],
            timestamp=health_info["timestamp"],
            details=health_info
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ChromaDB health check failed: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get detailed ChromaDB statistics.
    
    Returns comprehensive statistics including:
    - Connection pool metrics
    - Request statistics
    - Collection information
    - Performance metrics
    """
    try:
        chroma_client = await get_chroma_client()
        stats = await chroma_client.get_stats()
        
        return StatsResponse(
            connection_pool=stats["connection_pool"],
            collections=stats["collections"],
            embedding_function=stats["embedding_function"],
            persist_directory=stats["persist_directory"],
            timestamp=stats["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ChromaDB statistics: {str(e)}"
        )


@router.get("/health/summary", response_model=HealthSummaryResponse)
async def get_health_summary():
    """
    Get health monitoring summary.
    
    Returns summary of health monitoring including:
    - Current health status
    - Consecutive failure count
    - Monitoring status
    - Key metrics summary
    """
    try:
        health_monitor = get_health_monitor()
        summary = await health_monitor.get_health_summary()
        
        return HealthSummaryResponse(
            status=summary["status"],
            consecutive_failures=summary["consecutive_failures"],
            monitoring_active=summary["monitoring_active"],
            last_check=summary["last_check"],
            uptime_seconds=summary["uptime_seconds"],
            metrics_summary=summary["metrics_summary"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get health summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health summary: {str(e)}"
        )


@router.post("/health/check")
async def perform_health_check():
    """
    Perform an immediate health check.
    
    Triggers a fresh health check and returns the results.
    This is useful for manual health verification.
    """
    try:
        health_monitor = get_health_monitor()
        health_report = await health_monitor.check_health()
        
        return {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "health_report": health_report.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Manual health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/collections")
async def list_collections():
    """
    List all ChromaDB collections.
    
    Returns a list of all available collections in the ChromaDB instance.
    """
    try:
        chroma_client = await get_chroma_client()
        collections = await chroma_client.list_collections()
        
        return {
            "collections": collections,
            "count": len(collections),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.get("/collections/{collection_name}/info")
async def get_collection_info(collection_name: str):
    """
    Get information about a specific collection.
    
    Args:
        collection_name: Name of the collection to get info for
        
    Returns:
        Collection information including document count and metadata
    """
    try:
        chroma_client = await get_chroma_client()
        
        # Get the collection
        collection = await chroma_client.get_or_create_collection(collection_name)
        
        # Get collection info using the connection pool
        async with chroma_client.connection_pool.get_connection() as connection:
            count = collection.count()
            
            # Get a sample of documents to show structure
            sample_results = collection.peek(limit=5)
            
        return {
            "name": collection_name,
            "document_count": count,
            "sample_documents": {
                "ids": sample_results.get("ids", []),
                "documents": sample_results.get("documents", [])[:3],  # Limit for response size
                "metadatas": sample_results.get("metadatas", [])[:3]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get collection info for {collection_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection info: {str(e)}"
        )


@router.post("/monitoring/start")
async def start_monitoring():
    """
    Start health monitoring.
    
    Starts the background health monitoring service if not already running.
    """
    try:
        health_monitor = get_health_monitor()
        await health_monitor.start_monitoring()
        
        return {
            "status": "started",
            "message": "Health monitoring started successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring: {str(e)}"
        )


@router.post("/monitoring/stop")
async def stop_monitoring():
    """
    Stop health monitoring.
    
    Stops the background health monitoring service.
    """
    try:
        health_monitor = get_health_monitor()
        await health_monitor.stop_monitoring()
        
        return {
            "status": "stopped",
            "message": "Health monitoring stopped successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop monitoring: {str(e)}"
        )