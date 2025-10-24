"""
Setup script for Firebase Authentication and Authorization.
Configures Firebase Auth, IAM roles, and JWT token validation.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings
from app.core.logging import get_logger
from app.config.firebase_config import get_firebase_config
from app.services.iam_service import get_iam_service

logger = get_logger(__name__)

# ... (rest of the file remains unchanged)
