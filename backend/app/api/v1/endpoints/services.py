"""
API endpoints for managing services.

This module provides RESTful API endpoints for interacting with the
service integration framework, including listing, retrieving, and managing services.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ....core.service_registry import ServiceRegistry
from ....models.service import Service, ServiceCreate, ServiceUpdate
from ...dependencies import get_service_registry

router = APIRouter()

@router.post("/", response_model=Service, status_code=201)
async def register_service(
    service_create: ServiceCreate,
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Register a new service."""
    # This is a simplified registration. In a real app, you'd have more robust
    # configuration and security around service registration.
    config = ServiceConfig(
        service_id=service_create.service_id,
        plugin=service_create.plugin,
        config=service_create.config,
        priority=service_create.priority,
        metadata=service_create.metadata
    )
    await registry.register_service(config)
    service = await registry.get_service(service_create.service_id)
    if not service:
        raise HTTPException(status_code=500, detail="Failed to register service.")
    health = await service.health_check()
    return Service(service_id=service.service_id, plugin=service.config.plugin, health=health, config=service.config)

@router.get("/", response_model=List[Service])
async def list_services(registry: ServiceRegistry = Depends(get_service_registry)):
    """List all registered services."""
    services = []
    for service in registry.get_all_services().values():
        health = await service.health_check()
        services.append(Service(service_id=service.service_id, plugin=service.config.plugin, health=health, config=service.config))
    return services

@router.get("/{service_id}", response_model=Service)
async def get_service(
    service_id: str,
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get details of a specific service."""
    service = registry.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found.")
    health = await service.health_check()
    return Service(service_id=service.service_id, plugin=service.config.plugin, health=health, config=service.config)

@router.put("/{service_id}", response_model=Service)
async def update_service(
    service_id: str,
    service_update: ServiceUpdate,
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Update the configuration of a service."""
    service = registry.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found.")
    
    await registry.update_service_config(service_id, service_update.config)
    updated_service = registry.get_service(service_id)
    health = await updated_service.health_check()
    return Service(service_id=updated_service.service_id, plugin=updated_service.config.plugin, health=health, config=updated_service.config)

@router.delete("/{service_id}", status_code=204)
async def unregister_service(
    service_id: str,
    registry: ServiceRegistry = Depends(get_service_registry)
):
    """Unregister a service."""
    await registry.unregister_service(service_id)
