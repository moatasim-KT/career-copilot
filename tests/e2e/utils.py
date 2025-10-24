"""
Clean utility functions and helpers for E2E testing.

This module provides common utility functions, test data generators,
and helper classes used across E2E test suites.
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx
import yaml


class TestDataGenerator:
    """Generator for test data used in E2E tests."""
    
    @staticmethod
    def create_test_user(user_id: int = 1, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a test user with realistic data.
        
        Args:
            user_id: Unique identifier for the user.
            email: Email address. If None, generates one based on user_id.
            
        Returns:
            Dictionary containing user data.
        """
        if email is None:
            email = f"testuser{user_id}@example.com"
        
        return {
            "id": user_id,
            "email": email,
            "profile": {
                "skills": ["Python", "FastAPI", "React", "PostgreSQL"][:user_id % 4 + 1],
                "experience_level": ["junior", "mid", "senior"][user_id % 3],
                "locations": ["San Francisco", "Remote", "New York"][:(user_id % 3) + 1],
                "preferences": {
                    "salary_min": 70000 + (user_id * 10000),
                    "salary_max": 120000 + (user_id * 15000),
                    "company_size": ["startup", "medium", "large"][:(user_id % 3) + 1],
                    "remote_work": user_id % 2 == 0
                }
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    
    @staticmethod
    def create_test_job(job_id: int = 1, company: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a test job posting with realistic data.
        
        Args:
            job_id: Unique identifier for the job.
            company: Company name. If None, generates one based on job_id.
            
        Returns:
            Dictionary containing job data.
        """
        if company is None:
            companies = ["TechCorp", "StartupXYZ", "BigTech Inc", "InnovateCo"]
            company = companies[job_id % len(companies)]
        
        job_titles = [
            "Senior Python Developer",
            "Full Stack Engineer", 
            "DevOps Engineer",
            "Data Scientist"
        ]
        
        locations = ["San Francisco, CA", "Remote", "New York, NY", "Austin, TX"]
        tech_stacks = [
            ["Python", "Django", "PostgreSQL"],
            ["React", "Node.js", "MongoDB"],
            ["AWS", "Docker", "Kubernetes"],
            ["Python", "Pandas", "TensorFlow"]
        ]
        
        return {
            "id": job_id,
            "title": job_titles[job_id % len(job_titles)],
            "company": company,
            "location": locations[job_id % len(locations)],
            "tech_stack": tech_stacks[job_id % len(tech_stacks)],
            "salary_min": 90000 + (job_id * 5000),
            "salary_max": 140000 + (job_id * 8000),
            "description": f"Exciting opportunity at {company} for a {job_titles[job_id % len(job_titles)]}",
            "requirements": [
                "3+ years experience",
                "Strong problem-solving skills",
                "Team collaboration"
            ],
            "status": "active",
            "posted_date": "2024-01-01T00:00:00Z",
            "application_deadline": "2024-02-01T00:00:00Z"
        }


class HTTPClient:
    """HTTP client for making API requests during E2E tests."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL for API requests.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = httpx.AsyncClient(timeout=timeout)
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make GET request to endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return await self.session.get(url, params=params)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make POST request to endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return await self.session.post(url, json=data)
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make PUT request to endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return await self.session.put(url, json=data)
    
    async def delete(self, endpoint: str) -> httpx.Response:
        """Make DELETE request to endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return await self.session.delete(url)
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()


class ConfigValidator:
    """Utility class for validating configuration files."""
    
    @staticmethod
    def validate_env_file(env_path: Union[str, Path], 
                         example_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate environment file against example template.
        
        Args:
            env_path: Path to the .env file to validate.
            example_path: Path to the .env.example template file.
            
        Returns:
            Dictionary containing validation results.
        """
        env_path = Path(env_path)
        example_path = Path(example_path)
        
        result = {
            "valid": True,
            "missing_variables": [],
            "extra_variables": [],
            "empty_required_variables": [],
            "errors": [],
            "warnings": [],
            "checked_files": [str(env_path), str(example_path)]
        }
        
        try:
            # Read example file to get required variables
            if not example_path.exists():
                result["errors"].append(f"Example file not found: {example_path}")
                result["valid"] = False
                return result
            
            with open(example_path, 'r', encoding='utf-8') as f:
                example_content = f.read()
            
            # Extract variable names from example file
            required_vars = set()
            for line in example_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    var_name = line.split('=', 1)[0].strip()
                    required_vars.add(var_name)
            
            # Read actual env file if it exists
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    env_content = f.read()
                
                # Extract variable names from env file
                env_vars = {}
                for line in env_content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        try:
                            var_name, var_value = line.split('=', 1)
                            env_vars[var_name.strip()] = var_value.strip()
                        except ValueError:
                            continue
                
                # Find missing variables
                env_var_names = set(env_vars.keys())
                result["missing_variables"] = list(required_vars - env_var_names)
                result["extra_variables"] = list(env_var_names - required_vars)
                
                # Mark as invalid if there are missing variables
                if result["missing_variables"]:
                    result["valid"] = False
                    
            else:
                result["errors"].append(f"Environment file not found: {env_path}")
                result["missing_variables"] = list(required_vars)
                result["valid"] = False
                
        except Exception as e:
            result["errors"].append(f"Error validating env file: {str(e)}")
            result["valid"] = False
        
        return result
    
    @staticmethod
    def validate_json_file(json_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate JSON file syntax and structure.
        
        Args:
            json_path: Path to the JSON file to validate.
            
        Returns:
            Dictionary containing validation results.
        """
        json_path = Path(json_path)
        
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "parsed_data": None,
            "file_type": "json",
            "file_path": str(json_path)
        }
        
        try:
            if not json_path.exists():
                result["errors"].append(f"JSON file not found: {json_path}")
                result["valid"] = False
                return result
            
            with open(json_path, 'r', encoding='utf-8') as f:
                parsed_data = json.load(f)
                result["parsed_data"] = parsed_data
                
        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON format: {str(e)}")
            result["valid"] = False
        except Exception as e:
            result["errors"].append(f"Error reading JSON file: {str(e)}")
            result["valid"] = False
        
        return result
    
    @staticmethod
    def validate_yaml_file(yaml_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate YAML file syntax and structure.
        
        Args:
            yaml_path: Path to the YAML file to validate.
            
        Returns:
            Dictionary containing validation results.
        """
        yaml_path = Path(yaml_path)
        
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "parsed_data": None,
            "file_type": "yaml",
            "file_path": str(yaml_path)
        }
        
        try:
            if not yaml_path.exists():
                result["errors"].append(f"YAML file not found: {yaml_path}")
                result["valid"] = False
                return result
            
            with open(yaml_path, 'r', encoding='utf-8') as f:
                parsed_data = yaml.safe_load(f)
                result["parsed_data"] = parsed_data
                
                # Check for common YAML issues
                if parsed_data is None:
                    result["warnings"].append("YAML file is empty or contains only null values")
                
        except yaml.YAMLError as e:
            result["errors"].append(f"Invalid YAML syntax: {str(e)}")
            result["valid"] = False
        except Exception as e:
            result["errors"].append(f"Error reading YAML file: {str(e)}")
            result["valid"] = False
        
        return result


class ServiceHealthChecker:
    """Utility class for checking service health."""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize health checker.
        
        Args:
            timeout: Timeout for health checks in seconds.
        """
        self.timeout = timeout
    
    async def check_http_service(self, url: str, expected_status: int = 200) -> Dict[str, Any]:
        """
        Check HTTP service health.
        
        Args:
            url: URL to check.
            expected_status: Expected HTTP status code.
            
        Returns:
            Dictionary containing health check results.
        """
        result = {
            "healthy": False,
            "response_time": 0.0,
            "status_code": None,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                result["status_code"] = response.status_code
                result["healthy"] = response.status_code == expected_status
                
        except httpx.TimeoutException:
            result["error"] = f"Timeout after {self.timeout}s"
        except httpx.ConnectError:
            result["error"] = "Connection failed"
        except Exception as e:
            result["error"] = str(e)
        finally:
            result["response_time"] = time.time() - start_time
        
        return result


async def wait_for_service(url: str, timeout: int = 60, interval: int = 2) -> bool:
    """
    Wait for a service to become available.
    
    Args:
        url: URL to check.
        timeout: Maximum time to wait in seconds.
        interval: Check interval in seconds.
        
    Returns:
        True if service becomes available, False if timeout.
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return True
        except:
            pass
        
        await asyncio.sleep(interval)
    
    return False


def load_test_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load test configuration from JSON file.
    
    Args:
        config_path: Path to configuration file.
        
    Returns:
        Dictionary containing configuration data.
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}