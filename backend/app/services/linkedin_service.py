"""
Linkedin Service for interacting with the Linkedin API.
"""

from typing import Dict, Any, Optional, List
import httpx
from ..core.config import get_settings

class LinkedinService:
    """Service for interacting with the Linkedin API."""

    def __init__(self):
        self.settings = get_settings()
        self.headers = {
            "Authorization": f"Bearer {self.settings.linkedin_token}",
            "Content-Type": "application/json",
        }

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile."""
        url = f"https://api.linkedin.com/v2/people/(id:{user_id})"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

_service = None

def get_linkedin_service() -> "LinkedinService":
    """Get the Linkedin service."""
    global _service
    if _service is None:
        _service = LinkedinService()
    return _service
