#!/usr/bin/env python3
"""
Service Initialization Script.

This script initializes and starts all production services including
LLM providers, integrations, monitoring, and core services.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.service_manager import get_service_manager
from app.core.service_integration import ServiceConfig, ServiceType
from app.services.llm_service_plugin import OpenAIServicePlugin, GroqServicePlugin, OllamaServicePlugin
from app.core.config_manager import get_config_manager
from app.core.logging import get_logger

logger = get_logger(__name__)


async def initialize_llm_services(service_manager):
    """Initialize LLM service providers."""
    config = get_config_manager()
    
    # OpenAI Service
    openai_config = config.get("ai.openai", {})
    if openai_config.get("api_key"):
        openai_service_config = ServiceConfig(
            service_id="openai_service",
            service_type=ServiceType.AI_PROVIDER,
            name="OpenAI Service",
            description="OpenAI GPT models for job application tracking",
            version="1.0.0",
            config={
                "plugin_type": "llm",
                "provider": "openai",
                "base_url": "https://api.openai.com/v1",
                "api_key": openai_config["api_key"],
                "models": ["gpt-4", "gpt-3.5-turbo"],
                "cost_per_token": 0.00003,  # Approximate cost
                "rate_limit": 60,
                "max_tokens": openai_config.get("max_tokens", 4000)
            },
            health_check_interval=60,
            enabled=True,
            auto_start=True
        )
        
        service_manager.register_service_plugin("llm", OpenAIServicePlugin)
        openai_plugin = OpenAIServicePlugin(openai_service_config)
        await service_manager.registry.register_service(openai_plugin)
        logger.info("OpenAI service configured")
    
    # GROQ Service
    groq_config = config.get("ai.groq", {})
    if groq_config.get("enabled", False) and groq_config.get("api_key"):
        groq_service_config = ServiceConfig(
            service_id="groq_service",
            service_type=ServiceType.AI_PROVIDER,
            name="GROQ Service",
            description="GROQ fast inference for job application tracking",
            version="1.0.0",
            config={
                "plugin_type": "llm",
                "provider": "groq",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": groq_config["api_key"],
                "models": ["mixtral-8x7b-32768", "llama2-70b-4096"],
                "cost_per_token": 0.00001,  # Lower cost than OpenAI
                "rate_limit": 100,
                "max_tokens": groq_config.get("max_tokens", 32768)
            },
            health_check_interval=60,
            enabled=True,
            auto_start=True
        )
        
        groq_plugin = GroqServicePlugin(groq_service_config)
        await service_manager.registry.register_service(groq_plugin)
        logger.info("GROQ service configured")
    
    # Ollama Service (local)
    ollama_config = config.get("ai.ollama", {})
    if ollama_config.get("enabled", False):
        ollama_service_config = ServiceConfig(
            service_id="ollama_service",
            service_type=ServiceType.AI_PROVIDER,
            name="Ollama Service",
            description="Local Ollama models for job application tracking",
            version="1.0.0",
            config={
                "plugin_type": "llm",
                "provider": "ollama",
                "base_url": ollama_config.get("base_url", "http://localhost:11434"),
                "api_key": "",  # No API key needed
    # ... (rest of the file remains unchanged)
