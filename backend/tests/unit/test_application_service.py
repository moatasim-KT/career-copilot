"""
Comprehensive unit tests for ApplicationService.
Target: Achieve 60%+ coverage for application_service.py
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.document import Document
from app.schemas.document import DocumentAssociation
from app.services.application_service import ApplicationService


@pytest.fixture
def mock_db():
	"""Create a mock database session"""
	return Mock(spec=Session)


@pytest.fixture
def application_service(mock_db):
	"""Create ApplicationService instance with mock database"""
	return ApplicationService(mock_db)


@pytest.fixture
def sample_application():
	"""Create a sample application with documents"""
	return Application(
		id=1,
		user_id=1,
		job_id=100,
		status="applied",
		documents=[
			{"document_id": 1, "type": "resume", "filename": "resume.pdf", "uploaded_at": "2024-01-15T10:00:00"},
			{"document_id": 2, "type": "cover_letter", "filename": "cover.pdf", "uploaded_at": "2024-01-15T10:05:00"},
		],
		created_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
		updated_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
	)


class TestGetApplication:
	"""Tests for get_application method"""

	def test_get_application_success(self, application_service, mock_db, sample_application):
		"""Test successfully retrieving an application"""
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.return_value = sample_application

		result = application_service.get_application(1, 1)

		assert result == sample_application
		mock_db.query.assert_called_once_with(Application)

	def test_get_application_not_found(self, application_service, mock_db):
		"""Test retrieving non-existent application"""
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.return_value = None

		result = application_service.get_application(999, 1)

		assert result is None

	def test_get_application_wrong_user(self, application_service, mock_db):
		"""Test retrieving application with wrong user_id"""
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.return_value = None

		result = application_service.get_application(1, 999)

		assert result is None


class TestGetApplicationDocuments:
	"""Tests for get_application_documents method"""

	def test_get_documents_success(self, application_service, mock_db, sample_application):
		"""Test successfully retrieving application documents"""
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.return_value = sample_application

		result = application_service.get_application_documents(1, 1)

		assert len(result) == 2
		assert all(isinstance(doc, DocumentAssociation) for doc in result)
		assert result[0].document_id == 1
		assert result[0].document_type == "resume"
		assert result[0].filename == "resume.pdf"
		assert result[1].document_id == 2
		assert result[1].document_type == "cover_letter"

	def test_get_documents_application_not_found(self, application_service, mock_db):
		"""Test getting documents for non-existent application"""
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.return_value = None

		result = application_service.get_application_documents(999, 1)

		assert result == []

	def test_get_documents_empty_list(self, application_service, mock_db):
		"""Test application with no documents"""
		app_no_docs = Application(id=1, user_id=1, job_id=100, status="applied", documents=[])
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.return_value = app_no_docs

		result = application_service.get_application_documents(1, 1)

		assert result == []


class TestRemoveDocumentFromApplication:
	"""Tests for remove_document_from_application method"""

	def test_remove_document_success(self, application_service, mock_db, sample_application):
		"""Test successfully removing a document from application"""
		# Mock application retrieval
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.side_effect = [
			sample_application,  # First call for get_application
			None,  # Second call for Document query (simulating no Document model)
		]

		result = application_service.remove_document_from_application(1, 1, 1)

		assert result is True
		assert len(sample_application.documents) == 1
		assert sample_application.documents[0]["document_id"] == 2
		mock_db.commit.assert_called_once()

	def test_remove_document_application_not_found(self, application_service, mock_db):
		"""Test removing document from non-existent application"""
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.return_value = None

		result = application_service.remove_document_from_application(999, 1, 1)

		assert result is False
		mock_db.commit.assert_not_called()

	def test_remove_nonexistent_document(self, application_service, mock_db, sample_application):
		"""Test removing document that doesn't exist in application"""
		original_doc_count = len(sample_application.documents)
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.side_effect = [sample_application, None]

		result = application_service.remove_document_from_application(1, 999, 1)

		assert result is True
		assert len(sample_application.documents) == original_doc_count
		mock_db.commit.assert_called_once()

	def test_remove_document_updates_timestamp(self, application_service, mock_db, sample_application):
		"""Test that removing document updates the updated_at timestamp"""
		original_updated_at = sample_application.updated_at
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.side_effect = [sample_application, None]

		application_service.remove_document_from_application(1, 1, 1)

		assert sample_application.updated_at > original_updated_at

	@patch("app.services.application_service.Document", None)
	def test_remove_document_no_document_model(self, application_service, mock_db, sample_application):
		"""Test removing document when Document model doesn't exist"""
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.return_value = sample_application

		result = application_service.remove_document_from_application(1, 1, 1)

		assert result is True
		mock_db.commit.assert_called_once()


class TestGetApplicationsUsingDocument:
	"""Tests for get_applications_using_document method"""

	def test_get_applications_using_document_success(self, application_service, mock_db):
		"""Test finding applications that use a specific document"""
		app1 = Application(id=1, user_id=1, job_id=100, documents=[{"document_id": 1, "type": "resume"}])
		app2 = Application(id=2, user_id=1, job_id=101, documents=[{"document_id": 1, "type": "resume"}, {"document_id": 2, "type": "cover_letter"}])
		app3 = Application(id=3, user_id=1, job_id=102, documents=[{"document_id": 2, "type": "cover_letter"}])

		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.all.return_value = [app1, app2, app3]

		result = application_service.get_applications_using_document(1, 1)

		assert len(result) == 2
		assert app1 in result
		assert app2 in result
		assert app3 not in result

	def test_get_applications_using_document_none_found(self, application_service, mock_db):
		"""Test when no applications use the document"""
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.all.return_value = []

		result = application_service.get_applications_using_document(999, 1)

		assert result == []

	def test_get_applications_using_document_filters_correctly(self, application_service, mock_db):
		"""Test that filtering logic works correctly"""
		# Application says it has doc 1, but actually doesn't (edge case)
		app_misleading = Application(
			id=1,
			user_id=1,
			job_id=100,
			documents=[{"document_id": 2, "type": "resume"}],  # Different doc ID
		)

		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.all.return_value = [app_misleading]

		result = application_service.get_applications_using_document(1, 1)

		assert result == []


class TestApplicationServiceIntegration:
	"""Integration-style tests for ApplicationService"""

	def test_service_initialization(self, mock_db):
		"""Test service initializes correctly"""
		service = ApplicationService(mock_db)
		assert service.db == mock_db

	def test_remove_and_verify_workflow(self, application_service, mock_db, sample_application):
		"""Test complete workflow: get documents -> remove -> verify"""
		# Setup mock responses
		mock_query = Mock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value.first.side_effect = [
			sample_application,  # get_application_documents call
			sample_application,  # remove_document_from_application call
			None,  # Document query
			sample_application,  # final verification
		]

		# Get initial documents
		initial_docs = application_service.get_application_documents(1, 1)
		assert len(initial_docs) == 2

		# Remove one document
		success = application_service.remove_document_from_application(1, 1, 1)
		assert success

		# Verify removal
		remaining_docs = application_service.get_application_documents(1, 1)
		assert len(remaining_docs) == 1
		assert remaining_docs[0].document_id == 2
