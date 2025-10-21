"""
Service for handling job application tracking results with pagination, filtering, and export functionality.
"""

import base64
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, text
from sqlalchemy.orm import Session, joinedload

from ..core.database import get_database_manager
from ..core.logging import get_logger
from ..models.database_models import ContractAnalysis, User
from ..models.pagination_models import (
    AnalysisStatus,
    ContractAnalysisListItem,
    ContractAnalysisListResponse,
    ContractFilterParams,
    CursorPaginationParams,
    ExportFormat,
    ExportParams,
    ExportResponse,
    PaginationMetadata,
    RiskLevel,
    SearchParams,
    SortField,
    SortOrder,
    SortParams,
)

logger = get_logger(__name__)


class ContractResultsService:
    """Service for managing job application tracking results with advanced querying capabilities."""
    
    def __init__(self):
        self.logger = logger
    
    def _get_risk_level(self, risk_score: Optional[float]) -> Optional[str]:
        """Determine risk level from risk score."""
        if risk_score is None:
            return None
        
        if risk_score < 0.3:
            return RiskLevel.LOW.value
        elif risk_score < 0.6:
            return RiskLevel.MEDIUM.value
        elif risk_score < 0.8:
            return RiskLevel.HIGH.value
        else:
            return RiskLevel.CRITICAL.value
    
    def _encode_cursor(self, values: Dict[str, Any]) -> str:
        """Encode cursor values to base64 string."""
        cursor_data = json.dumps(values, default=str)
        return base64.b64encode(cursor_data.encode()).decode()
    
    def _decode_cursor(self, cursor: str) -> Dict[str, Any]:
        """Decode cursor from base64 string."""
        try:
            cursor_data = base64.b64decode(cursor.encode()).decode()
            return json.loads(cursor_data)
        except Exception as e:
            self.logger.warning(f"Failed to decode cursor: {e}")
            return {}
    
    def _build_filter_conditions(
        self, 
        query, 
        filters: ContractFilterParams, 
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ):
        """Build SQLAlchemy filter conditions from filter parameters."""
        conditions = []
        
        # User filter (non-admin users can only see their own analyses)
        if not is_admin and user_id:
            conditions.append(ContractAnalysis.user_id == user_id)
        elif filters.user_id and is_admin:
            conditions.append(ContractAnalysis.user_id == filters.user_id)
        
        # Date filters
        if filters.date_from:
            conditions.append(ContractAnalysis.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(ContractAnalysis.created_at <= filters.date_to)
        if filters.completed_from:
            conditions.append(ContractAnalysis.completed_at >= filters.completed_from)
        if filters.completed_to:
            conditions.append(ContractAnalysis.completed_at <= filters.completed_to)
        
        # Status filters
        if filters.status:
            status_values = [status.value for status in filters.status]
            conditions.append(ContractAnalysis.analysis_status.in_(status_values))
        
        # Risk score filters
        if filters.min_risk_score is not None:
            conditions.append(ContractAnalysis.risk_score >= filters.min_risk_score)
        if filters.max_risk_score is not None:
            conditions.append(ContractAnalysis.risk_score <= filters.max_risk_score)
        
        # Risk level filters (derived from risk score)
        if filters.risk_level:
            risk_conditions = []
            for risk_level in filters.risk_level:
                if risk_level == RiskLevel.LOW:
                    risk_conditions.append(
                        and_(
                            ContractAnalysis.risk_score >= 0.0,
                            ContractAnalysis.risk_score < 0.3
                        )
                    )
                elif risk_level == RiskLevel.MEDIUM:
                    risk_conditions.append(
                        and_(
                            ContractAnalysis.risk_score >= 0.3,
                            ContractAnalysis.risk_score < 0.6
                        )
                    )
                elif risk_level == RiskLevel.HIGH:
                    risk_conditions.append(
                        and_(
                            ContractAnalysis.risk_score >= 0.6,
                            ContractAnalysis.risk_score < 0.8
                        )
                    )
                elif risk_level == RiskLevel.CRITICAL:
                    risk_conditions.append(ContractAnalysis.risk_score >= 0.8)
            
            if risk_conditions:
                conditions.append(or_(*risk_conditions))
        
        # File filters
        if filters.filename_pattern:
            # Support wildcards using LIKE
            pattern = filters.filename_pattern.replace('*', '%').replace('?', '_')
            conditions.append(ContractAnalysis.filename.like(f"%{pattern}%"))
        
        if filters.min_file_size is not None:
            conditions.append(ContractAnalysis.file_size >= filters.min_file_size)
        if filters.max_file_size is not None:
            conditions.append(ContractAnalysis.file_size <= filters.max_file_size)
        
        # Processing time filters
        if filters.min_processing_time is not None:
            conditions.append(ContractAnalysis.processing_time_seconds >= filters.min_processing_time)
        if filters.max_processing_time is not None:
            conditions.append(ContractAnalysis.processing_time_seconds <= filters.max_processing_time)
        
        # AI model filter
        if filters.ai_model:
            conditions.append(ContractAnalysis.ai_model_used.in_(filters.ai_model))
        
        return query.filter(and_(*conditions)) if conditions else query
    
    def _build_search_conditions(self, query, search: SearchParams):
        """Build search conditions for full-text search."""
        if not search.query:
            return query
        
        search_conditions = []
        search_term = search.query
        
        # Prepare search term based on options
        if not search.case_sensitive:
            search_term = search_term.lower()
        
        if search.whole_words_only:
            # Use word boundaries for whole word matching
            search_pattern = f"\\b{search_term}\\b"
        else:
            search_pattern = f"%{search_term}%"
        
        # Build search conditions for each field
        for field in search.search_fields:
            if field == "contract_text":
                if search.case_sensitive:
                    if search.whole_words_only:
                        search_conditions.append(
                            ContractAnalysis.contract_text.op("~")(search_pattern)
                        )
                    else:
                        search_conditions.append(
                            ContractAnalysis.contract_text.like(search_pattern)
                        )
                else:
                    if search.whole_words_only:
                        search_conditions.append(
                            ContractAnalysis.contract_text.op("~*")(search_pattern)
                        )
                    else:
                        search_conditions.append(
                            ContractAnalysis.contract_text.ilike(search_pattern)
                        )
            
            elif field == "filename":
                if search.case_sensitive:
                    search_conditions.append(
                        ContractAnalysis.filename.like(search_pattern)
                    )
                else:
                    search_conditions.append(
                        ContractAnalysis.filename.ilike(search_pattern)
                    )
            
            elif field in ["risky_clauses", "suggested_redlines"]:
                # Search in JSON fields
                json_field = getattr(ContractAnalysis, field)
                if search.case_sensitive:
                    search_conditions.append(
                        json_field.op("::text")(f"LIKE '%{search_term}%'")
                    )
                else:
                    search_conditions.append(
                        json_field.op("::text")(f"ILIKE '%{search_term}%'")
                    )
            
            elif field == "email_draft":
                if search.case_sensitive:
                    search_conditions.append(
                        ContractAnalysis.email_draft.like(search_pattern)
                    )
                else:
                    search_conditions.append(
                        ContractAnalysis.email_draft.ilike(search_pattern)
                    )
            
            elif field == "error_message":
                if search.case_sensitive:
                    search_conditions.append(
                        ContractAnalysis.error_message.like(search_pattern)
                    )
                else:
                    search_conditions.append(
                        ContractAnalysis.error_message.ilike(search_pattern)
                    )
        
        return query.filter(or_(*search_conditions)) if search_conditions else query
    
    def _build_sort_conditions(self, query, sort: SortParams):
        """Build sort conditions from sort parameters."""
        order_clauses = []
        
        for sort_field, sort_order in zip(sort.sort_by, sort.sort_order):
            if sort_field == SortField.CREATED_AT:
                field = ContractAnalysis.created_at
            elif sort_field == SortField.COMPLETED_AT:
                field = ContractAnalysis.completed_at
            elif sort_field == SortField.FILENAME:
                field = ContractAnalysis.filename
            elif sort_field == SortField.RISK_SCORE:
                field = ContractAnalysis.risk_score
            elif sort_field == SortField.PROCESSING_TIME:
                field = ContractAnalysis.processing_time_seconds
            elif sort_field == SortField.FILE_SIZE:
                field = ContractAnalysis.file_size
            elif sort_field == SortField.STATUS:
                field = ContractAnalysis.analysis_status
            else:
                continue  # Skip unknown fields
            
            if sort_order == SortOrder.DESC:
                order_clauses.append(desc(field))
            else:
                order_clauses.append(field)
        
        return query.order_by(*order_clauses) if order_clauses else query
    
    def _build_cursor_conditions(self, query, cursor_data: Dict[str, Any], sort: SortParams):
        """Build cursor-based pagination conditions."""
        if not cursor_data:
            return query
        
        # Build conditions based on sort fields
        cursor_conditions = []
        
        for i, (sort_field, sort_order) in enumerate(zip(sort.sort_by, sort.sort_order)):
            cursor_key = f"sort_{i}_{sort_field.value}"
            if cursor_key not in cursor_data:
                continue
            
            cursor_value = cursor_data[cursor_key]
            
            if sort_field == SortField.CREATED_AT:
                field = ContractAnalysis.created_at
                cursor_value = datetime.fromisoformat(cursor_value)
            elif sort_field == SortField.COMPLETED_AT:
                field = ContractAnalysis.completed_at
                cursor_value = datetime.fromisoformat(cursor_value) if cursor_value else None
            elif sort_field == SortField.FILENAME:
                field = ContractAnalysis.filename
            elif sort_field == SortField.RISK_SCORE:
                field = ContractAnalysis.risk_score
                cursor_value = float(cursor_value) if cursor_value is not None else None
            elif sort_field == SortField.PROCESSING_TIME:
                field = ContractAnalysis.processing_time_seconds
                cursor_value = float(cursor_value) if cursor_value is not None else None
            elif sort_field == SortField.FILE_SIZE:
                field = ContractAnalysis.file_size
                cursor_value = int(cursor_value)
            elif sort_field == SortField.STATUS:
                field = ContractAnalysis.analysis_status
            else:
                continue
            
            # Build condition based on sort order
            if sort_order == SortOrder.DESC:
                if cursor_value is not None:
                    cursor_conditions.append(field < cursor_value)
            else:
                if cursor_value is not None:
                    cursor_conditions.append(field > cursor_value)
        
        # Add ID condition for stable sorting
        if "id" in cursor_data:
            cursor_id = UUID(cursor_data["id"])
            cursor_conditions.append(ContractAnalysis.id > cursor_id)
        
        return query.filter(and_(*cursor_conditions)) if cursor_conditions else query
    
    def _create_cursor_from_item(self, item: ContractAnalysis, sort: SortParams) -> str:
        """Create cursor from the last item in the result set."""
        cursor_data = {"id": str(item.id)}
        
        for i, sort_field in enumerate(sort.sort_by):
            cursor_key = f"sort_{i}_{sort_field.value}"
            
            if sort_field == SortField.CREATED_AT:
                cursor_data[cursor_key] = item.created_at.isoformat()
            elif sort_field == SortField.COMPLETED_AT:
                cursor_data[cursor_key] = item.completed_at.isoformat() if item.completed_at else None
            elif sort_field == SortField.FILENAME:
                cursor_data[cursor_key] = item.filename
            elif sort_field == SortField.RISK_SCORE:
                cursor_data[cursor_key] = item.risk_score
            elif sort_field == SortField.PROCESSING_TIME:
                cursor_data[cursor_key] = item.processing_time_seconds
            elif sort_field == SortField.FILE_SIZE:
                cursor_data[cursor_key] = item.file_size
            elif sort_field == SortField.STATUS:
                cursor_data[cursor_key] = item.analysis_status
        
        return self._encode_cursor(cursor_data)
    
    def _convert_to_list_item(self, analysis: ContractAnalysis, username: Optional[str] = None) -> ContractAnalysisListItem:
        """Convert ContractAnalysis to ContractAnalysisListItem."""
        # Count risky clauses and redlines
        risky_clauses_count = 0
        redlines_count = 0
        
        if analysis.risky_clauses:
            if isinstance(analysis.risky_clauses, list):
                risky_clauses_count = len(analysis.risky_clauses)
            elif isinstance(analysis.risky_clauses, dict):
                risky_clauses_count = len(analysis.risky_clauses.get("clauses", []))
        
        if analysis.suggested_redlines:
            if isinstance(analysis.suggested_redlines, list):
                redlines_count = len(analysis.suggested_redlines)
            elif isinstance(analysis.suggested_redlines, dict):
                redlines_count = len(analysis.suggested_redlines.get("redlines", []))
        
        return ContractAnalysisListItem(
            id=analysis.id,
            filename=analysis.filename,
            file_hash=analysis.file_hash,
            file_size=analysis.file_size,
            analysis_status=analysis.analysis_status,
            risk_score=analysis.risk_score,
            risk_level=self._get_risk_level(analysis.risk_score),
            processing_time_seconds=analysis.processing_time_seconds,
            ai_model_used=analysis.ai_model_used,
            created_at=analysis.created_at,
            completed_at=analysis.completed_at,
            risky_clauses_count=risky_clauses_count,
            redlines_count=redlines_count,
            user_id=analysis.user_id,
            username=username
        )
    
    async def get_contract_analyses(
        self,
        pagination: CursorPaginationParams,
        filters: ContractFilterParams,
        sort: SortParams,
        search: Optional[SearchParams] = None,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> ContractAnalysisListResponse:
        """
        Get paginated list of contract analyses with filtering, sorting, and search.
        
        Args:
            pagination: Pagination parameters
            filters: Filter parameters
            sort: Sort parameters
            search: Search parameters (optional)
            user_id: Current user ID (for access control)
            is_admin: Whether the user is an admin
            
        Returns:
            ContractAnalysisListResponse: Paginated response with metadata
        """
        try:
            # For now, return a mock response to test the API structure
            # In a full implementation, this would query the actual database
            
            # Create mock list items
            mock_items = []
            
            # Create pagination metadata
            pagination_metadata = PaginationMetadata(
                total_count=0,
                has_next=False,
                has_previous=bool(pagination.cursor),
                next_cursor=None,
                previous_cursor=None,
                current_page_size=0,
                requested_limit=pagination.limit
            )
            
            # Create response
            return ContractAnalysisListResponse(
                items=mock_items,
                pagination=pagination_metadata,
                filters_applied=filters.model_dump(exclude_none=True),
                sort_applied={
                    "sort_by": [field.value for field in sort.sort_by],
                    "sort_order": [order.value for order in sort.sort_order]
                },
                search_applied=search.model_dump(exclude_none=True) if search else None,
                total_processing_time=None,
                average_risk_score=None
            )
            
        except Exception as e:
            self.logger.error(f"Error getting contract analyses: {e}", exc_info=True)
            raise
    
    async def export_contract_analyses(
        self,
        export_params: ExportParams,
        filters: ContractFilterParams,
        search: Optional[SearchParams] = None,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> ExportResponse:
        """
        Export contract analyses based on filters and search criteria.
        
        Args:
            export_params: Export parameters
            filters: Filter parameters
            search: Search parameters (optional)
            user_id: Current user ID (for access control)
            is_admin: Whether the user is an admin
            
        Returns:
            ExportResponse: Export operation details
        """
        try:
            export_id = str(uuid.uuid4())
            
            # For now, return a placeholder response
            # In a full implementation, this would queue a background job
            return ExportResponse(
                export_id=export_id,
                format=export_params.format,
                status="queued",
                download_url=None,
                file_size=None,
                expires_at=None,
                created_at=datetime.utcnow(),
                completed_at=None,
                error_message=None
            )
            
        except Exception as e:
            self.logger.error(f"Error exporting contract analyses: {e}", exc_info=True)
            raise


# Global service instance
contract_results_service = ContractResultsService()