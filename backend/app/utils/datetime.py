"""Time utilities for timezone-aware timestamps."""

from __future__ import annotations

from datetime import date, datetime, timezone


def utc_now() -> datetime:
	"""Return the current UTC time as a timezone-aware datetime."""
	return datetime.now(timezone.utc)


def utc_today() -> date:
	"""Return today's date in UTC."""
	return utc_now().date()
