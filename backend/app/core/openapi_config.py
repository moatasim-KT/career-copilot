"""
OpenAPI Configuration and Documentation Enhancement Module.

This module provides comprehensive OpenAPI configuration with examples,
enhanced descriptions, and interactive API playground setup.
"""

from typing import Any, Dict, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def get_openapi_tags() -> List[Dict[str, Any]]:
	"""
	Get OpenAPI tags with descriptions for API organization.

	Returns:
	    List[Dict[str, Any]]: List of OpenAPI tags with metadata
	"""
	return [
		{
			"name": "Contract Analysis",
			"description": "Core job application tracking endpoints for uploading, processing, and analyzing legal documents. "
			"Includes risk assessment, clause identification, and redline generation.",
			"externalDocs": {"description": "Contract Analysis Guide", "url": "https://docs.contractanalyzer.com/contract-analysis"},
		},
		{
			"name": "Enhanced Contract Upload",
			"description": "Advanced file upload capabilities with chunked upload support, progress tracking, "
			"duplicate detection, and comprehensive validation. Supports PDF, DOCX, and TXT formats.",
			"externalDocs": {"description": "Upload API Guide", "url": "https://docs.contractanalyzer.com/upload-api"},
		},
		{
			"name": "Real-time Analysis",
			"description": "WebSocket and Server-Sent Events endpoints for real-time analysis progress tracking, "
			"agent status monitoring, and live updates during contract processing.",
			"externalDocs": {"description": "Real-time API Guide", "url": "https://docs.contractanalyzer.com/realtime-api"},
		},
		{
			"name": "Agent Management",
			"description": "AI agent orchestration and management endpoints for controlling analysis workflows, "
			"monitoring agent health, and managing parallel execution.",
			"externalDocs": {"description": "Agent Management Guide", "url": "https://docs.contractanalyzer.com/agent-management"},
		},
		{
			"name": "Vector Search",
			"description": "ChromaDB-powered vector search endpoints for legal precedent matching, "
			"similarity search, and contract comparison using semantic embeddings.",
			"externalDocs": {"description": "Vector Search Guide", "url": "https://docs.contractanalyzer.com/vector-search"},
		},
		{
			"name": "External Integrations",
			"description": "Third-party service integrations including DocuSign for e-signatures, "
			"Slack for notifications, and email services for communication.",
			"externalDocs": {"description": "Integration Guide", "url": "https://docs.contractanalyzer.com/integrations"},
		},
		{
			"name": "Background Tasks",
			"description": "Asynchronous task management for long-running operations, batch processing, "
			"and scheduled analysis workflows with retry mechanisms.",
			"externalDocs": {"description": "Background Tasks Guide", "url": "https://docs.contractanalyzer.com/background-tasks"},
		},
		{
			"name": "Analytics",
			"description": "Business intelligence and analytics endpoints for risk trends, performance metrics, "
			"cost analysis, and compliance reporting with interactive dashboards.",
			"externalDocs": {"description": "Analytics Guide", "url": "https://docs.contractanalyzer.com/analytics"},
		},
		{
			"name": "Security & Authentication",
			"description": "Security endpoints for JWT authentication, role-based access control, "
			"audit logging, and security validation with comprehensive threat detection.",
			"externalDocs": {"description": "Security Guide", "url": "https://docs.contractanalyzer.com/security"},
		},
		{
			"name": "Health & Monitoring",
			"description": "System health checks, performance monitoring, service status, "
			"and operational metrics for production deployment and maintenance.",
			"externalDocs": {"description": "Monitoring Guide", "url": "https://docs.contractanalyzer.com/monitoring"},
		},
		{
			"name": "Configuration",
			"description": "System configuration management with environment-specific settings, "
			"feature flags, hot-reloading, and validation endpoints.",
			"externalDocs": {"description": "Configuration Guide", "url": "https://docs.contractanalyzer.com/configuration"},
		},
		{
			"name": "Workflows",
			"description": "Advanced workflow management for complex analysis pipelines, "
			"template-based processing, and batch operations with scheduling.",
			"externalDocs": {"description": "Workflow Guide", "url": "https://docs.contractanalyzer.com/workflows"},
		},
	]


