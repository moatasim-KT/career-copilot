"""
Standardized Error Handling for LLM Providers
Provides consistent error handling, retry logic, and fallback mechanisms across all LLM providers.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union
from uuid import uuid4

from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type,
    RetryError, AttemptManager
)

from ..core.logging import get_logger

logger = get_logger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    QUOTA_EXCEEDED = "quota_exceeded"
    MODEL_NOT_FOUND = "model_not_found"
    INVALID_REQUEST = "invalid_request"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


class RetryStrategy(str, Enum):
    """Retry strategies for different error types."""
    NO_RETRY = "no_retry"
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    CUSTOM = "custom"


@dataclass
class ErrorInfo:
    """Comprehensive error information."""
    error_id: str
    provider: str
    error_type: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    original_exception: Optional[Exception]
    timestamp: datetime
    request_id: Optional[str] = None
    model: Optional[str] = None
    retry_count: int = 0
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    strategy: RetryStrategy
    max_attempts: int
    base_delay: float
    max_delay: float
    exponential_base: float = 2.0
    jitter: bool = True
    
    @classmethod
    def no_retry(cls) -> 'RetryConfig':
        return cls(RetryStrategy.NO_RETRY, 1, 0, 0)
    
    @classmethod
    def exponential(cls, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0) -> 'RetryConfig':
        return cls(RetryStrategy.EXPONENTIAL_BACKOFF, max_attempts, base_delay, max_delay)
    
    @classmethod
    def linear(cls, max_attempts: int = 3, base_delay: float = 1.0) -> 'RetryConfig':
        return cls(RetryStrategy.LINEAR_BACKOFF, max_attempts, base_delay, base_delay * max_attempts)


class LLMError(Exception):
    """Base class for LLM-related errors."""
    
    def __init__(self, message: str, error_info: Optional[ErrorInfo] = None):
        super().__init__(message)
        self.error_info = error_info


class LLMAuthenticationError(LLMError):
    """Authentication-related errors."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded errors."""
    pass


class LLMQuotaExceededError(LLMError):
    """Quota exceeded errors."""
    pass


class LLMModelNotFoundError(LLMError):
    """Model not found errors."""
    pass


class LLMInvalidRequestError(LLMError):
    """Invalid request errors."""
    pass


class LLMTimeoutError(LLMError):
    """Timeout errors."""
    pass


class LLMConnectionError(LLMError):
    """Connection errors."""
    pass


class LLMServerError(LLMError):
    """Server-side errors."""
    pass


