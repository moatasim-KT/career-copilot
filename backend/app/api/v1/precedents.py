"""
API endpoints for precedent search and management.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...core.logging import get_logger
from ...services.precedent_seeder import get_precedent_seeder_service
from ...services.vector_store_service import PrecedentClause, get_vector_store_service

logger = get_logger(__name__)

router = APIRouter(prefix="/precedents", tags=["precedents"])


class PrecedentResponse(BaseModel):
    """Response model for precedent clauses."""
    id: str
    text: str
    category: str
    risk_level: str
    source_document: str
    effectiveness_score: float
    created_at: str
    metadata: Optional[Dict] = None


class SearchRequest(BaseModel):
    """Request model for precedent search."""
    query_text: str = Field(..., description="Text to search for")
    n_results: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    category_filter: Optional[str] = Field(default=None, description="Filter by category")
    risk_level_filter: Optional[str] = Field(default=None, description="Filter by risk level")
    min_effectiveness_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum effectiveness score")
    boost_high_effectiveness: bool = Field(default=True, description="Boost results with higher effectiveness scores")


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: str
    total_results: int
    results: List[PrecedentResponse]
    search_metadata: Dict


class CollectionStatsResponse(BaseModel):
    """Response model for collection statistics."""
    total_clauses: int
    categories: Dict[str, int]
    risk_levels: Dict[str, int]
    collection_name: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    collection_count: int
    embeddings_available: bool
    embedding_dimension: Optional[int] = None
    client_type: str
    collection_name: str


def _convert_precedent_to_response(precedent: PrecedentClause) -> PrecedentResponse:
    """Convert PrecedentClause to PrecedentResponse."""
    return PrecedentResponse(
        id=precedent.id,
        text=precedent.text,
        category=precedent.category,
        risk_level=precedent.risk_level,
        source_document=precedent.source_document,
        effectiveness_score=precedent.effectiveness_score,
        created_at=precedent.created_at.isoformat(),
        metadata=precedent.metadata
    )


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """Get vector database health status."""
    try:
        vector_store = get_vector_store_service()
        health = vector_store.health_check()
        
        if health.get("status") != "healthy":
            raise HTTPException(status_code=503, detail=f"Vector database unhealthy: {health.get('error', 'Unknown error')}")
        
        return HealthResponse(**health)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/stats", response_model=CollectionStatsResponse)
async def get_collection_stats():
    """Get collection statistics."""
    try:
        vector_store = get_vector_store_service()
        stats = vector_store.get_collection_stats()
        
        return CollectionStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get collection stats: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_precedents(request: SearchRequest):
    """Search for similar precedent clauses."""
    try:
        vector_store = get_vector_store_service()
        
        results = vector_store.search_similar_clauses(
            query_text=request.query_text,
            n_results=request.n_results,
            category_filter=request.category_filter,
            risk_level_filter=request.risk_level_filter,
            min_effectiveness_score=request.min_effectiveness_score,
            boost_high_effectiveness=request.boost_high_effectiveness
        )
        
        response_results = [_convert_precedent_to_response(precedent) for precedent in results]
        
        search_metadata = {
            "category_filter": request.category_filter,
            "risk_level_filter": request.risk_level_filter,
            "min_effectiveness_score": request.min_effectiveness_score,
            "boost_high_effectiveness": request.boost_high_effectiveness
        }
        
        return SearchResponse(
            query=request.query_text,
            total_results=len(response_results),
            results=response_results,
            search_metadata=search_metadata
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search")
async def search_precedents_get(
    query_text: str = Query(..., description="Text to search for"),
    n_results: int = Query(default=10, ge=1, le=50, description="Number of results to return"),
    category_filter: Optional[str] = Query(default=None, description="Filter by category"),
    risk_level_filter: Optional[str] = Query(default=None, description="Filter by risk level"),
    min_effectiveness_score: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Minimum effectiveness score"),
    boost_high_effectiveness: bool = Query(default=True, description="Boost results with higher effectiveness scores")
):
    """Search for similar precedent clauses (GET endpoint)."""
    request = SearchRequest(
        query_text=query_text,
        n_results=n_results,
        category_filter=category_filter,
        risk_level_filter=risk_level_filter,
        min_effectiveness_score=min_effectiveness_score,
        boost_high_effectiveness=boost_high_effectiveness
    )
    return await search_precedents(request)


@router.get("/category/{category}", response_model=List[PrecedentResponse])
async def get_precedents_by_category(
    category: str,
    risk_level: Optional[str] = Query(default=None, description="Filter by risk level"),
    n_results: int = Query(default=10, ge=1, le=50, description="Number of results to return")
):
    """Get precedents by category and optionally risk level."""
    try:
        vector_store = get_vector_store_service()
        
        results = vector_store.search_by_category_and_risk(
            category=category,
            risk_level=risk_level,
            n_results=n_results
        )
        
        return [_convert_precedent_to_response(precedent) for precedent in results]
        
    except Exception as e:
        logger.error(f"Failed to get precedents by category: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get precedents by category: {str(e)}")


@router.get("/top-effective", response_model=List[PrecedentResponse])
async def get_top_effective_precedents(
    category: Optional[str] = Query(default=None, description="Filter by category"),
    n_results: int = Query(default=10, ge=1, le=50, description="Number of results to return")
):
    """Get top effective precedent clauses."""
    try:
        vector_store = get_vector_store_service()
        
        results = vector_store.get_top_effective_clauses(
            category=category,
            n_results=n_results
        )
        
        return [_convert_precedent_to_response(precedent) for precedent in results]
        
    except Exception as e:
        logger.error(f"Failed to get top effective precedents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get top effective precedents: {str(e)}")


@router.get("/alternatives/{clause_id}", response_model=List[PrecedentResponse])
async def get_clause_alternatives(
    clause_id: str,
    n_results: int = Query(default=5, ge=1, le=20, description="Number of alternatives to return")
):
    """Get alternative clauses for a given clause ID."""
    try:
        vector_store = get_vector_store_service()
        
        results = vector_store.get_clause_alternatives(
            clause_id=clause_id,
            n_results=n_results
        )
        
        return [_convert_precedent_to_response(precedent) for precedent in results]
        
    except Exception as e:
        logger.error(f"Failed to get clause alternatives: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get clause alternatives: {str(e)}")


@router.get("/risk-alternatives")
async def get_risk_alternatives(
    query_text: str = Query(..., description="Text to find alternatives for"),
    target_risk_level: str = Query(..., description="Desired risk level (Low, Medium, High)"),
    n_results: int = Query(default=5, ge=1, le=20, description="Number of alternatives to return")
):
    """Find clauses similar to query but with different risk profile."""
    try:
        vector_store = get_vector_store_service()
        
        results = vector_store.find_similar_by_risk_profile(
            query_text=query_text,
            target_risk_level=target_risk_level,
            n_results=n_results
        )
        
        return [_convert_precedent_to_response(precedent) for precedent in results]
        
    except Exception as e:
        logger.error(f"Failed to get risk alternatives: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk alternatives: {str(e)}")


@router.get("/{clause_id}", response_model=PrecedentResponse)
async def get_precedent_by_id(clause_id: str):
    """Get a specific precedent clause by ID."""
    try:
        vector_store = get_vector_store_service()
        
        precedent = vector_store.get_precedent_by_id(clause_id)
        
        if not precedent:
            raise HTTPException(status_code=404, detail=f"Precedent clause not found: {clause_id}")
        
        return _convert_precedent_to_response(precedent)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get precedent by ID: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get precedent by ID: {str(e)}")


@router.post("/seed")
async def seed_precedents(force_reseed: bool = Query(default=False, description="Force reseed even if data exists")):
    """Seed the vector database with sample precedents."""
    try:
        seeder_service = get_precedent_seeder_service()
        
        result = seeder_service.seed_precedents(force_reseed=force_reseed)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to seed precedents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to seed precedents: {str(e)}")


@router.get("/categories/list")
async def list_categories():
    """Get list of available categories."""
    try:
        vector_store = get_vector_store_service()
        stats = vector_store.get_collection_stats()
        
        categories = list(stats.get("categories", {}).keys())
        
        return {
            "categories": categories,
            "total_categories": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list categories: {str(e)}")


@router.get("/risk-levels/list")
async def list_risk_levels():
    """Get list of available risk levels."""
    try:
        vector_store = get_vector_store_service()
        stats = vector_store.get_collection_stats()
        
        risk_levels = list(stats.get("risk_levels", {}).keys())
        
        return {
            "risk_levels": risk_levels,
            "total_risk_levels": len(risk_levels)
        }
        
    except Exception as e:
        logger.error(f"Failed to list risk levels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list risk levels: {str(e)}")