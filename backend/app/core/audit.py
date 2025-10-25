"""
Audit logging system for security monitoring and compliance.
"""

import json
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pathlib import Path

from fastapi import Request
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""
    
    # Authentication and Authorization
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    API_KEY_USED = "api_key_used"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    AUTHENTICATION_ATTEMPT = "authentication_attempt"
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    TOKEN_REFRESHED = "token_refreshed"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    PASSWORD_CHANGED = "password_changed"
    MFA_SETUP_INITIATED = "mfa_setup_initiated"
    SESSION_TIMEOUT = "session_timeout"
    
    # File Operations
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"
    FILE_ACCESS = "file_access"
    
    # Analysis Operations
    ANALYSIS_START = "analysis_start"
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_FAILED = "analysis_failed"
    ANALYSIS_TIMEOUT = "analysis_timeout"
    
    # Security Events
    SECURITY_VIOLATION = "security_violation"
    MALICIOUS_FILE_DETECTED = "malicious_file_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # System Events
    SYSTEM_START = "system_start"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIG_CHANGE = "config_change"
    ERROR_OCCURRED = "error_occurred"
    
    # Data Events
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Audit event model."""
    
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: str
    result: str  # success, failure, error
    details: Dict[str, Any] = {}
    request_id: Optional[str] = None
    duration_ms: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditLogger:
    """Centralized audit logging system."""
    
    def __init__(self):
        self.settings = get_settings()
        # Use default audit log file if not configured
        self.audit_log_file = getattr(self.settings, 'audit_log_file', 'logs/audit.log')
        self.logger = get_logger("audit")
        
        # Ensure audit log directory exists
        if self.audit_log_file:
            try:
                Path(self.audit_log_file).parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError):
                # Fallback to current directory if we can't create the logs directory
                self.audit_log_file = "audit.log"
    
    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        result: str = "success",
        severity: AuditSeverity = AuditSeverity.LOW,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[float] = None
    ) -> None:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            action: Description of action performed
            result: Result of action (success, failure, error)
            severity: Severity level
            user_id: User identifier
            session_id: Session identifier
            ip_address: Client IP address
            user_agent: Client user agent
            resource: Resource being accessed
            details: Additional event details
            request_id: Request identifier
            duration_ms: Duration in milliseconds
        """
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            request_id=request_id,
            duration_ms=duration_ms
        )
        
        # Log to structured logger
        log_data = event.dict()
        
        # Choose log level based on severity
        if severity == AuditSeverity.CRITICAL:
            self.logger.critical(f"AUDIT: {action}", extra=log_data)
        elif severity == AuditSeverity.HIGH:
            self.logger.error(f"AUDIT: {action}", extra=log_data)
        elif severity == AuditSeverity.MEDIUM:
            self.logger.warning(f"AUDIT: {action}", extra=log_data)
        else:
            self.logger.info(f"AUDIT: {action}", extra=log_data)
        
        # Write to audit log file if configured
        if self.audit_log_file:
            try:
                with open(self.audit_log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, default=str) + '\n')
            except Exception as e:
                logger.error(f"Failed to write to audit log file: {e}")
    
    def log_request(
        self,
        request: Request,
        event_type: AuditEventType,
        action: str,
        result: str = "success",
        severity: AuditSeverity = AuditSeverity.LOW,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ) -> None:
        """
        Log an audit event from a FastAPI request.
        
        Args:
            request: FastAPI request object
            event_type: Type of event
            action: Description of action performed
            result: Result of action
            severity: Severity level
            resource: Resource being accessed
            details: Additional event details
            duration_ms: Duration in milliseconds
        """
        # Extract request information
        ip_address = None
        if request.client:
            ip_address = request.client.host
        
        user_agent = request.headers.get("user-agent")
        request_id = getattr(request.state, "request_id", None)
        
        # Extract user information if available
        user_id = getattr(request.state, "user_id", None)
        session_id = getattr(request.state, "session_id", None)
        
        self.log_event(
            event_type=event_type,
            action=action,
            result=result,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            details=details,
            request_id=request_id,
            duration_ms=duration_ms
        )
    
    def log_file_upload(
        self,
        request: Request,
        filename: str,
        file_size: int,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log file upload event."""
        event_details = {
            "filename": filename,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        }
        if details:
            event_details.update(details)
        
        severity = AuditSeverity.MEDIUM if result == "success" else AuditSeverity.HIGH
        
        self.log_request(
            request=request,
            event_type=AuditEventType.FILE_UPLOAD,
            action=f"File upload: {filename}",
            result=result,
            severity=severity,
            resource=filename,
            details=event_details
        )
    
    def log_analysis_event(
        self,
        request: Request,
        event_type: AuditEventType,
        filename: str,
        result: str = "success",
        duration_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log job application tracking event."""
        event_details = {"filename": filename}
        if details:
            event_details.update(details)
        
        severity = AuditSeverity.LOW if result == "success" else AuditSeverity.MEDIUM
        
        self.log_request(
            request=request,
            event_type=event_type,
            action=f"Contract analysis: {filename}",
            result=result,
            severity=severity,
            resource=filename,
            details=event_details,
            duration_ms=duration_ms
        )
    
    def log_security_event(
        self,
        request: Request,
        event_type: AuditEventType,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.HIGH
    ) -> None:
        """Log security-related event."""
        self.log_request(
            request=request,
            event_type=event_type,
            action=action,
            result="security_violation",
            severity=severity,
            details=details
        )
    
    def log_system_event(
        self,
        event_type: AuditEventType,
        action: str,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log system-level event."""
        severity = AuditSeverity.MEDIUM if event_type in [
            AuditEventType.SYSTEM_START,
            AuditEventType.SYSTEM_SHUTDOWN
        ] else AuditSeverity.LOW
        
        self.log_event(
            event_type=event_type,
            action=action,
            result=result,
            severity=severity,
            details=details
        )


class SecurityMonitor:
    """Security monitoring and alerting."""
    
    def __init__(self):
        self.audit_logger = AuditLogger()
        self.failed_attempts: Dict[str, list] = {}
        self.suspicious_ips: set = set()
        
        # Thresholds
        self.max_failed_attempts = 5
        self.failed_attempt_window = 300  # 5 minutes
        self.rate_limit_window = 60  # 1 minute
        self.max_requests_per_minute = 100
    
    def check_rate_limit(self, ip_address: str, request: Request) -> bool:
        """
        Check if IP address is within rate limits.
        
        Args:
            ip_address: Client IP address
            request: FastAPI request object
            
        Returns:
            bool: True if within limits, False if exceeded
        """
        current_time = time.time()
        
        # Clean old entries
        if ip_address in self.failed_attempts:
            self.failed_attempts[ip_address] = [
                timestamp for timestamp in self.failed_attempts[ip_address]
                if current_time - timestamp < self.rate_limit_window
            ]
        
        # Check current rate
        request_count = len(self.failed_attempts.get(ip_address, []))
        
        if request_count >= self.max_requests_per_minute:
            self.audit_logger.log_security_event(
                request=request,
                event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                action=f"Rate limit exceeded for IP: {ip_address}",
                details={"request_count": request_count, "limit": self.max_requests_per_minute},
                severity=AuditSeverity.HIGH
            )
            return False
        
        # Record this request
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []
        self.failed_attempts[ip_address].append(current_time)
        
        return True
    
    def record_failed_attempt(self, ip_address: str, request: Request, reason: str) -> None:
        """Record a failed authentication/access attempt."""
        current_time = time.time()
        
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []
        
        self.failed_attempts[ip_address].append(current_time)
        
        # Clean old entries
        self.failed_attempts[ip_address] = [
            timestamp for timestamp in self.failed_attempts[ip_address]
            if current_time - timestamp < self.failed_attempt_window
        ]
        
        # Check if threshold exceeded
        if len(self.failed_attempts[ip_address]) >= self.max_failed_attempts:
            self.suspicious_ips.add(ip_address)
            
            self.audit_logger.log_security_event(
                request=request,
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                action=f"Multiple failed attempts from IP: {ip_address}",
                details={
                    "reason": reason,
                    "attempt_count": len(self.failed_attempts[ip_address]),
                    "threshold": self.max_failed_attempts
                },
                severity=AuditSeverity.CRITICAL
            )
    
    def is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is marked as suspicious."""
        return ip_address in self.suspicious_ips
    
    def clear_suspicious_ip(self, ip_address: str) -> None:
        """Clear suspicious status for IP address."""
        self.suspicious_ips.discard(ip_address)
        if ip_address in self.failed_attempts:
            del self.failed_attempts[ip_address]


# Global instances
audit_logger = AuditLogger()
security_monitor = SecurityMonitor()
