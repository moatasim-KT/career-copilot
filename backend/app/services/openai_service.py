"""
Enhanced OpenAI Service for Production Reliability
Provides robust OpenAI integration with comprehensive error handling, caching, and performance monitoring.
Updated to use OpenAI v1.0+ API.
"""

import asyncio
import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import httpx
from openai import OpenAI, AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.config import get_settings
from ..core.logging import get_logger
from .cache_service import get_cache_service
from ..monitoring.metrics_collector import get_metrics_collector

logger = get_logger(__name__)
settings = get_settings()
cache_service = get_cache_service()
metrics_collector = get_metrics_collector()


class OpenAIError(Exception):
    """Custom OpenAI service error."""
    pass


class OpenAIRateLimitError(OpenAIError):
    """OpenAI rate limit exceeded."""
    pass


class OpenAIServiceUnavailableError(OpenAIError):
    """OpenAI service unavailable."""
    pass


class EnhancedOpenAIService:
    """Enhanced OpenAI service with production reliability features."""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self._get_api_key()
        
        # Initialize OpenAI clients with new API
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            self.async_client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            self.async_client = None
            logger.warning("OpenAI API key not found")
        
        # Configuration
        self.default_model = "gpt-3.5-turbo"
        self.max_retries = 3
        self.timeout = 60
    
    def _get_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment or settings."""
        # Try environment variable first
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key
        
        # Try settings
        if hasattr(self.settings, 'openai_api_key'):
            return self.settings.openai_api_key
        
        # Try reading from secrets file
        secrets_file = Path("secrets/openai_api_key.txt")
        if secrets_file.exists():
            try:
                with open(secrets_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning(f"Failed to read OpenAI API key from secrets file: {e}")
        
        return None
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return self.client is not None and self.api_key is not None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((OpenAIRateLimitError, OpenAIServiceUnavailableError))
    )
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a chat completion using the new OpenAI API."""
        
        if not self.is_available():
            raise OpenAIError("OpenAI service is not available")
        
        model = model or self.default_model
        
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout,
                **kwargs
            )
            
            duration = time.time() - start_time
            
            # Log metrics
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
            metrics_collector.record_ai_request(
                provider="openai",
                model=model,
                status="success",
                duration=duration,
                token_usage=token_usage,
                cost=0.0  # Calculate cost if needed
            )
            
            # Convert response to dict for compatibility
            result = {
                "id": response.id,
                "object": response.object,
                "created": response.created,
                "model": response.model,
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                } if response.usage else None
            }
            
            logger.info(f"OpenAI chat completion successful: {model}, {duration:.2f}s")
            return result
            
        except Exception as e:
            # Log error metrics
            metrics_collector.record_ai_request(
                provider="openai",
                model=model,
                status="error",
                duration=time.time() - start_time,
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                cost=0.0,
                error_type=str(e)
            )
            
            # Handle specific OpenAI errors
            if "rate limit" in str(e).lower():
                raise OpenAIRateLimitError(f"OpenAI rate limit exceeded: {e}")
            elif "service unavailable" in str(e).lower():
                raise OpenAIServiceUnavailableError(f"OpenAI service unavailable: {e}")
            else:
                raise OpenAIError(f"OpenAI API error: {e}")
    
    async def async_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create an async chat completion using the new OpenAI API."""
        
        if not self.is_available():
            raise OpenAIError("OpenAI service is not available")
        
        model = model or self.default_model
        
        try:
            start_time = time.time()
            
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout,
                **kwargs
            )
            
            duration = time.time() - start_time
            
            # Log metrics
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
            metrics_collector.record_ai_request(
                provider="openai",
                model=model,
                status="success",
                duration=duration,
                token_usage=token_usage,
                cost=0.0  # Calculate cost if needed
            )
            
            # Convert response to dict for compatibility
            result = {
                "id": response.id,
                "object": response.object,
                "created": response.created,
                "model": response.model,
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                } if response.usage else None
            }
            
            logger.info(f"OpenAI async chat completion successful: {model}, {duration:.2f}s")
            return result
            
        except Exception as e:
            # Log error metrics
            metrics_collector.record_ai_request(
                provider="openai",
                model=model,
                status="error",
                duration=time.time() - start_time,
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                cost=0.0,
                error_type=str(e)
            )
            
            # Handle specific OpenAI errors
            if "rate limit" in str(e).lower():
                raise OpenAIRateLimitError(f"OpenAI rate limit exceeded: {e}")
            elif "service unavailable" in str(e).lower():
                raise OpenAIServiceUnavailableError(f"OpenAI service unavailable: {e}")
            else:
                raise OpenAIError(f"OpenAI API error: {e}")
    
    def simple_completion(self, prompt: str, model: Optional[str] = None, max_tokens: int = 150) -> str:
        """Simple completion for basic text generation."""
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.chat_completion(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            if response and response.get("choices"):
                return response["choices"][0]["message"]["content"]
            else:
                raise OpenAIError("No response content received")
                
        except Exception as e:
            logger.error(f"Simple completion failed: {e}")
            raise OpenAIError(f"Simple completion failed: {e}")


# Global service instance
_openai_service = None

def get_openai_service() -> EnhancedOpenAIService:
    """Get the global OpenAI service instance."""
    global _openai_service
    if _openai_service is None:
        _openai_service = EnhancedOpenAIService()
    return _openai_service

def get_enhanced_openai_service() -> EnhancedOpenAIService:
    """Get the enhanced OpenAI service instance (alias for compatibility)."""
    return get_openai_service()
