"""
Repository for interacting with the email_delivery_statuses table in the database.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.future import select

from ..services.sendgrid_service import EmailDeliveryStatus
from .base_repository import BaseRepository


class EmailDeliveryStatusRepository(BaseRepository):
    """Repository for email delivery statuses."""

    def __init__(self, session):
        super().__init__(session, EmailDeliveryStatus)

    async def create_status(
        self, message_id: str, recipient: str, status: str, error_message: Optional[str] = None
    ) -> EmailDeliveryStatus:
        """Create a new email delivery status."""
        new_status = EmailDeliveryStatus(
            message_id=message_id,
            recipient=recipient,
            status=status,
            error_message=error_message,
        )
        self.session.add(new_status)
        await self.session.commit()
        await self.session.refresh(new_status)
        return new_status

    async def get_status_by_message_id(self, message_id: str) -> Optional[EmailDeliveryStatus]:
        """Get an email delivery status by message ID."""
        result = await self.session.execute(
            select(EmailDeliveryStatus).where(EmailDeliveryStatus.message_id == message_id)
        )
        return result.scalars().first()

    async def update_status(
        self, message_id: str, status: str, error_message: Optional[str] = None
    ) -> Optional[EmailDeliveryStatus]:
        """Update an email delivery status."""
        status_to_update = await self.get_status_by_message_id(message_id)
        if status_to_update:
            status_to_update.status = status
            status_to_update.error_message = error_message
            if status == "delivered":
                from datetime import datetime
                status_to_update.delivered_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(status_to_update)
        return status_to_update
