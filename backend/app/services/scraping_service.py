"""
Scraping Service for scraping job boards and other websites.
"""

from typing import Dict, Any, Optional, List
import httpx
from bs4 import BeautifulSoup
from ..core.config import get_settings

class ScrapingService:
    """Service for scraping job boards and other websites."""

    def __init__(self):
        self.settings = get_settings()

    async def scrape(self, url: str) -> str:
        """Scrape a URL and return the content."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

_service = None

def get_scraping_service() -> "ScrapingService":
    """Get the scraping service."""
    global _service
    if _service is None:
        _service = ScrapingService()
    return _service
