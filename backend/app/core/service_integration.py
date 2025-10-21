"""
Service Integration Framework for Production-Ready Architecture.

This module provides a comprehensive framework for integrating and managing
services in a production environment with plugin architecture, service discovery,
health monitoring, and intelligent routing capabilities.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from .config_manager import get_config_manager
from .logging import get_logger

logger = get_logger(__name__)


class ServiceStatus(str, Enum):
    """Service status enumeration."""
    UNKNOWN = "unknown"
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"
    ERROR = "error"


class ServiceType(str, Enum):
    """Service type enumeration."""
    CORE = "core"
    AI_PROVIDER = "ai_provider"
    INTEGRATION = "integration"
    STORAGE = "storage"
    MONITORING = "monitoring"
    UTILITY = "utility"


@dataclass
class ServiceHealth:
    """Service health information."""
    status: ServiceStatus
    last_check: datetime
    response_time: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]


@dataclass
class ServiceMetrics:
    """Service performance metrics."""
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.request_count == 0:
            return 100.0
        return (self.success_count / self.request_count) * 100.0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        if self.request_count == 0:
            return 0.0
        return (self.error_count / self.request_count) * 100.0


@dataclass
class ServiceConfig:
    """Service configuration."""
    service_id: str
    service_type: ServiceType
    name: str
    description: str
    version: str
    config: Dict[str, Any] = field(default_factory=dict)
    health_check_url: Optional[str] = None
    health_check_interval: int = 30
    dependencies: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    auto_start: bool = True
    retry_attempts: int = 3
    timeout: int = 30


class ServicePlugin(ABC):
    """Abstract base class for service plugins."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.metrics = ServiceMetrics()
        self._health = ServiceHealth(
            status=ServiceStatus.UNKNOWN,
            last_check=datetime.now(),
            response_time=0.0
        )
        self._start_time = None
        self._callbacks: Dict[str, List[Callable]] = {
            'on_start': [],
            'on_stop': [],
            'on_health_change': [],
            'on_error': []
        }
    
    @property
    def service_id(self) -> str:
        """Get service ID."""
        return self.config.service_id
    
    @property
    def health(self) -> ServiceHealth:
        """Get current health status."""
        return self._health
    
    @abstractmethod
    async def start(self) -> bool:
        """Start the service."""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """Stop the service."""
        pass
    
    @abstractmethod
    async def health_check(self) -> ServiceHealth:
        """Perform health check."""
        pass
    
    async def initialize(self) -> bool:
        """Initialize the service."""
        try:
            logger.info(f"Initializing service: {self.service_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize service {self.service_id}: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup service resources."""
        try:
            logger.info(f"Cleaning up service: {self.service_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup service {self.service_id}: {e}")
            return False
    
    def add_callback(self, event: str, callback: Callable):
        """Add event callback."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    async def _trigger_callbacks(self, event: str, *args, **kwargs):
        """Trigger event callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self, *args, **kwargs)
                else:
                    callback(self, *args, **kwargs)
            except Exception as e:
                logger.error(f"Callback error for {event} on {self.service_id}: {e}")
    
    def update_metrics(self, success: bool, response_time: float):
        """Update service metrics."""
        self.metrics.request_count += 1
        self.metrics.last_request_time = datetime.now()
        
        if success:
            self.metrics.success_count += 1
        else:
            self.metrics.error_count += 1
        
        # Update average response time
        if self.metrics.request_count == 1:
            self.metrics.avg_response_time = response_time
        else:
            self.metrics.avg_response_time = (
                (self.metrics.avg_response_time * (self.metrics.request_count - 1) + response_time) /
                self.metrics.request_count
            )
        
        # Update uptime
        if self._start_time:
            self.metrics.uptime_seconds = (datetime.now() - self._start_time).total_seconds()
    
    async def _update_health(self, status: ServiceStatus, response_time: float = 0.0, 
                           error_message: Optional[str] = None, details: Optional[Dict] = None):
        """Update health status."""
        old_status = self._health.status
        
        self._health = ServiceHealth(
            status=status,
            last_check=datetime.now(),
            response_time=response_time,
            error_message=error_message,
            details=details or {}
        )
        
        # Trigger health change callback if status changed
        if old_status != status:
            await self._trigger_callbacks('on_health_change', old_status, status)


