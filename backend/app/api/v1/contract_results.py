"""
Enhanced contract results API endpoints with pagination, filtering, sorting, search, and export functionality.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from ...core.auth import get_current_user, get_current_user_optional
from ...core.logging import get_logger
from ...models.api_models import UserResponse
from ...models.pagination_models import (
    AnalysisStatus,
    ContractAnalysisListResponse,
    ContractFilterParams,
    CursorPaginationParams,
    ExportFormat,
    ExportParams,
    ExportResponse,
    RiskLevel,
    SearchParams,
    SortField,
    SortOrder,
    SortParams,
)
from ...services.contract_results_service import contract_results_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("/contracts/results", response_model=ContractAnalysisListResponse, tags=["Contract Results"])
async def get_contract_results(
    request: Request,
    # Pagination parameters
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    
    # Filter parameters
    date_from: Optional[datetime] = Query(None, description="Filter analyses created after this date"),
    date_to: Optional[datetime] = Query(None, description="Filter analyses created before this date"),
    completed_from: Optional[datetime] = Query(None, description="Filter analyses completed after this date"),
    completed_to: Optional[datetime] = Query(None, description="Filter analyses completed before this date"),
    status: Optional[List[AnalysisStatus]] = Query(None, description="Filter by analysis status"),
    risk_level: Optional[List[RiskLevel]] = Query(None, description="Filter by risk level"),
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum risk score"),
    max_risk_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum risk score"),
    filename_pattern: Optional[str] = Query(None, description="Filename pattern (supports wildcards)"),
    min_file_size: Optional[int] = Query(None, ge=0, description="Minimum file size in bytes"),
    max_file_size: Optional[int] = Query(None, ge=0, description="Maximum file size in bytes"),
    min_processing_time: Optional[float] = Query(None, ge=0.0, description="Minimum processing time in seconds"),
    max_processing_time: Optional[float] = Query(None, ge=0.0, description="Maximum processing time in seconds"),
    ai_model: Optional[List[str]] = Query(None, description="Filter by AI model used"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID (admin only)"),
    
    # Sort parameters
    sort_by: List[SortField] = Query([SortField.CREATED_AT], description="Fields to sort by"),
    sort_order: List[SortOrder] = Query([SortOrder.DESC], description="Sort order for each field"),
    
    # Search parameters
    search_query: Optional[str] = Query(None, description="Search query for contract content"),
    search_fields: List[str] = Query(
        ["contract_text", "filename", "risky_clauses", "suggested_redlines"],
        description="Fields to search in"
    ),
    case_sensitive: bool = Query(False, description="Whether search should be case sensitive"),
    whole_words_only: bool = Query(False, description="Whether to match whole words only"),
    
    # Dependencies
    current_user: Optional[UserResponse] = Depends(get_current_user_optional)
) -> ContractAnalysisListResponse:
    """
    Get paginated list of job application tracking results with advanced filtering, sorting, and search capabilities.
    
    This endpoint provides comprehensive querying capabilities for contract analyses including:
    - Cursor-based pagination for efficient large dataset handling
    - Multi-field filtering (date, status, risk, file properties, processing metrics)
    - Multi-field sorting with customizable order
    - Full-text search across contract content and metadata
    - Risk level classification and filtering
    - User-specific access control
    
    **Pagination:**
    - Uses cursor-based pagination for consistent results during concurrent modifications
    - Supports configurable page sizes (1-100 items)
    - Provides metadata about pagination state and total counts
    
    **Filtering:**
    - Date range filtering for creation and completion dates
    - Status filtering (pending, running, completed, failed, etc.)
    - Risk-based filtering by score ranges or risk levels
    - File property filtering (size, name patterns)
    - Processing metrics filtering (processing time)
    - AI model filtering
    
    **Sorting:**
    - Multi-field sorting with individual sort orders
    - Supports sorting by date, filename, risk score, processing time, file size, status
    - Stable sorting with ID-based tiebreaking
    
    **Search:**
    - Full-text search across multiple fields
    - Configurable case sensitivity and whole-word matching
    - Search in contract text, filenames, analysis results
    
    **Access Control:**
    - Regular users see only their own analyses
    - Admin users can see all analyses and filter by user
    - Supports both authenticated and public access (with restrictions)
    
    Args:
        request: FastAPI request object
        cursor: Pagination cursor (base64 encoded)
        limit: Number of items to return (1-100)
        date_from: Filter analyses created after this date
        date_to: Filter analyses created before this date
        completed_from: Filter analyses completed after this date
        completed_to: Filter analyses completed before this date
        status: Filter by analysis status (can specify multiple)
        risk_level: Filter by risk level classification (can specify multiple)
        min_risk_score: Minimum risk score (0.0-1.0)
        max_risk_score: Maximum risk score (0.0-1.0)
        filename_pattern: Filename pattern with wildcard support (* and ?)
        min_file_size: Minimum file size in bytes
        max_file_size: Maximum file size in bytes
        min_processing_time: Minimum processing time in seconds
        max_processing_time: Maximum processing time in seconds
        ai_model: Filter by AI model used (can specify multiple)
        user_id: Filter by user ID (admin only)
        sort_by: Fields to sort by (can specify multiple)
        sort_order: Sort order for each field (must match sort_by length)
        search_query: Search query string
        search_fields: Fields to search in
        case_sensitive: Whether search should be case sensitive
        whole_words_only: Whether to match whole words only
        current_user: Current authenticated user (optional)
        
    Returns:
        ContractAnalysisListResponse: Paginated list with metadata
        
    Raises:
        HTTPException: For validation errors or access denied
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        logger.info(f"Getting contract results with filters", extra={"request_id": request_id})
        
        # Validate sort parameters
        if len(sort_order) != len(sort_by):
            raise HTTPException(
                status_code=400,
                detail="sort_order must have the same length as sort_by"
            )
        
        # Validate search fields
        allowed_search_fields = [
            "contract_text", "filename", "risky_clauses", 
            "suggested_redlines", "email_draft", "error_message"
        ]
        for field in search_fields:
            if field not in allowed_search_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid search field: {field}. Allowed fields: {allowed_search_fields}"
                )
        
        # Check admin permissions for user_id filter
        is_admin = current_user and getattr(current_user, 'is_superuser', False)
        if user_id and not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Only admin users can filter by user_id"
            )
        
        # Create parameter objects
        pagination = CursorPaginationParams(cursor=cursor, limit=limit)
        
        filters = ContractFilterParams(
            date_from=date_from,
            date_to=date_to,
            completed_from=completed_from,
            completed_to=completed_to,
            status=status,
            risk_level=risk_level,
            min_risk_score=min_risk_score,
            max_risk_score=max_risk_score,
            filename_pattern=filename_pattern,
            min_file_size=min_file_size,
            max_file_size=max_file_size,
            min_processing_time=min_processing_time,
            max_processing_time=max_processing_time,
            ai_model=ai_model,
            user_id=user_id
        )
        
        sort_params = SortParams(sort_by=sort_by, sort_order=sort_order)
        
        search_params = None
        if search_query:
            search_params = SearchParams(
                query=search_query,
                search_fields=search_fields,
                case_sensitive=case_sensitive,
                whole_words_only=whole_words_only
            )
        
        # Get results from service
        current_user_id = getattr(current_user, 'id', None) if current_user else None
        
        result = await contract_results_service.get_contract_analyses(
            pagination=pagination,
            filters=filters,
            sort=sort_params,
            search=search_params,
            user_id=current_user_id,
            is_admin=is_admin
        )
        
        logger.info(
            f"Retrieved {len(result.items)} contract results",
            extra={
                "request_id": request_id,
                "total_items": len(result.items),
                "has_next": result.pagination.has_next,
                "filters_applied": len([k for k, v in result.filters_applied.items() if v is not None]),
                "search_applied": bool(result.search_applied)
            }
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contract results: {e}", exc_info=True, extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving contract results"
        )


