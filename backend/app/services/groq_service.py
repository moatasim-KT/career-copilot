"""
GROQ Integration Service
Provides comprehensive GROQ API integration with OpenAI compatibility,
optimizations, model selection, performance monitoring, and cost tracking.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import httpx
from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.exceptions import (
    ExternalServiceError,
    ValidationError,
    NetworkError,
    RateLimitError,
    AuthenticationError
)
from ..core.logging import get_logger
from ..core.caching import get_cache_manager
from ..monitoring.metrics_collector import get_metrics_collector
from ..utils.error_handler import get_error_handler, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)
settings = get_settings()
cache_manager = get_cache_manager()
metrics_collector = get_metrics_collector()


class GROQModel(str, Enum):
    """Available GROQ models."""
    # Current supported models (as of 2024)
    LLAMA3_1_8B = "llama-3.1-8b-instant"
    LLAMA3_1_70B = "llama-3.1-70b-versatile" 
    LLAMA3_2_1B = "llama-3.2-1b-preview"
    LLAMA3_2_3B = "llama-3.2-3b-preview"
    LLAMA3_2_11B = "llama-3.2-11b-text-preview"
    LLAMA3_2_90B = "llama-3.2-90b-text-preview"
    MIXTRAL_8X7B = "mixtral-8x7b-32768"
    GEMMA2_9B = "gemma2-9b-it"
    
    # Deprecated models (kept for backward compatibility)
    LLAMA3_8B = "llama3-8b-8192"
    LLAMA3_70B = "llama3-70b-8192"
    GEMMA_7B = "gemma-7b-it"


class GROQTaskType(str, Enum):
    """Task types optimized for GROQ models."""
    FAST_ANALYSIS = "fast_analysis"
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CONVERSATION = "conversation"
    CLASSIFICATION = "classification"


@dataclass
class GROQModelConfig:
    """Configuration for a GROQ model."""
    model: GROQModel
    max_tokens: int
    context_window: int
    cost_per_token: float
    tokens_per_minute_limit: int
    requests_per_minute_limit: int
    optimal_tasks: List[GROQTaskType]
    quality_score: float
    speed_score: float
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GROQRequest:
    """GROQ API request structure."""
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    stream: bool = False
    stop: Optional[List[str]] = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    user: Optional[str] = None


@dataclass
class GROQResponse:
    """GROQ API response structure."""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]
    system_fingerprint: Optional[str] = None
    
    def __init__(self, **kwargs):
        # Handle all known fields
        self.id = kwargs.get('id', '')
        self.object = kwargs.get('object', '')
        self.created = kwargs.get('created', 0)
        self.model = kwargs.get('model', '')
        self.choices = kwargs.get('choices', [])
        self.usage = kwargs.get('usage', {})
        self.system_fingerprint = kwargs.get('system_fingerprint')
        
        # Ignore unknown fields to handle API changes gracefully


@dataclass
class GROQMetrics:
    """GROQ service metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    avg_response_time: float = 0.0
    avg_tokens_per_request: float = 0.0
    avg_cost_per_request: float = 0.0
    error_rate: float = 0.0
    uptime_percentage: float = 100.0
    last_request_time: Optional[datetime] = None
    rate_limit_hits: int = 0
    model_usage: Dict[str, int] = field(default_factory=dict)
    task_performance: Dict[str, float] = field(default_factory=dict)


class GROQRateLimiter:
    """Advanced rate limiter for GROQ API."""
    
    def __init__(self, requests_per_minute: int, tokens_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.request_times: List[datetime] = []
        self.token_usage: List[tuple] = []  # (timestamp, tokens)
        self.burst_allowance = 5  # Allow small bursts
        self.last_reset = datetime.now()
    
    async def acquire(self, estimated_tokens: int = 0) -> bool:
        """Acquire rate limit permission with burst handling."""
        now = datetime.now()
        
        # Reset counters every minute
        if now - self.last_reset >= timedelta(minutes=1):
            self.request_times.clear()
            self.token_usage.clear()
            self.last_reset = now
        
        # Clean old entries (sliding window)
        cutoff = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]
        self.token_usage = [(t, tokens) for t, tokens in self.token_usage if t > cutoff]
        
        # Check request rate limit with burst allowance
        if len(self.request_times) >= self.requests_per_minute + self.burst_allowance:
            return False
        
        # Check token rate limit
        current_tokens = sum(tokens for _, tokens in self.token_usage)
        if current_tokens + estimated_tokens > self.tokens_per_minute:
            return False
        
        # Record this request
        self.request_times.append(now)
        if estimated_tokens > 0:
            self.token_usage.append((now, estimated_tokens))
        
        return True
    
    def get_wait_time(self) -> float:
        """Get recommended wait time before next request."""
        if not self.request_times:
            return 0.0
        
        oldest_request = min(self.request_times)
        time_since_oldest = (datetime.now() - oldest_request).total_seconds()
        
        if len(self.request_times) >= self.requests_per_minute:
            return max(0, 60 - time_since_oldest)
        
        return 0.0


