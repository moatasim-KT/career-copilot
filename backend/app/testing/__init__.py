"""
Endpoint Discovery and Testing Framework

This module provides comprehensive tools for discovering, testing, and validating
all FastAPI endpoints in the Career Copilot application.
"""

from .endpoint_discovery import EndpointDiscovery, EndpointInfo, ParameterInfo, ParameterLocation
from .endpoint_tester import EndpointTester, TestResult, ValidationResult, TestStatus
from .test_data_generator import TestDataGenerator, TestDataType

__all__ = [
    "EndpointDiscovery",
    "EndpointInfo",
    "EndpointTester",
    "ParameterInfo",
    "ParameterLocation",
    "TestDataGenerator",
    "TestDataType",
    "TestResult",
    "TestStatus",
    "ValidationResult",
]
