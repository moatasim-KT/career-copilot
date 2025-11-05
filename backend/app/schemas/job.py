"""Job schemas"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class JobCreate(BaseModel):
	company: str = Field(..., min_length=1, description="Company name is required")
	title: str = Field(..., min_length=1, description="Job title is required")
	location: str | None = None
	description: str | None = None
	requirements: str | None = None
	responsibilities: str | None = None
	salary_min: int | None = None
	salary_max: int | None = None
	job_type: str | None = None
	remote_option: str | None = None
	tech_stack: list[str] | None = Field(default_factory=list, description="List of technologies/skills")
	application_url: str | None = None
	notes: str | None = None
	documents_required: list[str] | None = None
	source: str | None = Field(default="manual", description="Source of the job posting")
	currency: str | None = None

	@field_validator("requirements", mode="before")
	@classmethod
	def validate_requirements(cls, v):
		"""Convert dict requirements to JSON string"""
		if v is None:
			return None
		if isinstance(v, dict):
			return json.dumps(v)
		return str(v)

	@field_validator("remote_option", mode="before")
	@classmethod
	def validate_remote_option(cls, v):
		"""Convert boolean remote_option to string"""
		if v is None:
			return None
		if isinstance(v, bool):
			return "yes" if v else "no"
		return str(v)

	@field_validator("tech_stack")
	@classmethod
	def validate_tech_stack(cls, v):
		if v is None:
			return []
		return v

	@field_validator("source")
	@classmethod
	def validate_source(cls, v):
		allowed_sources = ["manual", "scraped", "api", "linkedin", "indeed", "glassdoor", "adzuna", "usajobs", "github_jobs", "remoteok"]
		if v and v not in allowed_sources:
			return "manual"
		return v or "manual"


class JobUpdate(BaseModel):
	company: str | None = Field(None, min_length=1)
	title: str | None = Field(None, min_length=1)
	location: str | None = None
	description: str | None = None
	requirements: str | None = None
	responsibilities: str | None = None
	salary_min: int | None = None
	salary_max: int | None = None
	job_type: str | None = None
	remote_option: str | None = None
	tech_stack: list[str] | None = None
	application_url: str | None = None
	source: str | None = None
	status: str | None = None
	date_applied: datetime | None = None
	notes: str | None = None
	documents_required: list[str] | None = None

	@field_validator("source")
	@classmethod
	def validate_source(cls, v):
		if v is not None:
			allowed_sources = ["manual", "scraped", "api", "linkedin", "indeed", "glassdoor", "adzuna", "usajobs", "github_jobs", "remoteok"]
			if v not in allowed_sources:
				raise ValueError(f"Source must be one of: {', '.join(allowed_sources)}")
		return v

	@field_validator("status")
	@classmethod
	def validate_status(cls, v):
		if v is not None:
			allowed_statuses = ["not_applied", "applied", "interviewing", "offer", "rejected"]
			if v not in allowed_statuses:
				raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
		return v


class JobResponse(BaseModel):
	id: int
	user_id: int
	company: str
	title: str
	location: str | None
	description: str | None
	requirements: str | None
	responsibilities: str | None
	salary_min: int | None
	salary_max: int | None
	job_type: str | None
	remote_option: str | None
	tech_stack: list[str] | None
	documents_required: list[str] | None
	application_url: str | None
	source: str | None
	status: str
	date_applied: datetime | None
	notes: str | None
	created_at: datetime
	updated_at: datetime
	currency: str | None
