"""
Enhanced Audit Trail Service
Provides comprehensive audit logging and compliance tracking.
"""

import json
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import Request
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.database import get_database_manager
from ..core.logging import get_logger
from ..models.database_models import AuditLog, SecurityEvent

logger = get_logger(__name__)
settings = get_settings()


class AuditEventType(str, Enum):
    """Comprehensive audit event types."""
    
    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_CREATED = "token_created"
    TOKEN_REFRESHED = "token_refreshed"
    TOKEN_REVOKED = "token_revoked"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    
    # Authorization Events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    
    # File and Data Events
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"
    FILE_ACCESS = "file_access"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    
    # Contract Analysis Events
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    ANALYSIS_CANCELLED = "analysis_cancelled"
    REPORT_GENERATED = "report_generated"
    
    # Security Events
    MALWARE_DETECTED = "malware_detected"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    
    # System Events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIG_CHANGED = "config_changed"
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    ERROR_OCCURRED = "error_occurred"
    
    # Integration Events
    DOCUSIGN_ENVELOPE_CREATED = "docusign_envelope_created"
    DOCUSIGN_DOCUMENT_SIGNED = "docusign_document_signed"
    SLACK_MESSAGE_SENT = "slack_message_sent"
    EMAIL_SENT = "email_sent"
    
    # API Events
    API_CALL = "api_call"
    API_ERROR = "api_error"
    API_RATE_LIMITED = "api_rate_limited"
    
    # Compliance Events
    GDPR_REQUEST = "gdpr_request"
    DATA_RETENTION_POLICY = "data_retention_policy"
    COMPLIANCE_VIOLATION = "compliance_violation"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditAction(str, Enum):
    """Standard audit actions."""
    
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ACCESS = "access"
    MODIFY = "modify"
    EXPORT = "export"
    IMPORT = "import"


class AuditResult(str, Enum):
    """Audit event results."""
    
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    DENIED = "denied"
    TIMEOUT = "timeout"


class AuditEventModel(BaseModel):
    """Audit event data model."""
    
    id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: AuditAction
    result: AuditResult
    details: Dict[str, Any] = {}
    request_id: Optional[str] = None
    duration_ms: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ComplianceReport(BaseModel):
    """Compliance audit report."""
    
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    security_violations: int
    failed_logins: int
    unauthorized_access_attempts: int
    data_access_events: int
    compliance_violations: List[Dict[str, Any]]
    recommendations: List[str]


