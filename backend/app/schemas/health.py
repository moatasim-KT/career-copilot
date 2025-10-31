from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
	status: str
	timestamp: datetime
	components: dict[str, Any]


class ComponentHealth(BaseModel):
	status: str
	message: str | None = None
	details: dict[str, Any] | None = None
	response_time_ms: float | None = None


class HealthCheckResponse(BaseModel):
	status: str
	timestamp: datetime
	components: dict[str, ComponentHealth]


class DetailedHealthResponse(BaseModel):
	status: str
	timestamp: datetime
	components: dict[str, ComponentHealth]
	system_info: dict[str, Any] | None = None
	performance_metrics: dict[str, Any] | None = None
