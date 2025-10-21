"""
Enhanced External Service Manager
Provides centralized management of external service integrations with retry logic,
circuit breaker patterns, authentication flows, and fallback mechanisms.
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
import json

import httpx
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.exceptions import ExternalServiceError, NetworkError, AuthenticationError
from ..utils.error_handler import get_error_handler, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)


class ServiceStatus(str, Enum):
    """External service status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"
    MAINTENANCE = "maintenance"


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryConfig:
    """Retry configuration for external services"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_status_codes: List[int] = field(default_factory=lambda: [429, 502, 503, 504])
    retry_on_exceptions: List[type] = field(default_factory=lambda: [httpx.TimeoutException, httpx.ConnectError])


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = ExternalServiceError
    success_threshold: int = 3  # For half-open state


class ServiceHealth(BaseModel):
    """Service health information"""
    service_name: str
    status: ServiceStatus
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_count: int = 0
    success_count: int = 0
    last_error: Optional[str] = None
    uptime_percentage: float = 100.0
    circuit_state: CircuitState = CircuitState.CLOSED


class AuthenticationManager:
    """Manages authentication for external services"""
    
    def __init__(self):
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.refresh_callbacks: Dict[str, Callable] = {}
    
    def store_token(
        self,
        service_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        token_type: str = "Bearer"
    ):
        """Store authentication token for a service"""
        self.tokens[service_name] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "token_type": token_type,
            "created_at": datetime.utcnow()
        }
    
    def get_token(self, service_name: str) -> Optional[str]:
        """Get valid authentication token for a service"""
        if service_name not in self.tokens:
            return None
        
        token_info = self.tokens[service_name]
        expires_at = token_info.get("expires_at")
        
        # Check if token is expired
        if expires_at and datetime.utcnow() >= expires_at:
            # Try to refresh token
            if self._refresh_token(service_name):
                token_info = self.tokens[service_name]
            else:
                return None
        
        return f"{token_info['token_type']} {token_info['access_token']}"
    
    def register_refresh_callback(self, service_name: str, callback: Callable):
        """Register a callback function to refresh tokens"""
        self.refresh_callbacks[service_name] = callback
    
    def _refresh_token(self, service_name: str) -> bool:
        """Refresh token using registered callback"""
        if service_name in self.refresh_callbacks:
            try:
                return self.refresh_callbacks[service_name]()
            except Exception as e:
                logger.error(f"Failed to refresh token for {service_name}: {e}")
        return False
    
    def is_token_valid(self, service_name: str) -> bool:
        """Check if token is valid and not expired"""
        if service_name not in self.tokens:
            return False
        
        token_info = self.tokens[service_name]
        expires_at = token_info.get("expires_at")
        
        if expires_at:
            return datetime.utcnow() < expires_at
        
        return True  # No expiration set, assume valid


class CircuitBreaker:
    """Circuit breaker implementation for external services"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.next_attempt_time = None
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise ExternalServiceError(
                    "Circuit breaker is OPEN - service unavailable",
                    service_name=kwargs.get('service_name', 'unknown')
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset"""
        if self.last_failure_time is None:
            return True
        
        return (
            datetime.utcnow() - self.last_failure_time
        ).total_seconds() >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.next_attempt_time = datetime.utcnow() + timedelta(
                seconds=self.config.recovery_timeout
            )


class ExternalServiceManager:
    """Enhanced external service manager with comprehensive integration features"""
    
    def __init__(self):
        self.settings = get_settings()
        self.auth_manager = AuthenticationManager()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.service_health: Dict[str, ServiceHealth] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.error_handler = get_error_handler()
        
        # Initialize default configurations
        self._initialize_default_configs()
        self._initialize_services()
    
    def _initialize_default_configs(self):
        """Initialize default retry and circuit breaker configurations"""
        # Default retry configuration
        default_retry = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
        # Service-specific configurations
        self.retry_configs = {
            "docusign": RetryConfig(
                max_attempts=3,
                base_delay=2.0,
                max_delay=60.0,
                retry_on_status_codes=[429, 502, 503, 504]
            ),
            "slack": RetryConfig(
                max_attempts=2,
                base_delay=1.0,
                max_delay=10.0,
                retry_on_status_codes=[429, 502, 503]
            ),
            "gmail": RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=30.0,
                retry_on_status_codes=[429, 500, 502, 503, 504]
            ),
            "google_drive": RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=30.0,
                retry_on_status_codes=[429, 500, 502, 503, 504]
            ),
            "vector_store": default_retry
        }
        
        # Circuit breaker configurations
        circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=ExternalServiceError
        )
        
        for service_name in self.retry_configs.keys():
            self.circuit_breakers[service_name] = CircuitBreaker(circuit_config)
    
    def _initialize_services(self):
        """Initialize service health tracking"""
        services = ["docusign", "slack", "gmail", "google_drive", "vector_store"]
        
        for service_name in services:
            self.service_health[service_name] = ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.HEALTHY,
                last_check=datetime.utcnow()
            )
    
    async def make_request(
        self,
        service_name: str,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str, bytes]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        require_auth: bool = True
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic, circuit breaker, and authentication
        """
        retry_config = self.retry_configs.get(service_name, RetryConfig())
        circuit_breaker = self.circuit_breakers.get(service_name)
        
        if circuit_breaker:
            return await circuit_breaker.call(
                self._execute_request,
                service_name=service_name,
                method=method,
                url=url,
                headers=headers,
                json_data=json_data,
                data=data,
                params=params,
                timeout=timeout,
                require_auth=require_auth,
                retry_config=retry_config
            )
        else:
            return await self._execute_request(
                service_name=service_name,
                method=method,
                url=url,
                headers=headers,
                json_data=json_data,
                data=data,
                params=params,
                timeout=timeout,
                require_auth=require_auth,
                retry_config=retry_config
            )
    
    async def _execute_request(
        self,
        service_name: str,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str, bytes]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        require_auth: bool = True,
        retry_config: RetryConfig = None
    ) -> httpx.Response:
        """Execute HTTP request with retry logic"""
        
        if retry_config is None:
            retry_config = RetryConfig()
        
        # Prepare headers with authentication
        request_headers = headers or {}
        if require_auth:
            auth_token = self.auth_manager.get_token(service_name)
            if auth_token:
                request_headers["Authorization"] = auth_token
            elif service_name not in ["vector_store"]:  # Vector store doesn't need auth
                raise AuthenticationError(f"No valid authentication token for {service_name}")
        
        last_exception = None
        
        for attempt in range(retry_config.max_attempts):
            try:
                start_time = time.time()
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=request_headers,
                        json=json_data,
                        data=data,
                        params=params
                    )
                
                response_time = (time.time() - start_time) * 1000
                
                # Update service health on success
                self._update_service_health(service_name, True, response_time)
                
                # Check if we should retry based on status code
                if response.status_code in retry_config.retry_on_status_codes:
                    if attempt < retry_config.max_attempts - 1:
                        await self._wait_before_retry(attempt, retry_config)
                        continue
                
                return response
                
            except Exception as e:
                last_exception = e
                
                # Update service health on failure
                self._update_service_health(service_name, False, error=str(e))
                
                # Check if we should retry based on exception type
                should_retry = any(
                    isinstance(e, exc_type) 
                    for exc_type in retry_config.retry_on_exceptions
                )
                
                if should_retry and attempt < retry_config.max_attempts - 1:
                    await self._wait_before_retry(attempt, retry_config)
                    continue
                
                # If this is the last attempt or we shouldn't retry, raise the exception
                break
        
        # All retries exhausted, handle the failure
        if isinstance(last_exception, httpx.TimeoutException):
            raise NetworkError(
                f"Request to {service_name} timed out after {retry_config.max_attempts} attempts",
                operation=f"{method} {url}"
            )
        elif isinstance(last_exception, httpx.ConnectError):
            raise NetworkError(
                f"Failed to connect to {service_name} after {retry_config.max_attempts} attempts",
                operation=f"{method} {url}"
            )
        else:
            raise ExternalServiceError(
                f"Request to {service_name} failed after {retry_config.max_attempts} attempts: {str(last_exception)}",
                service_name=service_name
            )
    
    async def _wait_before_retry(self, attempt: int, retry_config: RetryConfig):
        """Calculate and wait before retry with exponential backoff and jitter"""
        delay = min(
            retry_config.base_delay * (retry_config.exponential_base ** attempt),
            retry_config.max_delay
        )
        
        if retry_config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        await asyncio.sleep(delay)
    
    def _update_service_health(
        self,
        service_name: str,
        success: bool,
        response_time: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Update service health metrics"""
        if service_name not in self.service_health:
            self.service_health[service_name] = ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.HEALTHY,
                last_check=datetime.utcnow()
            )
        
        health = self.service_health[service_name]
        health.last_check = datetime.utcnow()
        
        if success:
            health.success_count += 1
            health.response_time_ms = response_time
            
            # Update status based on circuit breaker state
            circuit_breaker = self.circuit_breakers.get(service_name)
            if circuit_breaker:
                if circuit_breaker.state == CircuitState.OPEN:
                    health.status = ServiceStatus.CIRCUIT_OPEN
                elif circuit_breaker.state == CircuitState.HALF_OPEN:
                    health.status = ServiceStatus.DEGRADED
                else:
                    health.status = ServiceStatus.HEALTHY
        else:
            health.error_count += 1
            health.last_error = error
            
            # Determine status based on error rate
            total_requests = health.success_count + health.error_count
            error_rate = health.error_count / total_requests if total_requests > 0 else 0
            
            if error_rate > 0.5:
                health.status = ServiceStatus.UNHEALTHY
            elif error_rate > 0.2:
                health.status = ServiceStatus.DEGRADED
        
        # Calculate uptime percentage
        total_requests = health.success_count + health.error_count
        if total_requests > 0:
            health.uptime_percentage = (health.success_count / total_requests) * 100
    
    def register_fallback_handler(self, service_name: str, handler: Callable):
        """Register a fallback handler for when a service is unavailable"""
        self.fallback_handlers[service_name] = handler
    
    async def call_with_fallback(
        self,
        service_name: str,
        primary_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Call primary function with fallback if service is unavailable"""
        try:
            return await primary_func(*args, **kwargs)
        except (ExternalServiceError, NetworkError, AuthenticationError) as e:
            logger.warning(f"Primary service {service_name} failed: {e}")
            
            # Try fallback handler
            if service_name in self.fallback_handlers:
                try:
                    logger.info(f"Using fallback handler for {service_name}")
                    return await self.fallback_handlers[service_name](*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback handler for {service_name} also failed: {fallback_error}")
            
            # No fallback available or fallback failed
            raise e
    
    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """Get health information for a specific service"""
        return self.service_health.get(service_name)
    
    def get_all_service_health(self) -> Dict[str, ServiceHealth]:
        """Get health information for all services"""
        return self.service_health.copy()
    
    async def health_check_all_services(self) -> Dict[str, ServiceHealth]:
        """Perform health check on all registered services"""
        health_checks = []
        
        for service_name in self.service_health.keys():
            health_checks.append(self._health_check_service(service_name))
        
        await asyncio.gather(*health_checks, return_exceptions=True)
        return self.get_all_service_health()
    
    async def _health_check_service(self, service_name: str):
        """Perform health check on a specific service"""
        try:
            # Define health check endpoints for each service
            health_endpoints = {
                "docusign": "https://demo.docusign.net/restapi/v2.1/accounts",
                "slack": "https://slack.com/api/api.test",
                "gmail": "https://www.googleapis.com/gmail/v1/users/me/profile",
                "google_drive": "https://www.googleapis.com/drive/v3/about",
                "vector_store": None  # Internal service
            }
            
            endpoint = health_endpoints.get(service_name)
            if not endpoint:
                # For internal services, just mark as healthy
                self._update_service_health(service_name, True)
                return
            
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(endpoint)
                
            response_time = (time.time() - start_time) * 1000
            success = response.status_code < 400
            
            self._update_service_health(
                service_name,
                success,
                response_time,
                f"HTTP {response.status_code}" if not success else None
            )
            
        except Exception as e:
            self._update_service_health(service_name, False, error=str(e))
    
    def reset_circuit_breaker(self, service_name: str):
        """Manually reset circuit breaker for a service"""
        if service_name in self.circuit_breakers:
            circuit_breaker = self.circuit_breakers[service_name]
            circuit_breaker.state = CircuitState.CLOSED
            circuit_breaker.failure_count = 0
            circuit_breaker.success_count = 0
            circuit_breaker.last_failure_time = None
            
            # Update service health
            if service_name in self.service_health:
                self.service_health[service_name].status = ServiceStatus.HEALTHY
            
            logger.info(f"Circuit breaker reset for {service_name}")
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all services"""
        stats = {
            "total_services": len(self.service_health),
            "healthy_services": 0,
            "degraded_services": 0,
            "unhealthy_services": 0,
            "circuit_open_services": 0,
            "services": {}
        }
        
        for service_name, health in self.service_health.items():
            # Count by status
            if health.status == ServiceStatus.HEALTHY:
                stats["healthy_services"] += 1
            elif health.status == ServiceStatus.DEGRADED:
                stats["degraded_services"] += 1
            elif health.status == ServiceStatus.UNHEALTHY:
                stats["unhealthy_services"] += 1
            elif health.status == ServiceStatus.CIRCUIT_OPEN:
                stats["circuit_open_services"] += 1
            
            # Service details
            circuit_breaker = self.circuit_breakers.get(service_name)
            stats["services"][service_name] = {
                "status": health.status.value,
                "uptime_percentage": health.uptime_percentage,
                "success_count": health.success_count,
                "error_count": health.error_count,
                "last_check": health.last_check.isoformat(),
                "response_time_ms": health.response_time_ms,
                "circuit_state": circuit_breaker.state.value if circuit_breaker else "unknown",
                "has_fallback": service_name in self.fallback_handlers
            }
        
        return stats


# Global instance
_external_service_manager = None


def get_external_service_manager() -> ExternalServiceManager:
    """Get global external service manager instance"""
    global _external_service_manager
    if _external_service_manager is None:
        _external_service_manager = ExternalServiceManager()
    return _external_service_manager