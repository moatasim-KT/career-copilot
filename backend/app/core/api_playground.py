"""
Interactive API Playground Module.

This module provides enhanced interactive API documentation and playground
functionality with custom examples, authentication helpers, and testing tools.
"""

import json
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path


class APIPlaygroundConfig:
    """Configuration for the API playground."""
    
    def __init__(
        self,
        title: str = "Career Copilot API Playground",
        description: str = "Interactive API testing environment",
        version: str = "1.0.0",
        enable_auth_helper: bool = True,
        enable_examples: bool = True,
        enable_code_generation: bool = True,
        custom_css: Optional[str] = None,
        custom_js: Optional[str] = None
    ):
        """
        Initialize playground configuration.
        
        Args:
            title: Playground title
            description: Playground description
            version: API version
            enable_auth_helper: Enable authentication helper
            enable_examples: Enable example requests
            enable_code_generation: Enable code generation
            custom_css: Custom CSS styles
            custom_js: Custom JavaScript
        """
        self.title = title
        self.description = description
        self.version = version
        self.enable_auth_helper = enable_auth_helper
        self.enable_examples = enable_examples
        self.enable_code_generation = enable_code_generation
        self.custom_css = custom_css
        self.custom_js = custom_js


class APIExampleGenerator:
    """Generator for API request/response examples."""
    
    @staticmethod
    def get_contract_upload_examples() -> Dict[str, Any]:
        """
        Get contract upload API examples.
        
        Returns:
            Dict[str, Any]: Upload examples with different scenarios
        """
        return {
            "basic_upload": {
                "summary": "Basic Contract Upload",
                "description": "Upload a simple PDF contract for analysis",
                "request": {
                    "method": "POST",
                    "url": "/api/v1/contracts/upload",
                    "headers": {
                        "Authorization": "Bearer YOUR_JWT_TOKEN",
                        "Content-Type": "multipart/form-data"
                    },
                    "form_data": {
                        "file": "@contract.pdf",
                        "analysis_options": json.dumps({
                            "include_risk_assessment": True,
                            "include_redlines": True,
                            "analysis_depth": "standard"
                        })
                    }
                },
                "response": {
                    "status": 200,
                    "body": {
                        "success": True,
                        "message": "Contract uploaded and validated successfully",
                        "data": {
                            "file_id": "abc123def456",
                            "filename": "contract_sanitized.pdf",
                            "file_size": 2048576,
                            "ready_for_analysis": True
                        }
                    }
                },
                "curl": """curl -X POST "http://localhost:8000/api/v1/contracts/upload" \\
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
     -F "file=@contract.pdf" \\
     -F 'analysis_options={"include_risk_assessment":true,"include_redlines":true}'"""
            },
            "chunked_upload": {
                "summary": "Chunked Upload for Large Files",
                "description": "Upload large contracts using chunked upload with progress tracking",
                "steps": [
                    {
                        "step": 1,
                        "description": "Initiate upload session",
                        "request": {
                            "method": "POST",
                            "url": "/api/v1/contracts/upload/initiate",
                            "body": {
                                "filename": "large_contract.pdf",
                                "total_size": 52428800,
                                "chunk_size": 1048576
                            }
                        }
                    },
                    {
                        "step": 2,
                        "description": "Upload chunks",
                        "request": {
                            "method": "POST",
                            "url": "/api/v1/contracts/upload/chunk/{session_id}",
                            "form_data": {
                                "chunk_index": 0,
                                "chunk_hash": "sha256_hash",
                                "file": "@chunk_0.bin"
                            }
                        }
                    },
                    {
                        "step": 3,
                        "description": "Finalize upload",
                        "request": {
                            "method": "POST",
                            "url": "/api/v1/contracts/upload/finalize/{session_id}"
                        }
                    }
                ]
            }
        }
    
    @staticmethod
    def get_analysis_examples() -> Dict[str, Any]:
        """
        Get job application tracking API examples.
        
        Returns:
            Dict[str, Any]: Analysis examples with different configurations
        """
        return {
            "comprehensive_analysis": {
                "summary": "Comprehensive Contract Analysis",
                "description": "Perform full analysis with all features enabled",
                "request": {
                    "method": "POST",
                    "url": "/api/v1/analyze-contract",
                    "body": {
                        "file_id": "abc123def456",
                        "analysis_type": "comprehensive",
                        "options": {
                            "include_risk_assessment": True,
                            "include_clause_analysis": True,
                            "include_redlines": True,
                            "include_precedents": True,
                            "risk_threshold": "medium",
                            "jurisdiction": "US",
                            "contract_type": "employment"
                        }
                    }
                },
                "response": {
                    "status": 200,
                    "body": {
                        "analysis_id": "analysis_789xyz",
                        "status": "processing",
                        "estimated_completion": "2024-01-15T10:35:00Z",
                        "websocket_url": "/ws/analysis/analysis_789xyz"
                    }
                }
            },
            "quick_analysis": {
                "summary": "Quick Risk Assessment",
                "description": "Fast analysis focusing only on high-risk clauses",
                "request": {
                    "method": "POST",
                    "url": "/api/v1/analyze-contract",
                    "body": {
                        "file_id": "abc123def456",
                        "analysis_type": "quick",
                        "options": {
                            "include_risk_assessment": True,
                            "risk_threshold": "high",
                            "max_processing_time": 30
                        }
                    }
                }
            }
        }
    
    @staticmethod
    def get_websocket_examples() -> Dict[str, Any]:
        """
        Get WebSocket API examples.
        
        Returns:
            Dict[str, Any]: WebSocket examples for real-time features
        """
        return {
            "analysis_progress": {
                "summary": "Real-time Analysis Progress",
                "description": "Monitor job application tracking progress via WebSocket",
                "connection": {
                    "url": "ws://localhost:8000/ws/analysis/{analysis_id}",
                    "headers": {
                        "Authorization": "Bearer YOUR_JWT_TOKEN"
                    }
                },
                "messages": [
                    {
                        "type": "progress_update",
                        "data": {
                            "analysis_id": "analysis_789xyz",
                            "status": "running",
                            "progress_percentage": 25.5,
                            "current_agent": "contract_analyzer",
                            "estimated_completion": "2024-01-15T10:35:00Z"
                        }
                    },
                    {
                        "type": "agent_completed",
                        "data": {
                            "agent_name": "contract_analyzer",
                            "status": "completed",
                            "execution_time": 12.3,
                            "result_summary": "Found 5 clauses for review"
                        }
                    }
                ]
            },
            "upload_progress": {
                "summary": "File Upload Progress",
                "description": "Track file upload progress in real-time",
                "connection": {
                    "url": "ws://localhost:8000/ws/contracts/upload/{session_id}"
                },
                "messages": [
                    {
                        "type": "upload_progress",
                        "data": {
                            "session_id": "upload_123",
                            "progress_percentage": 75.0,
                            "uploaded_size": 1572864,
                            "upload_speed": 1048576
                        }
                    }
                ]
            }
        }
    
    @staticmethod
    def get_authentication_examples() -> Dict[str, Any]:
        """
        Get authentication API examples.
        
        Returns:
            Dict[str, Any]: Authentication examples and flows
        """
        return {
            "login": {
                "summary": "User Login",
                "description": "Authenticate user and obtain JWT token",
                "request": {
                    "method": "POST",
                    "url": "/api/v1/auth/login",
                    "body": {
                        "username": "user@example.com",
                        "password": "secure_password"
                    }
                },
                "response": {
                    "status": 200,
                    "body": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "refresh_token": "refresh_token_here",
                        "user": {
                            "id": "user_123",
                            "email": "user@example.com",
                            "role": "user"
                        }
                    }
                }
            },
            "refresh_token": {
                "summary": "Refresh Access Token",
                "description": "Refresh expired access token using refresh token",
                "request": {
                    "method": "POST",
                    "url": "/api/v1/auth/refresh",
                    "body": {
                        "refresh_token": "refresh_token_here"
                    }
                }
            }
        }


