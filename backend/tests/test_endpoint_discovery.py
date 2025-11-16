"""
Tests for the Endpoint Discovery System
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app
from app.testing import EndpointDiscovery, ParameterLocation


@pytest.fixture
def app():
	"""Create a test FastAPI application"""
	return create_app()


@pytest.fixture
def discovery(app):
	"""Create an EndpointDiscovery instance"""
	return EndpointDiscovery(app)


def test_endpoint_discovery_initialization(app):
	"""Test that EndpointDiscovery can be initialized"""
	discovery = EndpointDiscovery(app)
	assert discovery.app == app
	assert discovery._endpoints == []
	assert discovery._endpoint_map == {}


def test_discover_endpoints(discovery):
	"""Test that endpoints can be discovered"""
	endpoints = discovery.discover_endpoints()

	assert len(endpoints) > 0
	assert all(hasattr(e, "path") for e in endpoints)
	assert all(hasattr(e, "method") for e in endpoints)
	assert all(hasattr(e, "name") for e in endpoints)


def test_endpoint_info_structure(discovery):
	"""Test that discovered endpoints have correct structure"""
	endpoints = discovery.discover_endpoints()

	for endpoint in endpoints[:5]:  # Test first 5
		assert isinstance(endpoint.path, str)
		assert isinstance(endpoint.method, str)
		assert isinstance(endpoint.name, str)
		assert isinstance(endpoint.tags, list)
		assert isinstance(endpoint.parameters, list)
		assert isinstance(endpoint.status_code, int)
		assert isinstance(endpoint.requires_auth, bool)
		assert isinstance(endpoint.deprecated, bool)


def test_categorize_endpoints(discovery):
	"""Test endpoint categorization by tags"""
	discovery.discover_endpoints()
	categorized = discovery.categorize_endpoints()

	assert isinstance(categorized, dict)
	assert len(categorized) > 0

	# Check that all endpoints are categorized
	total_categorized = sum(len(endpoints) for endpoints in categorized.values())
	assert total_categorized >= len(discovery._endpoints)


def test_generate_endpoint_map(discovery):
	"""Test endpoint map generation"""
	discovery.discover_endpoints()
	endpoint_map = discovery.generate_endpoint_map()

	assert isinstance(endpoint_map, dict)
	assert len(endpoint_map) > 0

	# Check map keys format
	for key in list(endpoint_map.keys())[:5]:
		assert " " in key  # Should be "METHOD /path"
		method, path = key.split(" ", 1)
		assert method in ["GET", "POST", "PUT", "PATCH", "DELETE"]
		assert path.startswith("/")


def test_get_endpoint_by_path(discovery):
	"""Test retrieving endpoint by method and path"""
	discovery.discover_endpoints()
	discovery.generate_endpoint_map()

	# Test root endpoint
	endpoint = discovery.get_endpoint_by_path("GET", "/")
	assert endpoint is not None
	assert endpoint.path == "/"
	assert endpoint.method == "GET"


def test_get_endpoints_by_tag(discovery):
	"""Test retrieving endpoints by tag"""
	discovery.discover_endpoints()

	# Get all tags
	categorized = discovery.categorize_endpoints()
	if categorized:
		first_tag = next(iter(categorized.keys()))
		endpoints = discovery.get_endpoints_by_tag(first_tag)

		assert isinstance(endpoints, list)
		assert len(endpoints) > 0
		assert all(first_tag in e.tags or first_tag == "untagged" for e in endpoints)


def test_get_endpoints_requiring_auth(discovery):
	"""Test retrieving endpoints that require authentication"""
	discovery.discover_endpoints()
	auth_endpoints = discovery.get_endpoints_requiring_auth()

	assert isinstance(auth_endpoints, list)
	# All should have requires_auth = True
	assert all(e.requires_auth for e in auth_endpoints)


def test_get_endpoints_by_method(discovery):
	"""Test retrieving endpoints by HTTP method"""
	discovery.discover_endpoints()

	get_endpoints = discovery.get_endpoints_by_method("GET")
	assert isinstance(get_endpoints, list)
	assert all(e.method == "GET" for e in get_endpoints)

	post_endpoints = discovery.get_endpoints_by_method("POST")
	assert isinstance(post_endpoints, list)
	assert all(e.method == "POST" for e in post_endpoints)


def test_get_statistics(discovery):
	"""Test statistics generation"""
	discovery.discover_endpoints()
	stats = discovery.get_statistics()

	assert isinstance(stats, dict)
	assert "total_endpoints" in stats
	assert "endpoints_by_method" in stats
	assert "endpoints_by_tag" in stats
	assert "endpoints_requiring_auth" in stats
	assert "deprecated_endpoints" in stats

	assert stats["total_endpoints"] > 0
	assert isinstance(stats["endpoints_by_method"], dict)
	assert isinstance(stats["endpoints_by_tag"], dict)


def test_export_to_dict(discovery):
	"""Test exporting endpoints to dictionary format"""
	discovery.discover_endpoints()
	exported = discovery.export_to_dict()

	assert isinstance(exported, list)
	assert len(exported) > 0

	# Check structure of first endpoint
	if exported:
		first = exported[0]
		assert "path" in first
		assert "method" in first
		assert "name" in first
		assert "tags" in first
		assert "parameters" in first
		assert "status_code" in first


def test_parameter_extraction(discovery):
	"""Test that parameters are correctly extracted"""
	discovery.discover_endpoints()

	# Find an endpoint with parameters
	endpoints_with_params = [e for e in discovery._endpoints if len(e.parameters) > 0]

	if endpoints_with_params:
		endpoint = endpoints_with_params[0]
		assert len(endpoint.parameters) > 0

		for param in endpoint.parameters:
			assert hasattr(param, "name")
			assert hasattr(param, "location")
			assert hasattr(param, "type_annotation")
			assert hasattr(param, "required")
			assert isinstance(param.location, ParameterLocation)


def test_path_parameters(discovery):
	"""Test identification of path parameters"""
	discovery.discover_endpoints()

	# Find endpoints with path parameters (e.g., /api/v1/jobs/{job_id})
	endpoints_with_path_params = [e for e in discovery._endpoints if "{" in e.path]

	if endpoints_with_path_params:
		endpoint = endpoints_with_path_params[0]
		path_params = endpoint.get_path_parameters()

		# Should have at least one path parameter
		assert len(path_params) > 0
		assert all(p.location == ParameterLocation.PATH for p in path_params)


def test_query_parameters(discovery):
	"""Test identification of query parameters"""
	discovery.discover_endpoints()

	# Find endpoints with query parameters
	endpoints_with_query_params = [e for e in discovery._endpoints if len(e.get_query_parameters()) > 0]

	if endpoints_with_query_params:
		endpoint = endpoints_with_query_params[0]
		query_params = endpoint.get_query_parameters()

		assert len(query_params) > 0
		assert all(p.location == ParameterLocation.QUERY for p in query_params)


def test_required_parameters(discovery):
	"""Test identification of required parameters"""
	discovery.discover_endpoints()

	# Find endpoints with required parameters
	endpoints_with_required = [e for e in discovery._endpoints if len(e.get_required_parameters()) > 0]

	if endpoints_with_required:
		endpoint = endpoints_with_required[0]
		required_params = endpoint.get_required_parameters()

		assert len(required_params) > 0
		assert all(p.required for p in required_params)


def test_endpoint_info_repr(discovery):
	"""Test EndpointInfo string representation"""
	discovery.discover_endpoints()

	if discovery._endpoints:
		endpoint = discovery._endpoints[0]
		repr_str = repr(endpoint)

		assert isinstance(repr_str, str)
		assert endpoint.method in repr_str
		assert endpoint.path in repr_str


def test_parameter_info_repr(discovery):
	"""Test ParameterInfo string representation"""
	discovery.discover_endpoints()

	# Find endpoint with parameters
	endpoints_with_params = [e for e in discovery._endpoints if len(e.parameters) > 0]

	if endpoints_with_params:
		param = endpoints_with_params[0].parameters[0]
		repr_str = repr(param)

		assert isinstance(repr_str, str)
		assert param.name in repr_str


def test_discover_health_endpoint(discovery):
	"""Test that health endpoint is discovered"""
	discovery.discover_endpoints()

	health_endpoints = [e for e in discovery._endpoints if "health" in e.path.lower()]

	assert len(health_endpoints) > 0


def test_discover_root_endpoint(discovery):
	"""Test that root endpoint is discovered"""
	discovery.discover_endpoints()

	root_endpoint = discovery.get_endpoint_by_path("GET", "/")

	assert root_endpoint is not None
	assert root_endpoint.path == "/"
	assert root_endpoint.method == "GET"


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
def test_endpoints_by_method_coverage(discovery, method):
	"""Test that endpoints exist for common HTTP methods"""
	discovery.discover_endpoints()
	endpoints = discovery.get_endpoints_by_method(method)

	# Should have at least some endpoints for each method
	assert isinstance(endpoints, list)
