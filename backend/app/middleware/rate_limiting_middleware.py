"""
Advanced Rate Limiting Middleware for Career Copilot.
Implements comprehensive rate limiting with IP blocking and CORS configuration.
"""

import time
from typing import Dict, Optional, Set, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.audit import audit_logger, AuditEventType, AuditSeverity

logger = get_logger(__name__)


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    requests_per_minute: int
    requests_per_hour: int
    burst_limit: int
    window_size: int = 60  # seconds
    block_duration: int = 300  # seconds (5 minutes)


@dataclass
class ClientInfo:
    """Client tracking information."""
    ip_address: str
    requests_minute: deque = field(default_factory=deque)
    requests_hour: deque = field(default_factory=deque)
    total_requests: int = 0
    blocked_until: Optional[datetime] = None
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    user_agent: Optional[str] = None
    violation_count: int = 0


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware with IP blocking and monitoring."""
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        
        # Client tracking
        self.clients: Dict[str, ClientInfo] = {}
        self.blocked_ips: Set[str] = set()
        
        # Rate limiting rules by endpoint pattern
        self.rate_limit_rules = {
            "default": RateLimitRule(
                requests_per_minute=self.settings.rate_limit_requests_per_minute,
                requests_per_hour=self.settings.rate_limit_requests_per_minute * 60,
                burst_limit=self.settings.rate_limit_burst
            ),
            "auth": RateLimitRule(
                requests_per_minute=10,
                requests_per_hour=100,
                burst_limit=20,
                block_duration=900  # 15 minutes for auth endpoints
            ),
            "upload": RateLimitRule(
                requests_per_minute=5,
                requests_per_hour=50,
                burst_limit=10,
                block_duration=600  # 10 minutes for upload endpoints
            ),
            "api": RateLimitRule(
                requests_per_minute=60,
                requests_per_hour=1000,
                burst_limit=100
            )
        }
        
        # Whitelist for internal services
        self.whitelist_ips = {"127.0.0.1", "::1", "localhost"}
        
        # Paths that have different rate limits
        self.endpoint_patterns = {
            "/api/v1/auth/": "auth",
            "/api/v1/upload": "upload",
            "/api/v1/": "api",
            "/health": None,  # No rate limiting
            "/docs": None,
            "/redoc": None
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting."""
        
        client_ip = self._get_client_ip(request)
        
        # Skip rate limiting for whitelisted IPs
        if client_ip in self.whitelist_ips:
            return await call_next(request)
        
        # Skip rate limiting for certain paths
        rule_type = self._get_rule_type(request.url.path)
        if rule_type is None:
            return await call_next(request)
        
        try:
            # Check if IP is blocked
            if await self._is_ip_blocked(client_ip):
                audit_logger.log_event(
                    event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                    action="Blocked IP attempted access",
                    severity=AuditSeverity.HIGH,
                    ip_address=client_ip,
                    user_agent=request.headers.get("user-agent"),
                    details={"path": request.url.path, "method": request.method}
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="IP address is temporarily blocked due to rate limit violations",
                    headers={"Retry-After": "900"}
                )
            
            # Check rate limits
            if not await self._check_rate_limit(client_ip, request, rule_type):
                # Rate limit exceeded
                await self._handle_rate_limit_violation(client_ip, request)
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(self.rate_limit_rules[rule_type].requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + 60)
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            await self._add_rate_limit_headers(response, client_ip, rule_type)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in rate limiting middleware: {e}")
            # Don't block requests on middleware errors
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address with proxy support."""
        # Check X-Forwarded-For header (from load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"
    
    def _get_rule_type(self, path: str) -> Optional[str]:
        """Determine which rate limiting rule to apply."""
        for pattern, rule_type in self.endpoint_patterns.items():
            if path.startswith(pattern):
                return rule_type
        return "default"
    
    async def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is currently blocked."""
        if ip_address in self.blocked_ips:
            return True
        
        # Check if client has a temporary block
        if ip_address in self.clients:
            client = self.clients[ip_address]
            if client.blocked_until and datetime.utcnow() < client.blocked_until:
                return True
            elif client.blocked_until and datetime.utcnow() >= client.blocked_until:
                # Block expired, remove it
                client.blocked_until = None
                client.violation_count = 0
        
        return False
    
    async def _check_rate_limit(self, ip_address: str, request: Request, rule_type: str) -> bool:
        """Check if request is within rate limits."""
        now = datetime.utcnow()
        current_time = time.time()
        
        # Get or create client info
        if ip_address not in self.clients:
            self.clients[ip_address] = ClientInfo(
                ip_address=ip_address,
                user_agent=request.headers.get("user-agent")
            )
        
        client = self.clients[ip_address]
        client.last_seen = now
        client.total_requests += 1
        
        # Get rate limit rule
        rule = self.rate_limit_rules[rule_type]
        
        # Clean old requests from minute window
        minute_ago = current_time - 60
        while client.requests_minute and client.requests_minute[0] < minute_ago:
            client.requests_minute.popleft()
        
        # Clean old requests from hour window
        hour_ago = current_time - 3600
        while client.requests_hour and client.requests_hour[0] < hour_ago:
            client.requests_hour.popleft()
        
        # Check minute limit
        if len(client.requests_minute) >= rule.requests_per_minute:
            return False
        
        # Check hour limit
        if len(client.requests_hour) >= rule.requests_per_hour:
            return False
        
        # Check burst limit (requests in last 10 seconds)
        burst_window = current_time - 10
        recent_requests = sum(1 for req_time in client.requests_minute if req_time > burst_window)
        if recent_requests >= rule.burst_limit:
            return False
        
        # Add current request to tracking
        client.requests_minute.append(current_time)
        client.requests_hour.append(current_time)
        
        return True
    
    async def _handle_rate_limit_violation(self, ip_address: str, request: Request):
        """Handle rate limit violation."""
        client = self.clients[ip_address]
        client.violation_count += 1
        
        # Determine rule type for block duration
        rule_type = self._get_rule_type(request.url.path)
        rule = self.rate_limit_rules[rule_type]
        
        # Progressive blocking based on violation count
        if client.violation_count >= 5:
            # Permanent block for repeated violations
            self.blocked_ips.add(ip_address)
            block_duration = 3600  # 1 hour
        elif client.violation_count >= 3:
            # Temporary block
            block_duration = rule.block_duration * 2  # Double the block time
        else:
            # Short temporary block
            block_duration = rule.block_duration
        
        client.blocked_until = datetime.utcnow() + timedelta(seconds=block_duration)
        
        # Log the violation
        audit_logger.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            action=f"Rate limit violation #{client.violation_count}",
            severity=AuditSeverity.HIGH if client.violation_count >= 3 else AuditSeverity.MEDIUM,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            details={
                "path": request.url.path,
                "method": request.method,
                "violation_count": client.violation_count,
                "block_duration": block_duration,
                "total_requests": client.total_requests
            }
        )
        
        logger.warning(
            f"Rate limit violation for IP {ip_address}",
            extra={
                "ip_address": ip_address,
                "violation_count": client.violation_count,
                "block_duration": block_duration,
                "path": request.url.path
            }
        )
    
    async def _add_rate_limit_headers(self, response: Response, ip_address: str, rule_type: str):
        """Add rate limiting headers to response."""
        if ip_address not in self.clients:
            return
        
        client = self.clients[ip_address]
        rule = self.rate_limit_rules[rule_type]
        
        # Calculate remaining requests
        remaining_minute = max(0, rule.requests_per_minute - len(client.requests_minute))
        remaining_hour = max(0, rule.requests_per_hour - len(client.requests_hour))
        
        # Add headers
        response.headers["X-RateLimit-Limit-Minute"] = str(rule.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(rule.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining_minute)
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining_hour)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
    
    def get_client_stats(self, ip_address: str) -> Optional[Dict]:
        """Get statistics for a specific client IP."""
        if ip_address not in self.clients:
            return None
        
        client = self.clients[ip_address]
        return {
            "ip_address": client.ip_address,
            "total_requests": client.total_requests,
            "requests_last_minute": len(client.requests_minute),
            "requests_last_hour": len(client.requests_hour),
            "violation_count": client.violation_count,
            "blocked_until": client.blocked_until.isoformat() if client.blocked_until else None,
            "first_seen": client.first_seen.isoformat(),
            "last_seen": client.last_seen.isoformat(),
            "user_agent": client.user_agent
        }
    
    def unblock_ip(self, ip_address: str) -> bool:
        """Manually unblock an IP address."""
        if ip_address in self.blocked_ips:
            self.blocked_ips.remove(ip_address)
        
        if ip_address in self.clients:
            self.clients[ip_address].blocked_until = None
            self.clients[ip_address].violation_count = 0
            return True
        
        return False
    
    def cleanup_old_clients(self, max_age_hours: int = 24):
        """Clean up old client tracking data."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        old_clients = [
            ip for ip, client in self.clients.items()
            if client.last_seen < cutoff_time and not client.blocked_until
        ]
        
        for ip in old_clients:
            del self.clients[ip]
        
        logger.info(f"Cleaned up {len(old_clients)} old client records")


# Global rate limiter instance
_rate_limiter: Optional[RateLimitingMiddleware] = None


def get_rate_limiter() -> Optional[RateLimitingMiddleware]:
    """Get the rate limiter instance."""
    return _rate_limiter


def set_rate_limiter(limiter: RateLimitingMiddleware):
    """Set the rate limiter instance."""
    global _rate_limiter
    _rate_limiter = limiter