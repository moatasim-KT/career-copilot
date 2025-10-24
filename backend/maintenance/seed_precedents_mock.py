#!/usr/bin/env python3
"""
Mock seed ChromaDB with sample precedent clauses for job application tracking.

This script populates the vector store with realistic legal precedent clauses
without requiring OpenAI API key for testing purposes.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.logging import get_logger

logger = get_logger(__name__)

# ... (rest of the file remains unchanged)
