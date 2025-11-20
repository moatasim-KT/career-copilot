#!/usr/bin/env python3
"""
Enhanced OpenAPI specification generator for FastAPI applications.
Generates comprehensive API documentation with examples and validation.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Add backend to path
sys.path.insert(0, "backend")

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def enhance_openapi_spec(openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
	"""Enhance the OpenAPI spec with additional metadata and examples"""

	# Add server information
	openapi_schema["servers"] = [
		{"url": "https://api.careercopilot.com", "description": "Production server"},
		{"url": "http://localhost:8000", "description": "Development server"},
	]

	# Add security schemes
	openapi_schema["components"]["securitySchemes"] = {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}}

	# Apply security globally
	openapi_schema["security"] = [{"bearerAuth": []}]

	# Add custom tags
	openapi_schema["tags"] = [
		{"name": "Authentication", "description": "User authentication and authorization"},
		{"name": "Users", "description": "User management operations"},
		{"name": "Jobs", "description": "Job posting management"},
		{"name": "Applications", "description": "Job application tracking"},
		{"name": "Analytics", "description": "Application analytics and insights"},
	]

	return openapi_schema


def main():
	"""Generate comprehensive API documentation"""

	print("🔍 Generating OpenAPI specification...")

	try:
		from app.main import app
	except ImportError:
		print("❌ Could not import FastAPI app. Make sure backend dependencies are installed.")
		return

	# Generate base OpenAPI spec
	openapi_schema = get_openapi(
		title="Career Copilot API",
		version="1.0.0",
		description="AI-powered job application tracking and career management platform",
		routes=app.routes,
	)

	# Enhance the specification
	enhanced_schema = enhance_openapi_spec(openapi_schema)

	# Save OpenAPI JSON
	docs_path = Path("docs/api")
	docs_path.mkdir(parents=True, exist_ok=True)

	with open(docs_path / "openapi.json", "w") as f:
		json.dump(enhanced_schema, f, indent=2)

	# Save OpenAPI YAML
	with open(docs_path / "openapi.yaml", "w") as f:
		yaml.dump(enhanced_schema, f, default_flow_style=False)

	print("✅ Generated OpenAPI specification")

	# Generate HTML documentation
	generate_html_docs(enhanced_schema, docs_path)

	print("✅ Generated HTML documentation")


def generate_html_docs(openapi_schema: Dict[str, Any], docs_path: Path):
	"""Generate HTML documentation"""

	html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Career Copilot API Documentation</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.7.2/swagger-ui.css" />
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.7.2/swagger-ui-bundle.js"></script>
    <script>
        const spec = {json.dumps(openapi_schema)};
        const ui = SwaggerUIBundle({{
            spec: spec,
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ],
            layout: "BaseLayout"
        }});
    </script>
</body>
</html>
"""

	with open(docs_path / "index.html", "w") as f:
		f.write(html_content)


if __name__ == "__main__":
	main()
