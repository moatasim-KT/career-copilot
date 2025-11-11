"""
Tests for the Test Data Generator
"""

import pytest
from datetime import datetime

from app.testing import TestDataGenerator, TestDataType
from app.testing.endpoint_discovery import EndpointInfo, ParameterInfo, ParameterLocation


@pytest.fixture
def generator():
    """Create a TestDataGenerator instance"""
    return TestDataGenerator(seed=42)


def test_generator_initialization():
    """Test that TestDataGenerator can be initialized"""
    generator = TestDataGenerator()
    assert generator is not None

    # Test with seed
    generator_with_seed = TestDataGenerator(seed=42)
    assert generator_with_seed is not None


def test_generate_int_value(generator):
    """Test integer value generation"""
    param = ParameterInfo(name="id", location=ParameterLocation.PATH, type_annotation=int, required=True)

    # Valid
    value = generator._generate_int_value(param, TestDataType.VALID)
    assert isinstance(value, int)
    assert value > 0

    # Invalid
    value = generator._generate_int_value(param, TestDataType.INVALID)
    assert isinstance(value, int)
    assert value < 0

    # Edge case
    value = generator._generate_int_value(param, TestDataType.EDGE_CASE)
    assert isinstance(value, int)


def test_generate_string_value(generator):
    """Test string value generation"""
    param = ParameterInfo(name="name", location=ParameterLocation.QUERY, type_annotation=str, required=True)

    # Valid
    value = generator._generate_string_value(param, TestDataType.VALID)
    assert isinstance(value, str)
    assert len(value) > 0

    # Invalid
    value = generator._generate_string_value(param, TestDataType.INVALID)
    assert isinstance(value, str)

    # Edge case
    value = generator._generate_string_value(param, TestDataType.EDGE_CASE)
    assert isinstance(value, str)


def test_generate_bool_value(generator):
    """Test boolean value generation"""
    value = generator._generate_bool_value(TestDataType.VALID)
    assert isinstance(value, bool)


def test_generate_float_value(generator):
    """Test float value generation"""
    param = ParameterInfo(name="salary", location=ParameterLocation.QUERY, type_annotation=float, required=True)

    # Valid
    value = generator._generate_float_value(param, TestDataType.VALID)
    assert isinstance(value, float)
    assert value > 0

    # Invalid
    value = generator._generate_float_value(param, TestDataType.INVALID)
    assert isinstance(value, float)


def test_generate_datetime_value(generator):
    """Test datetime value generation"""
    # Valid
    value = generator._generate_datetime_value(TestDataType.VALID)
    assert isinstance(value, str)
    # Should be valid ISO format
    datetime.fromisoformat(value)

    # Invalid
    value = generator._generate_datetime_value(TestDataType.INVALID)
    assert isinstance(value, str)


def test_generate_list_value(generator):
    """Test list value generation"""
    param = ParameterInfo(name="skills", location=ParameterLocation.QUERY, type_annotation=list, required=True)

    # Valid
    value = generator._generate_list_value(param, TestDataType.VALID)
    assert isinstance(value, list)

    # Invalid
    value = generator._generate_list_value(param, TestDataType.INVALID)
    assert isinstance(value, list)

    # Edge case
    value = generator._generate_list_value(param, TestDataType.EDGE_CASE)
    assert isinstance(value, list)


def test_generate_valid_job_data(generator):
    """Test job data generation"""
    job_data = generator.generate_valid_job_data()

    assert isinstance(job_data, dict)
    assert "title" in job_data
    assert "company" in job_data
    assert "location" in job_data
    assert "description" in job_data
    assert "url" in job_data
    assert "tech_stack" in job_data

    assert isinstance(job_data["title"], str)
    assert isinstance(job_data["company"], str)
    assert isinstance(job_data["tech_stack"], list)


def test_generate_valid_application_data(generator):
    """Test application data generation"""
    app_data = generator.generate_valid_application_data(job_id=1)

    assert isinstance(app_data, dict)
    assert "job_id" in app_data
    assert "status" in app_data
    assert "applied_date" in app_data

    assert app_data["job_id"] == 1
    assert isinstance(app_data["status"], str)


def test_generate_valid_user_data(generator):
    """Test user data generation"""
    user_data = generator.generate_valid_user_data()

    assert isinstance(user_data, dict)
    assert "username" in user_data
    assert "email" in user_data
    assert "password" in user_data
    assert "skills" in user_data

    assert isinstance(user_data["username"], str)
    assert isinstance(user_data["email"], str)
    assert "@" in user_data["email"]
    assert isinstance(user_data["skills"], list)


def test_generate_search_query_data(generator):
    """Test search query data generation"""
    search_data = generator.generate_search_query_data()

    assert isinstance(search_data, dict)
    assert "query" in search_data
    assert "skip" in search_data
    assert "limit" in search_data

    assert isinstance(search_data["query"], str)
    assert isinstance(search_data["skip"], int)
    assert isinstance(search_data["limit"], int)