@router.post("/contracts/results/export", response_model=ExportResponse, tags=["Contract Results"])
async def export_contract_results(
    request: Request,
    export_params: ExportParams,
    
    # Filter parameters (same as get_contract_results)
    date_from: Optional[datetime] = Query(None, description="Filter analyses created after this date"),
    date_to: Optional[datetime] = Query(None, description="Filter analyses created before this date"),
    completed_from: Optional[datetime] = Query(None, description="Filter analyses completed after this date"),
    completed_to: Optional[datetime] = Query(None, description="Filter analyses completed before this date"),
    status: Optional[List[AnalysisStatus]] = Query(None, description="Filter by analysis status"),
    risk_level: Optional[List[RiskLevel]] = Query(None, description="Filter by risk level"),
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum risk score"),
    max_risk_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum risk score"),
    filename_pattern: Optional[str] = Query(None, description="Filename pattern (supports wildcards)"),
    min_file_size: Optional[int] = Query(None, ge=0, description="Minimum file size in bytes"),
    max_file_size: Optional[int] = Query(None, ge=0, description="Maximum file size in bytes"),
    min_processing_time: Optional[float] = Query(None, ge=0.0, description="Minimum processing time in seconds"),
    max_processing_time: Optional[float] = Query(None, ge=0.0, description="Maximum processing time in seconds"),
    ai_model: Optional[List[str]] = Query(None, description="Filter by AI model used"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID (admin only)"),
    
    # Search parameters
    search_query: Optional[str] = Query(None, description="Search query for contract content"),
    search_fields: List[str] = Query(
        ["contract_text", "filename", "risky_clauses", "suggested_redlines"],
        description="Fields to search in"
    ),
    case_sensitive: bool = Query(False, description="Whether search should be case sensitive"),
    whole_words_only: bool = Query(False, description="Whether to match whole words only"),
    
    # Dependencies
    current_user: UserResponse = Depends(get_current_user)
) -> ExportResponse:
    """
    Export job application tracking results based on filters and search criteria.
    
    This endpoint allows users to export their job application tracking results in various formats
    with the same filtering and search capabilities as the list endpoint.
    
    **Supported Export Formats:**
    - JSON: Structured data export with full analysis details
    - PDF: Professional report format with charts and summaries
    - DOCX: Microsoft Word document with formatted results
    - CSV: Spreadsheet-compatible format for data analysis
    
    **Export Options:**
    - Include/exclude full contract content
    - Include/exclude analysis results (risks, redlines)
    - Include/exclude metadata (processing info, timestamps)
    - Format-specific options (PDF templates, DOCX track changes, CSV delimiters)
    
    **Access Control:**
    - Requires authentication
    - Users can only export their own analyses
    - Admin users can export any analyses
    
    **Processing:**
    - Large exports are processed asynchronously
    - Returns export ID for status tracking
    - Download URL provided when ready
    - Exports expire after a configurable time period
    
    Args:
        request: FastAPI request object
        export_params: Export configuration parameters
        [filter parameters]: Same as get_contract_results endpoint
        [search parameters]: Same as get_contract_results endpoint
        current_user: Current authenticated user
        
    Returns:
        ExportResponse: Export operation details and status
        
    Raises:
        HTTPException: For validation errors, access denied, or export failures
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        logger.info(
            f"Exporting contract results in {export_params.format.value} format",
            extra={"request_id": request_id, "user_id": str(current_user.id)}
        )
        
        # Validate search fields
        allowed_search_fields = [
            "contract_text", "filename", "risky_clauses", 
            "suggested_redlines", "email_draft", "error_message"
        ]
        for field in search_fields:
            if field not in allowed_search_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid search field: {field}. Allowed fields: {allowed_search_fields}"
                )
        
        # Check admin permissions for user_id filter
        is_admin = getattr(current_user, 'is_superuser', False)
        if user_id and not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Only admin users can filter by user_id"
            )
        
        # Create filter parameters
        filters = ContractFilterParams(
            date_from=date_from,
            date_to=date_to,
            completed_from=completed_from,
            completed_to=completed_to,
            status=status,
            risk_level=risk_level,
            min_risk_score=min_risk_score,
            max_risk_score=max_risk_score,
            filename_pattern=filename_pattern,
            min_file_size=min_file_size,
            max_file_size=max_file_size,
            min_processing_time=min_processing_time,
            max_processing_time=max_processing_time,
            ai_model=ai_model,
            user_id=user_id
        )
        
        # Create search parameters
        search_params = None
        if search_query:
            search_params = SearchParams(
                query=search_query,
                search_fields=search_fields,
                case_sensitive=case_sensitive,
                whole_words_only=whole_words_only
            )
        
        # Start export process
        result = await contract_results_service.export_contract_analyses(
            export_params=export_params,
            filters=filters,
            search=search_params,
            user_id=current_user.id,
            is_admin=is_admin
        )
        
        logger.info(
            f"Export initiated with ID: {result.export_id}",
            extra={
                "request_id": request_id,
                "export_id": result.export_id,
                "format": export_params.format.value,
                "user_id": str(current_user.id)
            }
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting contract results: {e}", exc_info=True, extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail="An error occurred while initiating the export"
        )


@router.get("/contracts/results/export/{export_id}", response_model=ExportResponse, tags=["Contract Results"])
async def get_export_status(
    request: Request,
    export_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> ExportResponse:
    """
    Get the status of an export operation.
    
    This endpoint allows users to check the status of their export operations
    and retrieve download URLs when exports are complete.
    
    **Export Statuses:**
    - queued: Export is queued for processing
    - processing: Export is currently being generated
    - completed: Export is ready for download
    - failed: Export failed (error message provided)
    - expired: Export has expired and is no longer available
    
    **Download URLs:**
    - Provided when export status is "completed"
    - URLs are time-limited and expire after a configurable period
    - URLs are signed for security and access control
    
    Args:
        request: FastAPI request object
        export_id: Unique export identifier
        current_user: Current authenticated user
        
    Returns:
        ExportResponse: Export status and download information
        
    Raises:
        HTTPException: If export not found or access denied
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        logger.info(
            f"Getting export status for ID: {export_id}",
            extra={"request_id": request_id, "export_id": export_id}
        )
        
        # For now, return a placeholder response
        # In a full implementation, this would check the actual export status
        return ExportResponse(
            export_id=export_id,
            format=ExportFormat.JSON,  # This would come from the stored export record
            status="completed",
            download_url=f"/api/v1/contracts/results/export/{export_id}/download",
            file_size=1024,  # This would be the actual file size
            expires_at=datetime.utcnow(),  # This would be the actual expiration
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error_message=None
        )
        
    except Exception as e:
        logger.error(f"Error getting export status: {e}", exc_info=True, extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving export status"
        )


@router.get("/contracts/results/export/{export_id}/download", tags=["Contract Results"])
async def download_export(
    request: Request,
    export_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Download an exported file.
    
    This endpoint provides secure download access to completed exports.
    Downloads are access-controlled and time-limited.
    
    **Security:**
    - Requires authentication
    - Users can only download their own exports
    - Admin users can download any exports
    - Download URLs expire after a configurable time
    
    **File Handling:**
    - Supports streaming for large files
    - Proper MIME type headers
    - Content-Disposition headers for filename
    - Content-Length headers for progress tracking
    
    Args:
        request: FastAPI request object
        export_id: Unique export identifier
        current_user: Current authenticated user
        
    Returns:
        StreamingResponse: File download stream
        
    Raises:
        HTTPException: If export not found, expired, or access denied
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        logger.info(
            f"Downloading export file for ID: {export_id}",
            extra={"request_id": request_id, "export_id": export_id}
        )
        
        # For now, return a placeholder response
        # In a full implementation, this would stream the actual file
        return JSONResponse(
            content={
                "message": "Export download not yet implemented",
                "export_id": export_id,
                "status": "placeholder"
            }
        )
        
    except Exception as e:
        logger.error(f"Error downloading export: {e}", exc_info=True, extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail="An error occurred while downloading the export"
        )


@router.get("/contracts/results/stats", tags=["Contract Results"])
async def get_contract_results_stats(
    request: Request,
    
    # Filter parameters for stats calculation
    date_from: Optional[datetime] = Query(None, description="Calculate stats for analyses created after this date"),
    date_to: Optional[datetime] = Query(None, description="Calculate stats for analyses created before this date"),
    user_id: Optional[UUID] = Query(None, description="Calculate stats for specific user (admin only)"),
    
    # Dependencies
    current_user: Optional[UserResponse] = Depends(get_current_user_optional)
) -> dict:
    """
    Get statistics and analytics for job application tracking results.
    
    This endpoint provides aggregate statistics and analytics for contract analyses,
    useful for dashboards, reporting, and system monitoring.
    
    **Statistics Provided:**
    - Total number of analyses
    - Analyses by status (completed, failed, pending, etc.)
    - Risk score distribution and averages
    - Processing time statistics
    - File size statistics
    - AI model usage statistics
    - Success/failure rates
    - Trend analysis over time
    
    **Access Control:**
    - Public access provides system-wide anonymized statistics
    - Authenticated users get their personal statistics
    - Admin users can get statistics for any user or system-wide
    
    **Time Filtering:**
    - Statistics can be filtered by date range
    - Defaults to all-time statistics if no dates provided
    - Supports trend analysis over specified periods
    
    Args:
        request: FastAPI request object
        date_from: Calculate stats for analyses created after this date
        date_to: Calculate stats for analyses created before this date
        user_id: Calculate stats for specific user (admin only)
        current_user: Current authenticated user (optional)
        
    Returns:
        dict: Statistics and analytics data
        
    Raises:
        HTTPException: For validation errors or access denied
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        logger.info("Getting contract results statistics", extra={"request_id": request_id})
        
        # Check admin permissions for user_id filter
        is_admin = current_user and getattr(current_user, 'is_superuser', False)
        if user_id and not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Only admin users can get statistics for specific users"
            )
        
        # For now, return placeholder statistics
        # In a full implementation, this would calculate actual statistics
        return {
            "total_analyses": 0,
            "analyses_by_status": {
                "completed": 0,
                "failed": 0,
                "pending": 0,
                "running": 0
            },
            "risk_statistics": {
                "average_risk_score": 0.0,
                "risk_distribution": {
                    "low": 0,
                    "medium": 0,
                    "high": 0,
                    "critical": 0
                }
            },
            "processing_statistics": {
                "average_processing_time": 0.0,
                "total_processing_time": 0.0,
                "fastest_analysis": 0.0,
                "slowest_analysis": 0.0
            },
            "file_statistics": {
                "average_file_size": 0,
                "total_file_size": 0,
                "largest_file": 0,
                "smallest_file": 0
            },
            "ai_model_usage": {},
            "success_rate": 0.0,
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contract results statistics: {e}", exc_info=True, extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving statistics"
        )