"""
Service Manager for proactive health monitoring.

This module provides a background task manager for periodically checking
the health of all registered services and updating their status.
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from .service_integration import ServiceRegistry
from .logging import get_logger

logger = get_logger(__name__)


class ServiceManager:
    """Manages periodic health checks for all registered services."""

    def __init__(self, check_interval: int = 60):
        self._registry: Optional[ServiceRegistry] = None
        self._check_interval = check_interval
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._initialized = False
        self._service_plugins = {}

    async def initialize(self) -> bool:
        """Initialize the service manager."""
        try:
            from .service_integration import get_service_registry
            self._registry = get_service_registry()
            self._initialized = True
            logger.info("Service manager initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize service manager: {e}")
            return False

    async def shutdown(self):
        """Shutdown the service manager."""
        if self._is_running:
            self.stop()
        self._initialized = False
        logger.info("Service manager shutdown complete")

    def register_service_plugin(self, name: str, plugin_class):
        """Register a service plugin class."""
        self._service_plugins[name] = plugin_class
        logger.info(f"Registered service plugin: {name}")

    async def start_service(self, service_id: str) -> bool:
        """Start a specific service."""
        if not self._registry:
            return False
        return await self._registry.start_service(service_id)

    async def run_health_checks(self) -> Dict[str, Any]:
        """Run health checks on all services and return individual service health."""
        if not self._registry:
            return {}
        
        health_results = {}
        
        # Use the correct method based on the registry type
        services = {}
        if hasattr(self._registry, 'get_all_services'):
            # This is the service_registry.ServiceRegistry
            services = self._registry.get_all_services()
        elif hasattr(self._registry, '_services'):
            # This is the service_integration.ServiceRegistry
            services = self._registry._services
        
        for service_id, service in services.items():
            try:
                health = await service.health_check()
                health_results[service_id] = {
                    "status": health.status.value,
                    "last_check": health.last_check.isoformat(),
                    "response_time": health.response_time,
                    "error_message": health.error_message,
                    "details": health.details
                }
            except Exception as e:
                logger.error(f"Health check failed for service {service_id}: {e}")
                health_results[service_id] = {
                    "status": "error",
                    "last_check": datetime.utcnow().isoformat(),
                    "response_time": 0.0,
                    "error_message": str(e),
                    "details": {}
                }
        
        return health_results

    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get metrics for all services."""
        if not self._registry:
            return {}
        
        metrics_results = {}
        
        # Use the correct method based on the registry type
        services = {}
        if hasattr(self._registry, 'get_all_services'):
            # This is the service_registry.ServiceRegistry
            services = self._registry.get_all_services()
        elif hasattr(self._registry, '_services'):
            # This is the service_integration.ServiceRegistry
            services = self._registry._services
        
        for service_id, service in services.items():
            try:
                metrics = service.metrics
                metrics_results[service_id] = {
                    "request_count": metrics.request_count,
                    "success_count": metrics.success_count,
                    "error_count": metrics.error_count,
                    "success_rate": metrics.success_rate,
                    "error_rate": metrics.error_rate,
                    "avg_response_time": metrics.avg_response_time,
                    "uptime_seconds": metrics.uptime_seconds,
                    "last_request_time": metrics.last_request_time.isoformat() if metrics.last_request_time else None
                }
            except Exception as e:
                logger.error(f"Failed to get metrics for service {service_id}: {e}")
                metrics_results[service_id] = {
                    "request_count": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "success_rate": 0.0,
                    "error_rate": 0.0,
                    "avg_response_time": 0.0,
                    "uptime_seconds": 0.0,
                    "last_request_time": None
                }
        
        return metrics_results

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        if not self._registry:
            return {}
        return await self._registry.get_system_health()

    async def stop_service(self, service_id: str) -> bool:
        """Stop a specific service."""
        if not self._registry:
            return False
        return await self._registry.stop_service(service_id)

    @property
    def registry(self) -> Optional[ServiceRegistry]:
        """Get the service registry."""
        return self._registry

    async def _monitor_health(self):
        """Periodically check the health of all services."""
        while self._is_running:
            try:
                if self._registry:
                    # Use the correct method based on the registry type
                    if hasattr(self._registry, 'get_all_services'):
                        # This is the service_registry.ServiceRegistry
                        services = self._registry.get_all_services()
                        for service_id, service in services.items():
                            health = await service.health_check()
                            logger.debug(f"Health check for '{service_id}': {health.status.value}")
                    elif hasattr(self._registry, '_services'):
                        # This is the service_integration.ServiceRegistry
                        services = self._registry._services
                        for service_id, service in services.items():
                            health = await service.health_check()
                            logger.debug(f"Health check for '{service_id}': {health.status.value}")
                    else:
                        logger.warning("Registry does not have expected methods for health monitoring")
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during health monitoring: {e}")

    def start(self):
        """Start the health monitoring background task."""
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._monitor_health())
            logger.info("Service health manager started.")

    def stop(self):
        """Stop the health monitoring background task."""
        if self._is_running and self._task:
            self._is_running = False
            self._task.cancel()


# Global service manager instance
_service_manager: Optional[ServiceManager] = None


async def get_service_manager() -> ServiceManager:
    """Get the global service manager instance."""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
        await _service_manager.initialize()
    return _service_manager
