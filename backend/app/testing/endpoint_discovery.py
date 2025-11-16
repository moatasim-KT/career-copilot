"""
Endpoint Discovery System

Automatically discovers and catalogs all FastAPI endpoints with their metadata.
"""

import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type, get_args, get_origin

from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)


class ParameterLocation(str, Enum):
	"""Location of a parameter in the request."""

	PATH = "path"
	QUERY = "query"
	HEADER = "header"
	COOKIE = "cookie"
	BODY = "body"


@dataclass
class ParameterInfo:
	"""Rich metadata captured for an endpoint parameter."""

	name: str
	location: ParameterLocation
	type_annotation: Type
	required: bool
	default: Any = None
	description: Optional[str] = None
	example: Optional[Any] = None

	def __repr__(self) -> str:
		req_str = "required" if self.required else "optional"
		annotation_name = getattr(self.type_annotation, "__name__", str(self.type_annotation))
		return f"<Parameter {self.name}: {annotation_name} ({self.location.value}, {req_str})>"


@dataclass
class EndpointInfo:
	"""Comprehensive information about a FastAPI endpoint."""

	path: str
	method: str
	name: str
	tags: List[str] = field(default_factory=list)
	summary: Optional[str] = None
	description: Optional[str] = None
	parameters: List[ParameterInfo] = field(default_factory=list)
	request_body_model: Optional[Type[BaseModel]] = None
	response_model: Optional[Type] = None
	status_code: int = 200
	requires_auth: bool = False
	deprecated: bool = False

	def __repr__(self) -> str:
		return f"<Endpoint {self.method} {self.path} ({self.name})>"

	def get_path_parameters(self) -> List[ParameterInfo]:
		"""Get all path parameters."""
		return [p for p in self.parameters if p.location == ParameterLocation.PATH]

	def get_query_parameters(self) -> List[ParameterInfo]:
		"""Get all query parameters."""
		return [p for p in self.parameters if p.location == ParameterLocation.QUERY]

	def get_body_parameters(self) -> List[ParameterInfo]:
		"""Get all body parameters."""
		return [p for p in self.parameters if p.location == ParameterLocation.BODY]

	def get_required_parameters(self) -> List[ParameterInfo]:
		"""Get all required parameters."""
		return [p for p in self.parameters if p.required]


