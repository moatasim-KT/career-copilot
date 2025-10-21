"""
Enhanced Multi-Provider LLM Manager
Provides intelligent routing, fallback mechanisms, and comprehensive monitoring
for multiple LLM providers including OpenAI, GROQ, and Ollama.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple
from uuid import uuid4

import httpx
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.caching import get_cache_manager
from ..monitoring.metrics_collector import get_metrics_collector
from .openai_service import get_enhanced_openai_service
from .ollama_service import get_enhanced_ollama_service
from .llm_error_handler import get_llm_error_handler, with_llm_error_handling
from .llm_cache_manager import get_llm_cache_manager
from .llm_benchmarking import get_benchmark_runner

logger = get_logger(__name__)
settings = get_settings()
cache_manager = get_cache_manager()
metrics_collector = get_metrics_collector()


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GROQ = "groq"
    OLLAMA = "ollama"


class TaskType(str, Enum):
    """Types of tasks for intelligent routing."""
    CONTRACT_ANALYSIS = "contract_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    LEGAL_PRECEDENT = "legal_precedent"
    NEGOTIATION = "negotiation"
    COMMUNICATION = "communication"
    GENERAL = "general"


class RoutingCriteria(str, Enum):
    """Criteria for provider selection."""
    COST = "cost"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SPEED = "speed"
    AVAILABILITY = "availability"


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4000
    cost_per_token: float = 0.0
    rate_limit_rpm: int = 60
    rate_limit_tpm: int = 40000
    timeout: int = 60
    priority: int = 1  # Lower number = higher priority
    capabilities: List[str] = field(default_factory=list)
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Standardized response from LLM providers."""
    content: str
    provider: LLMProvider
    model: str
    confidence_score: float
    processing_time: float
    token_usage: Dict[str, int]
    cost: float
    request_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderMetrics:
    """Metrics for provider performance monitoring."""
    provider: LLMProvider
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    avg_cost_per_request: float = 0.0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    last_request_time: Optional[datetime] = None
    error_rate: float = 0.0
    availability: float = 1.0
    health_score: float = 1.0


