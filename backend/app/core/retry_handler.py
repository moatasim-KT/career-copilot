"""
Enhanced retry handler with exponential backoff and circuit breaker pattern.
Provides comprehensive error handling and retry mechanisms for agent LLM calls.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .exceptions import (
    ContractAnalysisError,
    ErrorCategory,
    ErrorSeverity,
    ExternalServiceError,
    NetworkError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class RetryStrategy(str, Enum):
    """Retry strategy types."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 2.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_max: float = 1.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    
    # Retryable exceptions
    retryable_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        ExternalServiceError,
        NetworkError,
        RateLimitError,
        ConnectionError,
        TimeoutError,
    ])
    
    # Non-retryable exceptions
    non_retryable_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        ValueError,
        TypeError,
        KeyError,
    ])


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3
    half_open_max_calls: int = 5
    
    # Failure conditions
    failure_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        ExternalServiceError,
        NetworkError,
        TimeoutError,
        ConnectionError,
    ])


@dataclass
class RetryAttempt:
    """Information about a retry attempt."""
    attempt_number: int
    delay: float
    exception: Optional[Exception]
    timestamp: datetime
    correlation_id: str


@dataclass
class RetryResult:
    """Result of retry operation."""
    success: bool
    result: Any
    attempts: List[RetryAttempt]
    total_time: float
    final_exception: Optional[Exception]
    correlation_id: str