class ErrorClassifier:
    """Classifies errors and determines appropriate handling strategies."""
    
    def __init__(self):
        # Error classification rules
        self.classification_rules = {
            # Authentication errors
            "authentication": {
                "keywords": ["unauthorized", "invalid api key", "authentication", "forbidden"],
                "status_codes": [401, 403],
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.HIGH,
                "retry_config": RetryConfig.no_retry()
            },
            
            # Rate limit errors
            "rate_limit": {
                "keywords": ["rate limit", "too many requests", "quota exceeded"],
                "status_codes": [429],
                "category": ErrorCategory.RATE_LIMIT,
                "severity": ErrorSeverity.MEDIUM,
                "retry_config": RetryConfig.exponential(max_attempts=5, base_delay=2.0, max_delay=120.0)
            },
            
            # Model not found errors
            "model_not_found": {
                "keywords": ["model not found", "model does not exist", "invalid model"],
                "status_codes": [404],
                "category": ErrorCategory.MODEL_NOT_FOUND,
                "severity": ErrorSeverity.HIGH,
                "retry_config": RetryConfig.no_retry()
            },
            
            # Invalid request errors
            "invalid_request": {
                "keywords": ["invalid request", "bad request", "validation error"],
                "status_codes": [400],
                "category": ErrorCategory.INVALID_REQUEST,
                "severity": ErrorSeverity.MEDIUM,
                "retry_config": RetryConfig.no_retry()
            },
            
            # Timeout errors
            "timeout": {
                "keywords": ["timeout", "timed out", "deadline exceeded"],
                "status_codes": [408, 504],
                "category": ErrorCategory.TIMEOUT,
                "severity": ErrorSeverity.MEDIUM,
                "retry_config": RetryConfig.exponential(max_attempts=3, base_delay=1.0, max_delay=30.0)
            },
            
            # Connection errors
            "connection": {
                "keywords": ["connection", "network", "unreachable", "dns"],
                "status_codes": [502, 503],
                "category": ErrorCategory.CONNECTION,
                "severity": ErrorSeverity.MEDIUM,
                "retry_config": RetryConfig.exponential(max_attempts=3, base_delay=2.0, max_delay=60.0)
            },
            
            # Server errors
            "server_error": {
                "keywords": ["internal server error", "service unavailable"],
                "status_codes": [500, 502, 503, 504],
                "category": ErrorCategory.SERVER_ERROR,
                "severity": ErrorSeverity.HIGH,
                "retry_config": RetryConfig.exponential(max_attempts=3, base_delay=5.0, max_delay=120.0)
            }
        }
    
    def classify_error(self, exception: Exception, provider: str, context: Dict[str, Any] = None) -> ErrorInfo:
        """Classify an error and return comprehensive error information."""
        error_message = str(exception).lower()
        status_code = getattr(exception, 'status_code', None)
        
        # Try to match against classification rules
        for error_type, rules in self.classification_rules.items():
            # Check keywords
            if any(keyword in error_message for keyword in rules["keywords"]):
                return self._create_error_info(exception, provider, error_type, rules, context)
            
            # Check status codes
            if status_code and status_code in rules["status_codes"]:
                return self._create_error_info(exception, provider, error_type, rules, context)
        
        # Default classification for unknown errors
        return ErrorInfo(
            error_id=str(uuid4()),
            provider=provider,
            error_type="unknown",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            message=str(exception),
            original_exception=exception,
            timestamp=datetime.now(),
            context=context or {}
        )
    
    def _create_error_info(self, exception: Exception, provider: str, error_type: str, 
                          rules: Dict[str, Any], context: Dict[str, Any] = None) -> ErrorInfo:
        """Create ErrorInfo from classification rules."""
        return ErrorInfo(
            error_id=str(uuid4()),
            provider=provider,
            error_type=error_type,
            category=rules["category"],
            severity=rules["severity"],
            message=str(exception),
            original_exception=exception,
            timestamp=datetime.now(),
            context=context or {}
        )
    
    def get_retry_config(self, error_info: ErrorInfo) -> RetryConfig:
        """Get retry configuration for an error."""
        for error_type, rules in self.classification_rules.items():
            if error_info.error_type == error_type:
                return rules["retry_config"]
        
        # Default retry config for unknown errors
        return RetryConfig.exponential(max_attempts=2, base_delay=1.0, max_delay=10.0)


class FallbackManager:
    """Manages fallback strategies when primary providers fail."""
    
    def __init__(self):
        self.fallback_chains = {}
        self.provider_health = {}
        self.circuit_breakers = {}
    
    def register_fallback_chain(self, primary_provider: str, fallback_providers: List[str]):
        """Register a fallback chain for a provider."""
        self.fallback_chains[primary_provider] = fallback_providers
        logger.info(f"Registered fallback chain for {primary_provider}: {fallback_providers}")
    
    def get_next_provider(self, failed_provider: str, attempted_providers: List[str] = None) -> Optional[str]:
        """Get the next provider to try in the fallback chain."""
        attempted_providers = attempted_providers or []
        
        if failed_provider not in self.fallback_chains:
            return None
        
        fallback_providers = self.fallback_chains[failed_provider]
        
        for provider in fallback_providers:
            if provider not in attempted_providers and self._is_provider_healthy(provider):
                return provider
        
        return None
    
    def _is_provider_healthy(self, provider: str) -> bool:
        """Check if a provider is healthy (not circuit broken)."""
        if provider not in self.circuit_breakers:
            return True
        
        circuit_breaker = self.circuit_breakers[provider]
        return circuit_breaker.state != "open"
    
    def record_provider_failure(self, provider: str):
        """Record a provider failure for circuit breaker logic."""
        if provider not in self.circuit_breakers:
            self.circuit_breakers[provider] = CircuitBreaker(provider)
        
        self.circuit_breakers[provider].record_failure()
    
    def record_provider_success(self, provider: str):
        """Record a provider success for circuit breaker logic."""
        if provider not in self.circuit_breakers:
            self.circuit_breakers[provider] = CircuitBreaker(provider)
        
        self.circuit_breakers[provider].record_success()


