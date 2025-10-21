"""
Unified AI Service
A robust, production-ready AI service that supports multiple providers (OpenAI, Groq)
with intelligent fallback, load balancing, and error handling.
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import logging

from openai import OpenAI, AsyncOpenAI
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.caching import get_cache_manager
from ..monitoring.metrics_collector import get_metrics_collector

logger = get_logger(__name__)
settings = get_settings()
cache_manager = get_cache_manager()
metrics_collector = get_metrics_collector()


class AIProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    GROQ = "groq"


class AIModelType(str, Enum):
    """AI model types for different use cases."""
    FAST = "fast"           # Quick responses, lower cost
    BALANCED = "balanced"   # Balance of speed and quality
    PREMIUM = "premium"     # Highest quality, slower


@dataclass
class AIProviderConfig:
    """Configuration for an AI provider."""
    provider: AIProvider
    api_key: str
    models: Dict[AIModelType, str]
    max_tokens: int = 4000
    timeout: int = 30
    rate_limit_rpm: int = 60
    cost_per_1k_tokens: float = 0.001
    priority: int = 1  # Lower number = higher priority
    enabled: bool = True


@dataclass
class AIResponse:
    """Standardized AI response."""
    content: str
    provider: AIProvider
    model: str
    tokens_used: int
    processing_time: float
    cost_estimate: float
    success: bool = True
    error: Optional[str] = None


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass


class AIRateLimitError(AIProviderError):
    """Rate limit exceeded."""
    pass


class AIServiceUnavailableError(AIProviderError):
    """AI service unavailable."""
    pass


class UnifiedAIService:
    """Unified AI service supporting multiple providers with intelligent fallback."""
    
    def __init__(self):
        self.providers: Dict[AIProvider, AIProviderConfig] = {}
        self.clients: Dict[AIProvider, Any] = {}
        self.async_clients: Dict[AIProvider, Any] = {}
        self.provider_health: Dict[AIProvider, Dict] = {}
        self.last_health_check = {}
        
        self._initialize_providers()
        self._setup_health_monitoring()
    
    def _initialize_providers(self):
        """Initialize all available AI providers."""
        
        # OpenAI Configuration
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                self.providers[AIProvider.OPENAI] = AIProviderConfig(
                    provider=AIProvider.OPENAI,
                    api_key=openai_key,
                    models={
                        AIModelType.FAST: "gpt-3.5-turbo",
                        AIModelType.BALANCED: "gpt-4",
                        AIModelType.PREMIUM: "gpt-4-turbo-preview"
                    },
                    max_tokens=4000,
                    timeout=30,
                    rate_limit_rpm=60,
                    cost_per_1k_tokens=0.002,
                    priority=1,
                    enabled=True
                )
                
                self.clients[AIProvider.OPENAI] = OpenAI(api_key=openai_key)
                self.async_clients[AIProvider.OPENAI] = AsyncOpenAI(api_key=openai_key)
                
                logger.info("✅ OpenAI provider initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI provider: {e}")
        
        # Groq Configuration
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                self.providers[AIProvider.GROQ] = AIProviderConfig(
                    provider=AIProvider.GROQ,
                    api_key=groq_key,
                    models={
                        AIModelType.FAST: "llama-3.1-8b-instant",
                        AIModelType.BALANCED: "llama-3.1-70b-versatile",
                        AIModelType.PREMIUM: "llama-3.2-90b-text-preview"
                    },
                    max_tokens=8000,
                    timeout=30,
                    rate_limit_rpm=30,
                    cost_per_1k_tokens=0.0005,
                    priority=2,
                    enabled=True
                )
                
                self.clients[AIProvider.GROQ] = Groq(api_key=groq_key)
                
                logger.info("✅ Groq provider initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize Groq provider: {e}")
        
        if not self.providers:
            logger.error("❌ No AI providers available!")
        else:
            logger.info(f"✅ Initialized {len(self.providers)} AI providers: {list(self.providers.keys())}")
    
    def _setup_health_monitoring(self):
        """Setup health monitoring for providers."""
        for provider in self.providers:
            self.provider_health[provider] = {
                "status": "unknown",
                "last_success": None,
                "last_failure": None,
                "consecutive_failures": 0,
                "response_times": [],
                "error_rate": 0.0
            }
    
    def get_available_providers(self) -> List[AIProvider]:
        """Get list of available and healthy providers, sorted by priority."""
        available = []
        
        for provider, config in self.providers.items():
            if config.enabled and self._is_provider_healthy(provider):
                available.append(provider)
        
        # Sort by priority (lower number = higher priority)
        available.sort(key=lambda p: self.providers[p].priority)
        return available
    
    def _is_provider_healthy(self, provider: AIProvider) -> bool:
        """Check if a provider is healthy."""
        health = self.provider_health.get(provider, {})
        
        # Consider unhealthy if too many consecutive failures
        if health.get("consecutive_failures", 0) >= 3:
            # Allow retry after cooldown period
            last_failure = health.get("last_failure")
            if last_failure and datetime.now() - last_failure < timedelta(minutes=5):
                return False
        
        return True
    
    def _update_provider_health(self, provider: AIProvider, success: bool, response_time: float = 0, error: str = None):
        """Update provider health metrics."""
        health = self.provider_health[provider]
        
        if success:
            health["status"] = "healthy"
            health["last_success"] = datetime.now()
            health["consecutive_failures"] = 0
            health["response_times"].append(response_time)
            
            # Keep only last 10 response times
            if len(health["response_times"]) > 10:
                health["response_times"] = health["response_times"][-10:]
        else:
            health["status"] = "unhealthy"
            health["last_failure"] = datetime.now()
            health["consecutive_failures"] += 1
            
            logger.warning(f"Provider {provider} failure #{health['consecutive_failures']}: {error}")
    
    def get_best_provider(self, model_type: AIModelType = AIModelType.BALANCED) -> Optional[AIProvider]:
        """Get the best available provider for the given model type."""
        available = self.get_available_providers()
        
        if not available:
            return None
        
        # For now, return the highest priority available provider
        # In the future, could implement more sophisticated selection based on:
        # - Current load
        # - Response times
        # - Cost optimization
        # - Model capabilities
        
        return available[0]
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_type: AIModelType = AIModelType.BALANCED,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        provider: Optional[AIProvider] = None,
        **kwargs
    ) -> AIResponse:
        """
        Create a chat completion using the best available provider.
        
        Args:
            messages: List of chat messages
            model_type: Type of model to use (fast, balanced, premium)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            provider: Specific provider to use (optional)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            AIResponse with the completion result
        """
        
        # Determine which provider to use
        if provider and provider in self.providers:
            providers_to_try = [provider]
        else:
            providers_to_try = self.get_available_providers()
        
        if not providers_to_try:
            raise AIServiceUnavailableError("No AI providers available")
        
        last_error = None
        
        # Try providers in order of preference
        for provider_to_use in providers_to_try:
            try:
                return await self._make_request(
                    provider_to_use, messages, model_type, temperature, max_tokens, **kwargs
                )
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_to_use} failed: {e}")
                self._update_provider_health(provider_to_use, False, error=str(e))
                continue
        
        # All providers failed
        raise AIServiceUnavailableError(f"All AI providers failed. Last error: {last_error}")
    
    async def _make_request(
        self,
        provider: AIProvider,
        messages: List[Dict[str, str]],
        model_type: AIModelType,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> AIResponse:
        """Make a request to a specific provider."""
        
        config = self.providers[provider]
        model = config.models.get(model_type, config.models[AIModelType.BALANCED])
        max_tokens = max_tokens or config.max_tokens
        
        start_time = time.time()
        
        try:
            if provider == AIProvider.OPENAI:
                response = await self._openai_request(
                    model, messages, temperature, max_tokens, **kwargs
                )
            elif provider == AIProvider.GROQ:
                response = await self._groq_request(
                    model, messages, temperature, max_tokens, **kwargs
                )
            else:
                raise AIProviderError(f"Unsupported provider: {provider}")
            
            processing_time = time.time() - start_time
            
            # Update health metrics
            self._update_provider_health(provider, True, processing_time)
            
            # Record metrics (if method exists)
            try:
                if hasattr(metrics_collector, 'record_api_call'):
                    metrics_collector.record_api_call(
                        service=provider.value,
                        endpoint="chat_completion",
                        duration=processing_time,
                        success=True,
                        model=model
                    )
            except Exception as e:
                logger.debug(f"Failed to record metrics: {e}")
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_provider_health(provider, False, processing_time, str(e))
            
            # Record error metrics (if method exists)
            try:
                if hasattr(metrics_collector, 'record_api_call'):
                    metrics_collector.record_api_call(
                        service=provider.value,
                        endpoint="chat_completion",
                        duration=processing_time,
                        success=False,
                        error=str(e)
                    )
            except Exception as e:
                logger.debug(f"Failed to record error metrics: {e}")
            
            raise
    
    async def _openai_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> AIResponse:
        """Make request to OpenAI."""
        
        client = self.async_clients[AIProvider.OPENAI]
        
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=self.providers[AIProvider.OPENAI].timeout,
            **kwargs
        )
        
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        cost_estimate = tokens_used * self.providers[AIProvider.OPENAI].cost_per_1k_tokens / 1000
        
        return AIResponse(
            content=content,
            provider=AIProvider.OPENAI,
            model=model,
            tokens_used=tokens_used,
            processing_time=0,  # Will be set by caller
            cost_estimate=cost_estimate,
            success=True
        )
    
    async def _groq_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> AIResponse:
        """Make request to Groq."""
        
        client = self.clients[AIProvider.GROQ]
        
        # Groq doesn't have async client, so run in thread
        def _sync_groq_call():
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.providers[AIProvider.GROQ].timeout,
                **kwargs
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _sync_groq_call)
        
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        cost_estimate = tokens_used * self.providers[AIProvider.GROQ].cost_per_1k_tokens / 1000
        
        return AIResponse(
            content=content,
            provider=AIProvider.GROQ,
            model=model,
            tokens_used=tokens_used,
            processing_time=0,  # Will be set by caller
            cost_estimate=cost_estimate,
            success=True
        )
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        status = {}
        
        for provider, config in self.providers.items():
            health = self.provider_health[provider]
            
            avg_response_time = 0
            if health["response_times"]:
                avg_response_time = sum(health["response_times"]) / len(health["response_times"])
            
            status[provider.value] = {
                "enabled": config.enabled,
                "healthy": self._is_provider_healthy(provider),
                "status": health["status"],
                "consecutive_failures": health["consecutive_failures"],
                "avg_response_time": avg_response_time,
                "last_success": health["last_success"].isoformat() if health["last_success"] else None,
                "last_failure": health["last_failure"].isoformat() if health["last_failure"] else None,
                "models": {mt.value: model for mt, model in config.models.items()},
                "priority": config.priority
            }
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers."""
        results = {}
        
        test_messages = [
            {"role": "user", "content": "Hello, please respond with 'OK' to confirm you're working."}
        ]
        
        for provider in self.providers:
            try:
                response = await self.chat_completion(
                    messages=test_messages,
                    model_type=AIModelType.FAST,
                    max_tokens=10,
                    provider=provider
                )
                
                results[provider.value] = {
                    "status": "healthy",
                    "response_time": response.processing_time,
                    "model": response.model,
                    "success": True
                }
                
            except Exception as e:
                results[provider.value] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "success": False
                }
        
        return results


# Global service instance
_unified_ai_service = None

def get_unified_ai_service() -> UnifiedAIService:
    """Get the global unified AI service instance."""
    global _unified_ai_service
    if _unified_ai_service is None:
        _unified_ai_service = UnifiedAIService()
    return _unified_ai_service


# Convenience functions for backward compatibility
async def chat_completion(
    messages: List[Dict[str, str]],
    model_type: AIModelType = AIModelType.BALANCED,
    **kwargs
) -> AIResponse:
    """Convenience function for chat completion."""
    service = get_unified_ai_service()
    return await service.chat_completion(messages, model_type, **kwargs)


def get_ai_provider_status() -> Dict[str, Any]:
    """Get status of all AI providers."""
    service = get_unified_ai_service()
    return service.get_provider_status()