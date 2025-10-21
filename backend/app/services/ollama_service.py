"""
Enhanced Ollama Service for Local Deployment Scenarios
Provides robust local LLM integration with comprehensive error handling, caching, and performance monitoring.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.caching import get_cache_manager
from ..monitoring.metrics_collector import get_metrics_collector

logger = get_logger(__name__)
settings = get_settings()
cache_manager = get_cache_manager()
metrics_collector = get_metrics_collector()


class OllamaError(Exception):
    """Custom Ollama service error."""
    pass


class OllamaConnectionError(OllamaError):
    """Ollama connection error."""
    pass


class OllamaModelNotFoundError(OllamaError):
    """Ollama model not found."""
    pass


class ModelManager:
    """Manages Ollama model lifecycle and optimization."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.available_models = {}
        self.model_performance = {}
        self.last_model_check = None
        self.model_check_interval = 300  # 5 minutes
    
    async def refresh_models(self) -> List[str]:
        """Refresh available models list."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    
                    self.available_models = {}
                    for model in models:
                        model_name = model["name"]
                        self.available_models[model_name] = {
                            "name": model_name,
                            "size": model.get("size", 0),
                            "modified_at": model.get("modified_at"),
                            "digest": model.get("digest"),
                            "details": model.get("details", {})
                        }
                    
                    self.last_model_check = datetime.now()
                    logger.info(f"Refreshed Ollama models: {list(self.available_models.keys())}")
                    return list(self.available_models.keys())
                else:
                    logger.error(f"Failed to get Ollama models: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error refreshing Ollama models: {e}")
            return []
    
    async def get_available_models(self) -> List[str]:
        """Get available models, refreshing if needed."""
        now = datetime.now()
        
        if (self.last_model_check is None or 
            now - self.last_model_check > timedelta(seconds=self.model_check_interval)):
            await self.refresh_models()
        
        return list(self.available_models.keys())
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model if not available."""
        try:
            async with httpx.AsyncClient(timeout=300) as client:  # 5 minute timeout for model pulls
                payload = {"name": model_name}
                
                response = await client.post(f"{self.base_url}/api/pull", json=payload)
                
                if response.status_code == 200:
                    logger.info(f"Successfully pulled Ollama model: {model_name}")
                    await self.refresh_models()
                    return True
                else:
                    logger.error(f"Failed to pull Ollama model {model_name}: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error pulling Ollama model {model_name}: {e}")
            return False
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        return self.available_models.get(model_name)
    
    def record_model_performance(self, model_name: str, response_time: float, tokens: int):
        """Record model performance metrics."""
        if model_name not in self.model_performance:
            self.model_performance[model_name] = {
                "total_requests": 0,
                "total_response_time": 0.0,
                "total_tokens": 0,
                "avg_response_time": 0.0,
                "tokens_per_second": 0.0
            }
        
        perf = self.model_performance[model_name]
        perf["total_requests"] += 1
        perf["total_response_time"] += response_time
        perf["total_tokens"] += tokens
        perf["avg_response_time"] = perf["total_response_time"] / perf["total_requests"]
        
        if response_time > 0:
            perf["tokens_per_second"] = tokens / response_time
    
    def get_best_model_for_task(self, task_type: str, available_models: List[str]) -> Optional[str]:
        """Get the best model for a specific task type."""
        # Model preferences for different tasks
        task_preferences = {
            "analysis": ["llama2:70b", "llama2:13b", "mistral:7b", "llama2:7b"],
            "generation": ["mistral:7b", "llama2:13b", "llama2:7b"],
            "conversation": ["llama2:7b", "mistral:7b"],
            "code": ["codellama:13b", "codellama:7b", "llama2:13b"],
            "reasoning": ["llama2:70b", "llama2:13b", "mistral:7b"]
        }
        
        preferred_models = task_preferences.get(task_type, task_preferences["generation"])
        
        # Find the first available preferred model
        for model in preferred_models:
            if model in available_models:
                return model
        
        # Fallback to first available model
        return available_models[0] if available_models else None


