"""
Audit repository for security and compliance logging operations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.database_models import AuditLog, User
from .base_repository import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Repository for audit logging operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)
    
    async def log_event(
        self,
        event_type: str,
        user_id: Optional[UUID] = None,
        event_data: Optional[Dict] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        result: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (e.g., 'user_login', 'contract_analysis')
            user_id: ID of the user who performed the action (optional)
            event_data: Additional event details as JSON (optional)
            resource_type: Type of resource accessed (optional)
            resource_id: ID of the resource accessed (optional)
            action: Action performed (CREATE, READ, UPDATE, DELETE) (optional)
            result: Result of the action (SUCCESS, FAILURE, ERROR) (optional)
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)
            session_id: Session identifier (optional)
            request_id: Request correlation ID (optional)
            
        Returns:
            Created audit log instance
        """
        return await self.create(
            event_type=event_type,
            user_id=user_id,
            event_data=event_data,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id
        )
    
    async def log_user_login(
        self,
        user_id: UUID,
        ip_address: str,
        user_agent: str,
        success: bool,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """
        Log a user login attempt.
        
        Args:
            user_id: User UUID
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether login was successful
            session_id: Session identifier (optional)
            request_id: Request correlation ID (optional)
            
        Returns:
            Created audit log instance
        """
        return await self.log_event(
            event_type="user_login",
            user_id=user_id,
            action="LOGIN",
            result="SUCCESS" if success else "FAILURE",
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id
        )
    
    async def log_user_logout(
        self,
        user_id: UUID,
        ip_address: str,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """
        Log a user logout.
        
        Args:
            user_id: User UUID
            ip_address: Client IP address
            session_id: Session identifier (optional)
            request_id: Request correlation ID (optional)
            
        Returns:
            Created audit log instance
        """
        return await self.log_event(
            event_type="user_logout",
            user_id=user_id,
            action="LOGOUT",
            result="SUCCESS",
            ip_address=ip_address,
            session_id=session_id,
            request_id=request_id
        )
    
    async def log_contract_analysis(
        self,
        user_id: UUID,
        analysis_id: str,
        action: str,
        result: str,
        ip_address: Optional[str] = None,
        processing_time: Optional[float] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """
        Log a job application tracking event.
        
        Args:
            user_id: User UUID
            analysis_id: Contract analysis UUID
            action: Action performed (CREATE, READ, UPDATE, DELETE)
            result: Result of the action (SUCCESS, FAILURE, ERROR)
            ip_address: Client IP address (optional)
            processing_time: Analysis processing time in seconds (optional)
            request_id: Request correlation ID (optional)
            
        Returns:
            Created audit log instance
        """
        event_data = {}
        if processing_time is not None:
            event_data["processing_time_seconds"] = processing_time
        
        return await self.log_event(
            event_type="contract_analysis",
            user_id=user_id,
            resource_type="contract_analysis",
            resource_id=analysis_id,
            action=action,
            result=result,
            ip_address=ip_address,
            event_data=event_data if event_data else None,
            request_id=request_id
        )
    
    async def log_security_event(
        self,
        event_type: str,
        description: str,
        severity: str = "medium",
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """
        Log a security-related event.
        
        Args:
            event_type: Type of security event
            description: Description of the security event
            severity: Severity level (low, medium, high, critical)
            user_id: User UUID (optional)
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)
            request_id: Request correlation ID (optional)
            
        Returns:
            Created audit log instance
        """
        return await self.log_event(
            event_type=event_type,
            user_id=user_id,
            event_data={
                "description": description,
                "severity": severity
            },
            result="SECURITY_EVENT",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id
        )
    
    async def get_user_activity(
        self,
        user_id: UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        event_type: Optional[str] = None
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific user.
        
        Args:
            user_id: User UUID
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            event_type: Filter by event type (optional)
            
        Returns:
            List of audit log instances
        """
        query = select(AuditLog).where(AuditLog.user_id == user_id)
        
        if event_type:
            query = query.where(AuditLog.event_type == event_type)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(AuditLog.created_at))
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_security_events(
        self,
        severity: Optional[str] = None,
        hours: int = 24,
        limit: Optional[int] = None
    ) -> List[AuditLog]:
        """
        Get recent security events.
        
        Args:
            severity: Filter by severity level (optional)
            hours: Number of hours to look back
            limit: Maximum number of events to return
            
        Returns:
            List of security-related audit log instances
        """
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        query = select(AuditLog).where(
            and_(
                AuditLog.created_at >= time_threshold,
                AuditLog.result == "SECURITY_EVENT"
            )
        )
        
        if severity:
            query = query.where(
                AuditLog.event_data["severity"].astext == severity
            )
        
        query = query.order_by(desc(AuditLog.created_at))
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_failed_login_attempts(
        self,
        hours: int = 24,
        ip_address: Optional[str] = None
    ) -> List[AuditLog]:
        """
        Get failed login attempts.
        
        Args:
            hours: Number of hours to look back
            ip_address: Filter by IP address (optional)
            
        Returns:
            List of failed login audit log instances
        """
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        query = select(AuditLog).where(
            and_(
                AuditLog.event_type == "user_login",
                AuditLog.result == "FAILURE",
                AuditLog.created_at >= time_threshold
            )
        )
        
        if ip_address:
            query = query.where(AuditLog.ip_address == ip_address)
        
        query = query.order_by(desc(AuditLog.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search_logs(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        result: Optional[str] = None,
        ip_address: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AuditLog]:
        """
        Search audit logs with multiple filters.
        
        Args:
            event_type: Filter by event type (optional)
            user_id: Filter by user ID (optional)
            resource_type: Filter by resource type (optional)
            action: Filter by action (optional)
            result: Filter by result (optional)
            ip_address: Filter by IP address (optional)
            date_from: Filter logs created after this date (optional)
            date_to: Filter logs created before this date (optional)
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            List of matching audit log instances
        """
        query = select(AuditLog)
        
        # Apply filters
        if event_type:
            query = query.where(AuditLog.event_type == event_type)
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        
        if action:
            query = query.where(AuditLog.action == action)
        
        if result:
            query = query.where(AuditLog.result == result)
        
        if ip_address:
            query = query.where(AuditLog.ip_address == ip_address)
        
        if date_from:
            query = query.where(AuditLog.created_at >= date_from)
        
        if date_to:
            query = query.where(AuditLog.created_at <= date_to)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(AuditLog.created_at))
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_audit_statistics(self, days: int = 30) -> Dict:
        """
        Get audit log statistics.
        
        Args:
            days: Number of days to include in statistics
            
        Returns:
            Dictionary with audit statistics
        """
        date_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Total events
        total_result = await self.session.execute(
            select(func.count(AuditLog.id)).where(
                AuditLog.created_at >= date_threshold
            )
        )
        total_events = total_result.scalar()
        
        # Events by type
        type_result = await self.session.execute(
            select(AuditLog.event_type, func.count(AuditLog.id))
            .where(AuditLog.created_at >= date_threshold)
            .group_by(AuditLog.event_type)
        )
        events_by_type = dict(type_result.fetchall())
        
        # Events by result
        result_result = await self.session.execute(
            select(AuditLog.result, func.count(AuditLog.id))
            .where(AuditLog.created_at >= date_threshold)
            .group_by(AuditLog.result)
        )
        events_by_result = dict(result_result.fetchall())
        
        # Unique users
        users_result = await self.session.execute(
            select(func.count(func.distinct(AuditLog.user_id)))
            .where(
                and_(
                    AuditLog.created_at >= date_threshold,
                    AuditLog.user_id.isnot(None)
                )
            )
        )
        unique_users = users_result.scalar()
        
        # Unique IP addresses
        ips_result = await self.session.execute(
            select(func.count(func.distinct(AuditLog.ip_address)))
            .where(
                and_(
                    AuditLog.created_at >= date_threshold,
                    AuditLog.ip_address.isnot(None)
                )
            )
        )
        unique_ips = ips_result.scalar()
        
        return {
            "total_events": total_events,
            "events_by_type": events_by_type,
            "events_by_result": events_by_result,
            "unique_users": unique_users,
            "unique_ip_addresses": unique_ips,
            "period_days": days
        }
    
    async def cleanup_old_logs(self, days_old: int = 90) -> int:
        """
        Clean up old audit logs.
        
        Args:
            days_old: Delete logs older than this many days
            
        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        result = await self.session.execute(
            select(AuditLog.id).where(AuditLog.created_at < cutoff_date)
        )
        
        log_ids = result.scalars().all()
        
        if log_ids:
            from sqlalchemy import delete
            await self.session.execute(
                delete(AuditLog).where(AuditLog.id.in_(log_ids))
            )
        
        return len(log_ids)