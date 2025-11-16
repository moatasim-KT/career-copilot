"""
Dashboard Layout Schemas
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DashboardLayoutBase(BaseModel):
    """Base dashboard layout schema"""

    layout_config: Dict[str, Any] = Field(
        ...,
        description="Dashboard configuration including widgets, positions, and settings",
    )


class DashboardLayoutCreate(DashboardLayoutBase):
    """Create dashboard layout"""

    pass


class DashboardLayoutUpdate(BaseModel):
    """Update dashboard layout (partial)"""

    layout_config: Optional[Dict[str, Any]] = None


class DashboardLayoutResponse(DashboardLayoutBase):
    """Dashboard layout response"""

    id: Optional[int] = None
    user_id: int
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
