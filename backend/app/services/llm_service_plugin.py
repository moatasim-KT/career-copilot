"""
LLM Service Plugin for AI provider integration.

This module provides service plugins for different LLM providers including
OpenAI, GROQ, Ollama, and other AI services with intelligent routing and fallback.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.service_integration import ServicePlugin, ServiceConfig, ServiceHealth, ServiceStatus
from ..services.base_service_plugin import HTTPServicePlugin
from ..core.logging import get_logger

logger = get_logger(__name__)


class LLMServicePlugin(HTTPServicePlugin):
    """Base plugin for LLM services."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.provider_name = config.config.get("provider", "unknown")
        self.api_key = config.config.get("api_key", "")
        self.models = config.config.get("models", [])
        self.cost_per_token = config.config.get("cost_per_token", 0.0)
        self.rate_limit = config.config.get("rate_limit", 60)  # requests per minute
        self.max_tokens = config.config.get("max_tokens", 4000)
        
        # LLM-specific metrics
        self.token_usage = {"input": 0, "output": 0, "total": 0}
        self.total_cost = 0.0
        self.model_usage = {}
        
        # Rate limiting
        self._request_times = []
        self._rate_limit_lock = asyncio.Lock()
    
    async def health_check(self) -> ServiceHealth:
        """Perform LLM-specific health check."""
        if not self.session:
            return ServiceHealth(
                status=ServiceStatus.STOPPED,
                last_check=datetime.now(),
                response_time=0.0,
                error_message="Service not started"
            )
        
        try:
            # Test with a simple completion request
            start_time = time.time()
            
            health_result = await self._test_completion()
            response_time = time.time() - start_time
            
            if health_result["success"]:
                status = ServiceStatus.HEALTHY
                error_message = None
                details = {
                    "provider": self.provider_name,
                    "available_models": self.models,
                    "rate_limit": self.rate_limit,
                    "token_usage": self.token_usage,
                    "total_cost": self.total_cost
                }
            else:
                status = ServiceStatus.UNHEALTHY
                error_message = health_result.get("error", "Health check failed")
                details = {"provider": self.provider_name}
            
            return ServiceHealth(
                status=status,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=error_message,
                details=details
            )
            
        except Exception as e:
            return ServiceHealth(
                status=ServiceStatus.ERROR,
                last_check=datetime.now(),
                response_time=0.0,
                error_message=str(e),
                details={"provider": self.provider_name}
            )
    
    async def _test_completion(self) -> Dict[str, Any]:
        """Test completion endpoint with a simple request."""
        # This should be overridden by specific provider implementations
        return {"success": True}
    
    async def get_completion(self, prompt: str, model: Optional[str] = None, 
                           **kwargs) -> Dict[str, Any]:
        """Get completion from LLM provider."""
        if not await self._check_rate_limit():
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "provider": self.provider_name
            }
        
        model = model or (self.models[0] if self.models else "default")
        
        start_time = time.time()
        
        try:
            result = await self._make_completion_request(prompt, model, **kwargs)
            response_time = time.time() - start_time
            
            # Update metrics
            success = result.get("success", False)
            self.update_metrics(success, response_time)
            
            # Update LLM-specific metrics
            if success and "usage" in result:
                usage = result["usage"]
                self.token_usage["input"] += usage.get("prompt_tokens", 0)
                self.token_usage["output"] += usage.get("completion_tokens", 0)
                self.token_usage["total"] += usage.get("total_tokens", 0)
                
                # Calculate cost
                total_tokens = usage.get("total_tokens", 0)
                cost = total_tokens * self.cost_per_token
                self.total_cost += cost
                
                # Track model usage
                if model not in self.model_usage:
                    self.model_usage[model] = {"requests": 0, "tokens": 0, "cost": 0.0}
                
                self.model_usage[model]["requests"] += 1
                self.model_usage[model]["tokens"] += total_tokens
                self.model_usage[model]["cost"] += cost
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "error": str(e),
                "provider": self.provider_name,
                "response_time": response_time
            }
    
    async def _make_completion_request(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """Make completion request to provider API."""
        # This should be overridden by specific provider implementations
        raise NotImplementedError("Subclasses must implement _make_completion_request")
    
    async def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits."""
        async with self._rate_limit_lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            self._request_times = [t for t in self._request_times if now - t < 60]
            
            # Check if we're within rate limit
            if len(self._request_times) >= self.rate_limit:
                return False
            
            # Add current request time
            self._request_times.append(now)
            return True
    
    def get_provider_metrics(self) -> Dict[str, Any]:
        """Get provider-specific metrics."""
        return {
            "provider": self.provider_name,
            "token_usage": self.token_usage,
            "total_cost": self.total_cost,
            "model_usage": self.model_usage,
            "rate_limit": self.rate_limit,
            "current_requests_per_minute": len(self._request_times)
        }


class OpenAIServicePlugin(LLMServicePlugin):
    """OpenAI service plugin."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.base_url = config.config.get("base_url", "https://api.openai.com/v1")
        self.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    async def _test_completion(self) -> Dict[str, Any]:
        """Test OpenAI completion endpoint."""
        try:
            payload = {
                "model": self.models[0] if self.models else "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }
            
            result = await self.make_request("POST", "chat/completions", json=payload)
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _make_completion_request(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """Make OpenAI completion request."""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", 0.1),
            **{k: v for k, v in kwargs.items() if k not in ["max_tokens", "temperature"]}
        }
        
        result = await self.make_request("POST", "chat/completions", json=payload)
        
        if result["success"]:
            data = result["data"]
            return {
                "success": True,
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", model),
                "provider": self.provider_name,
                "response_time": result["response_time"]
            }
        else:
            return result


class GroqServicePlugin(LLMServicePlugin):
    """GROQ service plugin."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.base_url = config.config.get("base_url", "https://api.groq.com/openai/v1")
        self.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    async def _test_completion(self) -> Dict[str, Any]:
        """Test GROQ completion endpoint."""
        try:
            payload = {
                "model": self.models[0] if self.models else "llama3-8b-8192",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }
            
            result = await self.make_request("POST", "chat/completions", json=payload)
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _make_completion_request(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """Make GROQ completion request."""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", 0.1),
            **{k: v for k, v in kwargs.items() if k not in ["max_tokens", "temperature"]}
        }
        
        result = await self.make_request("POST", "chat/completions", json=payload)
        
        if result["success"]:
            data = result["data"]
            return {
                "success": True,
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", model),
                "provider": self.provider_name,
                "response_time": result["response_time"]
            }
        else:
            return result


class OllamaServicePlugin(LLMServicePlugin):
    """Ollama service plugin for local LLM deployment."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.base_url = config.config.get("base_url", "http://localhost:11434")
        # Ollama doesn't require API key authentication
        self.api_key = ""
    
    async def _test_completion(self) -> Dict[str, Any]:
        """Test Ollama completion endpoint."""
        try:
            # First check if Ollama is running
            result = await self.make_request("GET", "api/tags")
            if not result["success"]:
                return result
            
            # Test with a simple generation
            payload = {
                "model": self.models[0] if self.models else "llama2",
                "prompt": "Hello",
                "stream": False
            }
            
            result = await self.make_request("POST", "api/generate", json=payload)
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _make_completion_request(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """Make Ollama completion request."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.1),
                "num_predict": kwargs.get("max_tokens", self.max_tokens)
            }
        }
        
        result = await self.make_request("POST", "api/generate", json=payload)
        
        if result["success"]:
            data = result["data"]
            return {
                "success": True,
                "content": data.get("response", ""),
                "usage": {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                },
                "model": data.get("model", model),
                "provider": self.provider_name,
                "response_time": result["response_time"]
            }
        else:
            return result