class AuditTrailService:
    """Enhanced audit trail service with compliance features."""
    
    def __init__(self):
        """Initialize audit trail service."""
        self.retention_days = getattr(settings, 'audit_retention_days', 2555)  # 7 years default
        logger.info("Audit Trail Service initialized")
    
    async def log_event(
        self,
        event_type: AuditEventType,
        action: AuditAction,
        result: AuditResult = AuditResult.SUCCESS,
        severity: AuditSeverity = AuditSeverity.LOW,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[float] = None
    ) -> str:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            action: Action performed
            result: Result of the action
            severity: Event severity
            user_id: User identifier
            session_id: Session identifier
            ip_address: Client IP address
            user_agent: Client user agent
            resource_type: Type of resource accessed
            resource_id: Specific resource identifier
            details: Additional event details
            request_id: Request correlation ID
            duration_ms: Operation duration in milliseconds
            
        Returns:
            Audit event ID
        """
        try:
            event_id = str(uuid4())
            
            # Create audit event
            audit_event = AuditEventModel(
                id=event_id,
                timestamp=datetime.now(timezone.utc),
                event_type=event_type,
                severity=severity,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                result=result,
                details=details or {},
                request_id=request_id,
                duration_ms=duration_ms
            )
            
            # Store in database
            await self._store_audit_event(audit_event)
            
            # Check for security events
            if self._is_security_event(event_type, result):
                await self._create_security_event(audit_event)
            
            # Log to application logger
            log_message = f"AUDIT: {action.value} {resource_type or 'system'} - {result.value}"
            log_data = audit_event.dict()
            
            if severity == AuditSeverity.CRITICAL:
                logger.critical(log_message, extra=log_data)
            elif severity == AuditSeverity.HIGH:
                logger.error(log_message, extra=log_data)
            elif severity == AuditSeverity.MEDIUM:
                logger.warning(log_message, extra=log_data)
            else:
                logger.info(log_message, extra=log_data)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return "" 
   
    async def log_request(
        self,
        request: Request,
        event_type: AuditEventType,
        action: AuditAction,
        result: AuditResult = AuditResult.SUCCESS,
        severity: AuditSeverity = AuditSeverity.LOW,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ) -> str:
        """
        Log audit event from FastAPI request.
        
        Args:
            request: FastAPI request object
            event_type: Type of event
            action: Action performed
            result: Result of the action
            severity: Event severity
            resource_type: Type of resource accessed
            resource_id: Specific resource identifier
            details: Additional event details
            duration_ms: Operation duration in milliseconds
            
        Returns:
            Audit event ID
        """
        # Extract request information
        ip_address = None
        if request.client:
            ip_address = request.client.host
        
        user_agent = request.headers.get("user-agent")
        request_id = getattr(request.state, "request_id", None)
        user_id = getattr(request.state, "user_id", None)
        session_id = getattr(request.state, "session_id", None)
        
        return await self.log_event(
            event_type=event_type,
            action=action,
            result=result,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            request_id=request_id,
            duration_ms=duration_ms
        )
    
    async def get_audit_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_types: Optional[List[AuditEventType]] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[AuditEventModel]:
        """
        Retrieve audit events with filtering.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            user_id: Filter by user ID
            event_types: Filter by event types
            severity: Filter by severity
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of audit events
        """
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                from sqlalchemy import select, and_, desc
                
                # Build query conditions
                conditions = []
                
                if start_date:
                    conditions.append(AuditLog.created_at >= start_date)
                if end_date:
                    conditions.append(AuditLog.created_at <= end_date)
                if user_id:
                    conditions.append(AuditLog.user_id == user_id)
                if event_types:
                    event_type_values = [et.value for et in event_types]
                    conditions.append(AuditLog.event_type.in_(event_type_values))
                
                # Execute query
                query = select(AuditLog).where(and_(*conditions)) if conditions else select(AuditLog)
                query = query.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
                
                result = await session.execute(query)
                audit_logs = result.scalars().all()
                
                # Convert to audit event models
                events = []
                for log in audit_logs:
                    event = AuditEventModel(
                        id=str(log.id),
                        timestamp=log.created_at,
                        event_type=AuditEventType(log.event_type),
                        severity=AuditSeverity.MEDIUM,  # Default if not stored
                        user_id=str(log.user_id) if log.user_id else None,
                        session_id=log.session_id,
                        ip_address=str(log.ip_address) if log.ip_address else None,
                        user_agent=log.user_agent,
                        resource_type=log.resource_type,
                        resource_id=log.resource_id,
                        action=AuditAction(log.action) if log.action else AuditAction.ACCESS,
                        result=AuditResult(log.result) if log.result else AuditResult.SUCCESS,
                        details=log.event_data or {},
                        request_id=log.request_id
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            logger.error(f"Error retrieving audit events: {e}")
            return []
    
    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceReport:
        """
        Generate compliance audit report for a date range.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Compliance report
        """
        try:
            # Get all events in the date range
            events = await self.get_audit_events(
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Large limit for comprehensive report
            )
            
            # Analyze events
            events_by_type = {}
            events_by_severity = {}
            security_violations = 0
            failed_logins = 0
            unauthorized_access_attempts = 0
            data_access_events = 0
            compliance_violations = []
            
            for event in events:
                # Count by type
                event_type = event.event_type.value
                events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
                
                # Count by severity
                severity = event.severity.value
                events_by_severity[severity] = events_by_severity.get(severity, 0) + 1
                
                # Count specific security events
                if event.event_type in [
                    AuditEventType.SECURITY_VIOLATION,
                    AuditEventType.MALWARE_DETECTED,
                    AuditEventType.SUSPICIOUS_ACTIVITY
                ]:
                    security_violations += 1
                
                if event.event_type == AuditEventType.LOGIN_FAILURE:
                    failed_logins += 1
                
                if event.event_type == AuditEventType.UNAUTHORIZED_ACCESS:
                    unauthorized_access_attempts += 1
                
                if event.event_type in [
                    AuditEventType.FILE_ACCESS,
                    AuditEventType.DATA_EXPORT,
                    AuditEventType.FILE_DOWNLOAD
                ]:
                    data_access_events += 1
                
                # Check for compliance violations
                if event.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
                    compliance_violations.append({
                        "timestamp": event.timestamp.isoformat(),
                        "event_type": event.event_type.value,
                        "severity": event.severity.value,
                        "user_id": event.user_id,
                        "details": event.details
                    })
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                events,
                security_violations,
                failed_logins,
                unauthorized_access_attempts
            )
            
            return ComplianceReport(
                report_id=str(uuid4()),
                generated_at=datetime.now(timezone.utc),
                period_start=start_date,
                period_end=end_date,
                total_events=len(events),
                events_by_type=events_by_type,
                events_by_severity=events_by_severity,
                security_violations=security_violations,
                failed_logins=failed_logins,
                unauthorized_access_attempts=unauthorized_access_attempts,
                data_access_events=data_access_events,
                compliance_violations=compliance_violations,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return ComplianceReport(
                report_id=str(uuid4()),
                generated_at=datetime.now(timezone.utc),
                period_start=start_date,
                period_end=end_date,
                total_events=0,
                events_by_type={},
                events_by_severity={},
                security_violations=0,
                failed_logins=0,
                unauthorized_access_attempts=0,
                data_access_events=0,
                compliance_violations=[],
                recommendations=[]
            )
    
    async def cleanup_old_events(self) -> int:
        """
        Clean up old audit events based on retention policy.
        
        Returns:
            Number of events cleaned up
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
            
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                from sqlalchemy import delete
                
                # Delete old audit logs
                result = await session.execute(
                    delete(AuditLog).where(AuditLog.created_at < cutoff_date)
                )
                
                deleted_count = result.rowcount
                await session.commit()
                
                logger.info(f"Cleaned up {deleted_count} old audit events")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old audit events: {e}")
            return 0
    
    async def _store_audit_event(self, event: AuditEventModel) -> None:
        """Store audit event in database."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                audit_log = AuditLog(
                    id=event.id,
                    user_id=event.user_id,
                    event_type=event.event_type.value,
                    event_data=event.details,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    action=event.action.value,
                    result=event.result.value,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    session_id=event.session_id,
                    request_id=event.request_id,
                    created_at=event.timestamp
                )
                
                session.add(audit_log)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error storing audit event: {e}")
    
    def _is_security_event(self, event_type: AuditEventType, result: AuditResult) -> bool:
        """Check if event should be treated as a security event."""
        security_event_types = {
            AuditEventType.LOGIN_FAILURE,
            AuditEventType.UNAUTHORIZED_ACCESS,
            AuditEventType.MALWARE_DETECTED,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.SECURITY_VIOLATION,
            AuditEventType.RATE_LIMIT_EXCEEDED,
            AuditEventType.BRUTE_FORCE_ATTEMPT,
            AuditEventType.PRIVILEGE_ESCALATION
        }
        
        return event_type in security_event_types or result == AuditResult.DENIED
    
    async def _create_security_event(self, audit_event: AuditEventModel) -> None:
        """Create security event record."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                security_event = SecurityEvent(
                    user_id=audit_event.user_id,
                    event_type=audit_event.event_type.value,
                    event_category="security",
                    severity=audit_event.severity.value,
                    ip_address=audit_event.ip_address,
                    user_agent=audit_event.user_agent,
                    session_id=audit_event.session_id,
                    request_id=audit_event.request_id,
                    action=f"{audit_event.action.value} {audit_event.resource_type or 'system'}",
                    resource=audit_event.resource_id,
                    result=audit_event.result.value,
                    details=audit_event.details,
                    created_at=audit_event.timestamp
                )
                
                session.add(security_event)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error creating security event: {e}")
    
    def _generate_recommendations(
        self,
        events: List[AuditEventModel],
        security_violations: int,
        failed_logins: int,
        unauthorized_access_attempts: int
    ) -> List[str]:
        """Generate security recommendations based on audit data."""
        recommendations = []
        
        if failed_logins > 100:
            recommendations.append(
                "High number of failed login attempts detected. "
                "Consider implementing stronger password policies and account lockout mechanisms."
            )
        
        if unauthorized_access_attempts > 50:
            recommendations.append(
                "Multiple unauthorized access attempts detected. "
                "Review user permissions and consider implementing additional access controls."
            )
        
        if security_violations > 10:
            recommendations.append(
                "Security violations detected. "
                "Conduct security review and update security policies."
            )
        
        # Check for unusual activity patterns
        user_activity = {}
        for event in events:
            if event.user_id:
                user_activity[event.user_id] = user_activity.get(event.user_id, 0) + 1
        
        high_activity_users = [
            user_id for user_id, count in user_activity.items()
            if count > len(events) * 0.1  # More than 10% of all activity
        ]
        
        if high_activity_users:
            recommendations.append(
                f"Unusual activity patterns detected for users: {', '.join(high_activity_users[:5])}. "
                "Consider reviewing these accounts for potential compromise."
            )
        
        if not recommendations:
            recommendations.append("No significant security issues detected in the audit period.")
        
        return recommendations


# Global instance
_audit_trail_service: Optional[AuditTrailService] = None


def get_audit_trail_service() -> AuditTrailService:
    """Get global audit trail service instance."""
    global _audit_trail_service
    if _audit_trail_service is None:
        _audit_trail_service = AuditTrailService()
    return _audit_trail_service