"""
Service Models for the Service Integration Framework.

This module defines the Pydantic models for representing services,
their status, health, and other related data structures.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
import datetime

class ServiceStatus(str, Enum):
    """Enum for service status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    STARTING = "starting"
    STOPPED = "stopped"
    ERROR = "error"

class ServiceHealth(BaseModel):
    """Model for service health information."""
    status: ServiceStatus = Field(..., description="Current status of the service.")
    last_check: datetime.datetime = Field(..., description="Timestamp of the last health check.")
    response_time: float = Field(..., description="Response time of the health check in seconds.")
    error_message: Optional[str] = Field(None, description="Error message if the service is unhealthy.")
    details: Dict[str, Any] = Field({}, description="Additional health check details.")

class ServiceConfig(BaseModel):
    """Model for service configuration."""
    service_id: str = Field(..., description="Unique identifier for the service.")
    plugin: str = Field(..., description="Plugin name to use for the service.")
    config: Dict[str, Any] = Field({}, description="Service-specific configuration.")
    priority: int = Field(10, description="Priority for service selection (lower is higher).")
    health_check_url: Optional[str] = Field(None, description="URL for health checks.")
    health_check_interval: int = Field(60, description="Interval for health checks in seconds.")
    metadata: Dict[str, Any] = Field({}, description="Additional service metadata.")

class Service(BaseModel):
    """Model representing a registered service."""
    service_id: str = Field(..., description="Unique identifier for the service.")
    plugin: str = Field(..., description="Plugin name of the service.")
    health: ServiceHealth = Field(..., description="Health status of the service.")
    config: ServiceConfig = Field(..., description="Configuration of the service.")
    
class ServiceCreate(BaseModel):
    """Model for creating a new service."""
    service_id: str
    plugin: str
    config: Dict[str, Any]
    priority: Optional[int] = 10
    metadata: Optional[Dict[str, Any]] = {}

class ServiceUpdate(BaseModel):
    """Model for updating an existing service."""
    config: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