class GROQCircuitBreaker:
    """Circuit breaker for GROQ API reliability."""
    
    def __init__(self, failure_threshold: int = 5, timeout_duration: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open
    
    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if (self.last_failure_time and 
                datetime.now() - self.last_failure_time >= timedelta(seconds=self.timeout_duration)):
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True
    
    def record_success(self):
        """Record successful request."""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class GROQService:
    """Comprehensive GROQ integration service."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize GROQ service."""
        self.api_key = api_key or self._get_api_key()
        self.base_url = base_url or "https://api.groq.com/openai/v1"
        self.client = httpx.AsyncClient(timeout=60.0)
        self.metrics = GROQMetrics()
        self.circuit_breaker = GROQCircuitBreaker()
        
        # Initialize model configurations
        self.model_configs = self._initialize_model_configs()
        
        # Initialize rate limiters per model
        self.rate_limiters = {
            model.value: GROQRateLimiter(
                config.requests_per_minute_limit,
                config.tokens_per_minute_limit
            )
            for model, config in self.model_configs.items()
        }
        
        # Performance tracking
        self.performance_history: Dict[str, List[float]] = {}
        self.cost_tracking: Dict[str, float] = {}
        
        logger.info("GROQ service initialized successfully")
    
    def _get_api_key(self) -> str:
        """Get GROQ API key from settings."""
        if hasattr(settings, 'groq_api_key') and settings.groq_api_key:
            if hasattr(settings.groq_api_key, 'get_secret_value'):
                return settings.groq_api_key.get_secret_value()
            return str(settings.groq_api_key)
        
        raise ValueError("GROQ API key not configured")
    
    def _initialize_model_configs(self) -> Dict[GROQModel, GROQModelConfig]:
        """Initialize GROQ model configurations."""
        return {
            # Current supported models
            GROQModel.LLAMA3_1_8B: GROQModelConfig(
                model=GROQModel.LLAMA3_1_8B,
                max_tokens=8192,
                context_window=128000,
                cost_per_token=0.00000005,
                tokens_per_minute_limit=30000,
                requests_per_minute_limit=100,
                optimal_tasks=[
                    GROQTaskType.CONVERSATION,
                    GROQTaskType.TRANSLATION,
                    GROQTaskType.SUMMARIZATION,
                    GROQTaskType.FAST_ANALYSIS
                ],
                quality_score=0.85,
                speed_score=0.98,
                metadata={
                    "description": "Fast and efficient Llama 3.1 8B model",
                    "best_for": "High-throughput applications and general tasks"
                }
            ),
            GROQModel.LLAMA3_2_3B: GROQModelConfig(
                model=GROQModel.LLAMA3_2_3B,
                max_tokens=8192,
                context_window=128000,
                cost_per_token=0.00000002,
                tokens_per_minute_limit=50000,
                requests_per_minute_limit=150,
                optimal_tasks=[
                    GROQTaskType.CONVERSATION,
                    GROQTaskType.CLASSIFICATION,
                    GROQTaskType.SUMMARIZATION
                ],
                quality_score=0.75,
                speed_score=0.99,
                metadata={
                    "description": "Ultra-fast Llama 3.2 3B model for simple tasks",
                    "best_for": "High-speed processing and simple analysis"
                }
            ),
            GROQModel.LLAMA3_2_11B: GROQModelConfig(
                model=GROQModel.LLAMA3_2_11B,
                max_tokens=8192,
                context_window=128000,
                cost_per_token=0.00000018,
                tokens_per_minute_limit=15000,
                requests_per_minute_limit=50,
                optimal_tasks=[
                    GROQTaskType.REASONING,
                    GROQTaskType.FAST_ANALYSIS,
                    GROQTaskType.CODE_GENERATION
                ],
                quality_score=0.88,
                speed_score=0.95,
                metadata={
                    "description": "Balanced Llama 3.2 11B model for complex tasks",
                    "best_for": "Balanced performance and quality"
                }
            ),
            GROQModel.MIXTRAL_8X7B: GROQModelConfig(
                model=GROQModel.MIXTRAL_8X7B,
                max_tokens=32768,
                context_window=32768,
                cost_per_token=0.00000027,
                tokens_per_minute_limit=6000,
                requests_per_minute_limit=30,
                optimal_tasks=[
                    GROQTaskType.FAST_ANALYSIS,
                    GROQTaskType.REASONING,
                    GROQTaskType.CODE_GENERATION
                ],
                quality_score=0.9,
                speed_score=0.95,
                metadata={
                    "description": "High-performance mixture of experts model",
                    "best_for": "Complex reasoning and analysis tasks"
                }
            ),
            GROQModel.GEMMA2_9B: GROQModelConfig(
                model=GROQModel.GEMMA2_9B,
                max_tokens=8192,
                context_window=8192,
                cost_per_token=0.00000007,
                tokens_per_minute_limit=15000,
                requests_per_minute_limit=60,
                optimal_tasks=[
                    GROQTaskType.CONVERSATION,
                    GROQTaskType.CLASSIFICATION,
                    GROQTaskType.TRANSLATION
                ],
                quality_score=0.82,
                speed_score=0.96,
                metadata={
                    "description": "Efficient Gemma 2 model for lightweight tasks",
                    "best_for": "Fast processing and classification"
                }
            ),
            # Deprecated models (disabled by default)
            GROQModel.LLAMA3_1_70B: GROQModelConfig(
                model=GROQModel.LLAMA3_1_70B,
                max_tokens=8192,
                context_window=128000,
                cost_per_token=0.00000059,
                tokens_per_minute_limit=6000,
                requests_per_minute_limit=30,
                optimal_tasks=[
                    GROQTaskType.REASONING,
                    GROQTaskType.CODE_GENERATION,
                    GROQTaskType.FAST_ANALYSIS
                ],
                quality_score=0.92,
                speed_score=0.93,
                enabled=False,  # May be deprecated
                metadata={
                    "description": "High-quality Llama 3.1 70B model (check availability)",
                    "best_for": "Advanced analysis and reasoning tasks"
                }
            ),
            GROQModel.LLAMA3_8B: GROQModelConfig(
                model=GROQModel.LLAMA3_8B,
                max_tokens=8192,
                context_window=8192,
                cost_per_token=0.00000005,
                tokens_per_minute_limit=30000,
                requests_per_minute_limit=100,
                optimal_tasks=[
                    GROQTaskType.CONVERSATION,
                    GROQTaskType.TRANSLATION,
                    GROQTaskType.SUMMARIZATION
                ],
                quality_score=0.8,
                speed_score=0.98,
                enabled=False,  # Deprecated
                metadata={
                    "description": "DEPRECATED: Use llama-3.1-8b-instant instead",
                    "best_for": "Deprecated model"
                }
            ),
            GROQModel.LLAMA3_70B: GROQModelConfig(
                model=GROQModel.LLAMA3_70B,
                max_tokens=8192,
                context_window=8192,
                cost_per_token=0.00000059,
                tokens_per_minute_limit=6000,
                requests_per_minute_limit=30,
                optimal_tasks=[
                    GROQTaskType.REASONING,
                    GROQTaskType.CODE_GENERATION,
                    GROQTaskType.FAST_ANALYSIS
                ],
                quality_score=0.92,
                speed_score=0.93,
                enabled=False,  # Deprecated
                metadata={
                    "description": "DEPRECATED: Use llama-3.2-11b-text-preview instead",
                    "best_for": "Deprecated model"
                }
            ),
            GROQModel.GEMMA_7B: GROQModelConfig(
                model=GROQModel.GEMMA_7B,
                max_tokens=8192,
                context_window=8192,
                cost_per_token=0.00000007,
                tokens_per_minute_limit=15000,
                requests_per_minute_limit=60,
                optimal_tasks=[
                    GROQTaskType.CONVERSATION,
                    GROQTaskType.CLASSIFICATION,
                    GROQTaskType.TRANSLATION
                ],
                quality_score=0.78,
                speed_score=0.96,
                enabled=False,  # Deprecated
                metadata={
                    "description": "DEPRECATED: Use gemma2-9b-it instead",
                    "best_for": "Deprecated model"
                }
            )
        }
    
    async def get_optimal_model(
        self, 
        task_type: GROQTaskType,
        priority: str = "balanced"  # speed, quality, cost, balanced
    ) -> GROQModel:
        """Get optimal model for a specific task type and priority."""
        suitable_models = []
        
        for model, config in self.model_configs.items():
            if not config.enabled:
                continue
            
            if task_type in config.optimal_tasks:
                suitable_models.append((model, config))
        
        if not suitable_models:
            # Fallback to general-purpose models
            suitable_models = [(model, config) for model, config in self.model_configs.items() 
                             if config.enabled]
        
        if not suitable_models:
            # Final fallback to the most reliable model
            logger.warning("No enabled models found, falling back to llama-3.1-8b-instant")
            return GROQModel.LLAMA3_1_8B
        
        # Sort by priority
        if priority == "speed":
            suitable_models.sort(key=lambda x: x[1].speed_score, reverse=True)
        elif priority == "quality":
            suitable_models.sort(key=lambda x: x[1].quality_score, reverse=True)
        elif priority == "cost":
            suitable_models.sort(key=lambda x: x[1].cost_per_token)
        else:  # balanced
            suitable_models.sort(
                key=lambda x: (x[1].quality_score + x[1].speed_score) / 2,
                reverse=True
            )
        
        return suitable_models[0][0]
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[GROQModel] = None,
        task_type: GROQTaskType = GROQTaskType.CONVERSATION,
        priority: str = "balanced",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using GROQ API with optimizations."""
        error_handler = get_error_handler()
        
        # Validate inputs
        if not messages:
            raise ValidationError(
                "Messages list cannot be empty",
                field="messages",
                details={"task_type": task_type.value, "model": model.value if model else None}
            )
        
        if not all(isinstance(msg, dict) and "content" in msg for msg in messages):
            raise ValidationError(
                "All messages must be dictionaries with 'content' field",
                field="messages",
                details={"message_count": len(messages)}
            )
        
        # Check API key
        if not self.api_key:
            raise AuthenticationError(
                "GROQ API key not configured",
                details={"service": "groq"}
            )
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            raise ExternalServiceError(
                "GROQ service is temporarily unavailable due to repeated failures",
                service_name="groq",
                details={"circuit_breaker_state": "open", "failure_count": self.circuit_breaker.failure_count}
            )
        
        # Select optimal model if not specified
        try:
            if model is None:
                model = await self.get_optimal_model(task_type, priority)
        except Exception as e:
            raise ExternalServiceError(
                f"Failed to select optimal GROQ model: {str(e)}",
                service_name="groq",
                details={"task_type": task_type.value, "priority": priority}
            )
        
        model_config = self.model_configs[model]
        
        # Validate model is enabled
        if not model_config.enabled:
            raise ExternalServiceError(
                f"GROQ model {model.value} is currently disabled",
                service_name="groq",
                details={"model": model.value, "reason": "model_disabled"}
            )
        
        # Check rate limits
        estimated_tokens = sum(len(msg.get("content", "").split()) for msg in messages) * 1.5
        rate_limiter = self.rate_limiters[model.value]
        
        if not await rate_limiter.acquire(int(estimated_tokens)):
            wait_time = rate_limiter.get_wait_time()
            self.metrics.rate_limit_hits += 1
            
            raise RateLimitError(
                f"GROQ API rate limit exceeded for model {model.value}",
                limit=model_config.requests_per_minute_limit,
                window="1 minute",
                details={
                    "model": model.value,
                    "estimated_tokens": int(estimated_tokens),
                    "wait_time": wait_time
                }
            )
        
        # Prepare request
        request_data = GROQRequest(
            model=model.value,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or min(model_config.max_tokens, 4000),
            **kwargs
        )
        
        request_id = str(uuid4())
        start_time = time.time()
        
        try:
            # Make API request
            response = await self._make_api_request(request_data, request_id)
            processing_time = time.time() - start_time
            
            # Validate response structure
            if not response.choices or not response.choices[0]:
                raise ExternalServiceError(
                    "Invalid response structure from GROQ API",
                    service_name="groq",
                    details={"model": model.value, "request_id": request_id}
                )
            
            # Extract response data
            choice = response.choices[0]
            if "message" not in choice or "content" not in choice["message"]:
                raise ExternalServiceError(
                    "Missing content in GROQ API response",
                    service_name="groq",
                    details={"model": model.value, "choice_keys": list(choice.keys())}
                )
            
            content = choice["message"]["content"]
            usage = response.usage
            
            # Validate content
            if not content or not content.strip():
                logger.warning(f"GROQ API returned empty content for model {model.value}")
                content = "[No content generated]"
            
            # Calculate cost
            total_tokens = usage.get("total_tokens", 0)
            cost = total_tokens * model_config.cost_per_token
            
            # Update metrics
            self._update_metrics(model, processing_time, usage, cost, True)
            self.circuit_breaker.record_success()
            
            # Track performance
            self._track_performance(model.value, task_type.value, processing_time)
            
            # Prepare standardized response
            result = {
                "content": content,
                "model": model.value,
                "usage": usage,
                "cost": cost,
                "processing_time": processing_time,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "confidence_score": self._calculate_confidence_score(content, model_config),
                "metadata": {
                    "task_type": task_type.value,
                    "priority": priority,
                    "temperature": temperature,
                    "finish_reason": choice.get("finish_reason"),
                    "model_config": {
                        "quality_score": model_config.quality_score,
                        "speed_score": model_config.speed_score
                    }
                }
            }
            
            logger.info(
                f"GROQ completion successful: {model.value} "
                f"({processing_time:.2f}s, {total_tokens} tokens, ${cost:.6f})"
            )
            
            return result
            
        except httpx.ConnectError as e:
            processing_time = time.time() - start_time
            self._update_metrics(model, processing_time, {}, 0.0, False)
            self.circuit_breaker.record_failure()
            
            raise NetworkError(
                "Failed to connect to GROQ API",
                operation="generate_completion",
                details={
                    "model": model.value,
                    "request_id": request_id,
                    "processing_time": processing_time
                }
            )
            
        except httpx.TimeoutException as e:
            processing_time = time.time() - start_time
            self._update_metrics(model, processing_time, {}, 0.0, False)
            self.circuit_breaker.record_failure()
            
            raise ExternalServiceError(
                "GROQ API request timed out",
                service_name="groq",
                details={
                    "model": model.value,
                    "request_id": request_id,
                    "processing_time": processing_time,
                    "timeout_duration": self.timeout
                }
            )
            
        except httpx.HTTPStatusError as e:
            processing_time = time.time() - start_time
            self._update_metrics(model, processing_time, {}, 0.0, False)
            self.circuit_breaker.record_failure()
            
            # Handle specific HTTP status codes
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Invalid GROQ API key",
                    details={"model": model.value, "status_code": e.response.status_code}
                )
            elif e.response.status_code == 429:
                raise RateLimitError(
                    "GROQ API rate limit exceeded",
                    details={"model": model.value, "status_code": e.response.status_code}
                )
            elif e.response.status_code >= 500:
                raise ExternalServiceError(
                    f"GROQ API server error: {e.response.status_code}",
                    service_name="groq",
                    status_code=e.response.status_code,
                    details={"model": model.value, "request_id": request_id}
                )
            else:
                raise ExternalServiceError(
                    f"GROQ API error: {e.response.status_code}",
                    service_name="groq",
                    status_code=e.response.status_code,
                    details={"model": model.value, "request_id": request_id}
                )
            
        except (ValidationError, AuthenticationError, RateLimitError, NetworkError, ExternalServiceError):
            # Re-raise known application errors
            processing_time = time.time() - start_time
            self._update_metrics(model, processing_time, {}, 0.0, False)
            self.circuit_breaker.record_failure()
            raise
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_metrics(model, processing_time, {}, 0.0, False)
            self.circuit_breaker.record_failure()
            
            # Check if it's a model deprecation error and try fallback
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ["decommissioned", "no longer supported", "deprecated", "not found"]):
                logger.warning(f"Model {model.value} appears to be deprecated: {str(e)}")
                
                # Disable the deprecated model
                if model in self.model_configs:
                    self.model_configs[model].enabled = False
                
                # Try with a fallback model (llama-3.1-8b-instant is most reliable)
                fallback_model = GROQModel.LLAMA3_1_8B
                if fallback_model != model and self.model_configs[fallback_model].enabled:
                    logger.info(f"Retrying with fallback model: {fallback_model.value}")
                    return await self.generate_completion(
                        messages, 
                        model=fallback_model,
                        task_type=task_type,
                        priority=priority,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                else:
                    raise ExternalServiceError(
                        f"Model {model.value} is deprecated and no fallback available",
                        service_name="groq",
                        details={"deprecated_model": model.value, "error": str(e)}
                    )
            
            # Handle unexpected errors
            error_context = error_handler.handle_error(
                error=e,
                category=ErrorCategory.EXTERNAL_SERVICE,
                severity=ErrorSeverity.HIGH,
                user_message="GROQ API request failed unexpectedly",
                technical_details={
                    "model": model.value,
                    "request_id": request_id,
                    "processing_time": processing_time,
                    "error_type": type(e).__name__
                }
            )
            
            raise ExternalServiceError(
                f"Unexpected GROQ API error: {str(e)}",
                service_name="groq",
                details={
                    "model": model.value,
                    "request_id": request_id,
                    "error_id": error_context.error_id
                },
                cause=e
            )
    
    async def _make_api_request(self, request_data: GROQRequest, request_id: str) -> GROQResponse:
        """Make API request to GROQ."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Request-ID": request_id
        }
        
        payload = {
            "model": request_data.model,
            "messages": request_data.messages,
            "temperature": request_data.temperature,
            "max_tokens": request_data.max_tokens,
            "top_p": request_data.top_p,
            "stream": request_data.stream,
            "frequency_penalty": request_data.frequency_penalty,
            "presence_penalty": request_data.presence_penalty
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        if request_data.stop:
            payload["stop"] = request_data.stop
        if request_data.user:
            payload["user"] = request_data.user
        
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers
        )
        
        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("error", {}).get("message", error_detail)
            except:
                pass
            
            # Handle specific error types
            if response.status_code == 429:
                raise RuntimeError(f"GROQ rate limit exceeded: {error_detail}")
            elif response.status_code == 400 and ("decommissioned" in error_detail or "no longer supported" in error_detail):
                raise RuntimeError(f"GROQ model deprecated: {error_detail}")
            else:
                raise RuntimeError(f"GROQ API error {response.status_code}: {error_detail}")
        
        data = response.json()
        return GROQResponse(**data)
    
    def _calculate_confidence_score(self, content: str, model_config: GROQModelConfig) -> float:
        """Calculate confidence score based on response and model characteristics."""
        base_confidence = model_config.quality_score
        
        # Adjust based on response characteristics
        if len(content) > 500:
            base_confidence += 0.05
        
        if content.count('\n') > 3:  # Well-structured response
            base_confidence += 0.03
        
        # Check for reasoning indicators
        reasoning_indicators = ["because", "therefore", "analysis", "conclusion", "evidence"]
        if any(indicator in content.lower() for indicator in reasoning_indicators):
            base_confidence += 0.02
        
        return min(base_confidence, 1.0)
    
    def _update_metrics(
        self, 
        model: GROQModel, 
        processing_time: float, 
        usage: Dict[str, int], 
        cost: float, 
        success: bool
    ):
        """Update service metrics."""
        self.metrics.total_requests += 1
        self.metrics.last_request_time = datetime.now()
        
        if success:
            self.metrics.successful_requests += 1
            total_tokens = usage.get("total_tokens", 0)
            self.metrics.total_tokens_used += total_tokens
            self.metrics.total_cost += cost
            
            # Update averages
            self.metrics.avg_response_time = (
                (self.metrics.avg_response_time * (self.metrics.successful_requests - 1) + 
                 processing_time) / self.metrics.successful_requests
            )
            
            if self.metrics.successful_requests > 0:
                self.metrics.avg_tokens_per_request = (
                    self.metrics.total_tokens_used / self.metrics.successful_requests
                )
                self.metrics.avg_cost_per_request = (
                    self.metrics.total_cost / self.metrics.successful_requests
                )
            
            # Track model usage
            model_name = model.value
            self.metrics.model_usage[model_name] = self.metrics.model_usage.get(model_name, 0) + 1
            
        else:
            self.metrics.failed_requests += 1
        
        # Calculate error rate
        if self.metrics.total_requests > 0:
            self.metrics.error_rate = self.metrics.failed_requests / self.metrics.total_requests
            self.metrics.uptime_percentage = (
                self.metrics.successful_requests / self.metrics.total_requests * 100
            )
    
    def _track_performance(self, model: str, task_type: str, processing_time: float):
        """Track performance by model and task type."""
        key = f"{model}:{task_type}"
        
        if key not in self.performance_history:
            self.performance_history[key] = []
        
        self.performance_history[key].append(processing_time)
        
        # Keep only last 100 measurements
        if len(self.performance_history[key]) > 100:
            self.performance_history[key] = self.performance_history[key][-100:]
        
        # Update task performance metrics
        self.metrics.task_performance[key] = sum(self.performance_history[key]) / len(self.performance_history[key])
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for GROQ service."""
        health_status = {
            "service": "groq",
            "status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "api_key_configured": bool(self.api_key),
            "circuit_breaker_state": self.circuit_breaker.state,
            "models": {},
            "metrics": self.get_metrics_summary(),
            "errors": []
        }
        
        try:
            # Test API connectivity
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await self.client.get(f"{self.base_url}/models", headers=headers)
            
            if response.status_code == 200:
                health_status["status"] = "healthy"
                
                # Check individual models
                available_models = response.json().get("data", [])
                model_ids = [model["id"] for model in available_models]
                
                for groq_model in self.model_configs:
                    model_name = groq_model.value
                    health_status["models"][model_name] = {
                        "available": model_name in model_ids,
                        "enabled": self.model_configs[groq_model].enabled,
                        "rate_limiter_status": "ok"
                    }
            else:
                health_status["status"] = "unhealthy"
                health_status["errors"].append(f"API returned status {response.status_code}")
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["errors"].append(str(e))
        
        return health_status
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "error_rate": round(self.metrics.error_rate, 4),
            "uptime_percentage": round(self.metrics.uptime_percentage, 2),
            "total_tokens_used": self.metrics.total_tokens_used,
            "total_cost": round(self.metrics.total_cost, 6),
            "avg_response_time": round(self.metrics.avg_response_time, 3),
            "avg_tokens_per_request": round(self.metrics.avg_tokens_per_request, 1),
            "avg_cost_per_request": round(self.metrics.avg_cost_per_request, 6),
            "rate_limit_hits": self.metrics.rate_limit_hits,
            "model_usage": self.metrics.model_usage,
            "task_performance": {
                k: round(v, 3) for k, v in self.metrics.task_performance.items()
            },
            "last_request_time": self.metrics.last_request_time.isoformat() if self.metrics.last_request_time else None
        }
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get detailed cost analysis."""
        cost_by_model = {}
        
        for model_name, usage_count in self.metrics.model_usage.items():
            model_enum = next((m for m in GROQModel if m.value == model_name), None)
            if model_enum and model_enum in self.model_configs:
                config = self.model_configs[model_enum]
                estimated_cost = usage_count * self.metrics.avg_tokens_per_request * config.cost_per_token
                cost_by_model[model_name] = {
                    "usage_count": usage_count,
                    "cost_per_token": config.cost_per_token,
                    "estimated_cost": round(estimated_cost, 6)
                }
        
        return {
            "total_cost": round(self.metrics.total_cost, 6),
            "cost_by_model": cost_by_model,
            "avg_cost_per_request": round(self.metrics.avg_cost_per_request, 6),
            "cost_efficiency": round(self.metrics.total_cost / max(self.metrics.total_tokens_used, 1) * 1000, 6)  # Cost per 1K tokens
        }
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """Get detailed performance analysis."""
        performance_by_model = {}
        
        for key, times in self.performance_history.items():
            if times:
                model, task = key.split(":", 1)
                if model not in performance_by_model:
                    performance_by_model[model] = {}
                
                performance_by_model[model][task] = {
                    "avg_time": round(sum(times) / len(times), 3),
                    "min_time": round(min(times), 3),
                    "max_time": round(max(times), 3),
                    "sample_count": len(times)
                }
        
        return {
            "overall_avg_response_time": round(self.metrics.avg_response_time, 3),
            "performance_by_model": performance_by_model,
            "fastest_model": min(
                self.metrics.task_performance.items(),
                key=lambda x: x[1],
                default=("none", 0)
            )[0].split(":")[0] if self.metrics.task_performance else "none"
        }
    
    async def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = GROQMetrics()
        self.performance_history.clear()
        self.cost_tracking.clear()
        logger.info("GROQ service metrics reset")
    
    async def close(self):
        """Close the service and cleanup resources."""
        await self.client.aclose()
        logger.info("GROQ service closed")


# Global instance
_groq_service = None


def get_groq_service() -> GROQService:
    """Get global GROQ service instance."""
    global _groq_service
    if _groq_service is None:
        _groq_service = GROQService()
    return _groq_service