def get_openapi_examples() -> Dict[str, Any]:
	"""
	Get comprehensive OpenAPI examples for request/response documentation.

	Returns:
	    Dict[str, Any]: Dictionary of examples organized by endpoint
	"""
	return {
		"contract_upload": {
			"summary": "Upload a contract for analysis",
			"description": "Example of uploading a PDF contract file with metadata",
			"value": {
				"file": "contract.pdf (binary data)",
				"analysis_options": {
					"include_risk_assessment": True,
					"include_redlines": True,
					"include_precedents": True,
					"analysis_depth": "comprehensive",
				},
			},
		},
		"contract_upload_response": {
			"summary": "Successful contract upload response",
			"description": "Response after successful contract upload and validation",
			"value": {
				"success": True,
				"message": "Contract uploaded and validated successfully",
				"data": {
					"file_id": "abc123def456",
					"filename": "employment_agreement_sanitized.pdf",
					"original_filename": "Employment Agreement - John Doe.pdf",
					"file_size": 2048576,
					"mime_type": "application/pdf",
					"detected_type": "pdf",
					"content_length": 15420,
					"upload_timestamp": "2024-01-15T10:30:00Z",
					"ready_for_analysis": True,
					"document_type": "employment_agreement",
					"processing_status": "completed",
					"file_hash": "sha256:abc123...",
					"security_scan_passed": True,
					"duplicate": False,
				},
			},
		},
		"analysis_request": {
			"summary": "Request job application tracking",
			"description": "Example of requesting comprehensive job application tracking",
			"value": {
				"file_id": "abc123def456",
				"analysis_type": "comprehensive",
				"options": {
					"include_risk_assessment": True,
					"include_clause_analysis": True,
					"include_redlines": True,
					"include_precedents": True,
					"risk_threshold": "medium",
					"jurisdiction": "US",
					"contract_type": "employment",
				},
			},
		},
		"analysis_response": {
			"summary": "Contract analysis results",
			"description": "Comprehensive analysis results with risk assessment and recommendations",
			"value": {
				"analysis_id": "analysis_789xyz",
				"status": "completed",
				"overall_risk_score": 7.2,
				"risk_level": "high",
				"processing_time": 45.3,
				"risky_clauses": [
					{
						"clause_id": "clause_001",
						"text": "Employee agrees to work unlimited overtime without additional compensation",
						"risk_level": "critical",
						"risk_score": 9.5,
						"category": "compensation",
						"explanation": "This clause violates labor laws in most jurisdictions",
						"suggested_revision": "Employee may work reasonable overtime with appropriate compensation",
						"legal_precedents": ["Case A v. Company B", "Labor Code Section 123"],
					}
				],
				"suggested_redlines": [
					{
						"original_text": "unlimited overtime without additional compensation",
						"suggested_text": "reasonable overtime with appropriate compensation as per labor laws",
						"justification": "Ensures compliance with labor regulations",
						"priority": "high",
					}
				],
				"recommendations": [
					{
						"category": "legal_compliance",
						"priority": "high",
						"description": "Review overtime compensation clauses for legal compliance",
						"action_items": ["Consult employment lawyer", "Update compensation structure"],
					}
				],
				"metadata": {
					"agents_used": ["contract_analyzer", "risk_assessor", "legal_precedent"],
					"model_versions": {"gpt-4": "2024-01", "claude-3": "2024-01"},
					"confidence_score": 0.92,
					"processing_stages": ["document_parsing", "clause_extraction", "risk_analysis", "precedent_matching"],
				},
			},
		},
		"upload_progress": {
			"summary": "Upload progress tracking",
			"description": "Real-time upload progress information",
			"value": {
				"session_id": "upload_session_123",
				"filename": "contract.pdf",
				"progress_percentage": 75.5,
				"uploaded_size": 1572864,
				"total_size": 2097152,
				"current_chunk": 12,
				"total_chunks": 16,
				"upload_speed": 1048576,
				"estimated_completion": "2024-01-15T10:32:15Z",
				"status": "uploading",
			},
		},
		"error_response": {
			"summary": "Error response format",
			"description": "Standard error response with detailed information",
			"value": {
				"error": "Validation Error",
				"message": "File size exceeds maximum allowed limit",
				"error_code": "FILE_SIZE_EXCEEDED",
				"error_id": "err_123abc456def",
				"details": {"file_size_mb": 52.3, "max_size_mb": 50.0, "field": "file"},
				"suggestions": [
					"Reduce file size by compressing the document",
					"Split large documents into smaller sections",
					"Contact support for enterprise limits",
				],
				"timestamp": "2024-01-15T10:30:00Z",
				"request_id": "req_789xyz123",
			},
		},
		"health_check": {
			"summary": "System health status",
			"description": "Comprehensive system health information",
			"value": {
				"status": "healthy",
				"timestamp": "2024-01-15T10:30:00Z",
				"version": "1.0.0",
				"environment": "production",
				"services": {
					"database": {"status": "healthy", "response_time_ms": 12},
					"vector_store": {"status": "healthy", "response_time_ms": 8},
					"llm_providers": {
						"openai": {"status": "healthy", "response_time_ms": 245},
						"groq": {"status": "healthy", "response_time_ms": 156},
						"gemini": {"status": "degraded", "response_time_ms": 1200},
					},
					"external_services": {"docusign": {"status": "healthy"}, "slack": {"status": "healthy"}, "email": {"status": "healthy"}},
				},
				"metrics": {"active_analyses": 3, "queue_size": 12, "avg_processing_time": 42.5, "success_rate": 0.98},
			},
		},
	}