class EnhancedOllamaService:
    """Enhanced Ollama service with production reliability features."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = getattr(self.settings, "ollama_base_url", "http://localhost:11434")
        self.default_model = getattr(self.settings, "ollama_model", "llama2")
        self.enabled = getattr(self.settings, "ollama_enabled", False)
        
        # Configuration
        self.timeout = 120  # 2 minutes for local models
        self.cache_ttl = 7200  # 2 hours (longer for local models)
        self.max_retries = 2  # Fewer retries for local service
        
        # Model manager
        self.model_manager = ModelManager(self.base_url)
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cached_responses": 0,
            "total_tokens": 0,
            "avg_response_time": 0.0,
            "response_times": [],
            "model_usage": {}
        }
        
        # Connection health
        self.last_health_check = None
        self.health_status = "unknown"
        self.connection_failures = 0
        self.max_connection_failures = 3
        
        logger.info(f"Enhanced Ollama service initialized: {self.base_url}")
    
    def _generate_cache_key(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """Generate cache key for request."""
        cache_data = {
            "messages": messages,
            "model": model,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }
        
        cache_str = json.dumps(cache_data, sort_keys=True)
        return f"ollama_completion:{hashlib.md5(cache_str.encode()).hexdigest()}"
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Rough estimation: 1 token ≈ 4 characters for most models
        return max(1, len(text) // 4)
    
    def _update_metrics(self, success: bool, response_time: float, model: str, tokens: int = 0):
        """Update service metrics."""
        self.metrics["total_requests"] += 1
        
        if success:
            self.metrics["successful_requests"] += 1
            self.connection_failures = 0
        else:
            self.metrics["failed_requests"] += 1
            self.connection_failures += 1
        
        self.metrics["total_tokens"] += tokens
        
        # Update response times
        self.metrics["response_times"].append(response_time)
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
        
        # Calculate average response time
        if self.metrics["response_times"]:
            self.metrics["avg_response_time"] = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
        
        # Track model usage
        if model not in self.metrics["model_usage"]:
            self.metrics["model_usage"][model] = {"requests": 0, "tokens": 0}
        
        self.metrics["model_usage"][model]["requests"] += 1
        self.metrics["model_usage"][model]["tokens"] += tokens
        
        # Record model performance
        if success:
            self.model_manager.record_model_performance(model, response_time, tokens)
    
    async def is_available(self) -> bool:
        """Check if Ollama service is available."""
        if not self.enabled:
            return False
        
        if self.connection_failures >= self.max_connection_failures:
            logger.warning("Ollama service marked as unavailable due to connection failures")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                available = response.status_code == 200
                
                if available:
                    self.health_status = "healthy"
                    self.last_health_check = datetime.now()
                else:
                    self.health_status = "unhealthy"
                
                return available
                
        except Exception as e:
            logger.warning(f"Ollama availability check failed: {e}")
            self.health_status = "error"
            return False
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
    )
    async def _make_ollama_request(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Dict[str, Any]:
        """Make Ollama API request with retry logic."""
        try:
            # Convert messages to Ollama format
            if len(messages) == 1:
                # Simple prompt format
                prompt = messages[0]["content"]
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.1),
                        "num_predict": kwargs.get("max_tokens", 1000),
                        "top_p": kwargs.get("top_p", 0.9),
                        "repeat_penalty": kwargs.get("repeat_penalty", 1.1)
                    }
                }
                endpoint = "api/generate"
            else:
                # Chat format
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.1),
                        "num_predict": kwargs.get("max_tokens", 1000),
                        "top_p": kwargs.get("top_p", 0.9),
                        "repeat_penalty": kwargs.get("repeat_penalty", 1.1)
                    }
                }
                endpoint = "api/chat"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/{endpoint}", json=payload)
                
                if response.status_code != 200:
                    error_text = response.text
                    if "model not found" in error_text.lower():
                        raise OllamaModelNotFoundError(f"Model {model} not found")
                    else:
                        raise OllamaError(f"Ollama API error: {response.status_code} - {error_text}")
                
                data = response.json()
                
                # Extract content based on endpoint
                if endpoint == "api/generate":
                    content = data.get("response", "")
                else:
                    content = data.get("message", {}).get("content", "")
                
                return {
                    "content": content,
                    "model": data.get("model", model),
                    "total_duration": data.get("total_duration", 0),
                    "load_duration": data.get("load_duration", 0),
                    "prompt_eval_count": data.get("prompt_eval_count", 0),
                    "prompt_eval_duration": data.get("prompt_eval_duration", 0),
                    "eval_count": data.get("eval_count", 0),
                    "eval_duration": data.get("eval_duration", 0)
                }
                
        except httpx.TimeoutException as e:
            logger.warning(f"Ollama request timeout: {e}")
            raise OllamaError(f"Request timeout: {e}")
        
        except httpx.ConnectError as e:
            logger.warning(f"Ollama connection error: {e}")
            raise OllamaConnectionError(f"Connection error: {e}")
        
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise OllamaError(f"API error: {e}")
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        task_type: str = "generation",
        use_cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion with caching and error handling."""
        start_time = time.time()
        request_id = str(uuid4())
        
        try:
            # Check if service is available
            if not await self.is_available():
                raise OllamaConnectionError("Ollama service is not available")
            
            # Get available models and select best one
            available_models = await self.model_manager.get_available_models()
            
            if not available_models:
                raise OllamaError("No Ollama models available")
            
            # Select model
            if model and model in available_models:
                selected_model = model
            else:
                selected_model = self.model_manager.get_best_model_for_task(task_type, available_models)
                if not selected_model:
                    selected_model = available_models[0]
            
            # Check cache first
            if use_cache:
                cache_key = self._generate_cache_key(messages, selected_model, **kwargs)
                cached_result = await cache_manager.async_get(cache_key)
                
                if cached_result:
                    self.metrics["cached_responses"] += 1
                    response_time = time.time() - start_time
                    self._update_metrics(True, response_time, selected_model)
                    
                    logger.info(f"Cache hit for Ollama request {request_id}")
                    return {
                        **cached_result,
                        "cached": True,
                        "request_id": request_id,
                        "response_time": response_time
                    }
            
            # Make API request
            response_data = await self._make_ollama_request(messages, selected_model, **kwargs)
            
            response_time = time.time() - start_time
            
            # Estimate tokens
            prompt_tokens = sum(self._estimate_tokens(msg["content"]) for msg in messages)
            completion_tokens = self._estimate_tokens(response_data["content"])
            total_tokens = prompt_tokens + completion_tokens
            
            # Update metrics
            self._update_metrics(True, response_time, selected_model, total_tokens)
            
            # Prepare result
            result = {
                "content": response_data["content"],
                "model": response_data["model"],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                },
                "cost": 0.0,  # Ollama is free
                "performance": {
                    "total_duration": response_data.get("total_duration", 0),
                    "load_duration": response_data.get("load_duration", 0),
                    "eval_duration": response_data.get("eval_duration", 0),
                    "tokens_per_second": completion_tokens / (response_data.get("eval_duration", 1) / 1e9) if response_data.get("eval_duration") else 0
                },
                "cached": False,
                "request_id": request_id,
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache result
            if use_cache:
                await cache_manager.async_set(cache_key, result, self.cache_ttl)
            
            # Record metrics for monitoring
            if metrics_collector:
                metrics_collector.record_ai_request(
                    model=selected_model,
                    provider="ollama",
                    tokens=total_tokens,
                    cost=0.0,
                    response_time=response_time,
                    success=True
                )
            
            logger.info(f"Ollama completion successful: {request_id}, model: {selected_model}, tokens: {total_tokens}")
            
            return result
            
        except OllamaModelNotFoundError as e:
            # Try to pull the model if it's not found
            if model and model not in await self.model_manager.get_available_models():
                logger.info(f"Attempting to pull missing model: {model}")
                if await self.model_manager.pull_model(model):
                    # Retry the request with the newly pulled model
                    return await self.generate_completion(messages, model, task_type, use_cache, **kwargs)
            
            response_time = time.time() - start_time
            self._update_metrics(False, response_time, model or "unknown")
            
            logger.error(f"Ollama model not found: {request_id}, error: {e}")
            raise OllamaError(f"Model not found: {e}")
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_metrics(False, response_time, model or "unknown")
            
            # Record error metrics
            if metrics_collector:
                metrics_collector.record_ai_request(
                    model=model or "unknown",
                    provider="ollama",
                    tokens=0,
                    cost=0.0,
                    response_time=response_time,
                    success=False
                )
            
            logger.error(f"Ollama completion failed: {request_id}, error: {e}")
            raise OllamaError(f"Completion failed: {e}")
    
    async def analyze_contract(
        self,
        contract_text: str,
        analysis_type: str = "comprehensive",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze contract using Ollama with specialized prompts."""
        system_prompts = {
            "comprehensive": """You are an expert contract analyst. Analyze the contract for risks and provide recommendations.
Focus on:
1. Financial risks (payment terms, penalties, costs)
2. Legal risks (liability, indemnification, termination)
3. Operational risks (deliverables, timelines, dependencies)
4. Compliance risks (regulations, standards, requirements)

Provide specific recommendations for each identified risk.""",
            
            "risk_assessment": """You are a legal risk assessment expert. Identify and categorize risks in this contract.
For each risk, provide:
- Risk category (Financial, Legal, Operational, Compliance)
- Risk level (High, Medium, Low)
- Specific description
- Potential impact
- Mitigation recommendations""",
            
            "quick_review": """You are a contract reviewer. Provide a quick analysis focusing on the most important risks and issues in this contract."""
        }
        
        system_prompt = system_prompts.get(analysis_type, system_prompts["comprehensive"])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this contract:\n\n{contract_text[:6000]}"}  # Limit for local models
        ]
        
        try:
            result = await self.generate_completion(
                messages=messages,
                model=model,
                task_type="analysis",
                temperature=0.1,
                max_tokens=1500
            )
            
            return {
                "analysis": result["content"],
                "analysis_type": analysis_type,
                "model_used": result["model"],
                "tokens_used": result["usage"]["total_tokens"],
                "performance": result["performance"],
                "request_id": result["request_id"],
                "timestamp": result["timestamp"]
            }
            
        except Exception as e:
            logger.error(f"Contract analysis failed: {e}")
            raise OllamaError(f"Contract analysis failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Ollama service."""
        try:
            start_time = time.time()
            
            # Check if service is available
            available = await self.is_available()
            
            if not available:
                return {
                    "status": "unhealthy",
                    "error": "Service not available",
                    "available_models": [],
                    "connection_failures": self.connection_failures
                }
            
            # Get available models
            models = await self.model_manager.get_available_models()
            
            # Simple test request if models are available
            test_result = None
            if models:
                try:
                    messages = [{"role": "user", "content": "Hello"}]
                    
                    result = await self.generate_completion(
                        messages=messages,
                        model=models[0],
                        max_tokens=5,
                        use_cache=False
                    )
                    
                    test_result = {
                        "success": True,
                        "model_used": result["model"],
                        "request_id": result["request_id"]
                    }
                    
                except Exception as e:
                    test_result = {
                        "success": False,
                        "error": str(e)
                    }
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy" if test_result and test_result["success"] else "degraded",
                "response_time": response_time,
                "available_models": models,
                "connection_failures": self.connection_failures,
                "test_result": test_result,
                "service_url": self.base_url
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "available_models": [],
                "connection_failures": self.connection_failures,
                "service_url": self.base_url
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics."""
        success_rate = 0.0
        if self.metrics["total_requests"] > 0:
            success_rate = (self.metrics["successful_requests"] / self.metrics["total_requests"]) * 100
        
        return {
            "total_requests": self.metrics["total_requests"],
            "successful_requests": self.metrics["successful_requests"],
            "failed_requests": self.metrics["failed_requests"],
            "cached_responses": self.metrics["cached_responses"],
            "success_rate": success_rate,
            "total_tokens": self.metrics["total_tokens"],
            "avg_response_time": self.metrics["avg_response_time"],
            "connection_failures": self.connection_failures,
            "health_status": self.health_status,
            "model_usage": self.metrics["model_usage"],
            "model_performance": self.model_manager.model_performance,
            "service_url": self.base_url,
            "enabled": self.enabled
        }
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return await self.model_manager.get_available_models()
    
    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        return self.model_manager.get_model_info(model)
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a new model."""
        return await self.model_manager.pull_model(model_name)
    
    async def clear_cache(self) -> bool:
        """Clear Ollama response cache."""
        try:
            # Clear cache entries matching Ollama pattern
            cleared_count = cache_manager.invalidate_pattern("ollama_completion:*")
            logger.info(f"Cleared {cleared_count} Ollama cache entries")
            return True
        except Exception as e:
            logger.error(f"Failed to clear Ollama cache: {e}")
            return False


# Global service instance
_enhanced_ollama_service = None


def get_enhanced_ollama_service() -> EnhancedOllamaService:
    """Get the global enhanced Ollama service instance."""
    global _enhanced_ollama_service
    
    if _enhanced_ollama_service is None:
        _enhanced_ollama_service = EnhancedOllamaService()
    
    return _enhanced_ollama_service