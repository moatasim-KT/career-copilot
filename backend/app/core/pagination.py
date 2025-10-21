"""
Pagination utilities for API responses.
"""

from math import ceil
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
	"""Pagination parameters for API requests."""

	page: int = Field(default=1, ge=1, description="Page number (1-based)")
	page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
	sort_by: Optional[str] = Field(default=None, description="Field to sort by")
	sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")

	@property
	def offset(self) -> int:
		"""Calculate offset for database queries."""
		return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
	"""Paginated response model."""

	items: List[T] = Field(description="List of items in current page")
	pagination: Dict[str, Any] = Field(description="Pagination metadata")

	class Config:
		json_encoders = {
			# Add any custom encoders here
		}


class PaginationMetadata(BaseModel):
	"""Pagination metadata."""

	page: int = Field(description="Current page number")
	page_size: int = Field(description="Number of items per page")
	total_items: int = Field(description="Total number of items")
	total_pages: int = Field(description="Total number of pages")
	has_next: bool = Field(description="Whether there is a next page")
	has_previous: bool = Field(description="Whether there is a previous page")
	next_page: Optional[int] = Field(description="Next page number")
	previous_page: Optional[int] = Field(description="Previous page number")


def create_pagination_metadata(page: int, page_size: int, total_items: int) -> PaginationMetadata:
	"""Create pagination metadata."""
	total_pages = ceil(total_items / page_size) if total_items > 0 else 1

	return PaginationMetadata(
		page=page,
		page_size=page_size,
		total_items=total_items,
		total_pages=total_pages,
		has_next=page < total_pages,
		has_previous=page > 1,
		next_page=page + 1 if page < total_pages else None,
		previous_page=page - 1 if page > 1 else None,
	)


def create_paginated_response(items: List[T], pagination_params: PaginationParams, total_items: int) -> PaginatedResponse[T]:
	"""Create a paginated response."""
	pagination_metadata = create_pagination_metadata(pagination_params.page, pagination_params.page_size, total_items)

	return PaginatedResponse(items=items, pagination=pagination_metadata.dict())


class PaginationHelper:
	"""Helper class for pagination operations."""

	@staticmethod
	def apply_sorting(items: List[Dict], sort_by: Optional[str], sort_order: str) -> List[Dict]:
		"""Apply sorting to a list of items."""
		if not sort_by or not items:
			return items

		try:
			reverse = sort_order.lower() == "desc"
			return sorted(items, key=lambda x: x.get(sort_by, ""), reverse=reverse)
		except (KeyError, TypeError):
			# If sorting fails, return original list
			return items

	@staticmethod
	def apply_pagination(items: List[T], pagination_params: PaginationParams) -> List[T]:
		"""Apply pagination to a list of items."""
		start = pagination_params.offset
		end = start + pagination_params.page_size
		return items[start:end]

	@staticmethod
	def paginate_query(query, pagination_params: PaginationParams):
		"""Apply pagination to a SQLAlchemy query."""
		return query.offset(pagination_params.offset).limit(pagination_params.page_size)