def get_openapi_servers() -> List[Dict[str, Any]]:
	"""
	Get OpenAPI server configurations for different environments.

	Returns:
	    List[Dict[str, Any]]: List of server configurations
	"""
	return [
		{"url": "https://api.contractanalyzer.com", "description": "Production server"},
		{"url": "https://staging-api.contractanalyzer.com", "description": "Staging server"},
		{"url": "http://localhost:8000", "description": "Development server"},
	]


def get_openapi_security_schemes() -> Dict[str, Any]:
	"""
	Get OpenAPI security scheme definitions.

	Returns:
	    Dict[str, Any]: Security scheme configurations
	"""
	return {
		"BearerAuth": {
			"type": "http",
			"scheme": "bearer",
			"bearerFormat": "JWT",
			"description": "JWT token authentication. Obtain token from /api/v1/auth/login endpoint.",
		},
		"ApiKeyAuth": {
			"type": "apiKey",
			"in": "header",
			"name": "X-API-Key",
			"description": "API key authentication for service-to-service communication.",
		},
	}


def customize_openapi_schema(app: FastAPI) -> Dict[str, Any]:
	"""
	Create customized OpenAPI schema with enhanced documentation.

	Args:
	    app: FastAPI application instance

	Returns:
	    Dict[str, Any]: Customized OpenAPI schema
	"""
	if app.openapi_schema:
		return app.openapi_schema

	openapi_schema = get_openapi(
		title="Career Copilot API",
		version="1.0.0",
		description="""
# Career Copilot API

A comprehensive AI-powered job application tracking platform that provides intelligent risk assessment, 
clause analysis, and legal precedent matching for enterprise contract management.

## Features

### 🔍 **Intelligent Contract Analysis**
- Multi-agent AI system for comprehensive contract review
- Risk scoring and clause-level analysis
- Automated redline generation and suggestions
- Legal precedent matching using vector search

### 📁 **Advanced File Management**
- Chunked upload support for large documents
- Real-time progress tracking via WebSocket
- Duplicate detection and deduplication
- Support for PDF, DOCX, and TXT formats

### 🤖 **AI Agent Orchestration**
- Parallel agent execution for faster processing
- Intelligent LLM provider routing based on task complexity
- Fallback mechanisms and error recovery
- Cost optimization and token usage tracking

### 🔗 **External Integrations**
- DocuSign integration for e-signature workflows
- Slack notifications and interactive commands
- Email template system with HTML support
- Cloud storage and backup capabilities

### 📊 **Analytics & Monitoring**
- Real-time performance metrics and dashboards
- Risk trend analysis and compliance reporting
- Cost tracking and usage analytics
- Comprehensive audit logging

### 🔒 **Enterprise Security**
- JWT-based authentication with role-based access control
- Comprehensive input validation and sanitization
- Malware scanning and threat detection
- Audit trails and compliance reporting

## Getting Started

1. **Authentication**: Obtain a JWT token from `/api/v1/auth/login`
2. **Upload Contract**: Use `/api/v1/contracts/upload` to upload documents
3. **Analyze Contract**: Submit analysis requests to `/api/v1/analyze-contract`
4. **Monitor Progress**: Track analysis progress via WebSocket at `/ws/analysis/{analysis_id}`
5. **Retrieve Results**: Get analysis results from `/api/v1/contracts/{contract_id}/results`

## Rate Limits

- **Standard Users**: 100 requests per minute
- **Premium Users**: 1000 requests per minute
- **Enterprise Users**: Custom limits available

## Support

For technical support and API questions:
- Documentation: [https://docs.contractanalyzer.com](https://docs.contractanalyzer.com)
- Support Email: support@contractanalyzer.com
- Status Page: [https://status.contractanalyzer.com](https://status.contractanalyzer.com)
        """,
		routes=app.routes,
		tags=get_openapi_tags(),
		servers=get_openapi_servers(),
	)

	# Initialize components if not present
	if "components" not in openapi_schema:
		openapi_schema["components"] = {}

	# Add security schemes
	openapi_schema["components"]["securitySchemes"] = get_openapi_security_schemes()

	# Add global security requirement
	openapi_schema["security"] = [{"BearerAuth": []}, {"ApiKeyAuth": []}]

	# Add examples to components
	examples = get_openapi_examples()
	openapi_schema["components"]["examples"] = examples

	# Add custom extensions
	openapi_schema["x-logo"] = {"url": "/static/logo.png", "altText": "Career Copilot Logo"}

	# Add contact information
	openapi_schema["info"]["contact"] = {
		"name": "Career Copilot API Support",
		"url": "https://docs.contractanalyzer.com",
		"email": "support@contractanalyzer.com",
	}

	# Add license information
	openapi_schema["info"]["license"] = {"name": "MIT License", "url": "https://opensource.org/licenses/MIT"}

	# Add terms of service
	openapi_schema["info"]["termsOfService"] = "https://contractanalyzer.com/terms"

	app.openapi_schema = openapi_schema
	return app.openapi_schema


