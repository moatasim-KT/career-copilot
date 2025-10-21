"""
Contract repository for job application tracking operations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.database_models import ContractAnalysis, User
from .base_repository import BaseRepository


class ContractRepository(BaseRepository[ContractAnalysis]):
    """Repository for job application tracking operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ContractAnalysis, session)
    
    async def create_analysis(
        self,
        user_id: UUID,
        filename: str,
        file_hash: str,
        file_size: int,
        contract_text: Optional[str] = None
    ) -> ContractAnalysis:
        """
        Create a new job application tracking record.
        
        Args:
            user_id: ID of the user who uploaded the contract
            filename: Original filename of the contract
            file_hash: SHA-256 hash of the file content
            file_size: Size of the file in bytes
            contract_text: Extracted text content (optional)
            
        Returns:
            Created job application tracking instance
        """
        return await self.create(
            user_id=user_id,
            filename=filename,
            file_hash=file_hash,
            file_size=file_size,
            contract_text=contract_text,
            analysis_status="pending"
        )
    
    async def update_analysis_status(
        self, 
        analysis_id: UUID, 
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[ContractAnalysis]:
        """
        Update analysis status.
        
        Args:
            analysis_id: Analysis UUID
            status: New status (pending, processing, completed, failed)
            error_message: Error message if status is failed
            
        Returns:
            Updated analysis instance or None if not found
        """
        update_data = {"analysis_status": status}
        
        if error_message:
            update_data["error_message"] = error_message
        
        if status == "completed":
            update_data["completed_at"] = datetime.utcnow()
        
        return await self.update_by_id(analysis_id, **update_data)
    
    async def save_analysis_results(
        self,
        analysis_id: UUID,
        risk_score: float,
        risky_clauses: List[Dict],
        suggested_redlines: List[Dict],
        email_draft: str,
        processing_time_seconds: float,
        ai_model_used: str,
        workflow_state: Optional[Dict] = None
    ) -> Optional[ContractAnalysis]:
        """
        Save complete analysis results.
        
        Args:
            analysis_id: Analysis UUID
            risk_score: Overall risk score (0.0-1.0)
            risky_clauses: List of risky clauses found
            suggested_redlines: List of redline suggestions
            email_draft: Generated email draft
            processing_time_seconds: Time taken for analysis
            ai_model_used: AI model that performed the analysis
            workflow_state: LangGraph workflow state (optional)
            
        Returns:
            Updated analysis instance or None if not found
        """
        return await self.update_by_id(
            analysis_id,
            analysis_status="completed",
            risk_score=risk_score,
            risky_clauses=risky_clauses,
            suggested_redlines=suggested_redlines,
            email_draft=email_draft,
            processing_time_seconds=processing_time_seconds,
            ai_model_used=ai_model_used,
            workflow_state=workflow_state,
            completed_at=datetime.utcnow()
        )
    
    async def get_user_analyses(
        self, 
        user_id: UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status_filter: Optional[str] = None
    ) -> List[ContractAnalysis]:
        """
        Get contract analyses for a specific user.
        
        Args:
            user_id: User UUID
            limit: Maximum number of analyses to return
            offset: Number of analyses to skip
            status_filter: Filter by analysis status (optional)
            
        Returns:
            List of job application tracking instances
        """
        query = select(ContractAnalysis).where(ContractAnalysis.user_id == user_id)
        
        if status_filter:
            query = query.where(ContractAnalysis.analysis_status == status_filter)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(ContractAnalysis.created_at))
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_analysis_with_user(self, analysis_id: UUID) -> Optional[ContractAnalysis]:
        """
        Get analysis with user information loaded.
        
        Args:
            analysis_id: Analysis UUID
            
        Returns:
            Analysis instance with user data or None if not found
        """
        result = await self.session.execute(
            select(ContractAnalysis)
            .options(selectinload(ContractAnalysis.user))
            .where(ContractAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()
    
    async def get_analyses_by_status(
        self, 
        status: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ContractAnalysis]:
        """
        Get analyses by status.
        
        Args:
            status: Analysis status to filter by
            limit: Maximum number of analyses to return
            offset: Number of analyses to skip
            
        Returns:
            List of job application tracking instances
        """
        return await self.list_by_field("analysis_status", status, limit=limit, offset=offset)
    
    async def get_pending_analyses(self, limit: Optional[int] = None) -> List[ContractAnalysis]:
        """
        Get pending analyses for processing.
        
        Args:
            limit: Maximum number of analyses to return
            
        Returns:
            List of pending job application tracking instances
        """
        return await self.get_analyses_by_status("pending", limit=limit)
    
    async def get_analyses_by_file_hash(self, file_hash: str) -> List[ContractAnalysis]:
        """
        Get analyses for the same file (by hash).
        
        Args:
            file_hash: SHA-256 hash of the file
            
        Returns:
            List of analyses for the same file
        """
        return await self.list_by_field("file_hash", file_hash)
    
    async def search_analyses(
        self,
        user_id: Optional[UUID] = None,
        filename_pattern: Optional[str] = None,
        status: Optional[str] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ContractAnalysis]:
        """
        Search analyses with multiple filters.
        
        Args:
            user_id: Filter by user ID (optional)
            filename_pattern: Filter by filename pattern (optional)
            status: Filter by analysis status (optional)
            min_risk_score: Minimum risk score filter (optional)
            max_risk_score: Maximum risk score filter (optional)
            date_from: Filter analyses created after this date (optional)
            date_to: Filter analyses created before this date (optional)
            limit: Maximum number of analyses to return
            offset: Number of analyses to skip
            
        Returns:
            List of matching job application tracking instances
        """
        query = select(ContractAnalysis)
        
        # Apply filters
        if user_id:
            query = query.where(ContractAnalysis.user_id == user_id)
        
        if filename_pattern:
            query = query.where(ContractAnalysis.filename.ilike(f"%{filename_pattern}%"))
        
        if status:
            query = query.where(ContractAnalysis.analysis_status == status)
        
        if min_risk_score is not None:
            query = query.where(ContractAnalysis.risk_score >= min_risk_score)
        
        if max_risk_score is not None:
            query = query.where(ContractAnalysis.risk_score <= max_risk_score)
        
        if date_from:
            query = query.where(ContractAnalysis.created_at >= date_from)
        
        if date_to:
            query = query.where(ContractAnalysis.created_at <= date_to)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(ContractAnalysis.created_at))
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_analysis_statistics(
        self, 
        user_id: Optional[UUID] = None,
        days: int = 30
    ) -> Dict:
        """
        Get analysis statistics.
        
        Args:
            user_id: Filter by user ID (optional)
            days: Number of days to include in statistics
            
        Returns:
            Dictionary with analysis statistics
        """
        date_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Base query
        base_query = select(ContractAnalysis).where(
            ContractAnalysis.created_at >= date_threshold
        )
        
        if user_id:
            base_query = base_query.where(ContractAnalysis.user_id == user_id)
        
        # Total analyses
        total_result = await self.session.execute(
            select(func.count(ContractAnalysis.id)).select_from(base_query.subquery())
        )
        total_analyses = total_result.scalar()
        
        # Completed analyses
        completed_result = await self.session.execute(
            base_query.where(ContractAnalysis.analysis_status == "completed")
        )
        completed_analyses = len(completed_result.scalars().all())
        
        # Failed analyses
        failed_result = await self.session.execute(
            base_query.where(ContractAnalysis.analysis_status == "failed")
        )
        failed_analyses = len(failed_result.scalars().all())
        
        # Average processing time
        avg_time_result = await self.session.execute(
            select(func.avg(ContractAnalysis.processing_time_seconds))
            .select_from(base_query.subquery())
            .where(ContractAnalysis.analysis_status == "completed")
        )
        avg_processing_time = avg_time_result.scalar() or 0
        
        # Average risk score
        avg_risk_result = await self.session.execute(
            select(func.avg(ContractAnalysis.risk_score))
            .select_from(base_query.subquery())
            .where(ContractAnalysis.analysis_status == "completed")
        )
        avg_risk_score = avg_risk_result.scalar() or 0
        
        return {
            "total_analyses": total_analyses,
            "completed_analyses": completed_analyses,
            "failed_analyses": failed_analyses,
            "pending_analyses": total_analyses - completed_analyses - failed_analyses,
            "success_rate": completed_analyses / total_analyses if total_analyses > 0 else 0,
            "average_processing_time_seconds": float(avg_processing_time),
            "average_risk_score": float(avg_risk_score),
            "period_days": days
        }
    
    async def get_high_risk_analyses(
        self, 
        risk_threshold: float = 0.7,
        limit: Optional[int] = None
    ) -> List[ContractAnalysis]:
        """
        Get analyses with high risk scores.
        
        Args:
            risk_threshold: Minimum risk score to be considered high risk
            limit: Maximum number of analyses to return
            
        Returns:
            List of high-risk job application tracking instances
        """
        query = select(ContractAnalysis).where(
            and_(
                ContractAnalysis.analysis_status == "completed",
                ContractAnalysis.risk_score >= risk_threshold
            )
        ).order_by(desc(ContractAnalysis.risk_score))
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def cleanup_old_analyses(self, days_old: int = 90) -> int:
        """
        Clean up old completed analyses.
        
        Args:
            days_old: Delete analyses older than this many days
            
        Returns:
            Number of analyses deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        result = await self.session.execute(
            select(ContractAnalysis.id).where(
                and_(
                    ContractAnalysis.created_at < cutoff_date,
                    ContractAnalysis.analysis_status.in_(["completed", "failed"])
                )
            )
        )
        
        analysis_ids = result.scalars().all()
        
        if analysis_ids:
            from sqlalchemy import delete
            await self.session.execute(
                delete(ContractAnalysis).where(
                    ContractAnalysis.id.in_(analysis_ids)
                )
            )
        
        return len(analysis_ids)


# Global instance management
_contract_repository = None


def get_contract_repository(session: AsyncSession = None) -> ContractRepository:
    """
    Get contract repository instance.
    
    Args:
        session: Database session (optional)
        
    Returns:
        ContractRepository instance
    """
    global _contract_repository
    
    if session:
        return ContractRepository(session)
    
    if _contract_repository is None:
        # This would typically use dependency injection in a real app
        # For now, we'll create a basic instance with database manager
        from ..core.database import get_database_manager
        import asyncio
        
        try:
            # Get database manager
            db_manager = asyncio.run(get_database_manager())
            _contract_repository = ContractRepository(db_manager)
        except Exception as e:
            logger.warning(f"Failed to initialize contract repository: {e}")
            # Return a mock repository for now
            _contract_repository = None
    
    return _contract_repository