"""
Repository for interacting with the user_notification_preferences table in the database.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.future import select

from ..models.database_models import UserNotificationPreference
from .base_repository import BaseRepository


class UserNotificationPreferenceRepository(BaseRepository):
    """Repository for user notification preferences."""

    def __init__(self, session):
        super().__init__(session, UserNotificationPreference)

    async def create_preference(
        self, user_id: UUID, notification_type: str, channel_id: str, is_enabled: bool = True
    ) -> UserNotificationPreference:
        """Create a new user notification preference."""
        new_preference = UserNotificationPreference(
            user_id=user_id,
            notification_type=notification_type,
            channel_id=channel_id,
            is_enabled=is_enabled,
        )
        self.session.add(new_preference)
        await self.session.commit()
        await self.session.refresh(new_preference)
        return new_preference

    async def get_preference(
        self, user_id: UUID, notification_type: str
    ) -> Optional[UserNotificationPreference]:
        """Get a user notification preference."""
        result = await self.session.execute(
            select(UserNotificationPreference).where(
                UserNotificationPreference.user_id == user_id,
                UserNotificationPreference.notification_type == notification_type,
            )
        )
        return result.scalars().first()

    async def update_preference(
        self, user_id: UUID, notification_type: str, channel_id: str, is_enabled: bool
    ) -> Optional[UserNotificationPreference]:
        """Update a user notification preference."""
        preference_to_update = await self.get_preference(user_id, notification_type)
        if preference_to_update:
            preference_to_update.channel_id = channel_id
            preference_to_update.is_enabled = is_enabled
            await self.session.commit()
            await self.session.refresh(preference_to_update)
        return preference_to_update
