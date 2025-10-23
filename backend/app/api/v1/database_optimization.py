"""
Database optimization management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.database_optimization_service import db_optimization_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/database", tags=["database-optimization"])


class OptimizationResponse(BaseModel):
    status: str
    message: str
    results: Dict[str, Any]


class DatabaseStatsResponse(BaseModel):
    status: str
    stats: Dict[str, Any]
    collected_at: str


@router.post("/optimize/indexes", response_model=OptimizationResponse)
async def create_performance_indexes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create performance indexes for enhanced features (admin only)"""
    # Check if user is admin (you might want to implement proper admin check)
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        results = db_optimization_service.create_performance_indexes(db)
        
        return OptimizationResponse(
            status="success",
            message=f"Index optimization completed. Created {len(results['indexes_created'])} indexes.",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error creating performance indexes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating performance indexes"
        )


@router.post("/optimize/queries", response_model=OptimizationResponse)
async def optimize_queries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Optimize database queries (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        results = db_optimization_service.optimize_queries(db)
        
        return OptimizationResponse(
            status=results["status"],
            message="Query optimization completed",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error optimizing queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error optimizing queries"
        )


@router.get("/analyze/performance", response_model=OptimizationResponse)
async def analyze_query_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze query performance (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        results = db_optimization_service.analyze_query_performance(db)
        
        return OptimizationResponse(
            status=results["status"],
            message="Query performance analysis completed",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error analyzing query performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing query performance"
        )


@router.get("/connection-pooling", response_model=OptimizationResponse)
async def analyze_connection_pooling(
    current_user: User = Depends(get_current_user)
):
    """Analyze connection pooling configuration (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        results = db_optimization_service.implement_connection_pooling()
        
        return OptimizationResponse(
            status=results["status"],
            message="Connection pooling analysis completed",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error analyzing connection pooling: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing connection pooling"
        )


@router.post("/cleanup")
async def cleanup_old_data(
    days_old: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up old data to improve performance (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if days_old < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete data newer than 30 days"
        )
    
    try:
        results = db_optimization_service.cleanup_old_data(db, days_old)
        
        return OptimizationResponse(
            status=results["status"],
            message=f"Data cleanup completed. Deleted {results.get('total_deleted', 0)} records.",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cleaning up old data"
        )


@router.get("/stats", response_model=DatabaseStatsResponse)
async def get_database_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get database statistics and health metrics (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        results = db_optimization_service.get_database_stats(db)
        
        return DatabaseStatsResponse(
            status=results["status"],
            stats=results.get("stats", {}),
            collected_at=results.get("collected_at", "")
        )
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving database statistics"
        )


@router.post("/optimize/all", response_model=OptimizationResponse)
async def optimize_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run all database optimizations (admin only)"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        all_results = {}
        
        # Create indexes
        logger.info("Creating performance indexes...")
        index_results = db_optimization_service.create_performance_indexes(db)
        all_results["indexes"] = index_results
        
        # Optimize queries
        logger.info("Optimizing queries...")
        query_results = db_optimization_service.optimize_queries(db)
        all_results["queries"] = query_results
        
        # Analyze performance
        logger.info("Analyzing performance...")
        perf_results = db_optimization_service.analyze_query_performance(db)
        all_results["performance"] = perf_results
        
        # Get connection pooling info
        logger.info("Analyzing connection pooling...")
        pool_results = db_optimization_service.implement_connection_pooling()
        all_results["connection_pooling"] = pool_results
        
        total_indexes_created = len(index_results.get("indexes_created", []))
        
        return OptimizationResponse(
            status="success",
            message=f"Complete database optimization finished. Created {total_indexes_created} indexes.",
            results=all_results
        )
        
    except Exception as e:
        logger.error(f"Error running complete optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error running complete database optimization"
        )