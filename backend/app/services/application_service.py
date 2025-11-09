"""
Application service for Career Co-Pilot system
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.application import Application

try:
	from app.models.document import Document
except Exception:  # pragma: no cover - fallback for environments without the model
	Document = None
from app.schemas.document import DocumentAssociation


class ApplicationService:
	"""Service for managing job applications"""

	def __init__(self, db: Session):
		self.db = db

	def get_application(self, application_id: int, user_id: int) -> Optional[Application]:
		"""Get an application by ID for a specific user"""
		return self.db.query(Application).filter(and_(Application.id == application_id, Application.user_id == user_id)).first()

	def get_application_documents(self, application_id: int, user_id: int) -> List[DocumentAssociation]:
		"""Get documents associated with an application"""

		application = self.get_application(application_id, user_id)
		if not application:
			return []

		# Convert stored document data to DocumentAssociation objects
		document_associations = []
		for doc_data in application.documents:
			association = DocumentAssociation(
				document_id=doc_data["document_id"],
				document_type=doc_data["type"],
				filename=doc_data["filename"],
				uploaded_at=datetime.fromisoformat(doc_data["uploaded_at"]),
			)
			document_associations.append(association)

		return document_associations

	def remove_document_from_application(self, application_id: int, document_id: int, user_id: int) -> bool:
		"""Remove a document association from an application"""

		application = self.get_application(application_id, user_id)
		if not application:
			return False

		# Filter out the document to remove
		updated_documents = [doc for doc in application.documents if doc["document_id"] != document_id]

		# Update application
		application.documents = updated_documents
		application.updated_at = datetime.now(timezone.utc)

		# If a Document ORM model exists, decrement its usage_count. Otherwise skip.
		if Document is not None:
			document = self.db.query(Document).filter(and_(Document.id == document_id, Document.user_id == user_id)).first()
			if document and getattr(document, "usage_count", 0) > 0:
				document.usage_count -= 1

		self.db.commit()

		return True

	def get_applications_using_document(self, document_id: int, user_id: int) -> List[Application]:
		"""Get all applications that use a specific document"""

		# Query applications that contain the document_id in their documents JSON
		applications = (
			self.db.query(Application)
			.filter(and_(Application.user_id == user_id, Application.documents.op("?")([{"document_id": document_id}])))
			.all()
		)

		# Filter applications that actually contain the document
		# (SQLAlchemy JSON operators can be tricky, so we double-check)
		filtered_applications = []
		for app in applications:
			for doc in app.documents:
				if doc.get("document_id") == document_id:
					filtered_applications.append(app)
					break

		return filtered_applications
