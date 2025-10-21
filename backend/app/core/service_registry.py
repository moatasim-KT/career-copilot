"""
Service Registry for managing service plugins.

This module provides a central registry for discovering, registering,
and managing service plugins within the application.
"""

import asyncio
from typing import Dict, Optional, Type

from ..models.service import ServiceConfig, ServiceStatus
from ..core.service_integration import ServicePlugin
from ..services.base_service_plugin import HTTPServicePlugin
from ..services.llm_service_plugin import OpenAIServicePlugin, GroqServicePlugin, OllamaServicePlugin
from ..core.logging import get_logger

logger = get_logger(__name__)

class ServiceRegistry:
    """A thread-safe registry for managing service plugins."""

    def __init__(self):
        self._services: Dict[str, ServicePlugin] = {}
        self._service_configs: Dict[str, ServiceConfig] = {}
        self._plugin_map: Dict[str, Type[ServicePlugin]] = {
            "HTTPServicePlugin": HTTPServicePlugin,
            "OpenAIServicePlugin": OpenAIServicePlugin,
            "GroqServicePlugin": GroqServicePlugin,
            "OllamaServicePlugin": OllamaServicePlugin,
        }
        self._lock = asyncio.Lock()

    async def register_service(self, config: ServiceConfig):
        """Register a new service with the given configuration."""
        async with self._lock:
            if config.service_id in self._services:
                logger.warning(f"Service '{config.service_id}' is already registered. Updating configuration.")
                await self.update_service_config(config.service_id, config.config)
            else:
                plugin_class = self._plugin_map.get(config.plugin)
                if not plugin_class:
                    raise ValueError(f"Unknown plugin type: {config.plugin}")
                
                self._service_configs[config.service_id] = config
                self._services[config.service_id] = plugin_class(config)
                logger.info(f"Service '{config.service_id}' registered with plugin '{config.plugin}'.")

    async def unregister_service(self, service_id: str):
        """Unregister a service."""
        async with self._lock:
            if service_id in self._services:
                await self.stop_service(service_id)
                del self._services[service_id]
                del self._service_configs[service_id]
                logger.info(f"Service '{service_id}' unregistered.")

    def get_service(self, service_id: str) -> Optional[ServicePlugin]:
        """Get a service instance by its ID."""
        return self._services.get(service_id)

    def get_all_services(self) -> Dict[str, ServicePlugin]:
        """Get all registered services."""
        return self._services

    async def start_service(self, service_id: str) -> bool:
        """Start a specific service."""
        service = self.get_service(service_id)
        if service:
            return await service.start()
        return False

    async def stop_service(self, service_id: str) -> bool:
        """Stop a specific service."""
        service = self.get_service(service_id)
        if service:
            return await service.stop()
        return False

    async def restart_service(self, service_id: str) -> bool:
        """Restart a specific service."""
        await self.stop_service(service_id)
        return await self.start_service(service_id)

    async def get_service_health(self, service_id: str):
        """Get the health of a specific service."""
        service = self.get_service(service_id)
        if service:
            return await service.health_check()
        return None

    async def update_service_config(self, service_id: str, config_data: Dict):
        """Update the configuration of a service."""
        async with self._lock:
            if service_id in self._service_configs:
                # Merge new config data into the existing config
                new_config = self._service_configs[service_id].config.copy()
                new_config.update(config_data)
                self._service_configs[service_id].config = new_config
                
                # Restart the service to apply the new configuration
                await self.restart_service(service_id)
                logger.info(f"Service '{service_id}' configuration updated and restarted.")

    async def shutdown(self):
        """Shutdown all registered services."""
        for service_id in self._services.keys():
            await self.stop_service(service_id)
