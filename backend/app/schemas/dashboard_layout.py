from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DashboardWidgetBase(BaseModel):
	id: str
	type: str = Field(..., regex="^(stats|chart|list|progress|calendar|quick-actions)$")
	title: str = Field(..., min_length=1, max_length=255)
	size: str = Field(..., regex="^(small|medium|large)$")
	position: Dict[str, int] = Field(default_factory=dict)
	visible: bool = True
	config: Dict[str, Any] = Field(default_factory=dict)


class DashboardLayoutBase(BaseModel):
	name: str = Field(..., min_length=1, max_length=255)
	widgets: List[DashboardWidgetBase] = Field(default_factory=list)
	is_default: bool = False


class DashboardLayoutCreate(DashboardLayoutBase):
	pass


class DashboardLayoutUpdate(BaseModel):
	name: Optional[str] = Field(None, min_length=1, max_length=255)
	widgets: Optional[List[DashboardWidgetBase]] = None
	is_default: Optional[bool] = None


class DashboardLayoutResponse(DashboardLayoutBase):
	id: str
	user_id: int
	created_at: datetime
	updated_at: datetime

	# Pydantic v2 configuration
	model_config = ConfigDict(from_attributes=True)
	model_config = ConfigDict(from_attributes=True)
