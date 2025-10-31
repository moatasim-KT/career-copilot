from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SavedSearchBase(BaseModel):
	name: str = Field(..., min_length=1, max_length=255)
	filters: dict[str, Any] = Field(default_factory=dict)
	is_default: bool = False


class SavedSearchCreate(SavedSearchBase):
	pass


class SavedSearchUpdate(BaseModel):
	name: str | None = Field(None, min_length=1, max_length=255)
	filters: dict[str, Any] | None = None
	is_default: bool | None = None


class SavedSearchResponse(SavedSearchBase):
	id: str
	user_id: int
	created_at: datetime
	updated_at: datetime
	last_used: datetime

	class Config:
		from_attributes = True