class CodeGenerator:
    """Generator for client code examples in different languages."""
    
    @staticmethod
    def generate_python_example(endpoint: str, method: str, body: Optional[Dict] = None) -> str:
        """
        Generate Python client code example.
        
        Args:
            endpoint: API endpoint URL
            method: HTTP method
            body: Request body (optional)
            
        Returns:
            str: Python code example
        """
        code = f"""import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
JWT_TOKEN = "your_jwt_token_here"

# Headers
headers = {{
    "Authorization": f"Bearer {{JWT_TOKEN}}",
    "Content-Type": "application/json"
}}

# Make request
"""
        
        if method.upper() == "GET":
            code += f"""response = requests.get(f"{{BASE_URL}}{endpoint}", headers=headers)"""
        elif method.upper() == "POST":
            if body:
                code += f"""
# Request body
data = {json.dumps(body, indent=4)}

response = requests.post(f"{{BASE_URL}}{endpoint}", headers=headers, json=data)"""
            else:
                code += f"""response = requests.post(f"{{BASE_URL}}{endpoint}", headers=headers)"""
        else:
            # Handle other HTTP methods
            code += f"""response = requests.{method.lower()}(f"{{BASE_URL}}{endpoint}", headers=headers)"""
        
        code += """

# Handle response
if response.status_code == 200:
    result = response.json()
    print("Success:", result)
else:
    print(f"Error {response.status_code}: {response.text}")"""
        
        return code
    
    @staticmethod
    def generate_javascript_example(endpoint: str, method: str, body: Optional[Dict] = None) -> str:
        """
        Generate JavaScript client code example.
        
        Args:
            endpoint: API endpoint URL
            method: HTTP method
            body: Request body (optional)
            
        Returns:
            str: JavaScript code example
        """
        code = f"""// Configuration
const BASE_URL = "http://localhost:8000";
const JWT_TOKEN = "your_jwt_token_here";

// Request options
const options = {{
    method: "{method.upper()}",
    headers: {{
        "Authorization": `Bearer ${{JWT_TOKEN}}`,
        "Content-Type": "application/json"
    }}"""
        
        if body:
            code += f""",
    body: JSON.stringify({json.dumps(body, indent=8)})"""
        
        code += f"""
}};

// Make request
fetch(`${{BASE_URL}}{endpoint}`, options)
    .then(response => {{
        if (!response.ok) {{
            throw new Error(`HTTP error! status: ${{response.status}}`);
        }}
        return response.json();
    }})
    .then(data => {{
        console.log("Success:", data);
    }})
    .catch(error => {{
        console.error("Error:", error);
    }});"""
        
        return code
    
    @staticmethod
    def generate_curl_example(endpoint: str, method: str, body: Optional[Dict] = None) -> str:
        """
        Generate cURL command example.
        
        Args:
            endpoint: API endpoint URL
            method: HTTP method
            body: Request body (optional)
            
        Returns:
            str: cURL command example
        """
        cmd = f"""curl -X {method.upper()} "http://localhost:8000{endpoint}" \\
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
     -H "Content-Type: application/json\""""
        
        if body:
            cmd += f""" \\
     -d '{json.dumps(body)}'"""
        
        return cmd


