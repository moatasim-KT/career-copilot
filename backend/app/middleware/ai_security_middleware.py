"""
Middleware for AI security validation and monitoring.
"""

from typing import Dict, Any, Callable
from fastapi import Request, Response
import json
from datetime import datetime

from ..core.logging import get_logger
from ..security.ai_security import AISecurityManager
from ..core.audit import audit_logger, AuditEventType, AuditSeverity

logger = get_logger(__name__)

class AISecurityMiddleware:
    """
    Middleware for handling AI security concerns.
    
    This middleware:
    1. Validates and sanitizes incoming prompts
    2. Validates model outputs
    3. Monitors model behavior
    4. Anonymizes sensitive data
    5. Handles security logging
    """
    
    def __init__(self):
        """Initialize AI security middleware."""
        self.security_manager = AISecurityManager()
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process the request through security checks."""
        try:
            # Only process AI-related endpoints
            if not self._is_ai_endpoint(request.url.path):
                return await call_next(request)
            
            # Get request body
            body = await self._get_request_body(request)
            
            if body:
                # Validate input prompt
                prompt = body.get("prompt", "")
                if prompt:
                    validation_result = await self.security_manager.validate_prompt(
                        prompt,
                        context={
                            "path": request.url.path,
                            "method": request.method,
                            "client": request.client.host if request.client else None
                        }
                    )
                    
                    # Block high-risk requests
                    if validation_result.risk_level == "critical":
                        return self._create_security_response(
                            "Request blocked due to security concerns",
                            validation_result
                        )
                    
                    # Update request with sanitized content
                    body["prompt"] = validation_result.sanitized_content
                    await self._update_request_body(request, body)
                    
                    # Log security event for high-risk requests
                    if validation_result.risk_level == "high":
                        self._log_security_event(
                            "High-risk AI request detected",
                            validation_result,
                            request
                        )
            
            # Process the request
            response = await call_next(request)
            
            # Validate the response
            if response.status_code == 200:
                response_body = await self._get_response_body(response)
                if response_body:
                    # Extract model output
                    output = response_body.get("content", "")
                    if output:
                        validation_result = await self.security_manager.validate_output(
                            output,
                            model_info=response_body.get("model", {})
                        )
                        
                        # Update response with sanitized content if needed
                        if validation_result.detected_threats:
                            response_body["content"] = validation_result.sanitized_content
                            await self._update_response_body(response, response_body)
                            
                            # Log security event for detected threats
                            self._log_security_event(
                                "Threats detected in AI response",
                                validation_result,
                                request
                            )
                    
                    # Monitor model behavior
                    monitoring_result = self.security_manager.monitor_model_behavior(
                        model_id=response_body.get("model", {}).get("id", "unknown"),
                        request_data=body or {},
                        response_data=response_body
                    )
                    
                    # Log anomalies
                    if monitoring_result["anomalies"]:
                        self._log_security_event(
                            "AI model behavior anomalies detected",
                            monitoring_result,
                            request
                        )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in AI security middleware: {str(e)}")
            return await call_next(request)
    
    def _is_ai_endpoint(self, path: str) -> bool:
        """Check if the endpoint is AI-related."""
        ai_endpoints = [
            "/api/v1/ai/",
            "/api/v1/chat/",
            "/api/v1/completion/",
            "/api/v1/embedding/"
        ]
        return any(path.startswith(endpoint) for endpoint in ai_endpoints)
    
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
    
    def _create_security_response(self, message: str, details: Any) -> Response:
        """Create a security block response."""
        return Response(
            content=json.dumps({
                "error": "security_violation",
                "message": message,
                "details": {
                    "risk_level": details.risk_level,
                    "threats": details.detected_threats
                }
            }),
            media_type="application/json",
            status_code=403
        )
    
    def _log_security_event(self, message: str, details: Any, request: Request):
        """Log security event."""
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
                "details": details
            }
        )