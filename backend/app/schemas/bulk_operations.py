"""Bulk operations schemas for jobs and applications"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .application import ApplicationCreate, ApplicationUpdate
from .job import JobCreate, JobUpdate


# Bulk Create Schemas
class BulkJobCreateRequest(BaseModel):
    """Request schema for bulk job creation"""
    jobs: List[JobCreate] = Field(..., min_length=1, max_length=1000, description="List of jobs to create (max 1000)")


class BulkApplicationCreateRequest(BaseModel):
    """Request schema for bulk application creation"""
    applications: List[ApplicationCreate] = Field(..., min_length=1, max_length=1000, description="List of applications to create (max 1000)")


# Bulk Update Schemas
class JobUpdateWithId(BaseModel):
    """Job update with ID"""
    id: int = Field(..., description="Job ID to update")
    data: JobUpdate = Field(..., description="Job update data")


class ApplicationUpdateWithId(BaseModel):
    """Application update with ID"""
    id: int = Field(..., description="Application ID to update")
    data: ApplicationUpdate = Field(..., description="Application update data")


class BulkJobUpdateRequest(BaseModel):
    """Request schema for bulk job updates"""
    updates: List[JobUpdateWithId] = Field(..., min_length=1, max_length=1000, description="List of job updates (max 1000)")


class BulkApplicationUpdateRequest(BaseModel):
    """Request schema for bulk application updates"""
    updates: List[ApplicationUpdateWithId] = Field(..., min_length=1, max_length=1000, description="List of application updates (max 1000)")


# Bulk Delete Schemas
class BulkDeleteRequest(BaseModel):
    """Request schema for bulk delete operations"""
    ids: List[int] = Field(..., min_length=1, max_length=1000, description="List of IDs to delete (max 1000)")
    soft_delete: bool = Field(default=False, description="If true, mark as deleted instead of removing from database")


# Response Schemas
class OperationError(BaseModel):
    """Error details for a failed operation"""
    index: int = Field(..., description="Index of the item in the request array")
    id: Optional[int] = Field(None, description="ID of the item if available")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class BulkCreateResult(BaseModel):
    """Result of bulk create operation"""
    total: int = Field(..., description="Total number of items in request")
    successful: int = Field(..., description="Number of successfully created items")
    failed: int = Field(..., description="Number of failed items")
    created_ids: List[int] = Field(default_factory=list, description="IDs of successfully created items")
    errors: List[OperationError] = Field(default_factory=list, description="Details of failed operations")


class BulkUpdateResult(BaseModel):
    """Result of bulk update operation"""
    total: int = Field(..., description="Total number of items in request")
    successful: int = Field(..., description="Number of successfully updated items")
    failed: int = Field(..., description="Number of failed items")
    updated_ids: List[int] = Field(default_factory=list, description="IDs of successfully updated items")
    errors: List[OperationError] = Field(default_factory=list, description="Details of failed operations")


class BulkDeleteResult(BaseModel):
    """Result of bulk delete operation"""
    total: int = Field(..., description="Total number of items in request")
    successful: int = Field(..., description="Number of successfully deleted items")
    failed: int = Field(..., description="Number of failed items")
    deleted_ids: List[int] = Field(default_factory=list, description="IDs of successfully deleted items")
    soft_deleted: bool = Field(..., description="Whether soft delete was used")
    errors: List[OperationError] = Field(default_factory=list, description="Details of failed operations")