class PlaygroundRenderer:
    """Renderer for the interactive API playground HTML."""
    
    def __init__(self, config: APIPlaygroundConfig):
        """
        Initialize the playground renderer.
        
        Args:
            config: Playground configuration
        """
        self.config = config
        self.example_generator = APIExampleGenerator()
        self.code_generator = CodeGenerator()
    
    def render_playground_html(self) -> str:
        """
        Render the complete playground HTML.
        
        Returns:
            str: Complete HTML for the playground
        """
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    {self._render_custom_css()}
</head>
<body>
    <div class="container-fluid">
        {self._render_header()}
        {self._render_navigation()}
        <div class="row">
            <div class="col-md-3">
                {self._render_sidebar()}
            </div>
            <div class="col-md-9">
                {self._render_main_content()}
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/plugins/autoloader/prism-autoloader.min.js"></script>
    {self._render_custom_js()}
</body>
</html>"""
    
    def _render_header(self) -> str:
        """Render the playground header."""
        return f"""
        <header class="bg-primary text-white py-3 mb-4">
            <div class="container">
                <h1><i class="fas fa-code"></i> {self.config.title}</h1>
                <p class="mb-0">{self.config.description}</p>
            </div>
        </header>"""
    
    def _render_navigation(self) -> str:
        """Render the navigation tabs."""
        return """
        <nav class="mb-4">
            <div class="nav nav-tabs" id="nav-tab" role="tablist">
                <button class="nav-link active" id="nav-examples-tab" data-bs-toggle="tab" 
                        data-bs-target="#nav-examples" type="button" role="tab">
                    <i class="fas fa-play-circle"></i> Examples
                </button>
                <button class="nav-link" id="nav-auth-tab" data-bs-toggle="tab" 
                        data-bs-target="#nav-auth" type="button" role="tab">
                    <i class="fas fa-key"></i> Authentication
                </button>
                <button class="nav-link" id="nav-websocket-tab" data-bs-toggle="tab" 
                        data-bs-target="#nav-websocket" type="button" role="tab">
                    <i class="fas fa-plug"></i> WebSocket
                </button>
                <button class="nav-link" id="nav-code-tab" data-bs-toggle="tab" 
                        data-bs-target="#nav-code" type="button" role="tab">
                    <i class="fas fa-code"></i> Code Generator
                </button>
            </div>
        </nav>"""
    
    def _render_sidebar(self) -> str:
        """Render the sidebar with endpoint categories."""
        return """
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-list"></i> API Endpoints</h5>
            </div>
            <div class="card-body">
                <div class="accordion" id="endpointAccordion">
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button" type="button" data-bs-toggle="collapse" 
                                    data-bs-target="#contractEndpoints">
                                Contract Management
                            </button>
                        </h2>
                        <div id="contractEndpoints" class="accordion-collapse collapse show">
                            <div class="accordion-body">
                                <ul class="list-unstyled">
                                    <li><a href="#upload" class="text-decoration-none">Upload Contract</a></li>
                                    <li><a href="#analyze" class="text-decoration-none">Analyze Contract</a></li>
                                    <li><a href="#results" class="text-decoration-none">Get Results</a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                    data-bs-target="#authEndpoints">
                                Authentication
                            </button>
                        </h2>
                        <div id="authEndpoints" class="accordion-collapse collapse">
                            <div class="accordion-body">
                                <ul class="list-unstyled">
                                    <li><a href="#login" class="text-decoration-none">Login</a></li>
                                    <li><a href="#refresh" class="text-decoration-none">Refresh Token</a></li>
                                    <li><a href="#logout" class="text-decoration-none">Logout</a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>"""
    
    def _render_main_content(self) -> str:
        """Render the main content area."""
        return f"""
        <div class="tab-content" id="nav-tabContent">
            <div class="tab-pane fade show active" id="nav-examples" role="tabpanel">
                {self._render_examples_tab()}
            </div>
            <div class="tab-pane fade" id="nav-auth" role="tabpanel">
                {self._render_auth_tab()}
            </div>
            <div class="tab-pane fade" id="nav-websocket" role="tabpanel">
                {self._render_websocket_tab()}
            </div>
            <div class="tab-pane fade" id="nav-code" role="tabpanel">
                {self._render_code_generator_tab()}
            </div>
        </div>"""
    
    def _render_examples_tab(self) -> str:
        """Render the examples tab content."""
        upload_examples = self.example_generator.get_contract_upload_examples()
        analysis_examples = self.example_generator.get_analysis_examples()
        
        return f"""
        <div class="row">
            <div class="col-12">
                <h3>API Examples</h3>
                <p>Interactive examples for common API operations.</p>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5>Contract Upload</h5>
                    </div>
                    <div class="card-body">
                        <pre><code class="language-bash">{upload_examples['basic_upload']['curl']}</code></pre>
                        <button class="btn btn-primary btn-sm" onclick="tryExample('upload')">
                            <i class="fas fa-play"></i> Try It
                        </button>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5>Contract Analysis</h5>
                    </div>
                    <div class="card-body">
                        <pre><code class="language-json">{json.dumps(analysis_examples['comprehensive_analysis']['request']['body'], indent=2)}</code></pre>
                        <button class="btn btn-primary btn-sm" onclick="tryExample('analyze')">
                            <i class="fas fa-play"></i> Try It
                        </button>
                    </div>
                </div>
            </div>
        </div>"""
    
    def _render_auth_tab(self) -> str:
        """Render the authentication tab content."""
        if not self.config.enable_auth_helper:
            return "<p>Authentication helper is disabled.</p>"
        
        return """
        <div class="row">
            <div class="col-12">
                <h3>Authentication Helper</h3>
                <p>Get and manage your API authentication tokens.</p>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Login</h5>
                    </div>
                    <div class="card-body">
                        <form id="loginForm">
                            <div class="mb-3">
                                <label for="username" class="form-label">Username/Email</label>
                                <input type="text" class="form-control" id="username" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-sign-in-alt"></i> Login
                            </button>
                        </form>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Current Token</h5>
                    </div>
                    <div class="card-body">
                        <div id="tokenDisplay">
                            <p class="text-muted">No token available. Please login first.</p>
                        </div>
                        <button class="btn btn-secondary btn-sm" onclick="copyToken()" id="copyTokenBtn" style="display:none;">
                            <i class="fas fa-copy"></i> Copy Token
                        </button>
                    </div>
                </div>
            </div>
        </div>"""
    
    def _render_websocket_tab(self) -> str:
        """Render the WebSocket tab content."""
        return """
        <div class="row">
            <div class="col-12">
                <h3>WebSocket Testing</h3>
                <p>Test real-time WebSocket connections for progress tracking.</p>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Connection</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="wsUrl" class="form-label">WebSocket URL</label>
                            <input type="text" class="form-control" id="wsUrl" 
                                   value="ws://localhost:8000/ws/analysis/test">
                        </div>
                        <button class="btn btn-success" onclick="connectWebSocket()" id="connectBtn">
                            <i class="fas fa-plug"></i> Connect
                        </button>
                        <button class="btn btn-danger" onclick="disconnectWebSocket()" id="disconnectBtn" style="display:none;">
                            <i class="fas fa-times"></i> Disconnect
                        </button>
                        <div class="mt-3">
                            <span class="badge bg-secondary" id="connectionStatus">Disconnected</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Messages</h5>
                    </div>
                    <div class="card-body">
                        <div id="wsMessages" style="height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px;">
                            <p class="text-muted">No messages yet. Connect to start receiving messages.</p>
                        </div>
                        <button class="btn btn-outline-secondary btn-sm mt-2" onclick="clearMessages()">
                            <i class="fas fa-trash"></i> Clear
                        </button>
                    </div>
                </div>
            </div>
        </div>"""
    
    def _render_code_generator_tab(self) -> str:
        """Render the code generator tab content."""
        if not self.config.enable_code_generation:
            return "<p>Code generation is disabled.</p>"
        
        return """
        <div class="row">
            <div class="col-12">
                <h3>Code Generator</h3>
                <p>Generate client code in different programming languages.</p>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Configuration</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="codeEndpoint" class="form-label">Endpoint</label>
                            <select class="form-select" id="codeEndpoint">
                                <option value="/api/v1/contracts/upload">Upload Contract</option>
                                <option value="/api/v1/analyze-contract">Analyze Contract</option>
                                <option value="/api/v1/auth/login">Login</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="codeMethod" class="form-label">Method</label>
                            <select class="form-select" id="codeMethod">
                                <option value="POST">POST</option>
                                <option value="GET">GET</option>
                                <option value="PUT">PUT</option>
                                <option value="DELETE">DELETE</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="codeLanguage" class="form-label">Language</label>
                            <select class="form-select" id="codeLanguage">
                                <option value="python">Python</option>
                                <option value="javascript">JavaScript</option>
                                <option value="curl">cURL</option>
                            </select>
                        </div>
                        <button class="btn btn-primary" onclick="generateCode()">
                            <i class="fas fa-code"></i> Generate Code
                        </button>
                    </div>
                </div>
            </div>
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>Generated Code</h5>
                    </div>
                    <div class="card-body">
                        <pre><code id="generatedCode" class="language-python">// Select options and click "Generate Code" to see the example</code></pre>
                        <button class="btn btn-outline-secondary btn-sm" onclick="copyCode()">
                            <i class="fas fa-copy"></i> Copy Code
                        </button>
                    </div>
                </div>
            </div>
        </div>"""
    
    def _render_custom_css(self) -> str:
        """Render custom CSS styles."""
        default_css = """
        <style>
        .card { margin-bottom: 1rem; }
        .accordion-button:not(.collapsed) { background-color: #e7f3ff; }
        pre { background-color: #f8f9fa; padding: 1rem; border-radius: 0.375rem; }
        .badge { font-size: 0.875em; }
        #wsMessages { font-family: monospace; font-size: 0.875rem; }
        .message-timestamp { color: #6c757d; font-size: 0.75rem; }
        .message-type { font-weight: bold; }
        .nav-tabs .nav-link { color: #495057; }
        .nav-tabs .nav-link.active { color: #0d6efd; }
        </style>"""
        
        if self.config.custom_css:
            return f"{default_css}\n<style>{self.config.custom_css}</style>"
        
        return default_css
    
    def _render_custom_js(self) -> str:
        """Render custom JavaScript functionality."""
        default_js = """
        <script>
        let currentToken = null;
        let websocket = null;
        
        // Authentication functions
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/api/v1/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    currentToken = data.access_token;
                    updateTokenDisplay(data);
                } else {
                    alert('Login failed: ' + response.statusText);
                }
            } catch (error) {
                alert('Login error: ' + error.message);
            }
        });
        
        function updateTokenDisplay(tokenData) {
            const display = document.getElementById('tokenDisplay');
            display.innerHTML = `
                <div class="alert alert-success">
                    <strong>Token obtained successfully!</strong><br>
                    <small>Expires: ${new Date(Date.now() + tokenData.expires_in * 1000).toLocaleString()}</small>
                </div>
                <textarea class="form-control" rows="3" readonly>${tokenData.access_token}</textarea>
            `;
            document.getElementById('copyTokenBtn').style.display = 'inline-block';
        }
        
        function copyToken() {
            if (currentToken) {
                navigator.clipboard.writeText(currentToken);
                alert('Token copied to clipboard!');
            }
        }
        
        // WebSocket functions
        function connectWebSocket() {
            const url = document.getElementById('wsUrl').value;
            websocket = new WebSocket(url);
            
            websocket.onopen = function() {
                updateConnectionStatus('Connected', 'success');
                document.getElementById('connectBtn').style.display = 'none';
                document.getElementById('disconnectBtn').style.display = 'inline-block';
            };
            
            websocket.onmessage = function(event) {
                addMessage('Received', event.data);
            };
            
            websocket.onclose = function() {
                updateConnectionStatus('Disconnected', 'secondary');
                document.getElementById('connectBtn').style.display = 'inline-block';
                document.getElementById('disconnectBtn').style.display = 'none';
            };
            
            websocket.onerror = function(error) {
                addMessage('Error', error.toString());
            };
        }
        
        function disconnectWebSocket() {
            if (websocket) {
                websocket.close();
            }
        }
        
        function updateConnectionStatus(status, type) {
            const badge = document.getElementById('connectionStatus');
            badge.textContent = status;
            badge.className = `badge bg-${type}`;
        }
        
        function addMessage(type, content) {
            const messages = document.getElementById('wsMessages');
            const timestamp = new Date().toLocaleTimeString();
            const messageDiv = document.createElement('div');
            messageDiv.innerHTML = `
                <div class="message-timestamp">${timestamp}</div>
                <div class="message-type">${type}:</div>
                <div>${content}</div>
                <hr>
            `;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function clearMessages() {
            document.getElementById('wsMessages').innerHTML = 
                '<p class="text-muted">Messages cleared.</p>';
        }
        
        // Code generation functions
        function generateCode() {
            const endpoint = document.getElementById('codeEndpoint').value;
            const method = document.getElementById('codeMethod').value;
            const language = document.getElementById('codeLanguage').value;
            
            let code = '';
            
            if (language === 'python') {
                code = generatePythonCode(endpoint, method);
            } else if (language === 'javascript') {
                code = generateJavaScriptCode(endpoint, method);
            } else if (language === 'curl') {
                code = generateCurlCode(endpoint, method);
            }
            
            document.getElementById('generatedCode').textContent = code;
            document.getElementById('generatedCode').className = `language-${language}`;
            Prism.highlightAll();
        }
        
        function generatePythonCode(endpoint, method) {
            return `import requests

# Configuration
BASE_URL = "http://localhost:8000"
JWT_TOKEN = "your_jwt_token_here"

# Headers
headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

# Make request
response = requests.${method.toLowerCase()}(f"{BASE_URL}${endpoint}", headers=headers)

# Handle response
if response.status_code == 200:
    result = response.json()
    print("Success:", result)
else:
    print(f"Error {response.status_code}: {response.text}")`;
        }
        
        function generateJavaScriptCode(endpoint, method) {
            return `// Configuration
const BASE_URL = "http://localhost:8000";
const JWT_TOKEN = "your_jwt_token_here";

// Make request
fetch(`${BASE_URL}${endpoint}`, {
    method: "${method}",
    headers: {
        "Authorization": `Bearer ${JWT_TOKEN}`,
        "Content-Type": "application/json"
    }
})
.then(response => {
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
})
.then(data => {
    console.log("Success:", data);
})
.catch(error => {
    console.error("Error:", error);
});`;
        }
        
        function generateCurlCode(endpoint, method) {
            return `curl -X ${method} "http://localhost:8000${endpoint}" \\
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
     -H "Content-Type: application/json"`;
        }
        
        function copyCode() {
            const code = document.getElementById('generatedCode').textContent;
            navigator.clipboard.writeText(code);
            alert('Code copied to clipboard!');
        }
        
        // Example functions
        function tryExample(type) {
            alert(`This would execute the ${type} example. In a real implementation, this would make the actual API call.`);
        }
        </script>"""
        
        if self.config.custom_js:
            return f"{default_js}\n<script>{self.config.custom_js}</script>"
        
        return default_js


def setup_api_playground(app: FastAPI, config: Optional[APIPlaygroundConfig] = None) -> None:
    """
    Set up the interactive API playground for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        config: Playground configuration (optional)
    """
    if not config:
        config = APIPlaygroundConfig()
    
    renderer = PlaygroundRenderer(config)
    
    @app.get("/playground", response_class=HTMLResponse, include_in_schema=False)
    async def api_playground(request: Request) -> HTMLResponse:
        """
        Serve the interactive API playground.
        
        Args:
            request: FastAPI request object
            
        Returns:
            HTMLResponse: HTML page for the playground
        """
        html_content = renderer.render_playground_html()
        return HTMLResponse(content=html_content)
    
    # Add playground link to the main docs
    @app.get("/playground-redirect", include_in_schema=False)
    async def playground_redirect():
        """Redirect to the playground from docs."""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/playground")


# Export main components
__all__ = [
    'APIPlaygroundConfig',
    'APIExampleGenerator', 
    'CodeGenerator',
    'PlaygroundRenderer',
    'setup_api_playground'
]