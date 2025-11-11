"""
Test Data Generation System

Generates valid, invalid, and edge case test data for endpoint testing.
"""

import random
import string
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Type, get_args, get_origin

from pydantic import BaseModel

from .endpoint_discovery import EndpointInfo, ParameterInfo, ParameterLocation


class TestDataType(str, Enum):
    """Types of test data to generate"""

    VALID = "valid"
    INVALID = "invalid"
    EDGE_CASE = "edge_case"


class TestDataGenerator:
    """
    Generates test data for endpoint parameters.

    This class provides comprehensive test data generation including:
    - Valid data that should pass validation
    - Invalid data that should fail validation
    - Edge cases (empty strings, null values, boundary values)
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the test data generator.

        Args:
            seed: Random seed for reproducible test data
        """
        if seed is not None:
            random.seed(seed)

    def generate_test_data(self, endpoint: EndpointInfo, data_type: TestDataType = TestDataType.VALID) -> Dict[str, Any]:
        """
        Generate test data for an endpoint.

        Args:
            endpoint: The endpoint to generate data for
            data_type: Type of test data to generate

        Returns:
            Dictionary of parameter names to test values
        """
        test_data = {}

        # Generate data for path parameters
        for param in endpoint.get_path_parameters():
            test_data[param.name] = self._generate_parameter_value(param, data_type)

        # Generate data for query parameters
        for param in endpoint.get_query_parameters():
            if param.required or data_type == TestDataType.VALID:
                test_data[param.name] = self._generate_parameter_value(param, data_type)

        # Generate data for body parameters
        if endpoint.request_body_model:
            test_data["body"] = self._generate_model_data(endpoint.request_body_model, data_type)

        return test_data

    def generate_multiple_test_cases(self, endpoint: EndpointInfo) -> List[Dict[str, Any]]:
        """
        Generate multiple test cases for an endpoint.

        Args:
            endpoint: The endpoint to generate test cases for

        Returns:
            List of test data dictionaries
        """
        test_cases = []

        # Generate valid test cases
        test_cases.append({"type": TestDataType.VALID, "data": self.generate_test_data(endpoint, TestDataType.VALID)})

        # Generate invalid test cases
        test_cases.append({"type": TestDataType.INVALID, "data": self.generate_test_data(endpoint, TestDataType.INVALID)})

        # Generate edge case test cases
        test_cases.append({"type": TestDataType.EDGE_CASE, "data": self.generate_test_data(endpoint, TestDataType.EDGE_CASE)})

        # Generate missing required parameter test cases
        if endpoint.get_required_parameters():
            for param in endpoint.get_required_parameters():
                missing_data = self.generate_test_data(endpoint, TestDataType.VALID)
                if param.name in missing_data:
                    del missing_data[param.name]
                test_cases.append({"type": "missing_required", "data": missing_data, "missing_param": param.name})

        return test_cases

    def _generate_parameter_value(self, param: ParameterInfo, data_type: TestDataType) -> Any:
        """
        Generate a value for a specific parameter.

        Args:
            param: The parameter to generate a value for
            data_type: Type of test data to generate

        Returns:
            Generated value
        """
        type_annotation = param.type_annotation

        # Handle Optional types
        origin = get_origin(type_annotation)
        if origin is not None:
            args = get_args(type_annotation)
            if len(args) > 0:
                # Use the first non-None type
                for arg in args:
                    if arg is not type(None):
                        type_annotation = arg
                        break

        # Generate based on type
        if type_annotation == int or type_annotation == "int":
            return self._generate_int_value(param, data_type)
        elif type_annotation == str or type_annotation == "str":
            return self._generate_string_value(param, data_type)
        elif type_annotation == bool or type_annotation == "bool":
            return self._generate_bool_value(data_type)
        elif type_annotation == float or type_annotation == "float":
            return self._generate_float_value(param, data_type)
        elif type_annotation == datetime:
            return self._generate_datetime_value(data_type)
        elif type_annotation == list or origin == list:
            return self._generate_list_value(param, data_type)
        else:
            # Default to string for unknown types
            return self._generate_string_value(param, data_type)

    def _generate_int_value(self, param: ParameterInfo, data_type: TestDataType) -> int:
        """Generate integer test values"""
        if data_type == TestDataType.VALID:
            # Common valid IDs and counts
            if "id" in param.name.lower():
                return random.randint(1, 1000)
            elif "count" in param.name.lower() or "limit" in param.name.lower():
                return random.randint(1, 100)
            elif "skip" in param.name.lower() or "offset" in param.name.lower():
                return random.randint(0, 50)
            elif "page" in param.name.lower():
                return random.randint(1, 10)
            else:
                return random.randint(1, 1000)
        elif data_type == TestDataType.INVALID:
            # Invalid integers (negative where positive expected)
            if "id" in param.name.lower():
                return -1
            else:
                return -999
        else:  # EDGE_CASE
            # Edge cases: 0, very large numbers
            return random.choice([0, 1, 999999, 2147483647])

    def _generate_string_value(self, param: ParameterInfo, data_type: TestDataType) -> str:
        """Generate string test values"""
        if data_type == TestDataType.VALID:
            # Generate contextual strings based on parameter name
            if "email" in param.name.lower():
                return f"test{random.randint(1, 1000)}@example.com"
            elif "name" in param.name.lower():
                return random.choice(["John Doe", "Jane Smith", "Bob Johnson", "Alice Williams"])
            elif "title" in param.name.lower():
                return random.choice(["Senior Software Engineer", "Product Manager", "Data Scientist", "DevOps Engineer"])
            elif "company" in param.name.lower():
                return random.choice(["Google", "Microsoft", "Amazon", "Apple", "Meta"])
            elif "location" in param.name.lower():
                return random.choice(["San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Remote"])
            elif "url" in param.name.lower():
                return f"https://example.com/{random.randint(1, 1000)}"
            elif "description" in param.name.lower():
                return "This is a test description with some sample content."
            elif "status" in param.name.lower():
                return random.choice(["active", "pending", "completed", "cancelled"])
            else:
                return f"test_value_{random.randint(1, 1000)}"
        elif data_type == TestDataType.INVALID:
            # Invalid strings (empty, too long, special characters)
            return random.choice(["", "   ", "a" * 10000, "<script>alert('xss')</script>", "'; DROP TABLE users; --"])
        else:  # EDGE_CASE
            # Edge cases
            return random.choice(["", "a", "A" * 255, "Test with émojis 🚀", "Test\nwith\nnewlines", "Test\twith\ttabs"])

    def _generate_bool_value(self, data_type: TestDataType) -> bool:
        """Generate boolean test values"""
        if data_type == TestDataType.VALID:
            return random.choice([True, False])
        elif data_type == TestDataType.INVALID:
            # Booleans don't really have invalid values in Python
            return random.choice([True, False])
        else:  # EDGE_CASE
            return random.choice([True, False])

    def _generate_float_value(self, param: ParameterInfo, data_type: TestDataType) -> float:
        """Generate float test values"""
        if data_type == TestDataType.VALID:
            if "salary" in param.name.lower():
                return round(random.uniform(50000, 200000), 2)
            elif "rate" in param.name.lower() or "percentage" in param.name.lower():
                return round(random.uniform(0, 100), 2)
            else:
                return round(random.uniform(0, 1000), 2)
        elif data_type == TestDataType.INVALID:
            return -999.99
        else:  # EDGE_CASE
            return random.choice([0.0, 0.01, 999999.99, float("inf"), float("-inf")])

    def _generate_datetime_value(self, data_type: TestDataType) -> str:
        """Generate datetime test values (as ISO strings)"""
        if data_type == TestDataType.VALID:
            # Random date within the last year
            days_ago = random.randint(0, 365)
            date = datetime.now() - timedelta(days=days_ago)
            return date.isoformat()
        elif data_type == TestDataType.INVALID:
            return "invalid-date-format"
        else:  # EDGE_CASE
            return random.choice(
                [
                    "1970-01-01T00:00:00",
                    "2099-12-31T23:59:59",
                    datetime.now().isoformat(),
                    (datetime.now() + timedelta(days=365)).isoformat(),
                ]
            )

    def _generate_list_value(self, param: ParameterInfo, data_type: TestDataType) -> List[Any]:
        """Generate list test values"""
        if data_type == TestDataType.VALID:
            # Generate a list of 1-5 items
            size = random.randint(1, 5)
            if "skill" in param.name.lower():
                return random.sample(["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript"], min(size, 7))
            elif "tag" in param.name.lower():
                return random.sample(["backend", "frontend", "devops", "ml", "data"], min(size, 5))
            else:
                return [f"item_{i}" for i in range(size)]
        elif data_type == TestDataType.INVALID:
            # Invalid list (empty when required, or wrong type items)
            return []
        else:  # EDGE_CASE
            # Edge cases: empty list, single item, many items
            return random.choice([[], ["single"], [f"item_{i}" for i in range(100)]])

    def _generate_model_data(self, model: Type[BaseModel], data_type: TestDataType) -> Dict[str, Any]:
        """
        Generate test data for a Pydantic model.

        Args:
            model: The Pydantic model class
            data_type: Type of test data to generate

        Returns:
            Dictionary of field names to values
        """
        data = {}

        # Get model fields
        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation
            is_required = field_info.is_required()

            # Skip optional fields for invalid/edge cases sometimes
            if not is_required and data_type != TestDataType.VALID and random.random() < 0.5:
                continue

            # Create a mock parameter info for generation
            mock_param = ParameterInfo(
                name=field_name,
                location=ParameterLocation.BODY,
                type_annotation=field_type,
                required=is_required,
                default=field_info.default if field_info.default is not None else None,
            )

            data[field_name] = self._generate_parameter_value(mock_param, data_type)

        return data

    def generate_valid_job_data(self) -> Dict[str, Any]:
        """Generate valid job creation data"""
        return {
            "title": random.choice(["Senior Software Engineer", "Product Manager", "Data Scientist", "DevOps Engineer"]),
            "company": random.choice(["Google", "Microsoft", "Amazon", "Apple", "Meta"]),
            "location": random.choice(["San Francisco, CA", "New York, NY", "Seattle, WA", "Remote"]),
            "description": "Exciting opportunity to work on cutting-edge technology with a great team.",
            "url": f"https://example.com/jobs/{random.randint(1000, 9999)}",
            "salary_min": random.randint(80000, 120000),
            "salary_max": random.randint(150000, 250000),
            "job_type": random.choice(["full-time", "part-time", "contract"]),
            "remote": random.choice([True, False]),
            "tech_stack": random.sample(["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"], 3),
        }

    def generate_valid_application_data(self, job_id: int = 1) -> Dict[str, Any]:
        """Generate valid application creation data"""
        return {
            "job_id": job_id,
            "status": random.choice(["interested", "applied", "interview", "offer"]),
            "applied_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "notes": "Applied through company website. Received confirmation email.",
        }

    def generate_valid_user_data(self) -> Dict[str, Any]:
        """Generate valid user creation data"""
        username = f"user_{random.randint(1000, 9999)}"
        return {
            "username": username,
            "email": f"{username}@example.com",
            "password": "SecurePassword123!",
            "skills": random.sample(["Python", "JavaScript", "Java", "C++", "Go", "Rust"], 3),
            "preferred_locations": random.sample(["San Francisco", "New York", "Seattle", "Remote"], 2),
            "experience_level": random.choice(["junior", "mid", "senior", "lead"]),
        }

    def generate_search_query_data(self) -> Dict[str, Any]:
        """Generate valid search query parameters"""
        return {
            "query": random.choice(["software engineer", "data scientist", "product manager", "devops"]),
            "location": random.choice(["San Francisco", "New York", "Remote", None]),
            "remote": random.choice([True, False, None]),
            "min_salary": random.choice([80000, 100000, 120000, None]),
            "max_salary": random.choice([150000, 200000, 250000, None]),
            "skip": 0,
            "limit": random.choice([10, 20, 50]),
        }

    def generate_filter_data(self) -> Dict[str, Any]:
        """Generate valid filter parameters"""
        return {
            "status": random.choice(["active", "applied", "interview", "offer", "rejected", None]),
            "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "company": random.choice(["Google", "Microsoft", "Amazon", None]),
        }

    def generate_bulk_operation_data(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Generate data for bulk operations.

        Args:
            count: Number of items to generate

        Returns:
            List of data dictionaries
        """
        return [self.generate_valid_job_data() for _ in range(count)]

    def generate_edge_case_strings(self) -> List[str]:
        """Generate a list of edge case strings for testing"""
        return [
            "",  # Empty string
            " ",  # Single space
            "   ",  # Multiple spaces
            "a",  # Single character
            "A" * 255,  # Maximum typical length
            "A" * 1000,  # Very long string
            "Test with émojis 🚀🎉",  # Unicode
            "Test\nwith\nnewlines",  # Newlines
            "Test\twith\ttabs",  # Tabs
            "Test with 'quotes'",  # Single quotes
            'Test with "quotes"',  # Double quotes
            "Test with <html>",  # HTML
            "Test with <script>alert('xss')</script>",  # XSS attempt
            "'; DROP TABLE users; --",  # SQL injection attempt
            "../../../etc/passwd",  # Path traversal
            "null",  # String "null"
            "undefined",  # String "undefined"
            "NaN",  # String "NaN"
        ]

    def generate_edge_case_numbers(self) -> List[int]:
        """Generate a list of edge case numbers for testing"""
        return [
            0,  # Zero
            1,  # One
            -1,  # Negative one
            999999,  # Large positive
            -999999,  # Large negative
            2147483647,  # Max 32-bit int
            -2147483648,  # Min 32-bit int
        ]

    def generate_edge_case_dates(self) -> List[str]:
        """Generate a list of edge case dates for testing"""
        return [
            "1970-01-01T00:00:00",  # Unix epoch
            "2099-12-31T23:59:59",  # Far future
            datetime.now().isoformat(),  # Current time
            (datetime.now() - timedelta(days=365 * 10)).isoformat(),  # 10 years ago
            (datetime.now() + timedelta(days=365 * 10)).isoformat(),  # 10 years future
            "invalid-date",  # Invalid format
            "2023-02-30T00:00:00",  # Invalid date
        ]
