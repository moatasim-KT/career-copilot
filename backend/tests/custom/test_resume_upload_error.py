"""Test for resume upload error scenario.

This test verifies that the system properly handles errors when the
ResumeParserService is missing expected methods (like validate_resume_file).
This simulates a scenario where stale code might cause runtime errors.
"""

import io
import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import create_app


def override_get_db(db: Session):
	"""Override the get_db dependency for testing."""
	try:
		yield db
	finally:
		db.close()


@pytest.fixture(scope="module")
def client_fixture(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="module")
def access_token(client_fixture):
    response = client_fixture.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser_resume",
            "email": "resume@example.com",
            "password": "testpassword123",
        },
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    elif response.status_code == 400:
        response = client_fixture.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser_resume",
                "password": "testpassword123",
            },
        )
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to create or login test user: {response.text}")


class DummyResumeParserService:
	"""Dummy ResumeParserService that is MISSING the validate_resume_file method.

	This simulates a scenario where the code might be out of sync,
	such as during hot-reloading issues or version mismatches.
	"""

	__version__ = "0.0.1-broken"

	def __init__(self):
		pass

	# Intentionally NOT implementing validate_resume_file
	# This will cause an AttributeError when the endpoint tries to call it

	def parse_resume_sync(self, file_path: str, filename: str, user_id: int):
		"""Dummy parse method."""
		return {
			"filename": filename,
			"user_id": user_id,
			"skills": [],
			"experience_level": "junior",
		}


class TestResumeUploadError:
	"""Test cases for resume upload error handling."""

	def test_upload_resume_with_broken_parser_service(self, client_fixture, access_token):
		"""Test that upload fails gracefully when ResumeParserService is missing validate_resume_file."""

		# Create a dummy PDF file for testing
		pdf_content = b"%PDF-1.4\n%Test PDF content\nThis is a test resume.\nSkills: Python, JavaScript"

		# Mock the resume_parser in the resume module with our broken service
		with patch("backend.app.api.v1.resume.resume_parser", DummyResumeParserService()):
			# Create file-like object
			files = {"file": ("test_resume.pdf", io.BytesIO(pdf_content), "application/pdf")}

			# Attempt to upload the resume
			response = client_fixture.post(
				"/api/v1/resume/upload",
				files=files,
				headers={"Authorization": f"Bearer {access_token}"},
			)

			# The endpoint should return a 500 error because validate_resume_file doesn't exist
			# This tests that the error is properly caught and reported
			assert response.status_code == 500, f"Expected 500 error, got {response.status_code}: {response.text}"

			# Check that error message indicates an internal server error
			data = response.json()
			assert "detail" in data
			# The error should mention internal server error
			assert "Internal server error" in data["detail"]

	def test_upload_resume_with_real_parser_service(self, client_fixture, access_token):
		"""Test that upload works correctly with the real ResumeParserService."""

		# Create a temporary PDF file for testing
		with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
			tmp_file.write(b"%PDF-1.4\n%Test PDF\nJohn Doe\njohn@example.com\nSkills: Python, Testing")
			tmp_file_path = tmp_file.name

		try:
			# Open the file and upload it
			with open(tmp_file_path, "rb") as f:
				files = {"file": ("test_resume.pdf", f, "application/pdf")}

				# Upload with the REAL ResumeParserService (no mocking)
				response = client_fixture.post(
					"/api/v1/resume/upload",
					files=files,
					headers={"Authorization": f"Bearer {access_token}"},
				)

			# With the real service, upload should succeed (or fail with a proper validation error)
			# Not a 500 internal server error due to missing method
			assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}: {response.text}"

			if response.status_code == 200:
				data = response.json()
				assert "upload_id" in data
				assert data["parsing_status"] == "pending"

		finally:
			# Clean up temporary file
			if os.path.exists(tmp_file_path):
				os.remove(tmp_file_path)
