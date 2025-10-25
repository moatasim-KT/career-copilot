"""
Consolidated Security Middleware
Integrates JWT authentication, RBAC, audit logging, threat detection, AI security validation, and monitoring.
"""

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Callable
from uuid import uuid4

from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.audit import audit_logger, AuditEventType, AuditSeverity
from ..services.jwt_token_manager import get_jwt_token_manager, TokenValidationResult
from ..services.rbac_service import get_rbac_service, Permission, PermissionContext
from ..services.audit_trail_service import (
    get_audit_trail_service,
    AuditAction,
    AuditResult
)
from ..security.malware_scanner import MalwareScanner, ScanStatus
from ..security.ai_security import AISecurityManager

logger = get_logger(__name__)
settings = get_settings()


class SecurityContext:
    """Security context for requests."""
    
    def __init__(self):
        self.user_id: Optional[str] = None
        self.username: Optional[str] = None
        self.email: Optional[str] = None
        self.roles: List[str] = []
        self.permissions: List[str] = []
        self.security_level: str = "public"
        self.session_id: Optional[str] = None
        self.is_authenticated: bool = False
        self.mfa_verified: bool = False
        self.token_type: Optional[str] = None
        self.request_id: str = str(uuid4())


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.max_requests_per_minute = 100
        self.max_requests_per_hour = 1000
        self.blocked_ips: Set[str] = set()
    
    def is_rate_limited(self, identifier: str, ip_address: str) -> bool:
        """Check if request should be rate limited."""
        current_time = time.time()
        
        # Check if IP is blocked
        if ip_address in self.blocked_ips:
            return True
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < 3600  # Keep last hour
            ]
        else:
            self.requests[identifier] = []
        
        # Check rate limits
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < 60  # Last minute
        ]
        
        if len(recent_requests) >= self.max_requests_per_minute:
            return True
        
        if len(self.requests[identifier]) >= self.max_requests_per_hour:
            return True
        
        # Record this request
        self.requests[identifier].append(current_time)
        return False
    
    def block_ip(self, ip_address: str) -> None:
        """Block an IP address."""
        self.blocked_ips.add(ip_address)
        logger.warning(f"IP address blocked: {ip_address}")