def test_generate_filter_data(generator):
    """Test filter data generation"""
    filter_data = generator.generate_filter_data()

    assert isinstance(filter_data, dict)
    assert "start_date" in filter_data
    assert "end_date" in filter_data


def test_generate_bulk_operation_data(generator):
    """Test bulk operation data generation"""
    bulk_data = generator.generate_bulk_operation_data(count=5)

    assert isinstance(bulk_data, list)
    assert len(bulk_data) == 5
    assert all(isinstance(item, dict) for item in bulk_data)


def test_generate_edge_case_strings(generator):
    """Test edge case string generation"""
    edge_cases = generator.generate_edge_case_strings()

    assert isinstance(edge_cases, list)
    assert len(edge_cases) > 0
    assert "" in edge_cases  # Empty string
    assert any(len(s) > 100 for s in edge_cases)  # Long strings


def test_generate_edge_case_numbers(generator):
    """Test edge case number generation"""
    edge_cases = generator.generate_edge_case_numbers()

    assert isinstance(edge_cases, list)
    assert len(edge_cases) > 0
    assert 0 in edge_cases
    assert any(n < 0 for n in edge_cases)  # Negative numbers
    assert any(n > 1000000 for n in edge_cases)  # Large numbers


def test_generate_edge_case_dates(generator):
    """Test edge case date generation"""
    edge_cases = generator.generate_edge_case_dates()

    assert isinstance(edge_cases, list)
    assert len(edge_cases) > 0
    assert any("1970" in d for d in edge_cases)  # Unix epoch


def test_contextual_string_generation(generator):
    """Test that strings are generated contextually based on parameter name"""
    # Email parameter
    email_param = ParameterInfo(name="email", location=ParameterLocation.QUERY, type_annotation=str, required=True)
    email_value = generator._generate_string_value(email_param, TestDataType.VALID)
    assert "@" in email_value

    # Name parameter
    name_param = ParameterInfo(name="name", location=ParameterLocation.QUERY, type_annotation=str, required=True)
    name_value = generator._generate_string_value(name_param, TestDataType.VALID)
    assert len(name_value) > 0

    # URL parameter
    url_param = ParameterInfo(name="url", location=ParameterLocation.QUERY, type_annotation=str, required=True)
    url_value = generator._generate_string_value(url_param, TestDataType.VALID)
    assert url_value.startswith("http")


def test_contextual_int_generation(generator):
    """Test that integers are generated contextually based on parameter name"""
    # ID parameter
    id_param = ParameterInfo(name="id", location=ParameterLocation.PATH, type_annotation=int, required=True)
    id_value = generator._generate_int_value(id_param, TestDataType.VALID)
    assert id_value > 0

    # Limit parameter
    limit_param = ParameterInfo(name="limit", location=ParameterLocation.QUERY, type_annotation=int, required=False)
    limit_value = generator._generate_int_value(limit_param, TestDataType.VALID)
    assert limit_value > 0
    assert limit_value <= 100


def test_reproducibility_with_seed():
    """Test that using the same seed produces the same results"""
    gen1 = TestDataGenerator(seed=42)
    gen2 = TestDataGenerator(seed=42)

    job1 = gen1.generate_valid_job_data()
    job2 = gen2.generate_valid_job_data()

    # Should generate the same data with same seed
    assert job1["title"] == job2["title"]
    assert job1["company"] == job2["company"]


def test_generate_test_data_for_endpoint(generator):
    """Test generating test data for a complete endpoint"""
    # Create a mock endpoint
    endpoint = EndpointInfo(
        path="/api/v1/jobs/{job_id}",
        method="GET",
        name="get_job",
        parameters=[
            ParameterInfo(name="job_id", location=ParameterLocation.PATH, type_annotation=int, required=True),
            ParameterInfo(name="include_details", location=ParameterLocation.QUERY, type_annotation=bool, required=False),
        ],
    )

    # Generate valid test data
    test_data = generator.generate_test_data(endpoint, TestDataType.VALID)

    assert isinstance(test_data, dict)
    assert "job_id" in test_data
    assert isinstance(test_data["job_id"], int)


def test_generate_multiple_test_cases(generator):
    """Test generating multiple test cases for an endpoint"""
    endpoint = EndpointInfo(
        path="/api/v1/jobs",
        method="GET",
        name="list_jobs",
        parameters=[
            ParameterInfo(name="skip", location=ParameterLocation.QUERY, type_annotation=int, required=False),
            ParameterInfo(name="limit", location=ParameterLocation.QUERY, type_annotation=int, required=False),
        ],
    )

    test_cases = generator.generate_multiple_test_cases(endpoint)

    assert isinstance(test_cases, list)
    assert len(test_cases) > 0

    # Should have different types of test cases
    test_types = [tc["type"] for tc in test_cases]
    assert TestDataType.VALID in test_types or "valid" in test_types
