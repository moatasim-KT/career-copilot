"""
Endpoint Discovery and Testing Framework

This module provides comprehensive tools for discovering, testing, and validating
all FastAPI endpoints in the Career Copilot application.
"""

from .endpoint_discovery import EndpointDiscovery, EndpointInfo, ParameterInfo
from .endpoint_tester import EndpointTester, TestResult, ValidationResult
from .test_data_generator import TestDataGenerator

__all__ = [
    "EndpointDiscovery",
    "EndpointInfo",
    "ParameterInfo",
    "EndpointTester",
    "TestResult",
    "ValidationResult",
    "TestDataGenerator",
]
