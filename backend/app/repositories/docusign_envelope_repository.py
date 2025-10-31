"""
Repository for interacting with the docusign_envelopes table in the database.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.future import select

from ..models.database_models import DocuSignEnvelope
from .base_repository import BaseRepository


class DocuSignEnvelopeRepository(BaseRepository):
	"""Repository for DocuSign envelopes."""

	def __init__(self, session):
		super().__init__(session, DocuSignEnvelope)

	async def create_envelope(self, envelope_id: str, contract_analysis_id: UUID, status: str, recipients: List[dict]) -> DocuSignEnvelope:
		"""Create a new DocuSign envelope."""
		new_envelope = DocuSignEnvelope(
			envelope_id=envelope_id,
			contract_analysis_id=contract_analysis_id,
			status=status,
			recipients=recipients,
		)
		self.session.add(new_envelope)
		await self.session.commit()
		await self.session.refresh(new_envelope)
		return new_envelope

	async def get_envelope_by_envelope_id(self, envelope_id: str) -> Optional[DocuSignEnvelope]:
		"""Get a DocuSign envelope by envelope ID."""
		result = await self.session.execute(select(DocuSignEnvelope).where(DocuSignEnvelope.envelope_id == envelope_id))
		return result.scalars().first()

	async def update_envelope_status(self, envelope_id: str, status: str) -> Optional[DocuSignEnvelope]:
		"""Update a DocuSign envelope's status."""
		envelope_to_update = await self.get_envelope_by_envelope_id(envelope_id)
		if envelope_to_update:
			envelope_to_update.status = status
			await self.session.commit()
			await self.session.refresh(envelope_to_update)
		return envelope_to_update
