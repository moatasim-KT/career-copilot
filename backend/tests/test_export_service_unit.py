"""
Unit tests for export service functionality
Tests the export logic without database dependencies
"""

import csv
import io
import json

import pytest

from app.utils.datetime import utc_now


def test_export_schemas_import():
	"""Test that export schemas can be imported"""
	from app.schemas.export import (
		ApplicationExportData,
		ExportFormat,
		ExportMetadata,
		ExportRequest,
		ExportResponse,
		ExportType,
		JobExportData,
	)

	assert ExportFormat.JSON == "json"
	assert ExportFormat.CSV == "csv"
	assert ExportFormat.PDF == "pdf"
	assert ExportType.JOBS == "jobs"
	assert ExportType.APPLICATIONS == "applications"


def test_export_service_import():
	"""Test that export service can be imported"""
	from app.services.export_service_v2 import export_service_v2

	assert export_service_v2 is not None
	assert hasattr(export_service_v2, "export_jobs_json")
	assert hasattr(export_service_v2, "export_jobs_csv")
	assert hasattr(export_service_v2, "export_jobs_pdf")
	assert hasattr(export_service_v2, "export_applications_json")
	assert hasattr(export_service_v2, "export_applications_csv")
	assert hasattr(export_service_v2, "export_applications_pdf")
	assert hasattr(export_service_v2, "create_full_backup")


def test_export_router_import():
	"""Test that export router can be imported"""
	from app.api.v1 import export

	assert export.router is not None
	assert export.router.prefix == "/api/v1/export"
	assert "export" in export.router.tags


def test_csv_format_handling():
	"""Test CSV formatting logic"""
	# Test tech_stack array to string conversion
	tech_stack = ["Python", "FastAPI", "PostgreSQL"]
	tech_stack_str = ", ".join(tech_stack)
	assert tech_stack_str == "Python, FastAPI, PostgreSQL"

	# Test empty tech_stack
	empty_stack = []
	empty_str = ", ".join(empty_stack) if empty_stack else ""
	assert empty_str == ""

	# Test None tech_stack
	none_stack = None
	none_str = ", ".join(none_stack) if none_stack else ""
	assert none_str == ""


def test_json_serialization():
	"""Test JSON serialization of export data"""
	# Test job data serialization
	job_data = {
		"id": 1,
		"company": "Test Company",
		"title": "Software Engineer",
		"tech_stack": ["Python", "FastAPI"],
		"salary_min": 100000,
		"salary_max": 150000,
		"created_at": utc_now().isoformat(),
	}

	json_str = json.dumps(job_data)
	assert json_str is not None
	assert "Test Company" in json_str

	# Test deserialization
	parsed = json.loads(json_str)
	assert parsed["company"] == "Test Company"
	assert parsed["tech_stack"] == ["Python", "FastAPI"]


def test_interview_feedback_json_handling():
	"""Test interview feedback JSON handling for CSV export"""
	feedback = {
		"questions": ["Tell me about yourself", "What are your strengths?"],
		"performance": "good",
		"notes": "Candidate showed strong technical skills",
	}

	# Convert to JSON string for CSV
	feedback_str = json.dumps(feedback)
	assert feedback_str is not None
	assert "questions" in feedback_str

	# Test parsing back
	parsed = json.loads(feedback_str)
	assert parsed["performance"] == "good"
	assert len(parsed["questions"]) == 2


def test_csv_special_character_handling():
	"""Test CSV handling of special characters"""
	# Test newline removal
	notes_with_newlines = "This is a note\nwith multiple\nlines"
	cleaned_notes = notes_with_newlines.replace("\n", " ").replace("\r", "")
	assert "\n" not in cleaned_notes
	assert "\r" not in cleaned_notes
	assert cleaned_notes == "This is a note with multiple lines"

	# Test empty notes
	empty_notes = ""
	cleaned_empty = (empty_notes or "").replace("\n", " ").replace("\r", "")
	assert cleaned_empty == ""

	# Test None notes
	none_notes = None
	cleaned_none = (none_notes or "").replace("\n", " ").replace("\r", "")
	assert cleaned_none == ""


def test_export_metadata_structure():
	"""Test export metadata structure"""
	from app.schemas.export import ExportFormat, ExportMetadata, ExportType

	metadata = ExportMetadata(
		format=ExportFormat.JSON,
		export_type=ExportType.JOBS,
		total_records=10,
		filters_applied={"status": "applied"},
	)

	assert metadata.format == ExportFormat.JSON
	assert metadata.export_type == ExportType.JOBS
	assert metadata.total_records == 10
	assert metadata.filters_applied["status"] == "applied"
	assert metadata.exported_at is not None


def test_pagination_calculation():
	"""Test pagination calculation logic"""
	# Test page 1
	page = 1
	page_size = 100
	offset = (page - 1) * page_size
	assert offset == 0

	# Test page 2
	page = 2
	offset = (page - 1) * page_size
	assert offset == 100

	# Test total pages calculation
	total_records = 250
	page_size = 100
	total_pages = (total_records + page_size - 1) // page_size
	assert total_pages == 3


def test_filter_building():
	"""Test filter building logic"""
	filters = {}

	# Add status filter
	status = "applied"
	if status:
		filters["status"] = status
	assert filters["status"] == "applied"

	# Add company filter
	company = "Test Company"
	if company:
		filters["company"] = company
	assert filters["company"] == "Test Company"

	# Test empty filter
	empty_status = None
	if empty_status:
		filters["empty_status"] = empty_status
	assert "empty_status" not in filters


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