class CircuitBreaker:
    """Circuit breaker implementation for preventing cascading failures."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.next_attempt_time: Optional[datetime] = None
        self.half_open_calls = 0
        
        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes: List[Dict[str, Any]] = []
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {config}")
    
    def can_execute(self) -> bool:
        """Check if execution is allowed based on circuit breaker state."""
        self.total_calls += 1
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
                return True
            return False
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls < self.config.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return False
    
    def record_success(self):
        """Record a successful execution."""
        self.total_successes += 1
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0  # Reset failure count on success
    
    def record_failure(self, exception: Exception):
        """Record a failed execution."""
        self.total_failures += 1
        
        # Check if this exception should trigger circuit breaker
        if not any(isinstance(exception, exc_type) for exc_type in self.config.failure_exceptions):
            return
        
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if not self.last_failure_time:
            return True
        
        return datetime.utcnow() >= (
            self.last_failure_time + timedelta(seconds=self.config.recovery_timeout)
        )
    
    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        old_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        
        self._record_state_change(old_state, self.state, "Recovery successful")
        logger.info(f"Circuit breaker '{self.name}' transitioned to CLOSED")
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        old_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.success_count = 0
        self.half_open_calls = 0
        self.next_attempt_time = datetime.utcnow() + timedelta(seconds=self.config.recovery_timeout)
        
        self._record_state_change(old_state, self.state, f"Failure threshold reached: {self.failure_count}")
        logger.warning(f"Circuit breaker '{self.name}' transitioned to OPEN after {self.failure_count} failures")
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        old_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.half_open_calls = 0
        
        self._record_state_change(old_state, self.state, "Testing recovery")
        logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN for testing")
    
    def _record_state_change(self, old_state: CircuitBreakerState, new_state: CircuitBreakerState, reason: str):
        """Record state change for monitoring."""
        self.state_changes.append({
            "timestamp": datetime.utcnow().isoformat(),
            "old_state": old_state.value,
            "new_state": new_state.value,
            "reason": reason,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
        })
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "failure_rate": self.total_failures / max(self.total_calls, 1),
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "next_attempt_time": self.next_attempt_time.isoformat() if self.next_attempt_time else None,
            "state_changes": self.state_changes[-10:],  # Last 10 state changes
        }


class CircuitBreakerOpenError(ContractAnalysisError):
    """Raised when circuit breaker is open."""
    
    def __init__(self, circuit_breaker_name: str, **kwargs):
        super().__init__(
            f"Circuit breaker '{circuit_breaker_name}' is open",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.EXTERNAL_SERVICE,
            recovery_suggestions=[
                "Wait for the service to recover",
                "Try again later",
                "Check service health status",
            ],
            **kwargs
        )


class RetryHandler:
    """Enhanced retry handler with exponential backoff and circuit breaker support."""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_metrics: Dict[str, Dict[str, Any]] = {}
    
    def get_or_create_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        if name not in self.circuit_breakers:
            config = config or CircuitBreakerConfig()
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_name: Optional[str] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> RetryResult:
        """Execute function with retry logic and optional circuit breaker."""
        retry_config = retry_config or RetryConfig()
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # Get circuit breaker if specified
        circuit_breaker = None
        if circuit_breaker_name:
            circuit_breaker = self.get_or_create_circuit_breaker(
                circuit_breaker_name, circuit_breaker_config
            )
        
        attempts: List[RetryAttempt] = []
        start_time = time.time()
        
        for attempt in range(retry_config.max_attempts):
            # Check circuit breaker
            if circuit_breaker and not circuit_breaker.can_execute():
                final_exception = CircuitBreakerOpenError(circuit_breaker_name)
                return RetryResult(
                    success=False,
                    result=None,
                    attempts=attempts,
                    total_time=time.time() - start_time,
                    final_exception=final_exception,
                    correlation_id=correlation_id
                )
            
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Record success
                if circuit_breaker:
                    circuit_breaker.record_success()
                
                attempts.append(RetryAttempt(
                    attempt_number=attempt + 1,
                    delay=0.0,
                    exception=None,
                    timestamp=datetime.utcnow(),
                    correlation_id=correlation_id
                ))
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_time=time.time() - start_time,
                    final_exception=None,
                    correlation_id=correlation_id
                )
            
            except Exception as e:
                # Record failure in circuit breaker
                if circuit_breaker:
                    circuit_breaker.record_failure(e)
                
                # Check if exception is retryable
                if not self._is_retryable_exception(e, retry_config):
                    attempts.append(RetryAttempt(
                        attempt_number=attempt + 1,
                        delay=0.0,
                        exception=e,
                        timestamp=datetime.utcnow(),
                        correlation_id=correlation_id
                    ))
                    
                    return RetryResult(
                        success=False,
                        result=None,
                        attempts=attempts,
                        total_time=time.time() - start_time,
                        final_exception=e,
                        correlation_id=correlation_id
                    )
                
                # Calculate delay for next attempt
                if attempt < retry_config.max_attempts - 1:
                    delay = self._calculate_delay(attempt, retry_config)
                    
                    attempts.append(RetryAttempt(
                        attempt_number=attempt + 1,
                        delay=delay,
                        exception=e,
                        timestamp=datetime.utcnow(),
                        correlation_id=correlation_id
                    ))
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed (correlation_id: {correlation_id}): {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    await asyncio.sleep(delay)
                else:
                    # Final attempt failed
                    attempts.append(RetryAttempt(
                        attempt_number=attempt + 1,
                        delay=0.0,
                        exception=e,
                        timestamp=datetime.utcnow(),
                        correlation_id=correlation_id
                    ))
        
        # All attempts failed
        final_exception = attempts[-1].exception if attempts else Exception("Unknown error")
        return RetryResult(
            success=False,
            result=None,
            attempts=attempts,
            total_time=time.time() - start_time,
            final_exception=final_exception,
            correlation_id=correlation_id
        )
    
    def _is_retryable_exception(self, exception: Exception, config: RetryConfig) -> bool:
        """Check if exception is retryable."""
        # Check non-retryable exceptions first
        for exc_type in config.non_retryable_exceptions:
            if isinstance(exception, exc_type):
                return False
        
        # Check retryable exceptions
        for exc_type in config.retryable_exceptions:
            if isinstance(exception, exc_type):
                return True
        
        # Default behavior for unknown exceptions
        return True
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt."""
        if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.exponential_base ** attempt)
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)
        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
        else:  # IMMEDIATE
            delay = 0.0
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay)
        
        # Add jitter if enabled
        if config.jitter and delay > 0:
            import random
            jitter = random.uniform(0, config.jitter_max)
            delay += jitter
        
        return delay
    
    def get_circuit_breaker_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers."""
        return {name: cb.get_metrics() for name, cb in self.circuit_breakers.items()}


# Global retry handler instance
_retry_handler: Optional[RetryHandler] = None


def get_retry_handler() -> RetryHandler:
    """Get the global retry handler instance."""
    global _retry_handler
    if _retry_handler is None:
        _retry_handler = RetryHandler()
    return _retry_handler


def with_retry(
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker_name: Optional[str] = None,
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
):
    """Decorator for adding retry logic to functions."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_handler = get_retry_handler()
            
            result = await retry_handler.execute_with_retry(
                func,
                *args,
                retry_config=retry_config,
                circuit_breaker_name=circuit_breaker_name,
                circuit_breaker_config=circuit_breaker_config,
                **kwargs
            )
            
            if result.success:
                return result.result
            else:
                raise result.final_exception
        
        return wrapper
    return decorator


def with_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
):
    """Decorator for adding circuit breaker to functions."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_handler = get_retry_handler()
            circuit_breaker = retry_handler.get_or_create_circuit_breaker(name, config)
            
            if not circuit_breaker.can_execute():
                raise CircuitBreakerOpenError(name)
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                circuit_breaker.record_success()
                return result
            
            except Exception as e:
                circuit_breaker.record_failure(e)
                raise
        
        return wrapper
    return decorator