class ConsolidatedSecurityMiddleware(BaseHTTPMiddleware):
    """Consolidated security middleware with comprehensive protection."""
    
    def __init__(self, app):
        super().__init__(app)
        self.jwt_manager = get_jwt_token_manager()
        self.rbac_service = get_rbac_service()
        self.audit_service = get_audit_trail_service()
        self.malware_scanner = MalwareScanner()
        self.ai_security_manager = AISecurityManager()
        self.rate_limiter = RateLimiter()
        self.security_scheme = HTTPBearer(auto_error=False)
        
        # Public paths that don't require authentication
        self.public_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
        }
        
        # AI-related endpoints for security validation
        self.ai_endpoints = [
            "/api/v1/ai/",
            "/api/v1/chat/",
            "/api/v1/completion/",
            "/api/v1/embedding/"
        ]
        
        # Paths that require specific permissions
        self.protected_paths = {
            "/api/v1/contracts": {
                "GET": [Permission.CONTRACT_READ],
                "POST": [Permission.CONTRACT_WRITE],
                "PUT": [Permission.CONTRACT_WRITE],
                "DELETE": [Permission.CONTRACT_DELETE],
            },
            "/api/v1/analysis": {
                "GET": [Permission.CONTRACT_READ],
                "POST": [Permission.CONTRACT_ANALYZE],
            },
            "/api/v1/users": {
                "GET": [Permission.USER_READ],
                "POST": [Permission.USER_WRITE],
                "PUT": [Permission.USER_WRITE],
                "DELETE": [Permission.USER_DELETE],
            },
            "/api/v1/admin": {
                "GET": [Permission.SYSTEM_ADMIN],
                "POST": [Permission.SYSTEM_ADMIN],
                "PUT": [Permission.SYSTEM_ADMIN],
                "DELETE": [Permission.SYSTEM_ADMIN],
            },
        }
        
        logger.info("Consolidated security middleware initialized")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through comprehensive security pipeline."""
        start_time = time.time()
        
        # Initialize security context
        security_context = SecurityContext()
        request.state.security_context = security_context
        request.state.request_id = security_context.request_id
        
        try:
            # 1. Rate limiting check
            await self._check_rate_limiting(request, security_context)
            
            # 2. Malware scanning for file uploads
            await self._scan_for_malware(request, security_context)
            
            # 3. AI security validation (for AI endpoints)
            if self._is_ai_endpoint(request.url.path):
                await self._validate_ai_security(request, security_context)
            
            # 4. Authentication
            await self._authenticate_request(request, security_context)
            
            # 5. Authorization
            await self._authorize_request(request, security_context)
            
            # 6. Process request
            response = await call_next(request)
            
            # 7. AI response validation (for AI endpoints)
            if self._is_ai_endpoint(request.url.path):
                response = await self._validate_ai_response(request, response, security_context)
            
            # 8. Log successful request
            duration_ms = (time.time() - start_time) * 1000
            await self._log_request_success(request, security_context, response, duration_ms)
            
            # 9. Add security headers
            self._add_security_headers(response)
            
            return response
            
        except HTTPException as e:
            # Log security violation
            duration_ms = (time.time() - start_time) * 1000
            await self._log_request_failure(request, security_context, e, duration_ms)
            raise
        except Exception as e:
            # Log unexpected error
            duration_ms = (time.time() - start_time) * 1000
            await self._log_request_error(request, security_context, e, duration_ms)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def _check_rate_limiting(self, request: Request, context: SecurityContext) -> None:
        """Check rate limiting for the request."""
        try:
            ip_address = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            
            # Create identifier for rate limiting
            identifier = f"{ip_address}:{user_agent}"
            
            if self.rate_limiter.is_rate_limited(identifier, ip_address):
                await self.audit_service.log_request(
                    request=request,
                    event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                    action=AuditAction.ACCESS,
                    result=AuditResult.DENIED,
                    severity=AuditSeverity.HIGH,
                    details={
                        "ip_address": ip_address,
                        "user_agent": user_agent,
                        "path": str(request.url.path),
                        "method": request.method
                    }
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in rate limiting check: {e}")
    
    async def _scan_for_malware(self, request: Request, context: SecurityContext) -> None:
        """Scan file uploads for malware."""
        try:
            # Check if this is a file upload request
            content_type = request.headers.get("content-type", "")
            
            if "multipart/form-data" in content_type or "application/octet-stream" in content_type:
                # For file uploads, we'll scan the content
                body = await request.body()
                if len(body) > 0:
                    # Scan the uploaded content
                    scan_result = await self.malware_scanner.scan_file(
                        body,
                        "uploaded_file"
                    )
                    
                    if scan_result.status in [ScanStatus.INFECTED, ScanStatus.SUSPICIOUS]:
                        await self.audit_service.log_request(
                            request=request,
                            event_type=AuditEventType.MALWARE_DETECTED,
                            action=AuditAction.CREATE,
                            result=AuditResult.DENIED,
                            severity=AuditSeverity.CRITICAL,
                            details={
                                "scan_result": scan_result.status.value,
                                "threats_found": scan_result.threats_found,
                                "file_hash": scan_result.file_hash
                            }
                        )
                        
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Malicious content detected: {', '.join(scan_result.threats_found)}"
                        )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in malware scanning: {e}")
    
    async def _validate_ai_security(self, request: Request, context: SecurityContext) -> None:
        """Validate AI security for AI endpoints."""
        try:
            # Get request body
            body = await self._get_request_body(request)
            
            if body:
                # Validate input prompt
                prompt = body.get("prompt", "")
                if prompt:
                    validation_result = await self.ai_security_manager.validate_prompt(
                        prompt,
                        context={
                            "path": request.url.path,
                            "method": request.method,
                            "client": request.client.host if request.client else None
                        }
                    )
                    
                    # Block high-risk requests
                    if validation_result.risk_level == "critical":
                        await self.audit_service.log_request(
                            request=request,
                            event_type=AuditEventType.SECURITY_ALERT,
                            action=AuditAction.ACCESS,
                            result=AuditResult.DENIED,
                            severity=AuditSeverity.CRITICAL,
                            details={
                                "ai_security_violation": True,
                                "risk_level": validation_result.risk_level,
                                "threats": validation_result.detected_threats
                            }
                        )
                        
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Request blocked due to AI security concerns"
                        )
                    
                    # Update request with sanitized content
                    body["prompt"] = validation_result.sanitized_content
                    await self._update_request_body(request, body)
                    
                    # Log security event for high-risk requests
                    if validation_result.risk_level == "high":
                        self._log_ai_security_event(
                            "High-risk AI request detected",
                            validation_result,
                            request
                        )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in AI security validation: {e}")
    
    async def _validate_ai_response(self, request: Request, response: Response, context: SecurityContext) -> Response:
        """Validate AI response for security threats."""
        try:
            if response.status_code == 200:
                response_body = await self._get_response_body(response)
                if response_body:
                    # Extract model output
                    output = response_body.get("content", "")
                    if output:
                        validation_result = await self.ai_security_manager.validate_output(
                            output,
                            model_info=response_body.get("model", {})
                        )
                        
                        # Update response with sanitized content if needed
                        if validation_result.detected_threats:
                            response_body["content"] = validation_result.sanitized_content
                            await self._update_response_body(response, response_body)
                            
                            # Log security event for detected threats
                            self._log_ai_security_event(
                                "Threats detected in AI response",
                                validation_result,
                                request
                            )
                    
                    # Monitor model behavior
                    body = await self._get_request_body(request)
                    monitoring_result = self.ai_security_manager.monitor_model_behavior(
                        model_id=response_body.get("model", {}).get("id", "unknown"),
                        request_data=body or {},
                        response_data=response_body
                    )
                    
                    # Log anomalies
                    if monitoring_result.get("anomalies"):
                        self._log_ai_security_event(
                            "AI model behavior anomalies detected",
                            monitoring_result,
                            request
                        )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in AI response validation: {e}")
            return response
    
    async def _authenticate_request(self, request: Request, context: SecurityContext) -> None:
        """Authenticate the request."""
        try:
            # Skip authentication for public paths
            if self._is_public_path(request.url.path):
                return
            
            # Extract JWT token
            token = self._extract_jwt_token(request)
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Validate token
            validation_result = await self.jwt_manager.validate_token(token)
            if not validation_result.is_valid:
                await self.audit_service.log_request(
                    request=request,
                    event_type=AuditEventType.LOGIN_FAILURE,
                    action=AuditAction.ACCESS,
                    result=AuditResult.DENIED,
                    severity=AuditSeverity.MEDIUM,
                    details={"error": validation_result.error}
                )
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=validation_result.error,
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Set security context
            claims = validation_result.claims
            context.user_id = claims.sub
            context.username = claims.username
            context.email = claims.email
            context.roles = claims.roles
            context.permissions = claims.permissions
            context.security_level = claims.security_level
            context.session_id = claims.session_id
            context.is_authenticated = True
            context.mfa_verified = claims.mfa_verified
            context.token_type = claims.token_type
            
            # Set request state for other middleware/handlers
            request.state.user_id = context.user_id
            request.state.session_id = context.session_id
            request.state.is_authenticated = True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in authentication: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    async def _authorize_request(self, request: Request, context: SecurityContext) -> None:
        """Authorize the request based on RBAC."""
        try:
            # Skip authorization for public paths
            if self._is_public_path(request.url.path):
                return
            
            # Skip authorization for unauthenticated requests (will be handled by authentication)
            if not context.is_authenticated:
                return
            
            # Check path-based permissions
            required_permissions = self._get_required_permissions(
                request.url.path,
                request.method
            )
            
            if required_permissions:
                # Create permission context
                permission_context = PermissionContext(
                    user_id=context.user_id,
                    resource_type=self._extract_resource_type(request.url.path),
                    resource_id=self._extract_resource_id(request.url.path),
                    action=request.method.lower(),
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent")
                )
                
                # Check permissions
                access_result = await self.rbac_service.check_multiple_permissions(
                    user_id=context.user_id,
                    required_permissions=required_permissions,
                    require_all=False,  # Any permission is sufficient
                    context=permission_context
                )
                
                if not access_result.allowed:
                    await self.audit_service.log_request(
                        request=request,
                        event_type=AuditEventType.UNAUTHORIZED_ACCESS,
                        action=AuditAction.ACCESS,
                        result=AuditResult.DENIED,
                        severity=AuditSeverity.HIGH,
                        details={
                            "required_permissions": [p.value for p in required_permissions],
                            "user_permissions": [p.value for p in access_result.user_permissions],
                            "reason": access_result.reason
                        }
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions: {access_result.reason}"
                    )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in authorization: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authorization failed"
            )
    
    def _is_ai_endpoint(self, path: str) -> bool:
        """Check if the endpoint is AI-related."""
        return any(path.startswith(endpoint) for endpoint in self.ai_endpoints)
    
    async def _get_request_body(self, request: Request) -> Dict[str, Any]:
        """Get JSON body from request."""
        try:
            return await request.json()
        except:
            return {}
    
    async def _update_request_body(self, request: Request, body: Dict[str, Any]):
        """Update request body with modified content."""
        setattr(request.state, "_body", json.dumps(body).encode())
    
    async def _get_response_body(self, response: Response) -> Dict[str, Any]:
        """Get JSON body from response."""
        try:
            body = response.body
            if isinstance(body, bytes):
                return json.loads(body.decode())
            return {}
        except:
            return {}
    
    async def _update_response_body(self, response: Response, body: Dict[str, Any]):
        """Update response body with modified content."""
        response.body = json.dumps(body).encode()
        response.headers["content-length"] = str(len(response.body))
    
    def _extract_jwt_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request."""
        # Try Authorization header first
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        # Try cookie as fallback
        return request.cookies.get("access_token")
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (doesn't require authentication)."""
        return any(path.startswith(public_path) for public_path in self.public_paths)
    
    def _get_required_permissions(self, path: str, method: str) -> List[Permission]:
        """Get required permissions for a path and method."""
        for protected_path, methods in self.protected_paths.items():
            if path.startswith(protected_path):
                return methods.get(method, [])
        return []
    
    def _extract_resource_type(self, path: str) -> Optional[str]:
        """Extract resource type from path."""
        if "/contracts" in path:
            return "contract"
        elif "/analysis" in path:
            return "analysis"
        elif "/users" in path:
            return "user"
        elif "/admin" in path:
            return "system"
        elif "/ai/" in path or "/chat/" in path:
            return "ai_service"
        return None
    
    def _extract_resource_id(self, path: str) -> Optional[str]:
        """Extract resource ID from path."""
        # Simple extraction - in practice, you might use regex or path parsing
        parts = path.split("/")
        if len(parts) > 3:
            # Look for UUID-like patterns
            for part in parts[3:]:
                if len(part) == 36 and part.count("-") == 4:  # UUID format
                    return part
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _log_ai_security_event(self, message: str, details: Any, request: Request):
        """Log AI security event."""
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            action="AI security alert",
            severity=AuditSeverity.HIGH,
            user_id=getattr(request.state, "user_id", None),
            details={
                "message": message,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "timestamp": datetime.utcnow().isoformat(),
                "ai_security_details": details
            }
        )
    
    async def _log_request_success(
        self,
        request: Request,
        context: SecurityContext,
        response: Response,
        duration_ms: float
    ) -> None:
        """Log successful request."""
        try:
            await self.audit_service.log_request(
                request=request,
                event_type=AuditEventType.API_CALL,
                action=AuditAction.ACCESS,
                result=AuditResult.SUCCESS,
                severity=AuditSeverity.LOW,
                resource_type=self._extract_resource_type(request.url.path),
                resource_id=self._extract_resource_id(request.url.path),
                details={
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "user_agent": request.headers.get("user-agent"),
                    "authenticated": context.is_authenticated,
                    "mfa_verified": context.mfa_verified,
                    "is_ai_endpoint": self._is_ai_endpoint(request.url.path)
                },
                duration_ms=duration_ms
            )
        except Exception as e:
            logger.error(f"Error logging request success: {e}")
    
    async def _log_request_failure(
        self,
        request: Request,
        context: SecurityContext,
        exception: HTTPException,
        duration_ms: float
    ) -> None:
        """Log failed request."""
        try:
            event_type = AuditEventType.API_ERROR
            severity = AuditSeverity.MEDIUM
            
            if exception.status_code == 401:
                event_type = AuditEventType.UNAUTHORIZED_ACCESS
                severity = AuditSeverity.HIGH
            elif exception.status_code == 403:
                event_type = AuditEventType.PERMISSION_DENIED
                severity = AuditSeverity.HIGH
            elif exception.status_code == 429:
                event_type = AuditEventType.RATE_LIMIT_EXCEEDED
                severity = AuditSeverity.HIGH
            
            await self.audit_service.log_request(
                request=request,
                event_type=event_type,
                action=AuditAction.ACCESS,
                result=AuditResult.DENIED,
                severity=severity,
                resource_type=self._extract_resource_type(request.url.path),
                resource_id=self._extract_resource_id(request.url.path),
                details={
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": exception.status_code,
                    "error": exception.detail,
                    "user_agent": request.headers.get("user-agent"),
                    "authenticated": context.is_authenticated,
                    "is_ai_endpoint": self._is_ai_endpoint(request.url.path)
                },
                duration_ms=duration_ms
            )
        except Exception as e:
            logger.error(f"Error logging request failure: {e}")
    
    async def _log_request_error(
        self,
        request: Request,
        context: SecurityContext,
        exception: Exception,
        duration_ms: float
    ) -> None:
        """Log request error."""
        try:
            await self.audit_service.log_request(
                request=request,
                event_type=AuditEventType.API_ERROR,
                action=AuditAction.ACCESS,
                result=AuditResult.ERROR,
                severity=AuditSeverity.HIGH,
                resource_type=self._extract_resource_type(request.url.path),
                resource_id=self._extract_resource_id(request.url.path),
                details={
                    "method": request.method,
                    "path": str(request.url.path),
                    "error": str(exception),
                    "error_type": type(exception).__name__,
                    "user_agent": request.headers.get("user-agent"),
                    "authenticated": context.is_authenticated,
                    "is_ai_endpoint": self._is_ai_endpoint(request.url.path)
                },
                duration_ms=duration_ms
            )
        except Exception as e:
            logger.error(f"Error logging request error: {e}")
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"


# Alias for backward compatibility
SecurityMiddleware = ConsolidatedSecurityMiddleware
AISecurityMiddleware = ConsolidatedSecurityMiddleware