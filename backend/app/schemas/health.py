from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    components: Dict[str, Any]

class ComponentHealth(BaseModel):
    status: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[float] = None

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    components: Dict[str, ComponentHealth]

class DetailedHealthResponse(BaseModel):
    status: str
    timestamp: datetime
    components: Dict[str, ComponentHealth]
    system_info: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
