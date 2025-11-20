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
                "models": [ollama_config.get("model", "llama2")],
                "cost_per_token": 0.0,  # Free local inference
                "rate_limit": 1000,  # Higher limit for local
                "max_tokens": ollama_config.get("max_tokens", 4000)
            },
            health_check_interval=30,
            enabled=True,
            auto_start=True
        )
        
        ollama_plugin = OllamaServicePlugin(ollama_service_config)
        await service_manager.registry.register_service(ollama_plugin)
        logger.info("Ollama service configured")


async def initialize_integration_services(service_manager):
    """Initialize external integration services."""
    config = get_config_manager()
    
    # DocuSign Integration
    docusign_config = config.get("integrations.docusign", {})
    if docusign_config.get("enabled", False):
        docusign_service_config = ServiceConfig(
            service_id="docusign_service",
            service_type=ServiceType.INTEGRATION,
            name="DocuSign Integration",
            description="DocuSign document signing integration",
            version="1.0.0",
            config={
                "plugin_type": "http",
                "base_url": "https://demo.docusign.net/restapi" if docusign_config.get("sandbox", True) else "https://www.docusign.net/restapi",
                "client_id": docusign_config.get("client_id"),
                "client_secret": docusign_config.get("client_secret"),
                "timeout": docusign_config.get("timeout", 30)
            },
            health_check_url="/v2.1/accounts",
            health_check_interval=300,  # 5 minutes
            enabled=True,
            auto_start=True
        )
        
        from ..services.base_service_plugin import HTTPServicePlugin
        docusign_plugin = HTTPServicePlugin(docusign_service_config)
        await service_manager.registry.register_service(docusign_plugin)
        logger.info("DocuSign service configured")
    
    # Email Service
    email_config = config.get("integrations.email", {})
    if email_config.get("enabled", False):
        email_service_config = ServiceConfig(
            service_id="email_service",
            service_type=ServiceType.INTEGRATION,
            name="Email Service",
            description="SMTP and Gmail email integration",
            version="1.0.0",
            config={
                "plugin_type": "email",
                "smtp_host": email_config.get("smtp", {}).get("host"),
                "smtp_port": email_config.get("smtp", {}).get("port", 587),
                "smtp_username": email_config.get("smtp", {}).get("username"),
                "smtp_password": email_config.get("smtp", {}).get("password"),
                "use_tls": email_config.get("smtp", {}).get("use_tls", True),
                "timeout": email_config.get("smtp", {}).get("timeout", 30)
            },
            health_check_interval=300,
            enabled=True,
            auto_start=True
        )
        
        # Would need to create EmailServicePlugin
        logger.info("Email service configuration prepared")
    
    # Slack Integration
    slack_config = config.get("integrations.slack", {})
    if slack_config.get("enabled", False):
        slack_service_config = ServiceConfig(
            service_id="slack_service",
            service_type=ServiceType.INTEGRATION,
            name="Slack Integration",
            description="Slack notifications and webhooks",
            version="1.0.0",
            config={
                "plugin_type": "http",
                "webhook_url": slack_config.get("webhook_url"),
                "bot_token": slack_config.get("bot_token"),
                "default_channel": slack_config.get("default_channel"),
                "timeout": slack_config.get("timeout", 10)
            },
            health_check_interval=300,
            enabled=True,
            auto_start=True
        )
        
        from ..services.base_service_plugin import HTTPServicePlugin
        slack_plugin = HTTPServicePlugin(slack_service_config)
        await service_manager.registry.register_service(slack_plugin)
        logger.info("Slack service configured")


async def initialize_core_services(service_manager):
    """Initialize core system services."""
    config = get_config_manager()
    
    # Database Service
    database_config = ServiceConfig(
        service_id="database_service",
        service_type=ServiceType.CORE,
        name="Database Service",
        description="Primary database connection and operations",
        version="1.0.0",
        config={
            "plugin_type": "database",
            "database_url": config.get("database.url"),
            "pool_size": config.get("database.pool_size", 10),
            "max_overflow": config.get("database.max_overflow", 20)
        },
        health_check_interval=30,
        enabled=True,
        auto_start=True
    )
    
    # Redis Cache Service
    redis_config = config.get("redis", {})
    if redis_config.get("enabled", False):
        cache_service_config = ServiceConfig(
            service_id="cache_service",
            service_type=ServiceType.CORE,
            name="Redis Cache Service",
            description="Redis caching and session storage",
            version="1.0.0",
            config={
                "plugin_type": "redis",
                "host": redis_config.get("host", "localhost"),
                "port": redis_config.get("port", 6379),
                "db": redis_config.get("db", 0),
                "password": redis_config.get("password"),
                "max_connections": redis_config.get("max_connections", 20)
            },
            health_check_interval=30,
            enabled=True,
            auto_start=True
        )
        
        logger.info("Cache service configuration prepared")


async def initialize_monitoring_services(service_manager):
    """Initialize monitoring and observability services."""
    config = get_config_manager()
    
    monitoring_config = config.get("monitoring", {})
    
    # Prometheus Metrics Service
    if monitoring_config.get("prometheus", False):
        prometheus_service_config = ServiceConfig(
            service_id="prometheus_service",
            service_type=ServiceType.MONITORING,
            name="Prometheus Metrics",
            description="Prometheus metrics collection and exposure",
            version="1.0.0",
            config={
                "plugin_type": "http",
                "base_url": f"http://localhost:{monitoring_config.get('metrics_port', 9090)}",
                "timeout": 10
            },
            health_check_url="/metrics",
            health_check_interval=60,
            enabled=True,
            auto_start=True
        )
        
        from ..services.base_service_plugin import HTTPServicePlugin
        prometheus_plugin = HTTPServicePlugin(prometheus_service_config)
        await service_manager.registry.register_service(prometheus_plugin)
        logger.info("Prometheus service configured")


async def main():
    """Main service initialization function."""
    print("Career Copilot - Service Initialization")
    print("=" * 50)
    
    try:
        # Get service manager
        service_manager = await get_service_manager()
        
        # Initialize different service categories
        print("Initializing LLM services...")
        await initialize_llm_services(service_manager)
        
        print("Initializing integration services...")
        await initialize_integration_services(service_manager)
        
        print("Initializing core services...")
        await initialize_core_services(service_manager)
        
        print("Initializing monitoring services...")
        await initialize_monitoring_services(service_manager)
        
        # Get system health
        health_status = await service_manager.get_system_health()
        
        print("\nService Initialization Summary:")
        print(f"  Total Services: {health_status['total_services']}")
        print(f"  Healthy Services: {health_status['healthy_services']}")
        print(f"  Degraded Services: {health_status['degraded_services']}")
        print(f"  Unhealthy Services: {health_status['unhealthy_services']}")
        print(f"  Overall Status: {health_status['overall_status'].upper()}")
        
        if health_status['overall_status'] in ['healthy', 'degraded']:
            print("\n✓ Service initialization completed successfully!")
            return 0
        else:
            print("\n⚠ Service initialization completed with issues!")
            return 1
            
    except Exception as e:
        print(f"\n✗ Service initialization failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))