@dataclass
class CircuitBreakerState:
    """Circuit breaker state for provider reliability."""
    state: str = "closed"  # closed, open, half-open
    failure_count: int = 0
    failure_threshold: int = 5
    timeout_duration: int = 60
    last_failure_time: Optional[datetime] = None
    next_attempt_time: Optional[datetime] = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.circuit_breaker = CircuitBreakerState()
        self.metrics = ProviderMetrics(provider=config.provider)
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.rate_limit_rpm,
            tokens_per_minute=config.rate_limit_tpm
        )
    
    @abstractmethod
    async def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> LLMResponse:
        """Generate completion from the provider."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        pass
    
    async def is_available(self) -> bool:
        """Check if provider is available considering circuit breaker."""
        if self.circuit_breaker.state == "open":
            if (self.circuit_breaker.next_attempt_time and 
                datetime.now() >= self.circuit_breaker.next_attempt_time):
                self.circuit_breaker.state = "half-open"
                return True
            return False
        return True
    
    def record_success(self):
        """Record successful request."""
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.state = "closed"
        self.metrics.successful_requests += 1
    
    def record_failure(self):
        """Record failed request."""
        self.circuit_breaker.failure_count += 1
        self.circuit_breaker.last_failure_time = datetime.now()
        self.metrics.failed_requests += 1
        
        if self.circuit_breaker.failure_count >= self.circuit_breaker.failure_threshold:
            self.circuit_breaker.state = "open"
            self.circuit_breaker.next_attempt_time = (
                datetime.now() + timedelta(seconds=self.circuit_breaker.timeout_duration)
            )


class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int, tokens_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.request_times: List[datetime] = []
        self.token_usage: List[tuple] = []  # (timestamp, tokens)
    
    async def acquire(self, estimated_tokens: int = 0) -> bool:
        """Acquire rate limit permission."""
        now = datetime.now()
        
        # Clean old entries
        cutoff = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]
        self.token_usage = [(t, tokens) for t, tokens in self.token_usage if t > cutoff]
        
        # Check request rate limit
        if len(self.request_times) >= self.requests_per_minute:
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


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client."""
        try:
            self.client = ChatOpenAI(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                api_key=self.config.api_key or settings.openai_api_key.get_secret_value(),
                timeout=self.config.timeout
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.config.enabled = False
    
    async def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> LLMResponse:
        """Generate completion using OpenAI."""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        request_id = str(uuid4())
        start_time = time.time()
        
        try:
            # Convert messages to LangChain format
            lc_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    lc_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    lc_messages.append(HumanMessage(content=msg["content"]))
            
            # Generate response
            response = await self.client.ainvoke(lc_messages)
            processing_time = time.time() - start_time
            
            # Extract token usage
            token_usage = self._extract_token_usage(response)
            cost = token_usage.get("total_tokens", 0) * self.config.cost_per_token
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(response.content, messages)
            
            llm_response = LLMResponse(
                content=response.content,
                provider=self.config.provider,
                model=self.config.model_name,
                confidence_score=confidence_score,
                processing_time=processing_time,
                token_usage=token_usage,
                cost=cost,
                request_id=request_id,
                timestamp=datetime.now(),
                metadata={
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "finish_reason": getattr(response, "finish_reason", None)
                }
            )
            
            self.record_success()
            self._update_metrics(llm_response)
            
            return llm_response
            
        except Exception as e:
            self.record_failure()
            logger.error(f"OpenAI completion failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check OpenAI health."""
        try:
            if not self.client:
                return False
            
            # Simple health check with minimal request
            messages = [HumanMessage(content="Hello")]
            await self.client.ainvoke(messages)
            return True
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
    
    def _extract_token_usage(self, response) -> Dict[str, int]:
        """Extract token usage from OpenAI response."""
        if hasattr(response, 'response_metadata'):
            usage = response.response_metadata.get('token_usage', {})
            return {
                "prompt_tokens": usage.get('prompt_tokens', 0),
                "completion_tokens": usage.get('completion_tokens', 0),
                "total_tokens": usage.get('total_tokens', 0)
            }
        
        # Fallback estimation
        estimated_tokens = len(response.content.split()) * 1.3
        return {
            "prompt_tokens": 0,
            "completion_tokens": int(estimated_tokens),
            "total_tokens": int(estimated_tokens)
        }
    
    def _calculate_confidence(self, content: str, messages: List[Dict[str, str]]) -> float:
        """Calculate confidence score for OpenAI response."""
        base_confidence = 0.85 if "gpt-4" in self.config.model_name else 0.75
        
        # Adjust based on response characteristics
        if len(content) > 500:
            base_confidence += 0.05
        if any(word in content.lower() for word in ["analysis", "recommendation", "conclusion"]):
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _update_metrics(self, response: LLMResponse):
        """Update provider metrics."""
        self.metrics.total_requests += 1
        self.metrics.avg_response_time = (
            (self.metrics.avg_response_time * (self.metrics.total_requests - 1) + 
             response.processing_time) / self.metrics.total_requests
        )
        self.metrics.total_tokens_used += response.token_usage.get("total_tokens", 0)
        self.metrics.total_cost += response.cost
        self.metrics.avg_cost_per_request = self.metrics.total_cost / self.metrics.total_requests
        self.metrics.last_request_time = response.timestamp
        
        # Calculate error rate
        if self.metrics.total_requests > 0:
            self.metrics.error_rate = self.metrics.failed_requests / self.metrics.total_requests


class GROQProvider(BaseLLMProvider):
    """Enhanced GROQ provider implementation using the dedicated GROQ service."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Import here to avoid circular imports
        from .groq_service import get_groq_service, GROQTaskType
        from .groq_optimizer import get_groq_optimizer
        from .groq_monitor import get_groq_monitor
        
        self.groq_service = get_groq_service()
        self.groq_optimizer = get_groq_optimizer()
        self.groq_monitor = get_groq_monitor()
        self.GROQTaskType = GROQTaskType
    
    async def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> LLMResponse:
        """Generate completion using enhanced GROQ service."""
        request_id = str(uuid4())
        start_time = time.time()
        
        try:
            # Determine task type from context
            task_type = self._determine_task_type(messages)
            
            # Use optimized completion if available
            if hasattr(self.groq_optimizer, 'optimized_completion'):
                result = await self.groq_optimizer.optimized_completion(
                    messages=messages,
                    task_type=task_type,
                    priority="balanced",
                    **kwargs
                )
            else:
                # Fallback to direct service
                result = await self.groq_service.generate_completion(
                    messages=messages,
                    task_type=task_type,
                    **kwargs
                )
            
            processing_time = time.time() - start_time
            
            # Convert to LLMResponse format
            llm_response = LLMResponse(
                content=result["content"],
                provider=self.config.provider,
                model=result["model"],
                confidence_score=result.get("confidence_score", 0.8),
                processing_time=processing_time,
                token_usage=result.get("usage", {}),
                cost=result.get("cost", 0.0),
                request_id=request_id,
                timestamp=datetime.now(),
                metadata=result.get("metadata", {})
            )
            
            self.record_success()
            self._update_metrics(llm_response)
            
            return llm_response
            
        except Exception as e:
            self.record_failure()
            logger.error(f"Enhanced GROQ completion failed: {e}")
            raise
    
    def _determine_task_type(self, messages: List[Dict[str, str]]):
        """Determine GROQ task type from message content."""
        content = " ".join(msg.get("content", "") for msg in messages).lower()
        
        if any(word in content for word in ["analyze", "analysis", "contract", "legal"]):
            return self.GROQTaskType.FAST_ANALYSIS
        elif any(word in content for word in ["code", "programming", "function", "class"]):
            return self.GROQTaskType.CODE_GENERATION
        elif any(word in content for word in ["reason", "logic", "because", "therefore"]):
            return self.GROQTaskType.REASONING
        elif any(word in content for word in ["summarize", "summary", "brief"]):
            return self.GROQTaskType.SUMMARIZATION
        elif any(word in content for word in ["translate", "translation"]):
            return self.GROQTaskType.TRANSLATION
        elif any(word in content for word in ["classify", "category", "type"]):
            return self.GROQTaskType.CLASSIFICATION
        else:
            return self.GROQTaskType.CONVERSATION
    
    async def health_check(self) -> bool:
        """Check GROQ health using enhanced service."""
        try:
            health_status = await self.groq_service.health_check()
            return health_status.get("status") == "healthy"
        except Exception as e:
            logger.warning(f"Enhanced GROQ health check failed: {e}")
            return False
    
    def _calculate_confidence(self, content: str, messages: List[Dict[str, str]]) -> float:
        """Calculate confidence score for GROQ response."""
        # Use enhanced confidence calculation from GROQ service
        base_confidence = 0.80
        
        # Adjust based on response characteristics
        if len(content) > 300:
            base_confidence += 0.05
        if content.count('\n') > 3:  # Well-structured response
            base_confidence += 0.05
        
        # Check for reasoning indicators
        reasoning_indicators = ["because", "therefore", "analysis", "conclusion", "evidence"]
        if any(indicator in content.lower() for indicator in reasoning_indicators):
            base_confidence += 0.02
        
        return min(base_confidence, 1.0)
    
    def _update_metrics(self, response: LLMResponse):
        """Update provider metrics."""
        self.metrics.total_requests += 1
        self.metrics.avg_response_time = (
            (self.metrics.avg_response_time * (self.metrics.total_requests - 1) + 
             response.processing_time) / self.metrics.total_requests
        )
        self.metrics.total_tokens_used += response.token_usage.get("total_tokens", 0)
        self.metrics.total_cost += response.cost
        self.metrics.avg_cost_per_request = self.metrics.total_cost / self.metrics.total_requests
        self.metrics.last_request_time = response.timestamp
        
        if self.metrics.total_requests > 0:
            self.metrics.error_rate = self.metrics.failed_requests / self.metrics.total_requests


class OllamaProvider(BaseLLMProvider):
    """Ollama provider implementation."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
    
    async def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> LLMResponse:
        """Generate completion using Ollama."""
        request_id = str(uuid4())
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                payload = {
                    "model": self.config.model_name,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                
                if response.status_code != 200:
                    raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")
                
                data = response.json()
                processing_time = time.time() - start_time
                
                content = data["message"]["content"]
                
                # Estimate token usage for Ollama
                estimated_tokens = len(content.split()) * 1.3
                token_usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": int(estimated_tokens),
                    "total_tokens": int(estimated_tokens)
                }
                
                confidence_score = self._calculate_confidence(content, messages)
                
                llm_response = LLMResponse(
                    content=content,
                    provider=self.config.provider,
                    model=self.config.model_name,
                    confidence_score=confidence_score,
                    processing_time=processing_time,
                    token_usage=token_usage,
                    cost=0.0,  # Ollama is free
                    request_id=request_id,
                    timestamp=datetime.now(),
                    metadata={
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "total_duration": data.get("total_duration", 0),
                        "load_duration": data.get("load_duration", 0),
                        "eval_duration": data.get("eval_duration", 0)
                    }
                )
                
                self.record_success()
                self._update_metrics(llm_response)
                
                return llm_response
                
        except Exception as e:
            self.record_failure()
            logger.error(f"Ollama completion failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check Ollama health."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    def _calculate_confidence(self, content: str, messages: List[Dict[str, str]]) -> float:
        """Calculate confidence score for Ollama response."""
        # Ollama confidence varies by model
        base_confidence = 0.70
        
        # Adjust based on model type
        if "llama" in self.config.model_name.lower():
            base_confidence = 0.75
        elif "mistral" in self.config.model_name.lower():
            base_confidence = 0.72
        
        # Adjust based on response quality
        if len(content) > 200:
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _update_metrics(self, response: LLMResponse):
        """Update provider metrics."""
        self.metrics.total_requests += 1
        self.metrics.avg_response_time = (
            (self.metrics.avg_response_time * (self.metrics.total_requests - 1) + 
             response.processing_time) / self.metrics.total_requests
        )
        self.metrics.total_tokens_used += response.token_usage.get("total_tokens", 0)
        self.metrics.total_cost += response.cost
        self.metrics.avg_cost_per_request = self.metrics.total_cost / max(self.metrics.total_requests, 1)
        self.metrics.last_request_time = response.timestamp
        
        if self.metrics.total_requests > 0:
            self.metrics.error_rate = self.metrics.failed_requests / self.metrics.total_requests


class EnhancedLLMManager:
    """Enhanced multi-provider LLM manager with intelligent routing and monitoring."""
    
    def __init__(self, config_manager=None):
        """Initialize the LLM manager."""
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.task_routing: Dict[TaskType, List[str]] = {}
        self.cache_ttl = 3600  # 1 hour
        self.config_manager = config_manager
        
        # Enhanced services
        self.enhanced_openai = get_enhanced_openai_service()
        self.enhanced_ollama = get_enhanced_ollama_service()
        self.error_handler = get_llm_error_handler()
        self.cache_manager = get_llm_cache_manager()
        self.benchmark_runner = get_benchmark_runner()
        
        self._initialize_providers()
        self._setup_task_routing()
    
    def _initialize_providers(self):
        """Initialize all configured providers."""
        try:
            # Use configuration manager if available
            if self.config_manager:
                provider_configs = self.config_manager.get_provider_configs()
                
                for provider_id, config in provider_configs.items():
                    if not config.enabled:
                        continue
                    
                    try:
                        if config.provider == LLMProvider.OPENAI:
                            self.providers[provider_id] = OpenAIProvider(config)
                        elif config.provider == LLMProvider.GROQ:
                            self.providers[provider_id] = GROQProvider(config)
                        elif config.provider == LLMProvider.OLLAMA:
                            self.providers[provider_id] = OllamaProvider(config)
                        
                        logger.info(f"Initialized provider: {provider_id}")
                    except Exception as e:
                        logger.error(f"Failed to initialize provider {provider_id}: {e}")
                
                logger.info(f"Initialized {len(self.providers)} LLM providers from configuration")
                return
        
        except Exception as e:
            logger.warning(f"Failed to use configuration manager: {e}")
        
        # Fallback to default initialization
        self._initialize_default_providers()
    
    def _initialize_default_providers(self):
        """Initialize providers with default configuration."""
        # OpenAI providers
        if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
            # GPT-4 for high-quality analysis
            gpt4_config = ProviderConfig(
                provider=LLMProvider.OPENAI,
                model_name="gpt-4",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.00003,
                rate_limit_rpm=60,
                rate_limit_tpm=40000,
                priority=1,
                capabilities=["analysis", "reasoning", "complex_tasks"],
                metadata={"quality": "high", "speed": "medium"}
            )
            self.providers["openai-gpt4"] = OpenAIProvider(gpt4_config)
            
            # GPT-3.5 for faster, cost-effective tasks
            gpt35_config = ProviderConfig(
                provider=LLMProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.000002,
                rate_limit_rpm=3500,
                rate_limit_tpm=90000,
                priority=2,
                capabilities=["generation", "communication", "simple_analysis"],
                metadata={"quality": "medium", "speed": "fast"}
            )
            self.providers["openai-gpt35"] = OpenAIProvider(gpt35_config)
        
        # GROQ providers
        groq_api_key = getattr(settings, 'groq_api_key', None)
        if groq_api_key:
            api_key_value = groq_api_key
            if hasattr(groq_api_key, 'get_secret_value'):
                api_key_value = groq_api_key.get_secret_value()
            
            # Mixtral for fast analysis
            mixtral_config = ProviderConfig(
                provider=LLMProvider.GROQ,
                model_name="llama3-8b-8192",
                api_key=api_key_value,
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.00000027,
                rate_limit_rpm=30,
                rate_limit_tpm=6000,
                priority=1,
                capabilities=["fast_analysis", "reasoning", "generation"],
                metadata={"quality": "high", "speed": "very_fast"}
            )
            self.providers["groq-mixtral"] = GROQProvider(mixtral_config)
            
            # Llama2 for general tasks
            llama_config = ProviderConfig(
                provider=LLMProvider.GROQ,
                model_name="llama2-70b-4096",
                api_key=api_key_value,
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.00000070,
                rate_limit_rpm=30,
                rate_limit_tpm=6000,
                priority=2,
                capabilities=["generation", "communication", "simple_analysis"],
                metadata={"quality": "medium", "speed": "fast"}
            )
            self.providers["groq-llama2"] = GROQProvider(llama_config)
        
        # Ollama providers
        ollama_enabled = getattr(settings, 'ollama_enabled', False)
        if ollama_enabled:
            ollama_model = getattr(settings, 'ollama_model', 'llama2')
            ollama_config = ProviderConfig(
                provider=LLMProvider.OLLAMA,
                model_name=ollama_model,
                base_url=getattr(settings, 'ollama_base_url', 'http://localhost:11434'),
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.0,  # Free
                rate_limit_rpm=60,
                rate_limit_tpm=10000,
                priority=3,
                capabilities=["local_processing", "privacy", "generation"],
                metadata={"quality": "medium", "speed": "medium", "cost": "free"}
            )
            self.providers["ollama-local"] = OllamaProvider(ollama_config)
        
        logger.info(f"Initialized {len(self.providers)} LLM providers with default configuration")
    
    async def get_completion_with_enhanced_features(
        self,
        messages: List[Dict[str, str]],
        task_type: TaskType = TaskType.GENERAL,
        preferred_provider: Optional[str] = None,
        use_cache: bool = True,
        use_fallback: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Get completion with all enhanced features (caching, error handling, fallback)."""
        try:
            # Check cache first
            if use_cache:
                cached_response = await self.cache_manager.get_cached_response(
                    messages, kwargs.get("model", ""), **kwargs
                )
                if cached_response:
                    return cached_response
            
            # Get best provider for task
            provider_id = self._select_best_provider(task_type, preferred_provider)
            
            if not provider_id:
                raise RuntimeError("No available providers for task")
            
            # Use enhanced services with error handling
            if "openai" in provider_id:
                response = await self._call_enhanced_openai(messages, **kwargs)
            elif "ollama" in provider_id:
                response = await self._call_enhanced_ollama(messages, task_type, **kwargs)
            elif "groq" in provider_id and provider_id in self.providers:
                response = await self._call_groq_provider(provider_id, messages, **kwargs)
            else:
                # Fallback to standard provider
                response = await self._call_standard_provider(provider_id, messages, **kwargs)
            
            # Cache the response
            if use_cache and response.get("success", True):
                await self.cache_manager.cache_response(
                    messages, response.get("model", ""), response, **kwargs
                )
            
            return response
            
        except Exception as e:
            # Handle error with fallback if enabled
            if use_fallback:
                return await self._handle_error_with_fallback(
                    e, messages, task_type, preferred_provider, **kwargs
                )
            else:
                raise
    
    async def _call_enhanced_openai(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Call enhanced OpenAI service."""
        return await self.enhanced_openai.generate_completion(messages, **kwargs)
    
    async def _call_enhanced_ollama(
        self, 
        messages: List[Dict[str, str]], 
        task_type: TaskType, 
        **kwargs
    ) -> Dict[str, Any]:
        """Call enhanced Ollama service."""
        # Map task type to Ollama task type
        ollama_task_map = {
            TaskType.CONTRACT_ANALYSIS: "analysis",
            TaskType.RISK_ASSESSMENT: "analysis", 
            TaskType.LEGAL_PRECEDENT: "analysis",
            TaskType.NEGOTIATION: "generation",
            TaskType.COMMUNICATION: "generation",
            TaskType.GENERAL: "generation"
        }
        
        ollama_task = ollama_task_map.get(task_type, "generation")
        
        return await self.enhanced_ollama.generate_completion(
            messages, task_type=ollama_task, **kwargs
        )
    
    async def _call_groq_provider(
        self, 
        provider_id: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Call GROQ provider with enhanced error handling."""
        provider = self.providers[provider_id]
        return await provider.generate_completion(messages, **kwargs)
    
    async def _call_standard_provider(
        self, 
        provider_id: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Call standard provider with enhanced error handling."""
        provider = self.providers[provider_id]
        return await provider.generate_completion(messages, **kwargs)
    
    async def _handle_error_with_fallback(
        self,
        error: Exception,
        messages: List[Dict[str, str]],
        task_type: TaskType,
        failed_provider: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Handle error with fallback to alternative providers."""
        # Get fallback provider
        fallback_provider = self.error_handler.get_fallback_provider(
            failed_provider or "unknown", 
            [failed_provider] if failed_provider else []
        )
        
        if fallback_provider:
            logger.info(f"Falling back to provider: {fallback_provider}")
            return await self.get_completion_with_enhanced_features(
                messages, task_type, fallback_provider, use_fallback=False, **kwargs
            )
        else:
            # No fallback available, raise original error
            raise error
    
    def _select_best_provider(self, task_type: TaskType, preferred_provider: Optional[str] = None) -> Optional[str]:
        """Select the best provider for a task type."""
        if preferred_provider and preferred_provider in self.providers:
            provider = self.providers[preferred_provider]
            if provider.is_available():
                return preferred_provider
        
        # Get providers for task type
        task_providers = self.task_routing.get(task_type, [])
        
        # Find first available provider
        for provider_id in task_providers:
            if provider_id in self.providers:
                provider = self.providers[provider_id]
                if provider.is_available():
                    return provider_id
        
        # Fallback to any available provider
        for provider_id, provider in self.providers.items():
            if provider.is_available():
                return provider_id
        
        return None
    
    async def run_benchmark(
        self,
        provider_name: str,
        model: str,
        test_suite: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run benchmark tests against a provider."""
        # Create provider function for benchmarking
        async def provider_func(messages, **kwargs):
            return await self.get_completion_with_enhanced_features(
                messages, 
                preferred_provider=f"{provider_name}-{model}",
                use_cache=False,  # Don't use cache for benchmarking
                **kwargs
            )
        
        # Run benchmark
        benchmark_result = await self.benchmark_runner.run_benchmark(
            provider_func, provider_name, model, test_suite
        )
        
        return {
            "provider": benchmark_result.provider,
            "model": benchmark_result.model,
            "overall_score": benchmark_result.overall_score,
            "successful_tests": benchmark_result.successful_tests,
            "total_tests": benchmark_result.total_tests,
            "avg_response_time": benchmark_result.avg_response_time,
            "avg_quality_score": benchmark_result.avg_quality_score,
            "total_cost": benchmark_result.total_cost,
            "timestamp": benchmark_result.timestamp.isoformat()
        }
    
    async def compare_providers(self, providers: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Compare multiple providers using benchmarks."""
        benchmarks = []
        
        for provider_name, model in providers:
            try:
                benchmark_result = await self.run_benchmark(provider_name, model)
                benchmarks.append(benchmark_result)
            except Exception as e:
                logger.error(f"Benchmark failed for {provider_name}:{model}: {e}")
        
        if len(benchmarks) < 2:
            raise ValueError("Need at least 2 successful benchmarks to compare")
        
        return self.benchmark_runner.compare_providers(benchmarks)
    
    def get_enhanced_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics from all enhanced services."""
        metrics = {
            "llm_manager": {
                "total_providers": len(self.providers),
                "available_providers": len([p for p in self.providers.values() if p.is_available()]),
                "task_routing": {task.value: providers for task, providers in self.task_routing.items()}
            },
            "cache": self.cache_manager.get_cache_statistics(),
            "error_handler": self.error_handler.get_error_statistics(),
            "enhanced_services": {}
        }
        
        # Add enhanced service metrics
        try:
            metrics["enhanced_services"]["openai"] = self.enhanced_openai.get_metrics()
        except Exception as e:
            logger.warning(f"Failed to get OpenAI metrics: {e}")
        
        try:
            metrics["enhanced_services"]["ollama"] = self.enhanced_ollama.get_metrics()
        except Exception as e:
            logger.warning(f"Failed to get Ollama metrics: {e}")
        
        return metrics
    
    async def health_check_all_enhanced(self) -> Dict[str, Any]:
        """Perform health checks on all enhanced services."""
        health_results = {}
        
        # Check enhanced OpenAI
        try:
            health_results["openai"] = await self.enhanced_openai.health_check()
        except Exception as e:
            health_results["openai"] = {"status": "error", "error": str(e)}
        
        # Check enhanced Ollama
        try:
            health_results["ollama"] = await self.enhanced_ollama.health_check()
        except Exception as e:
            health_results["ollama"] = {"status": "error", "error": str(e)}
        
        # Check standard providers
        for provider_id, provider in self.providers.items():
            try:
                health_results[provider_id] = await provider.health_check()
            except Exception as e:
                health_results[provider_id] = {"status": "error", "error": str(e)}
        
        return health_results
    
    async def clear_all_caches(self) -> Dict[str, bool]:
        """Clear all caches."""
        results = {}
        
        # Clear LLM cache manager
        try:
            await self.cache_manager.invalidate_cache()
            results["llm_cache"] = True
        except Exception as e:
            logger.error(f"Failed to clear LLM cache: {e}")
            results["llm_cache"] = False
        
        # Clear enhanced service caches
        try:
            await self.enhanced_openai.clear_cache()
            results["openai_cache"] = True
        except Exception as e:
            logger.error(f"Failed to clear OpenAI cache: {e}")
            results["openai_cache"] = False
        
        try:
            await self.enhanced_ollama.clear_cache()
            results["ollama_cache"] = True
        except Exception as e:
            logger.error(f"Failed to clear Ollama cache: {e}")
            results["ollama_cache"] = False
        
        return results
    
    def _setup_task_routing(self):
        """Setup intelligent task routing based on provider capabilities."""
        try:
            # Use configuration manager if available
            if self.config_manager:
                config = self.config_manager.get_config()
                self.task_routing = config.task_routing
                self.cache_ttl = config.cache_ttl
                logger.info("Loaded task routing from configuration")
                return
        except Exception as e:
            logger.warning(f"Failed to load task routing from configuration: {e}")
        
        # Fallback to default routing
        self.task_routing = {
            TaskType.CONTRACT_ANALYSIS: [
                "openai-gpt4", "groq-mixtral", "openai-gpt35", "ollama-local"
            ],
            TaskType.RISK_ASSESSMENT: [
                "openai-gpt4", "groq-mixtral", "openai-gpt35", "ollama-local"
            ],
            TaskType.LEGAL_PRECEDENT: [
                "openai-gpt4", "groq-mixtral", "openai-gpt35", "ollama-local"
            ],
            TaskType.NEGOTIATION: [
                "openai-gpt35", "groq-llama2", "openai-gpt4", "ollama-local"
            ],
            TaskType.COMMUNICATION: [
                "openai-gpt35", "groq-llama2", "ollama-local", "openai-gpt4"
            ],
            TaskType.GENERAL: [
                "openai-gpt35", "groq-llama2", "ollama-local", "openai-gpt4"
            ]
        }
    
    async def get_completion(
        self,
        prompt: str,
        task_type: TaskType = TaskType.GENERAL,
        routing_criteria: RoutingCriteria = RoutingCriteria.COST,
        preferred_provider: Optional[str] = None,
        fallback_enabled: bool = True,
        max_retries: int = 3,
        **kwargs
    ) -> LLMResponse:
        """
        Get completion with intelligent provider selection and fallback.
        
        Args:
            prompt: Input prompt
            task_type: Type of task for routing
            routing_criteria: Criteria for provider selection
            preferred_provider: Preferred provider ID
            fallback_enabled: Enable fallback to other providers
            max_retries: Maximum retry attempts
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with completion
        """
        # Check cache first
        cache_key = f"llm_completion:{task_type.value}:{hash(prompt)}"
        cached_response = await cache_manager.async_get(cache_key)
        if cached_response:
            logger.info("Returning cached LLM response")
            return cached_response
        
        # Convert prompt to messages format
        messages = [{"role": "user", "content": prompt}]
        
        # Get provider selection order
        provider_order = self._get_provider_order(
            task_type, routing_criteria, preferred_provider
        )
        
        if not provider_order:
            raise RuntimeError(f"No providers available for task type: {task_type}")
        
        last_error = None
        
        for attempt in range(max_retries):
            for provider_id in provider_order:
                provider = self.providers.get(provider_id)
                if not provider or not provider.config.enabled:
                    continue
                
                # Check if provider is available
                if not await provider.is_available():
                    logger.warning(f"Provider {provider_id} not available")
                    continue
                
                # Check rate limits
                estimated_tokens = len(prompt.split()) * 1.5
                if not await provider.rate_limiter.acquire(int(estimated_tokens)):
                    logger.warning(f"Rate limit exceeded for {provider_id}")
                    continue
                
                try:
                    response = await provider.generate_completion(messages, **kwargs)
                    
                    # Cache successful response
                    await cache_manager.async_set(cache_key, response, self.cache_ttl)
                    
                    # Record metrics
                    metrics_collector.record_ai_request(
                        provider=response.provider.value,
                        model=response.model,
                        status="success",
                        duration=response.processing_time,
                        token_usage=response.token_usage,
                        cost=response.cost
                    )
                    
                    logger.info(
                        f"Completion successful: {provider_id} "
                        f"({response.processing_time:.2f}s, "
                        f"confidence: {response.confidence_score:.2f})"
                    )
                    
                    return response
                    
                except Exception as e:
                    last_error = e
                    logger.warning(f"Provider {provider_id} failed: {e}")
                    
                    # Record failed request
                    metrics_collector.record_ai_request(
                        provider=provider.config.provider.value,
                        model=provider.config.model_name,
                        status="failed",
                        duration=0.0,
                        token_usage={},
                        cost=0.0
                    )
                    
                    if not fallback_enabled:
                        raise
                    
                    continue
            
            # Wait before retry
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All providers failed
        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")
    
    def _get_provider_order(
        self,
        task_type: TaskType,
        criteria: RoutingCriteria,
        preferred_provider: Optional[str] = None
    ) -> List[str]:
        """Get ordered list of providers based on routing criteria."""
        # Start with task-specific providers
        available_providers = []
        for provider_id in self.task_routing.get(task_type, []):
            if provider_id in self.providers and self.providers[provider_id].config.enabled:
                available_providers.append(provider_id)
        
        # Add preferred provider to front if specified
        if preferred_provider and preferred_provider in available_providers:
            available_providers.remove(preferred_provider)
            available_providers.insert(0, preferred_provider)
        
        # Sort by criteria
        if criteria == RoutingCriteria.COST:
            available_providers.sort(
                key=lambda p: self.providers[p].config.cost_per_token
            )
        elif criteria == RoutingCriteria.PERFORMANCE:
            available_providers.sort(
                key=lambda p: self.providers[p].metrics.avg_response_time
            )
        elif criteria == RoutingCriteria.QUALITY:
            available_providers.sort(
                key=lambda p: self.providers[p].config.priority
            )
        elif criteria == RoutingCriteria.SPEED:
            available_providers.sort(
                key=lambda p: (
                    self.providers[p].metrics.avg_response_time,
                    self.providers[p].config.priority
                )
            )
        elif criteria == RoutingCriteria.AVAILABILITY:
            available_providers.sort(
                key=lambda p: (
                    self.providers[p].metrics.error_rate,
                    -self.providers[p].metrics.availability
                )
            )
        
        return available_providers
    
    async def get_best_provider(
        self, 
        task_type: TaskType,
        criteria: RoutingCriteria = RoutingCriteria.COST
    ) -> Optional[str]:
        """Get the best provider for a specific task type and criteria."""
        provider_order = self._get_provider_order(task_type, criteria)
        return provider_order[0] if provider_order else None
    
    async def health_check_all_providers(self) -> Dict[str, bool]:
        """Check health of all providers."""
        health_results = {}
        
        tasks = []
        for provider_id, provider in self.providers.items():
            if provider.config.enabled:
                tasks.append((provider_id, provider.health_check()))
        
        # Run health checks in parallel
        for provider_id, task in tasks:
            try:
                health_results[provider_id] = await task
            except Exception as e:
                logger.error(f"Health check failed for {provider_id}: {e}")
                health_results[provider_id] = False
        
        return health_results
    
    def get_provider_metrics(self) -> Dict[str, ProviderMetrics]:
        """Get metrics for all providers."""
        return {
            provider_id: provider.metrics
            for provider_id, provider in self.providers.items()
        }
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider IDs."""
        return [
            provider_id for provider_id, provider in self.providers.items()
            if provider.config.enabled
        ]
    
    def get_provider_info(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific provider."""
        provider = self.providers.get(provider_id)
        if not provider:
            return None
        
        return {
            "provider_id": provider_id,
            "provider_type": provider.config.provider.value,
            "model_name": provider.config.model_name,
            "enabled": provider.config.enabled,
            "capabilities": provider.config.capabilities,
            "cost_per_token": provider.config.cost_per_token,
            "priority": provider.config.priority,
            "circuit_breaker_state": provider.circuit_breaker.state,
            "metrics": provider.metrics,
            "metadata": provider.config.metadata
        }
    
    async def clear_cache(self):
        """Clear LLM response cache."""
        await cache_manager.invalidate_pattern("llm_completion:*")
        logger.info("LLM response cache cleared")
    
    def reset_provider_metrics(self, provider_id: Optional[str] = None):
        """Reset metrics for specific provider or all providers."""
        if provider_id:
            if provider_id in self.providers:
                self.providers[provider_id].metrics = ProviderMetrics(
                    provider=self.providers[provider_id].config.provider
                )
        else:
            for provider in self.providers.values():
                provider.metrics = ProviderMetrics(provider=provider.config.provider)
        
        logger.info(f"Reset metrics for {provider_id or 'all providers'}")


# Global instance
_enhanced_llm_manager = None


def get_enhanced_llm_manager() -> EnhancedLLMManager:
    """Get global enhanced LLM manager instance."""
    global _enhanced_llm_manager
    if _enhanced_llm_manager is None:
        # Import here to avoid circular imports
        try:
            from .llm_config_manager import get_llm_config_manager
            config_manager = get_llm_config_manager()
            _enhanced_llm_manager = EnhancedLLMManager(config_manager)
        except ImportError:
            logger.warning("LLM config manager not available, using default configuration")
            _enhanced_llm_manager = EnhancedLLMManager()
    return _enhanced_llm_manager


# Alias for backward compatibility
get_llm_manager = get_enhanced_llm_manager