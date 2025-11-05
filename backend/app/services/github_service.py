"""
Github Service for interacting with the Github API.
"""

import httpx
from typing import Dict, Any, Optional, List
from ..core.config import get_settings

class GithubService:
    """Service for interacting with the Github API."""

    def __init__(self):
        self.settings = get_settings()
        self.headers = {
            "Authorization": f"token {self.settings.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def get_user_repos(self, username: str) -> List[Dict[str, Any]]:
        """Get user repositories."""
        url = f"https://api.github.com/users/{username}/repos"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_repo_issues(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get repository issues."""
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

_service = None

def get_github_service() -> "GithubService":
    """Get the Github service."""
    global _service
    if _service is None:
        _service = GithubService()
    return _service