class CircuitBreaker:
    """Circuit breaker for provider reliability."""
    
    def __init__(self, provider: str, failure_threshold: int = 5, timeout_duration: int = 60):
        self.provider = provider
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def record_failure(self):
        """Record a failure."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened for provider {self.provider}")
    
    def record_success(self):
        """Record a success."""
        self.failure_count = 0
        self.state = "closed"
    
    def can_attempt(self) -> bool:
        """Check if an attempt can be made."""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if (self.last_failure_time and 
                datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout_duration)):
                self.state = "half-open"
                return True
            return False
        
        # half-open state
        return True


class LLMErrorHandler:
    """Comprehensive error handler for LLM providers."""
    
    def __init__(self):
        self.classifier = ErrorClassifier()
        self.fallback_manager = FallbackManager()
        self.error_history = []
        self.max_history_size = 1000
        
        # Error statistics
        self.error_stats = {
            "total_errors": 0,
            "errors_by_provider": {},
            "errors_by_category": {},
            "errors_by_severity": {}
        }
    
    def handle_error(self, exception: Exception, provider: str, context: Dict[str, Any] = None) -> ErrorInfo:
        """Handle an error and return comprehensive error information."""
        error_info = self.classifier.classify_error(exception, provider, context)
        
        # Record error in history
        self._record_error(error_info)
        
        # Log error appropriately based on severity
        self._log_error(error_info)
        
        # Update circuit breaker
        self.fallback_manager.record_provider_failure(provider)
        
        return error_info
    
    def should_retry(self, error_info: ErrorInfo) -> bool:
        """Determine if an operation should be retried."""
        retry_config = self.classifier.get_retry_config(error_info)
        return retry_config.strategy != RetryStrategy.NO_RETRY and error_info.retry_count < retry_config.max_attempts
    
    def get_retry_delay(self, error_info: ErrorInfo) -> float:
        """Calculate retry delay based on error type and retry count."""
        retry_config = self.classifier.get_retry_config(error_info)
        
        if retry_config.strategy == RetryStrategy.NO_RETRY:
            return 0
        
        if retry_config.strategy == RetryStrategy.IMMEDIATE:
            return 0
        
        if retry_config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = retry_config.base_delay * (error_info.retry_count + 1)
        
        elif retry_config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = retry_config.base_delay * (retry_config.exponential_base ** error_info.retry_count)
        
        else:
            delay = retry_config.base_delay
        
        # Apply jitter if enabled
        if retry_config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
        
        return min(delay, retry_config.max_delay)
    
    def get_fallback_provider(self, failed_provider: str, attempted_providers: List[str] = None) -> Optional[str]:
        """Get a fallback provider for the failed provider."""
        return self.fallback_manager.get_next_provider(failed_provider, attempted_providers)
    
    def create_retry_decorator(self, provider: str, context: Dict[str, Any] = None):
        """Create a retry decorator for a specific provider."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                attempted_providers = [provider]
                last_error = None
                
                while True:
                    try:
                        # Check circuit breaker
                        if provider in self.fallback_manager.circuit_breakers:
                            circuit_breaker = self.fallback_manager.circuit_breakers[provider]
                            if not circuit_breaker.can_attempt():
                                raise LLMError(f"Circuit breaker open for provider {provider}")
                        
                        # Attempt the operation
                        result = await func(*args, **kwargs)
                        
                        # Record success
                        self.fallback_manager.record_provider_success(provider)
                        
                        return result
                        
                    except Exception as e:
                        error_info = self.handle_error(e, provider, context)
                        last_error = error_info
                        
                        # Check if we should retry with the same provider
                        if self.should_retry(error_info):
                            delay = self.get_retry_delay(error_info)
                            if delay > 0:
                                await asyncio.sleep(delay)
                            
                            error_info.retry_count += 1
                            continue
                        
                        # Try fallback provider
                        fallback_provider = self.get_fallback_provider(provider, attempted_providers)
                        if fallback_provider:
                            attempted_providers.append(fallback_provider)
                            provider = fallback_provider
                            continue
                        
                        # No more options, raise the last error
                        raise self._create_llm_exception(error_info)
                
            return wrapper
        return decorator
    
    def _record_error(self, error_info: ErrorInfo):
        """Record error in history and update statistics."""
        # Add to history
        self.error_history.append(error_info)
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
        
        # Update statistics
        self.error_stats["total_errors"] += 1
        
        # By provider
        if error_info.provider not in self.error_stats["errors_by_provider"]:
            self.error_stats["errors_by_provider"][error_info.provider] = 0
        self.error_stats["errors_by_provider"][error_info.provider] += 1
        
        # By category
        category = error_info.category.value
        if category not in self.error_stats["errors_by_category"]:
            self.error_stats["errors_by_category"][category] = 0
        self.error_stats["errors_by_category"][category] += 1
        
        # By severity
        severity = error_info.severity.value
        if severity not in self.error_stats["errors_by_severity"]:
            self.error_stats["errors_by_severity"][severity] = 0
        self.error_stats["errors_by_severity"][severity] += 1
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level based on severity."""
        log_message = (
            f"LLM Error [{error_info.error_id}] - "
            f"Provider: {error_info.provider}, "
            f"Type: {error_info.error_type}, "
            f"Category: {error_info.category.value}, "
            f"Message: {error_info.message}"
        )
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _create_llm_exception(self, error_info: ErrorInfo) -> LLMError:
        """Create appropriate LLM exception based on error category."""
        exception_map = {
            ErrorCategory.AUTHENTICATION: LLMAuthenticationError,
            ErrorCategory.RATE_LIMIT: LLMRateLimitError,
            ErrorCategory.QUOTA_EXCEEDED: LLMQuotaExceededError,
            ErrorCategory.MODEL_NOT_FOUND: LLMModelNotFoundError,
            ErrorCategory.INVALID_REQUEST: LLMInvalidRequestError,
            ErrorCategory.TIMEOUT: LLMTimeoutError,
            ErrorCategory.CONNECTION: LLMConnectionError,
            ErrorCategory.SERVER_ERROR: LLMServerError
        }
        
        exception_class = exception_map.get(error_info.category, LLMError)
        return exception_class(error_info.message, error_info)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        return {
            "total_errors": self.error_stats["total_errors"],
            "errors_by_provider": self.error_stats["errors_by_provider"],
            "errors_by_category": self.error_stats["errors_by_category"],
            "errors_by_severity": self.error_stats["errors_by_severity"],
            "recent_errors": len([e for e in self.error_history 
                                if datetime.now() - e.timestamp < timedelta(hours=1)]),
            "circuit_breaker_states": {
                provider: cb.state 
                for provider, cb in self.fallback_manager.circuit_breakers.items()
            }
        }
    
    def register_fallback_chain(self, primary_provider: str, fallback_providers: List[str]):
        """Register a fallback chain for a provider."""
        self.fallback_manager.register_fallback_chain(primary_provider, fallback_providers)


# Global error handler instance
_llm_error_handler = None


def get_llm_error_handler() -> LLMErrorHandler:
    """Get the global LLM error handler instance."""
    global _llm_error_handler
    
    if _llm_error_handler is None:
        _llm_error_handler = LLMErrorHandler()
        
        # Register default fallback chains
        _llm_error_handler.register_fallback_chain("openai", ["groq", "ollama"])
        _llm_error_handler.register_fallback_chain("groq", ["openai", "ollama"])
        _llm_error_handler.register_fallback_chain("ollama", ["openai", "groq"])
    
    return _llm_error_handler


# Convenience decorators
def with_llm_error_handling(provider: str, context: Dict[str, Any] = None):
    """Decorator for automatic LLM error handling."""
    error_handler = get_llm_error_handler()
    return error_handler.create_retry_decorator(provider, context)