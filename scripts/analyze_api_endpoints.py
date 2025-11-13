#!/usr/bin/env python3
"""
Automated API endpoint discovery and documentation generation.
Scans FastAPI routes and generates comprehensive API documentation.
"""

import importlib
import inspect
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add backend to path
sys.path.insert(0, "backend")


@dataclass
class APIEndpoint:
	"""API endpoint metadata"""

	path: str
	method: str
	summary: str
	description: str
	parameters: List[Dict[str, Any]]
	request_body: Optional[Dict[str, Any]]
	responses: Dict[str, Dict[str, Any]]
	tags: List[str]
	file_path: str
	line_number: int


@dataclass
class APIModule:
	"""API module containing multiple endpoints"""

	name: str
	endpoints: List[APIEndpoint]
	dependencies: List[str]


class APIAnalyzer:
	"""Analyzes FastAPI applications to extract endpoint information"""

	def __init__(self, app_path: str):
		self.app_path = Path(app_path)
		self.endpoints: List[APIEndpoint] = []

	def analyze_app(self) -> List[APIModule]:
		"""Analyze the entire FastAPI application"""
		modules = []

		# Find all API route files
		api_files = self._find_api_files()

		for api_file in api_files:
			module = self._analyze_api_file(api_file)
			if module:
				modules.append(module)

		return modules

	def _find_api_files(self) -> List[Path]:
		"""Find all API route files"""
		api_files = []
		api_dir = self.app_path / "app" / "api"

		if api_dir.exists():
			for file_path in api_dir.rglob("*.py"):
				if file_path.name != "__init__.py":
					api_files.append(file_path)

		return api_files

	def _analyze_api_file(self, file_path: Path) -> Optional[APIModule]:
		"""Analyze a single API file"""
		try:
			# Import the module
			module_name = self._get_module_name(file_path)
			spec = importlib.util.spec_from_file_location(module_name, file_path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)

			endpoints = []
			dependencies = []

			# Extract router information
			if hasattr(module, "router"):
				router = module.router
				endpoints = self._extract_router_endpoints(router, file_path)

			# Extract dependencies
			dependencies = self._extract_dependencies(module)

			if endpoints:
				return APIModule(name=module_name, endpoints=endpoints, dependencies=dependencies)

		except Exception as e:
			print(f"Error analyzing {file_path}: {e}")

		return None

	def _extract_router_endpoints(self, router, file_path: Path) -> List[APIEndpoint]:
		"""Extract endpoints from FastAPI router"""
		endpoints = []

		for route in router.routes:
			if hasattr(route, "methods") and hasattr(route, "path"):
				for method in route.methods:
					endpoint = APIEndpoint(
						path=route.path,
						method=method,
						summary=getattr(route, "summary", ""),
						description=getattr(route, "description", ""),
						parameters=self._extract_parameters(route),
						request_body=self._extract_request_body(route),
						responses=self._extract_responses(route),
						tags=getattr(route, "tags", []),
						file_path=str(file_path),
						line_number=getattr(route, "line_number", 0),
					)
					endpoints.append(endpoint)

		return endpoints

	def _extract_parameters(self, route) -> List[Dict[str, Any]]:
		"""Extract parameter information from route"""
		parameters = []

		# Extract path parameters
		if hasattr(route, "path"):
			import re

			path_params = re.findall(r"\{([^}]+)\}", route.path)
			for param in path_params:
				parameters.append({"name": param, "in": "path", "required": True, "schema": {"type": "string"}})

		# Extract query parameters from function signature
		if hasattr(route, "endpoint"):
			sig = inspect.signature(route.endpoint)
			for param_name, param in sig.parameters.items():
				if param_name not in ["request", "response", "db"] and param.default != inspect.Parameter.empty:
					parameters.append(
						{"name": param_name, "in": "query", "required": param.default == inspect.Parameter.empty, "schema": {"type": "string"}}
					)

		return parameters

	def _extract_request_body(self, route) -> Optional[Dict[str, Any]]:
		"""Extract request body information"""
		return None

	def _extract_responses(self, route) -> Dict[str, Dict[str, Any]]:
		"""Extract response information"""
		responses = {"200": {"description": "Successful response"}}

		if hasattr(route, "responses"):
			responses.update(route.responses)

		return responses

	def _extract_dependencies(self, module) -> List[str]:
		"""Extract module dependencies"""
		dependencies = []

		try:
			source = inspect.getsource(module)
			import_lines = [line for line in source.split("\n") if line.strip().startswith("from") or line.strip().startswith("import")]

			for line in import_lines:
				if "app." in line:
					parts = line.replace("from ", "").replace("import ", "").split()
					dep = parts[0]
					if dep.startswith("app."):
						dependencies.append(dep)

		except Exception:
			pass

		return list(set(dependencies))

	def _get_module_name(self, file_path: Path) -> str:
		"""Get module name from file path"""
		relative_path = file_path.relative_to(self.app_path)
		return str(relative_path).replace("/", ".").replace(".py", "")


def main():
	"""Main entry point"""
	analyzer = APIAnalyzer("backend")

	print("🔍 Analyzing API endpoints...")
	modules = analyzer.analyze_app()

	# Generate documentation
	output = {"generated_at": "2024-01-15T10:00:00Z", "modules": [asdict(module) for module in modules]}

	# Save to file
	output_path = Path("docs/api/endpoints.json")
	output_path.parent.mkdir(parents=True, exist_ok=True)

	with open(output_path, "w") as f:
		json.dump(output, f, indent=2)

	print(f"✅ Generated API documentation for {len(modules)} modules")

	# Generate Markdown documentation
	generate_markdown_docs(modules)


def generate_markdown_docs(modules: List[APIModule]):
	"""Generate Markdown documentation from modules"""
	docs_path = Path("docs/api")
	docs_path.mkdir(parents=True, exist_ok=True)

	# Generate index
	with open(docs_path / "README.md", "w") as f:
		f.write("# API Documentation\n\n")
		f.write("This documentation is automatically generated from the codebase.\n\n")
		f.write("## Modules\n\n")

		for module in modules:
			f.write(f"- [{module.name}]({module.name}.md)\n")

		f.write(f"\n*Generated on: {modules[0].endpoints[0].generated_at if modules else 'N/A'}*\n")

	# Generate module documentation
	for module in modules:
		with open(docs_path / f"{module.name}.md", "w") as f:
			f.write(f"# {module.name}\n\n")

			if module.dependencies:
				f.write("## Dependencies\n\n")
				for dep in module.dependencies:
					f.write(f"- `{dep}`\n")
				f.write("\n")

			f.write("## Endpoints\n\n")

			for endpoint in module.endpoints:
				f.write(f"### {endpoint.method} {endpoint.path}\n\n")

				if endpoint.summary:
					f.write(f"**{endpoint.summary}**\n\n")

				if endpoint.description:
					f.write(f"{endpoint.description}\n\n")

				if endpoint.parameters:
					f.write("**Parameters:**\n\n")
					for param in endpoint.parameters:
						required = " (required)" if param.get("required") else ""
						f.write(f"- `{param['name']}` ({param['in']}){required}\n")
					f.write("\n")

				if endpoint.responses:
					f.write("**Responses:**\n\n")
					for status, response in endpoint.responses.items():
						f.write(f"- `{status}`: {response.get('description', 'No description')}\n")
					f.write("\n")

				f.write(f"*Defined in: `{endpoint.file_path}:{endpoint.line_number}`*\n\n")
				f.write("---\n\n")


if __name__ == "__main__":
	main()
