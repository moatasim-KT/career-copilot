"""
Centralized API endpoint configuration.
Auto-generated from actual backend routes.
"""

API_ENDPOINTS = {
	# Health & Status
	"health": "/api/v1/health",
	"health_detailed": "/api/v1/health/detailed",
	"health_readiness": "/api/v1/health/readiness",
	"health_liveness": "/api/v1/health/liveness",
	"connection_test": "/api/v1/connection-test",
	# Contract Analysis
	"analyze_contract": "/api/v1/analyze-contract",
	"analyze_contract_async": "/api/v1/analyze-contract/async",
	"analysis_status": "/api/v1/analyze-contract/async/{task_id}/status",
	"analysis_progress": "/api/v1/analyze-contract/async/{task_id}/progress",
	"analysis_result": "/api/v1/analyze-contract/async/{task_id}/result",
	"cancel_analysis": "/api/v1/analyze-contract/async/{task_id}",
	# Contract Management
	"contracts_list": "/api/v1/contracts/list",
	"contract_upload": "/api/v1/contracts/upload",
	"contract_upload_initiate": "/api/v1/contracts/upload/initiate",
	"contract_upload_chunk": "/api/v1/contracts/upload/chunk/{session_id}",
	"contract_upload_finalize": "/api/v1/contracts/upload/finalize/{session_id}",
	"contract_upload_progress": "/api/v1/contracts/upload/progress/{session_id}",
	"contract_upload_cancel": "/api/v1/contracts/upload/cancel/{session_id}",
	"contract_download": "/api/v1/contracts/{file_id}/download",
	"contract_status": "/api/v1/contracts/{file_id}/status",
	"contract_delete": "/api/v1/contracts/{file_id}",
	# Analysis Results
	"analysis_results": "/api/v1/analysis/{analysis_id}/results",
	"analysis_redlines": "/api/v1/analysis/{analysis_id}/redlines",
	"accept_redline": "/api/v1/analysis/{analysis_id}/redlines/{redline_id}/accept",
	"generate_revised_contract": "/api/v1/analysis/{analysis_id}/contract/generate-revised",
	"download_contract": "/api/v1/analysis/{analysis_id}/contract/download/{filename}",
	# Authentication
	"login": "/api/v1/auth/login",
	"logout": "/api/v1/auth/logout",
	"refresh_token": "/api/v1/auth/refresh",
	"register": "/api/v1/auth/register",
	# User Management
	"user_profile": "/api/v1/users/me/profile",
	"user_settings": "/api/v1/users/me/settings",
	# Real-time Status
	"sse_progress": "/api/v1/sse/progress/{task_id}",
	"sse_dashboard": "/api/v1/sse/dashboard",
	# File Storage
	"file_upload": "/api/v1/file-storage/upload",
	"file_download": "/api/v1/file-storage/{file_id}",
	"file_info": "/api/v1/file-storage/{file_id}/info",
	"file_delete": "/api/v1/file-storage/{file_id}",
}


def get_endpoint(key: str, **kwargs) -> str:
	"""Get endpoint URL with path parameters replaced."""
	endpoint = API_ENDPOINTS.get(key)
	if not endpoint:
		raise ValueError(f"Unknown endpoint: {key}")

	# Replace path parameters
	for param, value in kwargs.items():
		endpoint = endpoint.replace(f"{{{param}}}", str(value))

	return endpoint
