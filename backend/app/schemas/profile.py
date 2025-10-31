"""Pydantic schemas for User Profile"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ProfileBase(BaseModel):
	skills: list[str] | None = []
	preferred_locations: list[str] | None = []
	experience_level: Literal["junior", "mid", "senior"] | None = None
	daily_application_goal: int | None = None


class ProfileUpdate(ProfileBase):
	pass


class ProfileResponse(ProfileBase):
	id: int
	username: str
	email: str

	model_config = {"from_attributes": True}
