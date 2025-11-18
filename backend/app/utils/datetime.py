"""Time utilities for timezone-aware timestamps."""

from __future__ import annotations

from datetime import date, datetime, timezone


def utc_now() -> datetime:
	"""Return the current UTC time as a timezone-naive datetime.

	Returns naive datetime to match PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns.
	All timestamps are implicitly UTC.
	"""
	return datetime.utcnow()


def utc_today() -> date:
	"""Return today's date in UTC."""
	return utc_now().date()
