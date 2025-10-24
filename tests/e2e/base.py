from __future__ import annotations

from typing import Any, Dict

import httpx


class BaseE2ETest:
    """Base class providing small helpers for E2E tests.

    Tests can either use fixtures directly or subclass this helper for common logic.
    """

    def __init__(self, client: httpx.AsyncClient, config: Dict[str, Any]):
        self.client = client
        self.config = config

    def url(self, path: str) -> str:
        """Return a full URL path for the configured client (client manages base_url)."""
        # httpx.AsyncClient already manages base_url; provide convenience only
        if path.startswith("/"):
            return path
        return f"/{path}"

    async def get_json(self, path: str, **kwargs) -> httpx.Response:
        resp = await self.client.get(self.url(path), **kwargs)
        return resp
"""
Base test classes and utilities for E2E testing.

This module provides common base classes, fixtures, and utilities
that can be used across different E2E test suites.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock

import pytest
from pydantic import BaseModel


class BaseE2ETest(ABC):
    """
    Abstract base class for E2E tests.
    
    Provides common functionality and structure for all E2E test classes.
    """
    
    def __init__(self):
        """Initialize the base E2E test."""
        self.logger = self._setup_logging()
        self.test_data: Dict[str, Any] = {}
        self.cleanup_tasks: List[callable] = []
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the test class."""
        class_name = self.__class__.__name__
        logger = logging.getLogger(f"e2e_test.{class_name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    async def setup(self):
        """Set up test environment and dependencies."""
        pass
    
    @abstractmethod
    async def teardown(self):
        """Clean up test environment and resources."""
        pass
    
    @abstractmethod
    async def run_test(self) -> Dict[str, Any]:
        """Execute the main test logic."""
        pass
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute the complete test lifecycle.
        
        Returns:
            Dictionary containing test results and metadata.
        """
        try:
            self.logger.info(f"Starting test: {self.__class__.__name__}")
            
            # Setup phase
            await self.setup()
            
            # Execute test
            result = await self.run_test()
            
            # Add metadata
            result.update({
                "test_class": self.__class__.__name__,
                "status": "completed"
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            return {
                "test_class": self.__class__.__name__,
                "status": "failed",
                "error": str(e)
            }
        finally:
            # Cleanup phase
            await self.teardown()
    
    def add_cleanup_task(self, task: callable):
        """Add a cleanup task to be executed during teardown."""
        self.cleanup_tasks.append(task)
    
    async def _run_cleanup_tasks(self):
        """Execute all registered cleanup tasks."""
        for task in self.cleanup_tasks:
            try:
                if asyncio.iscoroutinefunction(task):
                    await task()
                else:
                    task()
            except Exception as e:
                self.logger.warning(f"Cleanup task failed: {e}")


class ConfigurationTestBase(BaseE2ETest):
    """Base class for configuration validation tests."""
    
    def __init__(self):
        super().__init__()
        self.config_files: List[str] = []
        self.validation_errors: List[str] = []
    
    async def setup(self):
        """Set up configuration test environment."""
        self.logger.info("Setting up configuration test environment")
        # Base setup - can be extended by subclasses
    
    async def teardown(self):
        """Clean up configuration test environment."""
        self.logger.info("Cleaning up configuration test environment")
        await self._run_cleanup_tasks()
    
    def add_validation_error(self, error: str):
        """Add a validation error to the error list."""
        self.validation_errors.append(error)
        self.logger.warning(f"Validation error: {error}")
    
    def has_validation_errors(self) -> bool:
        """Check if there are any validation errors."""
        return len(self.validation_errors) > 0


class ServiceHealthTestBase(BaseE2ETest):
    """Base class for service health check tests."""
    
    def __init__(self):
        super().__init__()
        self.service_endpoints: Dict[str, str] = {}
        self.health_results: Dict[str, Dict[str, Any]] = {}
    
    async def setup(self):
        """Set up service health test environment."""
        self.logger.info("Setting up service health test environment")
        # Initialize default endpoints
        self.service_endpoints = {
            "backend": "http://localhost:8000/api/v1/health",  # FastAPI health endpoint
            "frontend": "http://localhost:3000",  # Next.js frontend
            "database": "postgresql://localhost:5432/career_copilot_test"  # PostgreSQL database
        }
    
    async def teardown(self):
        """Clean up service health test environment."""
        self.logger.info("Cleaning up service health test environment")
        await self._run_cleanup_tasks()
    
    def add_health_result(self, service: str, is_healthy: bool, 
                         response_time: float, details: Optional[Dict[str, Any]] = None):
        """Add a health check result."""
        self.health_results[service] = {
            "healthy": is_healthy,
            "response_time": response_time,
            "details": details or {}
        }
        
        status = "healthy" if is_healthy else "unhealthy"
        self.logger.info(f"Service {service}: {status} ({response_time:.2f}s)")
    
    def get_unhealthy_services(self) -> List[str]:
        """Get list of unhealthy services."""
        return [
            service for service, result in self.health_results.items()
            if not result.get("healthy", False)
        ]


class FeatureTestBase(BaseE2ETest):
    """Base class for feature validation tests."""
    
    def __init__(self):
        super().__init__()
        self.test_users: List[Dict[str, Any]] = []
        self.test_data_created: List[str] = []
    
    async def setup(self):
        """Set up feature test environment."""
        self.logger.info("Setting up feature test environment")
        # Create test users and data
        await self._create_test_users()
    
    async def teardown(self):
        """Clean up feature test environment."""
        self.logger.info("Cleaning up feature test environment")
        # Clean up test data
        await self._cleanup_test_data()
        await self._run_cleanup_tasks()
    
    async def _create_test_users(self):
        """Create test users for feature testing."""
        # Placeholder for test user creation
        # This will be implemented in subsequent tasks
        self.test_users = [
            {
                "id": 1,
                "email": "test1@example.com",
                "profile": {
                    "skills": ["Python", "FastAPI"],
                    "experience_level": "mid"
                }
            }
        ]
        self.logger.info(f"Created {len(self.test_users)} test users")
    
    async def _cleanup_test_data(self):
        """Clean up test data created during testing."""
        # Placeholder for test data cleanup
        # This will be implemented in subsequent tasks
        self.logger.info(f"Cleaned up {len(self.test_data_created)} test data items")


class IntegrationTestBase(BaseE2ETest):
    """Base class for integration workflow tests."""
    
    def __init__(self):
        super().__init__()
        self.workflow_steps: List[str] = []
        self.step_results: Dict[str, Any] = {}
    
    async def setup(self):
        """Set up integration test environment."""
        self.logger.info("Setting up integration test environment")
        # Initialize workflow tracking
        self.workflow_steps = []
        self.step_results = {}
    
    async def teardown(self):
        """Clean up integration test environment."""
        self.logger.info("Cleaning up integration test environment")
        await self._run_cleanup_tasks()
    
    def add_workflow_step(self, step_name: str):
        """Add a workflow step to track execution."""
        self.workflow_steps.append(step_name)
        self.logger.info(f"Workflow step added: {step_name}")
    
    def record_step_result(self, step_name: str, success: bool, 
                          duration: float, details: Optional[Dict[str, Any]] = None):
        """Record the result of a workflow step."""
        self.step_results[step_name] = {
            "success": success,
            "duration": duration,
            "details": details or {}
        }
        
        status = "completed" if success else "failed"
        self.logger.info(f"Step {step_name}: {status} ({duration:.2f}s)")
    
    def get_failed_steps(self) -> List[str]:
        """Get list of failed workflow steps."""
        return [
            step for step, result in self.step_results.items()
            if not result.get("success", False)
        ]