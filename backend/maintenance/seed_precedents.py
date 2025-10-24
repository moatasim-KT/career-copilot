#!/usr/bin/env python3
"""
Seed ChromaDB with sample precedent clauses for job application tracking.

This script populates the vector store with realistic legal precedent clauses
that can be used for RAG-based job application tracking.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.logging import get_logger
from app.services.vector_store import PrecedentClause, get_vector_store_service

logger = get_logger(__name__)

# ... (rest of the file remains unchanged)