class EndpointDiscovery:
	"""
	Discovers and catalogs all FastAPI endpoints with their metadata.

	This class provides comprehensive endpoint discovery capabilities including:
	- Enumerating all registered routes
	- Extracting parameter information
	- Identifying authentication requirements
	- Categorizing endpoints by tags and functionality
	"""

	def __init__(self, app: FastAPI):
		"""
		Initialize the endpoint discovery system.

		Args:
		    app: The FastAPI application instance registered with all routes.
		"""
		self.app = app
		self._endpoints: List[EndpointInfo] = []
		self._endpoint_map: Dict[str, EndpointInfo] = {}

	def discover_endpoints(self) -> List[EndpointInfo]:
		"""
		Discover all endpoints in the FastAPI application.

		Returns:
		    List of :class:`EndpointInfo` objects containing metadata for each endpoint.
		"""
		self._endpoints = []
		logger.debug("Starting endpoint discovery for %d routes", len(self.app.routes))

		for route in self.app.routes:
			if isinstance(route, APIRoute):
				endpoint_info = self._extract_endpoint_info(route)
				self._endpoints.append(endpoint_info)
				logger.debug("Discovered endpoint %s %s", endpoint_info.method, endpoint_info.path)

		logger.info("Endpoint discovery complete: %d endpoints cataloged", len(self._endpoints))

		return self._endpoints

	def _extract_endpoint_info(self, route: APIRoute) -> EndpointInfo:
		"""
		Extract comprehensive information from a FastAPI route.

		Args:
		    route: The APIRoute to extract information from.

		Returns:
		    EndpointInfo object with all extracted metadata.
		"""
		# Extract basic information
		path = route.path
		methods = route.methods or {"GET"}
		method = next(iter(methods))
		name = route.name or "unnamed"
		tags = list(route.tags) if route.tags else []
		summary = route.summary
		description = route.description
		response_model = route.response_model
		status_code = route.status_code or 200
		deprecated = route.deprecated or False

		# Extract parameters
		parameters = self._extract_parameters(route)

		# Check if authentication is required
		requires_auth = self._check_auth_requirement(route)

		# Extract request body model
		request_body_model = self._extract_request_body_model(route)

		return EndpointInfo(
			path=path,
			method=method,
			name=name,
			tags=tags,
			summary=summary,
			description=description,
			parameters=parameters,
			request_body_model=request_body_model,
			response_model=response_model,
			status_code=status_code,
			requires_auth=requires_auth,
			deprecated=deprecated,
		)

	def _extract_parameters(self, route: APIRoute) -> List[ParameterInfo]:
		"""
		Extract parameter information from a route.

		Args:
		    route: The APIRoute to extract parameters from.

		Returns:
		    List of :class:`ParameterInfo` instances ordered by declaration.
		"""
		parameters = []

		# Get the endpoint function signature
		endpoint_func = route.endpoint
		sig = inspect.signature(endpoint_func)

		for param_name, param in sig.parameters.items():
			# Skip special parameters
			if param_name in ["self", "cls", "request", "websocket", "db", "current_user"]:
				continue

			# Determine parameter location and type
			param_info = self._analyze_parameter(param_name, param, route)
			if param_info:
				parameters.append(param_info)

		return parameters

	def _analyze_parameter(self, param_name: str, param: inspect.Parameter, route: APIRoute) -> Optional[ParameterInfo]:
		"""
		Analyze a single parameter to extract its metadata.

		Args:
		    param_name: Name of the parameter.
		    param: The parameter object from inspect describing type/default.
		    route: The route this parameter belongs to.

		Returns:
		    ParameterInfo object or ``None`` if the parameter should be skipped.
		"""
		# Get type annotation
		type_annotation = param.annotation if param.annotation != inspect.Parameter.empty else Any

		# Determine if required
		required = param.default == inspect.Parameter.empty

		# Get default value
		default = param.default if param.default != inspect.Parameter.empty else None

		# Determine parameter location
		location = self._determine_parameter_location(param_name, type_annotation, route)

		# Skip if we couldn't determine location
		if location is None:
			return None

		return ParameterInfo(
			name=param_name,
			location=location,
			type_annotation=type_annotation,
			required=required,
			default=default,
		)

	def _determine_parameter_location(self, param_name: str, type_annotation: Type, route: APIRoute) -> Optional[ParameterLocation]:
		"""
		Determine where a parameter comes from (path, query, body, etc.).

		Args:
		    param_name: Name of the parameter to inspect.
		    type_annotation: Type annotation of the parameter.
		    route: The route this parameter belongs to.

		Returns:
		    ParameterLocation enum value or ``None`` when the location cannot be determined.
		"""
		# Check if it's a path parameter
		if f"{{{param_name}}}" in route.path:
			return ParameterLocation.PATH

		# Check if it's a Pydantic model (body parameter)
		try:
			if isinstance(type_annotation, type) and issubclass(type_annotation, BaseModel):
				return ParameterLocation.BODY
		except TypeError:
			pass

		# Check for Optional types that might contain BaseModel
		origin = get_origin(type_annotation)
		if origin is not None:
			args = get_args(type_annotation)
			for arg in args:
				try:
					if isinstance(arg, type) and issubclass(arg, BaseModel):
						return ParameterLocation.BODY
				except TypeError:
					pass

		# Default to query parameter for simple types
		return ParameterLocation.QUERY

	def _extract_request_body_model(self, route: APIRoute) -> Optional[Type[BaseModel]]:
		"""
		Extract the request body model if present.

		Args:
		    route: The APIRoute to extract from.

		Returns:
		    The Pydantic model class or ``None`` when the endpoint does not accept a body model.
		"""
		endpoint_func = route.endpoint
		sig = inspect.signature(endpoint_func)

		for param in sig.parameters.values():
			if param.annotation != inspect.Parameter.empty:
				try:
					if isinstance(param.annotation, type) and issubclass(param.annotation, BaseModel):
						return param.annotation
				except TypeError:
					pass

		return None

	def _check_auth_requirement(self, route: APIRoute) -> bool:
		"""
		Check if an endpoint requires authentication.

		Args:
		    route: The APIRoute to check.

		Returns:
		    True if authentication is required, False otherwise.
		"""
		# Check if the endpoint has a dependency on get_current_user
		endpoint_func = route.endpoint
		sig = inspect.signature(endpoint_func)

		for param_name, param in sig.parameters.items():
			if param_name == "current_user":
				return True

		return False

	def categorize_endpoints(self) -> Dict[str, List[EndpointInfo]]:
		"""
		Categorize endpoints by their tags.

		Returns:
		    Dictionary mapping tag names to lists of endpoints, including an ``"untagged"`` bucket.
		"""
		if not self._endpoints:
			self.discover_endpoints()

		categorized: Dict[str, List[EndpointInfo]] = {}

		for endpoint in self._endpoints:
			if not endpoint.tags:
				# Add to "untagged" category
				if "untagged" not in categorized:
					categorized["untagged"] = []
				categorized["untagged"].append(endpoint)
			else:
				# Add to each tag category
				for tag in endpoint.tags:
					if tag not in categorized:
						categorized[tag] = []
					categorized[tag].append(endpoint)

		logger.debug(
			"Categorized %d endpoints into %d tag buckets",
			len(self._endpoints),
			len(categorized),
		)
		return categorized

	def generate_endpoint_map(self) -> Dict[str, EndpointInfo]:
		"""
		Generate a map of endpoint keys to EndpointInfo objects.

		Returns:
		    Dictionary mapping "METHOD /path" to EndpointInfo instances for O(1) lookups.
		"""
		if not self._endpoints:
			self.discover_endpoints()

		self._endpoint_map = {}
		for endpoint in self._endpoints:
			key = f"{endpoint.method} {endpoint.path}"
			self._endpoint_map[key] = endpoint

		logger.debug("Generated endpoint map containing %d entries", len(self._endpoint_map))
		return self._endpoint_map

	def get_endpoint_by_path(self, method: str, path: str) -> Optional[EndpointInfo]:
		"""
		Get endpoint information by method and path.

		Args:
		    method: HTTP method (GET, POST, etc.)
		    path: Endpoint path

		Returns:
		    EndpointInfo object or None if not found
		"""
		if not self._endpoint_map:
			self.generate_endpoint_map()

		key = f"{method.upper()} {path}"
		return self._endpoint_map.get(key)

	def get_endpoints_by_tag(self, tag: str) -> List[EndpointInfo]:
		"""
		Get all endpoints with a specific tag.

		Args:
		    tag: The tag to filter by

		Returns:
		    List of EndpointInfo objects
		"""
		categorized = self.categorize_endpoints()
		return categorized.get(tag, [])

	def get_endpoints_requiring_auth(self) -> List[EndpointInfo]:
		"""
		Get all endpoints that require authentication.

		Returns:
		    List of EndpointInfo objects
		"""
		if not self._endpoints:
			self.discover_endpoints()

		return [e for e in self._endpoints if e.requires_auth]

	def get_endpoints_by_method(self, method: str) -> List[EndpointInfo]:
		"""
		Get all endpoints for a specific HTTP method.

		Args:
		    method: HTTP method (GET, POST, etc.)

		Returns:
		    List of EndpointInfo objects
		"""
		if not self._endpoints:
			self.discover_endpoints()

		return [e for e in self._endpoints if e.method == method.upper()]

	def get_statistics(self) -> Dict[str, Any]:
		"""
		Get statistics about discovered endpoints.

		Returns:
		    Dictionary with counts grouped by method, tag, and security posture.
		"""
		if not self._endpoints:
			self.discover_endpoints()

		categorized = self.categorize_endpoints()

		method_counts: Dict[str, int] = {}
		for endpoint in self._endpoints:
			method_counts[endpoint.method] = method_counts.get(endpoint.method, 0) + 1

		stats = {
			"total_endpoints": len(self._endpoints),
			"endpoints_by_method": method_counts,
			"endpoints_by_tag": {tag: len(endpoints) for tag, endpoints in categorized.items()},
			"endpoints_requiring_auth": len(self.get_endpoints_requiring_auth()),
			"deprecated_endpoints": len([e for e in self._endpoints if e.deprecated]),
		}
		logger.debug(
			"Endpoint statistics calculated: %d total, %d require auth",
			stats["total_endpoints"],
			stats["endpoints_requiring_auth"],
		)
		return stats

	def export_to_dict(self) -> List[Dict[str, Any]]:
		"""
		Export all endpoint information to a list of dictionaries.

		Returns:
		    List of dictionaries containing normalized endpoint information for serialization.
		"""
		if not self._endpoints:
			self.discover_endpoints()

		result = []
		for endpoint in self._endpoints:
			result.append(
				{
					"path": endpoint.path,
					"method": endpoint.method,
					"name": endpoint.name,
					"tags": endpoint.tags,
					"summary": endpoint.summary,
					"description": endpoint.description,
					"parameters": [
						{
							"name": p.name,
							"location": p.location.value,
							"type": str(p.type_annotation),
							"required": p.required,
							"default": str(p.default) if p.default is not None else None,
						}
						for p in endpoint.parameters
					],
					"request_body_model": endpoint.request_body_model.__name__ if endpoint.request_body_model else None,
					"response_model": str(endpoint.response_model) if endpoint.response_model else None,
					"status_code": endpoint.status_code,
					"requires_auth": endpoint.requires_auth,
					"deprecated": endpoint.deprecated,
				}
			)

		logger.debug("Exported %d endpoints to dictionary format", len(result))
		return result