def setup_api_documentation(app: FastAPI) -> None:
	"""
	Set up enhanced API documentation for the FastAPI application.

	Args:
	    app: FastAPI application instance
	"""
	# Set custom OpenAPI schema generator
	app.openapi = lambda: customize_openapi_schema(app)

	# Add custom CSS for documentation (if StaticFiles is available)
	if StaticFiles:
		try:
			app.mount("/static", StaticFiles(directory="static"), name="static")
		except Exception:
			# Static directory might not exist, skip mounting
			pass

	# Add custom JavaScript for interactive features
	custom_js = """
    <script>
    // Add custom JavaScript for enhanced API playground
    document.addEventListener('DOMContentLoaded', function() {
        // Add copy buttons to code examples
        const codeBlocks = document.querySelectorAll('pre code');
        codeBlocks.forEach(block => {
            const button = document.createElement('button');
            button.textContent = 'Copy';
            button.className = 'copy-button';
            button.onclick = () => {
                navigator.clipboard.writeText(block.textContent);
                button.textContent = 'Copied!';
                setTimeout(() => button.textContent = 'Copy', 2000);
            };
            block.parentElement.appendChild(button);
        });
        
        // Add example selector for request bodies
        const tryItButtons = document.querySelectorAll('.try-out__btn');
        tryItButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Add example data to request body
                setTimeout(() => {
                    const textareas = document.querySelectorAll('textarea[placeholder*="request body"]');
                    textareas.forEach(textarea => {
                        if (!textarea.value) {
                            // Add example based on endpoint
                            const endpoint = window.location.hash;
                            if (endpoint.includes('upload')) {
                                textarea.value = JSON.stringify({
                                    "analysis_options": {
                                        "include_risk_assessment": true,
                                        "include_redlines": true,
                                        "analysis_depth": "comprehensive"
                                    }
                                }, null, 2);
                            }
                        }
                    });
                }, 100);
            });
        });
    });
    </script>
    """

	# Custom CSS for better documentation appearance
	custom_css = """
    <style>
    .swagger-ui .topbar { display: none; }
    .swagger-ui .info { margin: 20px 0; }
    .swagger-ui .info .title { color: #2c3e50; }
    .copy-button {
        position: absolute;
        top: 10px;
        right: 10px;
        background: #007bff;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
        cursor: pointer;
        font-size: 12px;
    }
    .copy-button:hover { background: #0056b3; }
    pre { position: relative; }
    .swagger-ui .scheme-container { background: #f8f9fa; padding: 20px; border-radius: 5px; }
    .swagger-ui .info .description p { line-height: 1.6; }
    .swagger-ui .info .description h2 { color: #495057; margin-top: 30px; }
    .swagger-ui .info .description h3 { color: #6c757d; }
    </style>
    """

	# Store custom assets for injection
	app.state.custom_css = custom_css
	app.state.custom_js = custom_js


# Import StaticFiles for serving static assets
try:
	from fastapi.staticfiles import StaticFiles
except ImportError:
	# Fallback if StaticFiles is not available
	StaticFiles = None