class ServiceRegistry:
    """Service registry for managing service instances."""
    
    def __init__(self):
        self._services: Dict[str, ServicePlugin] = {}
        self._service_configs: Dict[str, ServiceConfig] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._dependents: Dict[str, Set[str]] = {}
        self._health_check_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
    
    async def register_service(self, service: ServicePlugin) -> bool:
        """Register a service."""
        async with self._lock:
            service_id = service.service_id
            
            if service_id in self._services:
                logger.warning(f"Service {service_id} already registered")
                return False
            
            try:
                # Initialize service
                if not await service.initialize():
                    logger.error(f"Failed to initialize service: {service_id}")
                    return False
                
                # Register service
                self._services[service_id] = service
                self._service_configs[service_id] = service.config
                
                # Build dependency graph
                self._dependencies[service_id] = set(service.config.dependencies)
                for dep in service.config.dependencies:
                    if dep not in self._dependents:
                        self._dependents[dep] = set()
                    self._dependents[dep].add(service_id)
                
                # Start health monitoring
                if service.config.health_check_interval > 0:
                    self._health_check_tasks[service_id] = asyncio.create_task(
                        self._health_monitor(service)
                    )
                
                logger.info(f"Service registered: {service_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to register service {service_id}: {e}")
                return False
    
    async def unregister_service(self, service_id: str) -> bool:
        """Unregister a service."""
        async with self._lock:
            if service_id not in self._services:
                logger.warning(f"Service {service_id} not found")
                return False
            
            try:
                service = self._services[service_id]
                
                # Stop health monitoring
                if service_id in self._health_check_tasks:
                    self._health_check_tasks[service_id].cancel()
                    del self._health_check_tasks[service_id]
                
                # Stop service
                await service.stop()
                await service.cleanup()
                
                # Remove from registry
                del self._services[service_id]
                del self._service_configs[service_id]
                
                # Update dependency graph
                if service_id in self._dependencies:
                    del self._dependencies[service_id]
                
                for dep_set in self._dependents.values():
                    dep_set.discard(service_id)
                
                if service_id in self._dependents:
                    del self._dependents[service_id]
                
                logger.info(f"Service unregistered: {service_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unregister service {service_id}: {e}")
                return False
    
    def get_service(self, service_id: str) -> Optional[ServicePlugin]:
        """Get service by ID."""
        return self._services.get(service_id)
    
    def list_services(self, service_type: Optional[ServiceType] = None, 
                     status: Optional[ServiceStatus] = None) -> List[ServicePlugin]:
        """List services with optional filtering."""
        services = list(self._services.values())
        
        if service_type:
            services = [s for s in services if s.config.service_type == service_type]
        
        if status:
            services = [s for s in services if s.health.status == status]
        
        return services
    
    def get_service_dependencies(self, service_id: str) -> Set[str]:
        """Get service dependencies."""
        return self._dependencies.get(service_id, set())
    
    def get_service_dependents(self, service_id: str) -> Set[str]:
        """Get services that depend on this service."""
        return self._dependents.get(service_id, set())
    
    async def start_service(self, service_id: str) -> bool:
        """Start a service and its dependencies."""
        if service_id not in self._services:
            logger.error(f"Service not found: {service_id}")
            return False
        
        # Start dependencies first
        for dep_id in self._dependencies.get(service_id, set()):
            if dep_id in self._services:
                dep_service = self._services[dep_id]
                if dep_service.health.status != ServiceStatus.HEALTHY:
                    if not await self.start_service(dep_id):
                        logger.error(f"Failed to start dependency {dep_id} for {service_id}")
                        return False
        
        # Start the service
        service = self._services[service_id]
        try:
            if await service.start():
                service._start_time = datetime.now()
                await service._trigger_callbacks('on_start')
                logger.info(f"Service started: {service_id}")
                return True
            else:
                logger.error(f"Failed to start service: {service_id}")
                return False
        except Exception as e:
            logger.error(f"Error starting service {service_id}: {e}")
            await service._trigger_callbacks('on_error', e)
            return False
    
    async def stop_service(self, service_id: str, stop_dependents: bool = True) -> bool:
        """Stop a service and optionally its dependents."""
        if service_id not in self._services:
            logger.error(f"Service not found: {service_id}")
            return False
        
        # Stop dependents first if requested
        if stop_dependents:
            for dependent_id in self._dependents.get(service_id, set()):
                if dependent_id in self._services:
                    await self.stop_service(dependent_id, stop_dependents=True)
        
        # Stop the service
        service = self._services[service_id]
        try:
            if await service.stop():
                await service._trigger_callbacks('on_stop')
                logger.info(f"Service stopped: {service_id}")
                return True
            else:
                logger.error(f"Failed to stop service: {service_id}")
                return False
        except Exception as e:
            logger.error(f"Error stopping service {service_id}: {e}")
            await service._trigger_callbacks('on_error', e)
            return False
    
    async def _health_monitor(self, service: ServicePlugin):
        """Monitor service health."""
        while True:
            try:
                await asyncio.sleep(service.config.health_check_interval)
                
                if service.service_id not in self._services:
                    break  # Service was unregistered
                
                # Perform health check
                start_time = time.time()
                health = await service.health_check()
                response_time = time.time() - start_time
                
                # Update health with response time
                await service._update_health(
                    health.status,
                    response_time,
                    health.error_message,
                    health.details
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {service.service_id}: {e}")
                await service._update_health(
                    ServiceStatus.ERROR,
                    error_message=str(e)
                )
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        services_by_status = {}
        total_services = len(self._services)
        
        for service in self._services.values():
            status = service.health.status.value
            if status not in services_by_status:
                services_by_status[status] = 0
            services_by_status[status] += 1
        
        healthy_count = services_by_status.get(ServiceStatus.HEALTHY.value, 0)
        degraded_count = services_by_status.get(ServiceStatus.DEGRADED.value, 0)
        unhealthy_count = services_by_status.get(ServiceStatus.UNHEALTHY.value, 0)
        
        # Determine overall system status
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        elif healthy_count == total_services:
            overall_status = "healthy"
        else:
            overall_status = "unknown"
        
        return {
            "overall_status": overall_status,
            "total_services": total_services,
            "healthy_services": healthy_count,
            "degraded_services": degraded_count,
            "unhealthy_services": unhealthy_count,
            "services_by_status": services_by_status,
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Shutdown all services."""
        logger.info("Shutting down service registry...")
        
        # Cancel all health check tasks
        for task in self._health_check_tasks.values():
            task.cancel()
        
        # Stop all services in reverse dependency order
        service_ids = list(self._services.keys())
        for service_id in reversed(service_ids):
            await self.stop_service(service_id, stop_dependents=False)
        
        # Clear registry
        self._services.clear()
        self._service_configs.clear()
        self._dependencies.clear()
        self._dependents.clear()
        self._health_check_tasks.clear()
        
        logger.info("Service registry shutdown complete")


class ServiceDiscovery:
    """Service discovery mechanism."""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.config = get_config_manager()
        self._discovery_plugins: List[Callable] = []
    
    def add_discovery_plugin(self, plugin: Callable):
        """Add a service discovery plugin."""
        self._discovery_plugins.append(plugin)
    
    async def discover_services(self) -> List[ServiceConfig]:
        """Discover available services."""
        discovered_services = []
        
        # Run all discovery plugins
        for plugin in self._discovery_plugins:
            try:
                services = await plugin()
                if isinstance(services, list):
                    discovered_services.extend(services)
            except Exception as e:
                logger.error(f"Service discovery plugin error: {e}")
        
        # Discover from configuration
        config_services = await self._discover_from_config()
        discovered_services.extend(config_services)
        
        return discovered_services
    
    async def _discover_from_config(self) -> List[ServiceConfig]:
        """Discover services from configuration."""
        services = []
        
        # Get service configurations from config manager
        services_config = self.config.get("services", {})
        
        for service_id, service_data in services_config.items():
            try:
                service_config = ServiceConfig(
                    service_id=service_id,
                    service_type=ServiceType(service_data.get("type", "utility")),
                    name=service_data.get("name", service_id),
                    description=service_data.get("description", ""),
                    version=service_data.get("version", "1.0.0"),
                    config=service_data.get("config", {}),
                    health_check_url=service_data.get("health_check_url"),
                    health_check_interval=service_data.get("health_check_interval", 30),
                    dependencies=service_data.get("dependencies", []),
                    tags=service_data.get("tags", {}),
                    enabled=service_data.get("enabled", True),
                    auto_start=service_data.get("auto_start", True),
                    retry_attempts=service_data.get("retry_attempts", 3),
                    timeout=service_data.get("timeout", 30)
                )
                services.append(service_config)
                
            except Exception as e:
                logger.error(f"Failed to parse service config for {service_id}: {e}")
        
        return services


class ServiceLoadBalancer:
    """Load balancer for service requests."""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._strategies = {
            "round_robin": self._round_robin,
            "least_connections": self._least_connections,
            "health_based": self._health_based,
            "random": self._random
        }
        self._round_robin_counters: Dict[str, int] = {}
    
    async def get_service_instance(self, service_type: ServiceType, 
                                 strategy: str = "health_based") -> Optional[ServicePlugin]:
        """Get a service instance using the specified load balancing strategy."""
        services = self.registry.list_services(service_type=service_type)
        healthy_services = [s for s in services if s.health.is_healthy()]
        
        if not healthy_services:
            logger.warning(f"No healthy services available for type: {service_type}")
            return None
        
        if len(healthy_services) == 1:
            return healthy_services[0]
        
        strategy_func = self._strategies.get(strategy, self._health_based)
        return await strategy_func(healthy_services)
    
    async def _round_robin(self, services: List[ServicePlugin]) -> ServicePlugin:
        """Round-robin load balancing."""
        service_type = services[0].config.service_type.value
        
        if service_type not in self._round_robin_counters:
            self._round_robin_counters[service_type] = 0
        
        index = self._round_robin_counters[service_type] % len(services)
        self._round_robin_counters[service_type] += 1
        
        return services[index]
    
    async def _least_connections(self, services: List[ServicePlugin]) -> ServicePlugin:
        """Least connections load balancing."""
        return min(services, key=lambda s: s.metrics.request_count)
    
    async def _health_based(self, services: List[ServicePlugin]) -> ServicePlugin:
        """Health-based load balancing (prefer faster response times)."""
        return min(services, key=lambda s: s.health.response_time)
    
    async def _random(self, services: List[ServicePlugin]) -> ServicePlugin:
        """Random load balancing."""
        import random
        return random.choice(services)


# Global service registry instance
service_registry = ServiceRegistry()
service_discovery = ServiceDiscovery(service_registry)
service_load_balancer = ServiceLoadBalancer(service_registry)


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    return service_registry


def get_service_discovery() -> ServiceDiscovery:
    """Get the global service discovery instance."""
    return service_discovery


def get_service_load_balancer() -> ServiceLoadBalancer:
    """Get the global service load balancer instance."""
    return service_load_balancer