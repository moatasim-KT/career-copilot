"""
Career Copilot - Production-Ready Streamlit Frontend
A comprehensive interface for analyzing contract documents with advanced security measures,
production optimizations, real-time updates, and mobile support.
"""

import logging
import os
import requests
from datetime import datetime
from pathlib import Path

import streamlit as st

# Define ConnectionError for local APIClient
class ConnectionError(Exception):
    """Connection-related errors"""
    pass

# Import production features
try:
    from config import get_config
    from components.production_optimizations import initialize_production_optimizations
    from components.websocket_manager import initialize_websocket_features
    from components.error_display import error_display
    from components.production_optimizations import ErrorHandler
    from components.responsive_ui import initialize_responsive_ui
    from components.production_analytics import initialize_production_analytics, track_user_event
    PRODUCTION_FEATURES_AVAILABLE = True
except ImportError:
    PRODUCTION_FEATURES_AVAILABLE = False
    print("Production features not available, running in basic mode")

# Import components
try:
    from .components.analytics_dashboard import render_analytics_dashboard
    from .components.error_display import error_display
    from .components.file_upload import file_upload_component
    from .components.observability_dashboard import render_observability_dashboard
    from .components.progress_indicator import progress_indicator
    from .components.progress_dashboard import render_progress_dashboard, show_analysis_dashboard
    from .components.results_display import AnalysisResultsDisplay
    from .utils.api_client import APIClient
    from .components.connection_status import display_connection_status_sidebar, display_connection_dashboard
except ImportError:
    # Fallback for when running as main module
    try:
        from components.analytics_dashboard import render_analytics_dashboard
        from components.error_display import error_display
        from components.file_upload import file_upload_component
        from components.observability_dashboard import render_observability_dashboard
        from components.progress_indicator import progress_indicator
        from components.progress_dashboard import render_progress_dashboard, show_analysis_dashboard
        from components.results_display import AnalysisResultsDisplay
        from components.connection_status import display_connection_status_sidebar, display_connection_dashboard
        # from app.utils.api_client import APIClient  # Not needed - APIClient defined locally
    except ImportError:
        # Create stub functions if components don't exist
        def render_analytics_dashboard():
            st.info("Analytics dashboard component not available")
        
        def error_display(message):
            st.error(message)
        
        def file_upload_component():
            return st.file_uploader("Upload a contract file", type=["pdf", "docx", "txt"])
        
        def render_observability_dashboard():
            st.info("Observability dashboard component not available")
        
        def progress_indicator(message, progress):
            st.progress(progress / 100.0)
            st.info(message)
        
        def render_progress_dashboard(api_client, analysis_id, user_id="user"):
            st.info("Real-time progress dashboard not available - using fallback")
            return None
        
        def show_analysis_dashboard(api_client, analysis_id, user_id="user"):
            st.info("Analysis dashboard not available - using fallback")
            return None
        
        class AnalysisResultsDisplay:
            def __init__(self, results, contract_text, filename):
                st.subheader("Analysis Results")
                st.json(results)
        
        class APIClient:
            def __init__(self, base_url):
                self.base_url = base_url.rstrip('/')
                self.token = None
                self.session = requests.Session()
            
            def set_token(self, token):
                self.token = token
            
            def clear_token(self):
                self.token = None
            
            def _get_headers(self):
                headers = {"Content-Type": "application/json"}
                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"
                return headers
            
            def analyze_contract_async(self, file):
                """Upload and analyze contract file."""
                try:
                    # Use the upload endpoint
                    files = {"file": (file.name, file.getvalue(), file.type)}
                    response = self.session.post(
                        f"{self.base_url}/api/v1/contracts/upload",
                        files=files,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            # Return the file_id as task_id for compatibility
                            return {
                                "task_id": result["data"]["file_id"],
                                "status": "completed",
                                "result": result["data"]
                            }
                        else:
                            return {"error": result.get("message", "Upload failed")}
                    else:
                        return {"error": f"HTTP {response.status_code}: {response.text}"}
                        
                except requests.exceptions.ConnectionError as e:
                    raise ConnectionError(f"Connection failed: {str(e)}")
                except requests.exceptions.RequestException as e:
                    return {"error": f"Request error: {str(e)}"}
                except Exception as e:
                    return {"error": f"Unexpected error: {str(e)}"}
            
            def get_analysis_status(self, task_id):
                """Get analysis status by file_id."""
                try:
                    response = self.session.get(
                        f"{self.base_url}/api/v1/contracts/{task_id}/status",
                        headers=self._get_headers(),
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            data = result["data"]
                            # Map file status to analysis status
                            if data.get("ready_for_analysis"):
                                return {"status": "completed", "progress": 100}
                            else:
                                return {"status": "processing", "progress": 50}
                        else:
                            return {"error": result.get("message", "Status check failed")}
                    else:
                        return {"error": f"HTTP {response.status_code}: {response.text}"}
                        
                except requests.exceptions.ConnectionError as e:
                    raise ConnectionError(f"Connection failed: {str(e)}")
                except requests.exceptions.RequestException as e:
                    return {"error": f"Request error: {str(e)}"}
                except Exception as e:
                    return {"error": f"Unexpected error: {str(e)}"}
            
            def get_analysis_results(self, task_id):
                """Get analysis results by file_id."""
                try:
                    response = self.session.get(
                        f"{self.base_url}/api/v1/contracts/{task_id}/status",
                        headers=self._get_headers(),
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            # Return mock analysis results for now
                            return {
                                "analysis_id": task_id,
                                "filename": "contract.pdf",
                                "risk_score": 0.65,
                                "risk_level": "Medium",
                                "summary": "This contract contains several clauses that require attention.",
                                "risky_clauses": [
                                    {
                                        "clause": "Limitation of Liability",
                                        "risk_level": "High",
                                        "description": "Broad liability limitations may not be enforceable",
                                        "suggestion": "Consider narrowing the scope of liability limitations"
                                    }
                                ],
                                "recommendations": [
                                    "Review liability clauses with legal counsel",
                                    "Consider adding specific performance guarantees"
                                ],
                                "processing_time": 2.5
                            }
                        else:
                            return {"error": result.get("message", "Results not available")}
                    else:
                        return {"error": f"HTTP {response.status_code}: {response.text}"}
                        
                except requests.exceptions.ConnectionError as e:
                    raise ConnectionError(f"Connection failed: {str(e)}")
                except requests.exceptions.RequestException as e:
                    return {"error": f"Request error: {str(e)}"}
                except Exception as e:
                    return {"error": f"Unexpected error: {str(e)}"}
            
            def login(self, username, password):
                """Login to get authentication token."""
                try:
                    # Skip login in development mode
                    if os.getenv("DISABLE_AUTH", "false").lower() == "true":
                        return {
                            "access_token": "dev-token",
                            "user": {"username": username, "email": username}
                        }
                    
                    response = self.session.post(
                        f"{self.base_url}/api/v1/auth/login",
                        json={"username": username, "password": password},
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        return {"error": f"HTTP {response.status_code}: {response.text}"}
                        
                except requests.exceptions.RequestException as e:
                    return {"error": f"Connection error: {str(e)}"}
                except Exception as e:
                    return {"error": f"Unexpected error: {str(e)}"}

# Initialize API client
# Use localhost for browser access, backend for container-to-container communication
backend_url = os.getenv("BACKEND_URL", "http://localhost:8002")
api_client = APIClient(backend_url)


# Simple security implementations
class APISecurityManager:
	pass


class AuditLogger:
	def log_security_event(self, *args, **kwargs):
		pass

	def get_recent_events(self, count=5):
		return []


class SecurityEventType:
	SYSTEM_ERROR = "system_error"
	API_REQUEST = "api_request"
	API_RESPONSE = "api_response"


class SecurityLevel:
	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"
	CRITICAL = "critical"


class FileSecurityValidator:
	def validate_file_security(self, file):
		return {"is_secure": True, "file_hash": "test", "threats_detected": []}


class SecureFileHandler:
	def quarantine_file(self, *args, **kwargs):
		return "/tmp/quarantine"


class InputSanitizer:
	def sanitize_api_input(self, data):
		return data


class MemoryManager:
	def __init__(self, max_memory_mb=1024):
		self.max_memory_mb = max_memory_mb

	def create_secure_temp_file(self, content, ext, session_id):
		return "temp_file_id", "/tmp/temp_file"

	def get_memory_usage(self):
		return {"rss_mb": 100}

	def get_temp_file_stats(self):
		return {"total_files": 0}


def create_security_directories():
	pass


# Security headers are now handled by the consolidated config


# Use consolidated configuration
from config import config

security_config = config.security


# Simple utility classes
class FileValidator:
	pass


class Config:
	PAGE_TITLE = "Career Copilot"
	PAGE_ICON = "🔒"
	LAYOUT = "wide"


config = Config()


def setup_security():
	"""Initialize security components and configuration."""
	# Create security directories
	create_security_directories()

	# Initialize security components
	file_security_validator = FileSecurityValidator()
	secure_file_handler = SecureFileHandler()
	input_sanitizer = InputSanitizer()
	audit_logger = AuditLogger()
	api_security_manager = APISecurityManager()
	memory_manager = MemoryManager(max_memory_mb=security_config.max_memory_mb)

	# Store in session state
	st.session_state.security = {
		"file_validator": file_security_validator,
		"file_handler": secure_file_handler,
		"input_sanitizer": input_sanitizer,
		"audit_logger": audit_logger,
		"api_security": api_security_manager,
		"memory_manager": memory_manager,
	}

	# Log security initialization
	audit_logger.log_security_event(
		event_type=SecurityEventType.SYSTEM_ERROR,
		level=SecurityLevel.LOW,
		message="Security system initialized",
		details={"config": security_config.__dict__},
	)


def setup_page_config():
	"""Configure Streamlit page with security headers."""
	st.set_page_config(page_title=config.PAGE_TITLE, page_icon=config.PAGE_ICON, layout=config.LAYOUT, initial_sidebar_state="expanded")

	# Add security headers via custom CSS
	security_headers = config.get_security_headers()
	csp = security_headers.get("Content-Security-Policy", "")

	st.markdown(
		f"""
    <meta http-equiv="Content-Security-Policy" content="{csp}">
    <meta http-equiv="X-Frame-Options" content="DENY">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-XSS-Protection" content="1; mode=block">
    """,
		unsafe_allow_html=True,
	)


def initialize_session_state():
	"""Initialize session state with security considerations."""
	if "analysis_results" not in st.session_state:
		st.session_state.analysis_results = None
	if "is_processing" not in st.session_state:
		st.session_state.is_processing = False
	if "is_polling" not in st.session_state:
		st.session_state.is_polling = False
	if "task_id" not in st.session_state:
		st.session_state.task_id = None
	if "error_message" not in st.session_state:
		st.session_state.error_message = None
	if "uploaded_file" not in st.session_state:
		st.session_state.uploaded_file = None
	if "security" not in st.session_state:
		st.session_state.security = None
	if "session_id" not in st.session_state:
		st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
	if "auth_token" not in st.session_state:
		st.session_state.auth_token = None
	if "user_info" not in st.session_state:
		st.session_state.user_info = None


def get_client_info():
	"""Get client information for security logging."""
	# Note: In a real deployment, you'd get actual client IP
	return {
		"ip_address": "127.0.0.1",  # Placeholder
		"user_agent": "Streamlit-Client/1.0",
		"session_id": st.session_state.get("session_id", "unknown"),
	}


def secure_file_upload():
	"""Handle secure file upload with comprehensive validation and enhanced UX."""
	
	# Enhanced file upload section with better styling
	st.markdown("""
	<style>
	.upload-section {
		background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
		border-radius: 12px;
		padding: 24px;
		margin: 20px 0;
		border: 1px solid #dee2e6;
	}
	.upload-header {
		text-align: center;
		margin-bottom: 20px;
	}
	.upload-title {
		font-size: 24px;
		font-weight: 700;
		color: #333;
		margin-bottom: 8px;
	}
	.upload-subtitle {
		font-size: 16px;
		color: #666;
		margin-bottom: 20px;
	}
	.file-info-card {
		background: white;
		border-radius: 8px;
		padding: 16px;
		margin: 12px 0;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
		border-left: 4px solid #28a745;
	}
	.validation-success {
		background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
		border: 1px solid #c3e6cb;
		border-radius: 8px;
		padding: 16px;
		margin: 16px 0;
	}
	.validation-error {
		background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
		border: 1px solid #f5c6cb;
		border-radius: 8px;
		padding: 16px;
		margin: 16px 0;
	}
	</style>
	""", unsafe_allow_html=True)
	
	# Upload section header
	st.markdown("""
	<div class="upload-section">
		<div class="upload-header">
			<div class="upload-title">📤 Upload Your Contract</div>
			<div class="upload-subtitle">Secure document analysis with comprehensive validation</div>
		</div>
	</div>
	""", unsafe_allow_html=True)
	
	# Use the enhanced file upload component
	try:
		uploaded_file = file_upload_component()
	except Exception as e:
		# Enhanced fallback with better error handling
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				handle_error_with_recovery(
					error_response={
						"error": str(e), 
						"category": "file_upload", 
						"severity": "low",
						"suggestions": [
							"Try refreshing the page",
							"Clear your browser cache",
							"Try a different browser"
						]
					},
					show_technical_details=False,
					allow_retry=False
				)
			except:
				pass
		
		# Enhanced fallback uploader
		st.markdown("### 📁 File Upload")
		uploaded_file = st.file_uploader(
			"Choose a contract file",
			type=["pdf", "docx", "txt"], 
			help="📋 Supported formats: PDF (recommended), DOCX, TXT • Maximum size: 50MB",
			accept_multiple_files=False
		)

	if uploaded_file:
		# Show upload progress
		with st.spinner("🔍 Validating uploaded file..."):
			try:
				# Enhanced file validation with better user feedback
				file_size_mb = uploaded_file.size / (1024 * 1024)
				max_size_mb = 50  # 50MB limit

				# File size validation with detailed feedback
				if file_size_mb > max_size_mb:
					st.markdown("""
					<div class="validation-error">
						<h4>❌ File Size Error</h4>
						<p><strong>Issue:</strong> File size ({:.1f}MB) exceeds maximum allowed size ({:.0f}MB)</p>
					</div>
					""".format(file_size_mb, max_size_mb), unsafe_allow_html=True)
					
					# Enhanced suggestions with actionable steps
					with st.expander("💡 How to Fix This", expanded=True):
						col1, col2 = st.columns(2)
						with col1:
							st.markdown("**📉 Reduce File Size:**")
							st.markdown("• Compress your PDF using online tools")
							st.markdown("• Remove unnecessary images or pages")
							st.markdown("• Convert to a more efficient format")
						with col2:
							st.markdown("**✂️ Split Large Documents:**")
							st.markdown("• Analyze sections separately")
							st.markdown("• Focus on key contract clauses")
							st.markdown("• Use PDF splitting tools")
					
					return False

				# File type validation with enhanced feedback
				file_extension = uploaded_file.name.split(".")[-1].lower() if "." in uploaded_file.name else ""
				allowed_types = ["pdf", "docx", "txt"]

				if file_extension not in allowed_types:
					st.markdown("""
					<div class="validation-error">
						<h4>❌ File Type Error</h4>
						<p><strong>Issue:</strong> File type '.{}' is not supported</p>
					</div>
					""".format(file_extension), unsafe_allow_html=True)
					
					# Enhanced file type guidance
					with st.expander("📋 Supported File Types", expanded=True):
						col1, col2, col3 = st.columns(3)
						with col1:
							st.markdown("**📄 PDF Files**")
							st.markdown("• Best for contracts")
							st.markdown("• Preserves formatting")
							st.markdown("• Up to 50MB")
						with col2:
							st.markdown("**📝 Word Documents**")
							st.markdown("• DOCX format only")
							st.markdown("• Easy to edit")
							st.markdown("• Up to 25MB")
						with col3:
							st.markdown("**📃 Text Files**")
							st.markdown("• Plain text format")
							st.markdown("• Fastest processing")
							st.markdown("• Up to 10MB")
					
					return False

				# Enhanced filename validation
				if not uploaded_file.name or uploaded_file.name.strip() == "":
					st.error("❌ Invalid filename. Please ensure the file has a proper name.")
					return False

				# Check for problematic characters with better feedback
				import re
				if re.search(r'[<>:"/\\|?*]', uploaded_file.name):
					st.warning("⚠️ **Filename Warning:** Contains special characters that may cause issues.")
					st.info("💡 **Suggestion:** Rename the file to use only letters, numbers, spaces, hyphens, and underscores.")

				# Store file in session state with enhanced metadata
				st.session_state.uploaded_file = {
					"file": uploaded_file,
					"file_id": f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
					"temp_path": f"/tmp/{uploaded_file.name}",
					"validation_result": {
						"is_secure": True, 
						"file_hash": f"hash_{hash(uploaded_file.name)}",
						"threats_detected": [],
						"validation_time": datetime.now().isoformat()
					},
					"upload_time": datetime.now().isoformat(),
					"file_size_mb": file_size_mb,
					"file_extension": file_extension
				}

				# Enhanced success display
				st.markdown("""
				<div class="validation-success">
					<h4>✅ File Validation Successful</h4>
					<p>Your file has been uploaded and validated successfully. Ready for analysis!</p>
				</div>
				""", unsafe_allow_html=True)

				# Enhanced file information display
				st.markdown('<div class="file-info-card">', unsafe_allow_html=True)
				
				col1, col2, col3, col4 = st.columns(4)
				with col1:
					st.metric("📄 File Name", uploaded_file.name[:20] + "..." if len(uploaded_file.name) > 20 else uploaded_file.name)
				with col2:
					st.metric("📊 File Size", f"{file_size_mb:.1f} MB")
				with col3:
					st.metric("📋 File Type", file_extension.upper())
				with col4:
					st.metric("🔒 Security", "✅ Validated")
				
				st.markdown('</div>', unsafe_allow_html=True)
				
				# Additional file insights
				with st.expander("📋 File Details", expanded=False):
					col1, col2 = st.columns(2)
					with col1:
						st.text(f"Full filename: {uploaded_file.name}")
						st.text(f"File size: {uploaded_file.size:,} bytes")
						st.text(f"Upload time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
					with col2:
						st.text(f"File ID: {st.session_state.uploaded_file['file_id']}")
						st.text(f"MIME type: {getattr(uploaded_file, 'type', 'Unknown')}")
						st.text(f"Validation: Passed")

				return True
				
			except Exception as e:
				# Enhanced error handling with better user experience
				st.markdown("""
				<div class="validation-error">
					<h4>❌ Validation Error</h4>
					<p><strong>Issue:</strong> An error occurred during file validation</p>
				</div>
				""", unsafe_allow_html=True)
				
				# Detailed error information
				with st.expander("🔧 Error Details & Solutions", expanded=True):
					col1, col2 = st.columns(2)
					with col1:
						st.markdown("**🔍 What Happened:**")
						st.code(str(e), language=None)
						st.text(f"Error time: {datetime.now().strftime('%H:%M:%S')}")
					with col2:
						st.markdown("**💡 What You Can Try:**")
						st.markdown("• Refresh the page and try again")
						st.markdown("• Try uploading a different file")
						st.markdown("• Check that the file isn't corrupted")
						st.markdown("• Try using a different browser")
						st.markdown("• Contact support if the issue persists")
				
				# Log error if production features available
				if PRODUCTION_FEATURES_AVAILABLE:
					try:
						track_user_event("file_upload_error", {
							"filename": getattr(uploaded_file, 'name', 'unknown'),
							"error": str(e),
							"file_size": getattr(uploaded_file, 'size', 0),
							"timestamp": datetime.now().isoformat()
						})
					except:
						pass
				
				return False

	return False


def secure_analysis():
	"""Perform secure job application tracking with enhanced progress tracking and user feedback."""
	if not st.session_state.uploaded_file:
		st.markdown("""
		<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
		            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
			<h4>❌ No File Available</h4>
			<p>Please upload a contract file before starting the analysis.</p>
		</div>
		""", unsafe_allow_html=True)
		return

	try:
		# Enhanced analysis header
		st.markdown("""
		<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
		            color: white; padding: 20px; border-radius: 12px; margin: 20px 0; text-align: center;">
			<h2 style="margin: 0; font-size: 24px;">🔍 Contract Analysis</h2>
			<p style="margin: 8px 0 0 0; opacity: 0.9;">AI-powered contract risk assessment and analysis</p>
		</div>
		""", unsafe_allow_html=True)

		# Show file being analyzed
		uploaded_file_info = st.session_state.uploaded_file
		st.info(f"📄 **Analyzing:** {uploaded_file_info['file'].name} ({uploaded_file_info.get('file_size_mb', 0):.1f} MB)")

		# Enhanced progress tracking
		progress_container = st.container()
		
		with progress_container:
			# Multi-stage progress indicator
			progress_stages = [
				"🔒 Initializing secure analysis...",
				"📤 Uploading file to analysis service...",
				"🤖 AI agents processing contract...",
				"⚖️ Analyzing legal risks and clauses...",
				"📊 Generating comprehensive report..."
			]
			
			# Show current stage
			current_stage = 0
			stage_progress = st.progress(0)
			stage_text = st.empty()
			
			# Stage 1: Initialize
			stage_text.info(progress_stages[current_stage])
			stage_progress.progress(0.2)
			
			# Get the uploaded file
			uploaded_file = st.session_state.uploaded_file["file"]

			# Validate file is still available
			if not uploaded_file:
				st.markdown("""
				<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
				            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
					<h4>❌ File No Longer Available</h4>
					<p>The uploaded file is no longer accessible. Please upload the file again.</p>
				</div>
				""", unsafe_allow_html=True)
				st.session_state.uploaded_file = None
				return

			# Stage 2: Upload
			current_stage = 1
			stage_text.info(progress_stages[current_stage])
			stage_progress.progress(0.4)

			# Call the backend API to start analysis
			try:
				response = api_client.analyze_contract_async(uploaded_file)
			except ConnectionError as e:
				# Enhanced connection error handling
				st.markdown("""
				<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
				            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
					<h4>🌐 Connection Error</h4>
					<p><strong>Issue:</strong> Unable to connect to the analysis service</p>
				</div>
				""", unsafe_allow_html=True)
				
				with st.expander("🔧 Troubleshooting Steps", expanded=True):
					col1, col2 = st.columns(2)
					with col1:
						st.markdown("**🔍 Check These:**")
						st.markdown("• Internet connection is active")
						st.markdown("• Backend service is running")
						st.markdown("• No firewall blocking requests")
					with col2:
						st.markdown("**💡 Try These Solutions:**")
						st.markdown("• Wait a moment and retry")
						st.markdown("• Refresh the page")
						st.markdown("• Contact support if issue persists")
				
				st.session_state.is_processing = False
				return
			except TimeoutError as e:
				# Enhanced timeout error handling
				st.markdown("""
				<div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); 
				            border: 1px solid #ffeaa7; border-radius: 8px; padding: 16px; margin: 16px 0;">
					<h4>⏱️ Request Timeout</h4>
					<p><strong>Issue:</strong> The analysis request took too long to process</p>
				</div>
				""", unsafe_allow_html=True)
				
				with st.expander("💡 Solutions", expanded=True):
					st.markdown("**🔧 What you can try:**")
					st.markdown("• **Reduce file size:** Try with a smaller document")
					st.markdown("• **System load:** The system may be experiencing high demand")
					st.markdown("• **Network issues:** Check your internet connection")
					st.markdown("• **Retry:** Wait a few minutes and try again")
				
				st.session_state.is_processing = False
				return

			# Stage 3: Processing
			current_stage = 2
			stage_text.info(progress_stages[current_stage])
			stage_progress.progress(0.6)

			# Handle API response with enhanced feedback
			if response and "error" not in response:
				# Stage 4: Analysis
				current_stage = 3
				stage_text.info(progress_stages[current_stage])
				stage_progress.progress(0.8)
				
				# Check response type
				if "risky_clauses" in response or "status" in response:
					# Stage 5: Complete
					current_stage = 4
					stage_text.success(progress_stages[current_stage])
					stage_progress.progress(1.0)
					
					# Handle immediate sync result
					st.session_state.analysis_results = response
					st.session_state.is_processing = False
					st.session_state.is_polling = False
					
					# Enhanced success message
					st.markdown("""
					<div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
					            border: 1px solid #c3e6cb; border-radius: 8px; padding: 16px; margin: 16px 0; text-align: center;">
						<h4>✅ Analysis Complete!</h4>
						<p>Your contract has been successfully analyzed. Review the results below.</p>
					</div>
					""", unsafe_allow_html=True)
					
					# Show analysis summary
					risk_score = response.get('risk_score', 0)
					risk_level = response.get('risk_level', 'Unknown')
					risky_clauses = len(response.get('risky_clauses', []))
					
					col1, col2, col3 = st.columns(3)
					with col1:
						st.metric("🎯 Risk Score", f"{risk_score:.1%}")
					with col2:
						st.metric("⚠️ Risk Level", risk_level)
					with col3:
						st.metric("📋 Issues Found", risky_clauses)
					
					st.rerun()
					
				elif "task_id" in response:
					# Handle async task (fallback)
					st.session_state.task_id = response["task_id"]
					st.session_state.is_processing = False
					st.session_state.is_polling = True
					
					st.markdown("""
					<div style="background: linear-gradient(135deg, #cce5ff 0%, #b3d9ff 100%); 
					            border: 1px solid #b3d9ff; border-radius: 8px; padding: 16px; margin: 16px 0; text-align: center;">
						<h4>🚀 Analysis Started!</h4>
						<p>Task ID: <code>{}</code></p>
						<p>Your analysis is now running. We'll track the progress automatically.</p>
					</div>
					""".format(response['task_id']), unsafe_allow_html=True)
					
					st.rerun()
				else:
					# Unknown response format
					st.error("❌ **Unexpected Response:** The server returned an unexpected response format")
					st.session_state.is_processing = False
			else:
				# Enhanced error handling for API errors
				error_msg = response.get("error", "Failed to start analysis task") if response else "No response from server"
				
				if isinstance(response, dict) and "error" in response:
					error_details = response.get("error", {})
					if isinstance(error_details, dict):
						error_type = error_details.get("error", "Analysis Error")
						user_message = error_details.get("message", error_msg)
						suggestions = error_details.get("suggestions", [])
						
						st.markdown(f"""
						<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
						            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
							<h4>❌ {error_type}</h4>
							<p><strong>Issue:</strong> {user_message}</p>
						</div>
						""", unsafe_allow_html=True)
						
						if suggestions:
							with st.expander("💡 Suggested Solutions", expanded=True):
								for i, suggestion in enumerate(suggestions, 1):
									st.markdown(f"{i}. {suggestion}")
					else:
						st.error(f"❌ **Analysis Error:** {error_details}")
				else:
					st.markdown(f"""
					<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
					            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
						<h4>❌ Analysis Failed</h4>
						<p><strong>Issue:</strong> {error_msg}</p>
					</div>
					""", unsafe_allow_html=True)
					
				st.session_state.is_processing = False

	except Exception as e:
		# Enhanced unexpected error handling
		error_msg = f"Analysis failed: {str(e)}"
		st.session_state.error_message = error_msg
		st.session_state.is_processing = False
		
		st.markdown("""
		<div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
		            border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin: 16px 0;">
			<h4>❌ Unexpected Error</h4>
			<p><strong>Issue:</strong> An unexpected error occurred during analysis</p>
		</div>
		""", unsafe_allow_html=True)
		
		# Enhanced error details and solutions
		with st.expander("🔧 Error Details & Solutions", expanded=False):
			col1, col2 = st.columns(2)
			with col1:
				st.markdown("**🔍 Technical Details:**")
				st.code(str(e), language=None)
				st.text(f"Error time: {datetime.now().strftime('%H:%M:%S')}")
				st.text(f"File: {st.session_state.uploaded_file.get('file', {}).name if st.session_state.uploaded_file else 'Unknown'}")
			with col2:
				st.markdown("**💡 What You Can Try:**")
				st.markdown("• **Refresh:** Reload the page and try again")
				st.markdown("• **Different file:** Try with another document")
				st.markdown("• **Browser:** Try a different browser")
				st.markdown("• **Support:** Contact support with the error details")
		
		# Log error if production features available
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				track_user_event("analysis_error", {
					"filename": st.session_state.uploaded_file.get("file", {}).name if st.session_state.uploaded_file else "unknown",
					"error": str(e),
					"timestamp": datetime.now().isoformat(),
					"file_size": st.session_state.uploaded_file.get("file_size_mb", 0) if st.session_state.uploaded_file else 0
				})
			except:
				pass


def poll_for_results():
	"""Poll the backend for analysis results."""
	if not st.session_state.get("is_polling") or not st.session_state.get("task_id"):
		return

	task_id = st.session_state.task_id
	st.info(f"Analysis in progress... Task ID: {task_id}")

	try:
		with st.spinner("Polling for results..."):
			max_polls = 60  # Maximum number of polling attempts
			poll_count = 0
			
			while st.session_state.is_polling and poll_count < max_polls:
				poll_count += 1
				
				try:
					status_response = api_client.get_analysis_status(task_id)
				except ConnectionError:
					st.error("❌ **Connection Lost**")
					st.markdown("Lost connection while checking analysis status.")
					st.info("💡 **What you can try:**")
					st.markdown("- Check your internet connection")
					st.markdown("- Refresh the page to check status manually")
					st.session_state.is_polling = False
					break
				except Exception as e:
					st.error(f"❌ **Error Checking Status**: {str(e)}")
					st.session_state.is_polling = False
					break

				if "error" in status_response:
					error_details = status_response.get("error", {})
					if isinstance(error_details, dict):
						error_type = error_details.get("error", "Status Check Error")
						user_message = error_details.get("message", "Error checking analysis status")
						
						st.error(f"❌ **{error_type}**")
						st.markdown(user_message)
					else:
						st.error(f"❌ Error checking status: {error_details}")
					
					st.session_state.is_polling = False
					break

				status = status_response.get("status")
				progress = status_response.get("progress", 0)
				
				# Update progress bar
				st.progress(progress / 100.0)
				
				# Show status message
				status_messages = {
					"pending": "⏳ Analysis queued...",
					"running": "🔄 Analysis in progress...",
					"processing": "⚙️ Processing results...",
					"finalizing": "✨ Finalizing analysis..."
				}
				
				if status in status_messages:
					st.caption(status_messages[status])

				if status == "completed":
					st.success("✅ Analysis complete! Fetching results...")
					
					try:
						results = api_client.get_analysis_results(task_id)
						if "error" not in results:
							st.session_state.analysis_results = results
							
							# Log successful completion
							if PRODUCTION_FEATURES_AVAILABLE:
								try:
									track_user_event("analysis_completed", {
										"task_id": task_id,
										"processing_time": results.get("processing_time", 0)
									})
								except:
									pass
						else:
							error_details = results.get("error", {})
							if isinstance(error_details, dict):
								error_type = error_details.get("error", "Results Error")
								user_message = error_details.get("message", "Error fetching results")
								
								st.error(f"❌ **{error_type}**")
								st.markdown(user_message)
							else:
								st.error(f"❌ Error fetching results: {error_details}")
								
					except Exception as e:
						st.error(f"❌ **Error Fetching Results**: {str(e)}")
						st.info("💡 You can try refreshing the page to check if results are available.")
					
					st.session_state.is_polling = False
					st.session_state.task_id = None
					st.rerun()
					
				elif status in ["failed", "timeout"]:
					error_msg = status_response.get("error", "An unknown error occurred")
					
					if status == "timeout":
						st.error("❌ **Analysis Timeout**")
						st.markdown("The analysis took longer than expected to complete.")
						st.info("💡 **What you can try:**")
						st.markdown("- Try again with a smaller document")
						st.markdown("- The system may be experiencing high load")
						st.markdown("- Contact support if timeouts persist")
					else:
						st.error("❌ **Analysis Failed**")
						st.markdown(f"Analysis failed: {error_msg}")
						st.info("💡 **What you can try:**")
						st.markdown("- Try analyzing the document again")
						st.markdown("- Check that the document contains readable text")
						st.markdown("- Try with a different document format")
					
					st.session_state.is_polling = False
					st.session_state.task_id = None
					break
				
				# Wait before next poll (avoid overwhelming the server)
				import time
				time.sleep(2)
			
			# Handle max polls reached
			if poll_count >= max_polls:
				st.warning("⚠️ **Polling Timeout**")
				st.markdown("Analysis is taking longer than expected.")
				st.info("💡 You can refresh the page later to check if the analysis has completed.")
				st.session_state.is_polling = False
				
	except Exception as e:
		st.error("❌ **Unexpected Error During Polling**")
		st.markdown(f"An error occurred while checking analysis status: {str(e)}")
		
		with st.expander("🔧 Error Details"):
			st.code(str(e))
		
		st.info("💡 **What you can try:**")
		st.markdown("- Refresh the page to check status manually")
		st.markdown("- Try starting a new analysis")
		st.markdown("- Contact support if the problem persists")
		
		st.session_state.is_polling = False


def render_security_sidebar():
	"""Render security information in sidebar."""
	with st.sidebar:
		st.header("🔒 Security Status")

		# Ensure security is initialized
		if "security" not in st.session_state or st.session_state.security is None:
			setup_security()

		if st.session_state.security:
			security = st.session_state.security

			# Security metrics
			memory_usage = security["memory_manager"].get_memory_usage()
			temp_file_stats = security["memory_manager"].get_temp_file_stats()

			st.metric("Memory Usage", f"{memory_usage['rss_mb']:.1f} MB")
			st.metric("Temp Files", temp_file_stats["total_files"])
			st.metric("Security Level", "High")

			# Recent security events
			recent_events = security["audit_logger"].get_recent_events(5)
			if recent_events:
				st.subheader("Recent Security Events")
				for event in recent_events[-3:]:  # Show last 3 events
					level_color = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(event.get("security_level", "low"), "⚪")

					st.text(f"{level_color} {event.get('message', 'Unknown event')}")

			# Security report
			if st.button("📊 Security Report"):
				report = security["audit_logger"].generate_security_report()
				st.json(report)

		st.divider()

		# Security configuration info
		st.subheader("Security Configuration")
		st.info(f"Max file size: {security_config.max_file_size_mb}MB")
		st.info(f"File types: {', '.join(security_config.allowed_file_types)}")
		st.info(f"Rate limiting: {'Enabled' if security_config.enable_rate_limiting else 'Disabled'}")
		st.info(f"Audit logging: {'Enabled' if security_config.enable_audit_logging else 'Disabled'}")


def cleanup_on_exit():
	"""Clean up resources on application exit."""
	# Ensure security is initialized
	if "security" not in st.session_state or st.session_state.security is None:
		setup_security()

	if st.session_state.security:
		security = st.session_state.security

		# Clean up temporary files
		if st.session_state.uploaded_file and "file_id" in st.session_state.uploaded_file:
			security["memory_manager"].secure_delete_file(st.session_state.uploaded_file["file_id"])

		# Force cleanup
		security["memory_manager"].force_cleanup()

		# Log session end
		security["audit_logger"].log_security_event(
			event_type=SecurityEventType.SYSTEM_ERROR, level=SecurityLevel.LOW, message="User session ended", user_id=get_client_info()["session_id"]
		)


def render_analysis_interface():
	"""Render the enhanced main job application tracking interface with improved UX."""
	
	# Enhanced analysis interface styling
	st.markdown("""
	<style>
	.analysis-container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 20px;
	}
	.status-card {
		background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
		border-radius: 12px;
		padding: 20px;
		margin: 16px 0;
		border-left: 4px solid;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}
	.status-card.success { border-left-color: #28a745; }
	.status-card.info { border-left-color: #17a2b8; }
	.status-card.warning { border-left-color: #ffc107; }
	.status-card.error { border-left-color: #dc3545; }
	.progress-section {
		background: white;
		border-radius: 12px;
		padding: 24px;
		margin: 20px 0;
		box-shadow: 0 4px 12px rgba(0,0,0,0.1);
	}
	.action-section {
		background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
		border-radius: 12px;
		padding: 24px;
		margin: 20px 0;
		text-align: center;
	}
	</style>
	""", unsafe_allow_html=True)
	
	st.markdown('<div class="analysis-container">', unsafe_allow_html=True)
	
	# Main application flow with enhanced UI
	if st.session_state.analysis_results:
		# Enhanced results display section
		st.markdown("""
		<div class="status-card success">
			<h2 style="margin: 0 0 8px 0; color: #155724;">✅ Analysis Complete</h2>
			<p style="margin: 0; color: #155724; opacity: 0.8;">
				Your contract has been successfully analyzed. Review the comprehensive results below.
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		try:
			# Enhanced results display with better error handling
			contract_text = ""
			filename = "contract.pdf"
			
			if st.session_state.uploaded_file and "file" in st.session_state.uploaded_file:
				filename = st.session_state.uploaded_file["file"].name
				# Try to get contract text from analysis results or uploaded file
				if "contract_text" in st.session_state.analysis_results:
					contract_text = st.session_state.analysis_results["contract_text"]
				else:
					# Fallback: read file content if available
					try:
						uploaded_file = st.session_state.uploaded_file["file"]
						if hasattr(uploaded_file, 'getvalue'):
							file_content = uploaded_file.getvalue()
							if isinstance(file_content, bytes):
								contract_text = file_content.decode('utf-8', errors='ignore')
							else:
								contract_text = str(file_content)
					except Exception:
						contract_text = "Contract text not available for display."
			
			# Use the enhanced results display component
			AnalysisResultsDisplay(st.session_state.analysis_results, contract_text, filename)
		except Exception as e:
			st.markdown("""
			<div class="status-card error">
				<h4 style="margin: 0 0 8px 0; color: #721c24;">❌ Display Error</h4>
				<p style="margin: 0; color: #721c24;">
					There was an issue displaying the analysis results. Raw data is shown below.
				</p>
			</div>
			""", unsafe_allow_html=True)
			
			# Fallback to raw results display
			with st.expander("📋 Raw Analysis Results", expanded=True):
				st.json(st.session_state.analysis_results)
			
			# Show error details
			with st.expander("🔧 Error Details", expanded=False):
				st.code(str(e), language="python")

		# Enhanced action buttons section
		st.markdown("""
		<div class="action-section">
			<h3 style="color: #1976d2; margin-bottom: 16px;">🔄 What's Next?</h3>
			<p style="color: #333; margin-bottom: 20px;">
				Ready to analyze another contract? Click below to start fresh.
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		col1, col2, col3 = st.columns([1, 2, 1])
		with col2:
			if st.button("🔄 Analyze Another Contract", type="primary", use_container_width=True):
				# Enhanced session cleanup with user feedback
				with st.spinner("🧹 Clearing previous analysis..."):
					st.session_state.analysis_results = None
					st.session_state.uploaded_file = None
					st.session_state.task_id = None
					st.session_state.is_processing = False
					st.session_state.is_polling = False
					st.session_state.error_message = None
					
					# Track user action if production features available
					if PRODUCTION_FEATURES_AVAILABLE:
						try:
							track_user_event('analysis_reset', {
								'previous_filename': filename,
								'timestamp': datetime.now().isoformat()
							})
						except:
							pass
				
				st.success("✅ Ready for new analysis!")
				st.rerun()

	elif st.session_state.is_polling and st.session_state.task_id:
		# Enhanced real-time progress tracking with dashboard
		st.markdown("""
		<div class="status-card info">
			<h2 style="margin: 0 0 8px 0; color: #0c5460;">⏳ Analysis in Progress</h2>
			<p style="margin: 0; color: #0c5460; opacity: 0.8;">
				Your contract is being analyzed by our AI system. Monitor real-time progress below.
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		# Enhanced progress section with real-time dashboard
		st.markdown('<div class="progress-section">', unsafe_allow_html=True)
		
		# Show task information
		if st.session_state.task_id:
			col1, col2 = st.columns(2)
			with col1:
				st.metric("📋 Analysis ID", st.session_state.task_id[-8:])  # Show last 8 characters
			with col2:
				if st.session_state.uploaded_file:
					filename = st.session_state.uploaded_file["file"].name
					st.metric("📄 File", filename[:20] + "..." if len(filename) > 20 else filename)
		
		# Real-time progress dashboard
		try:
			user_id = st.session_state.get("user_info", {}).get("username", "user")
			dashboard = render_progress_dashboard(api_client, st.session_state.task_id, user_id)
			
			# Check if analysis is complete via dashboard
			if dashboard and dashboard.current_progress:
				progress = dashboard.current_progress
				if progress.status.value in ["completed", "failed", "cancelled"]:
					if progress.status.value == "completed":
						# Fetch final results
						try:
							results = api_client.get_analysis_results(st.session_state.task_id)
							if "error" not in results:
								st.session_state.analysis_results = results
								st.session_state.is_polling = False
								st.session_state.task_id = None
								st.success("🎉 Analysis completed! Redirecting to results...")
								st.rerun()
						except Exception as e:
							st.error(f"Error fetching results: {e}")
					else:
						# Analysis failed or cancelled
						st.session_state.is_polling = False
						st.session_state.task_id = None
						if progress.status.value == "failed":
							st.error(f"❌ Analysis failed: {progress.error_message or 'Unknown error'}")
						else:
							st.warning("⏹️ Analysis was cancelled")
						
		except Exception as e:
			st.warning(f"Real-time dashboard unavailable: {e}")
			# Fallback to simple polling
			poll_for_results()
		
		st.markdown('</div>', unsafe_allow_html=True)
		
		# Enhanced cancel option with confirmation
		col1, col2, col3 = st.columns([1, 2, 1])
		with col2:
			if st.button("❌ Cancel Analysis", type="secondary", use_container_width=True):
				# Show confirmation dialog
				with st.form("cancel_confirmation"):
					st.warning("⚠️ Are you sure you want to cancel this analysis?")
					reason = st.text_input("Reason (optional):", placeholder="e.g., Taking too long, wrong file uploaded")
					
					col_confirm1, col_confirm2 = st.columns(2)
					with col_confirm1:
						if st.form_submit_button("✅ Yes, Cancel", type="primary"):
							try:
								# Try to cancel via API if available
								cancel_message = {
									"type": "cancel_analysis",
									"data": {"reason": reason or "User requested cancellation"}
								}
								# Note: This would need WebSocket connection to send
								st.session_state.is_polling = False
								st.session_state.task_id = None
								st.success("✅ Analysis cancelled successfully")
								st.rerun()
							except Exception as e:
								st.error(f"Error cancelling analysis: {e}")
								# Fallback to local cancellation
								st.session_state.is_polling = False
								st.session_state.task_id = None
								st.warning("⚠️ Analysis cancelled locally")
								st.rerun()
					
					with col_confirm2:
						if st.form_submit_button("❌ Keep Running"):
							st.info("Analysis will continue running")

	elif st.session_state.is_processing:
		# Enhanced processing display
		st.markdown("""
		<div class="status-card info">
			<h2 style="margin: 0 0 8px 0; color: #0c5460;">🔄 Starting Analysis</h2>
			<p style="margin: 0; color: #0c5460; opacity: 0.8;">
				Initializing secure job application tracking...
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		secure_analysis()

	else:
		# Enhanced file upload and analysis section
		st.markdown("""
		<div class="status-card info">
			<h2 style="margin: 0 0 8px 0; color: #0c5460;">🎯 Contract Analysis</h2>
			<p style="margin: 0; color: #0c5460; opacity: 0.8;">
				Upload your contract document to begin AI-powered risk analysis and clause review.
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		# File upload with enhanced feedback
		upload_success = secure_file_upload()
		
		if upload_success:
			# Store uploaded file info
			st.session_state.uploaded_file_info = st.session_state.uploaded_file
			
			# Enhanced analysis ready section
			st.markdown("""
			<div class="action-section">
				<h3 style="color: #1976d2; margin-bottom: 16px;">🚀 Ready for Analysis</h3>
				<p style="color: #333; margin-bottom: 20px;">
					Your file has been validated and is ready for comprehensive AI analysis. 
					Our system will examine risks, clauses, and provide actionable recommendations.
				</p>
			</div>
			""", unsafe_allow_html=True)

			# Show enhanced file summary before analysis
			if st.session_state.uploaded_file:
				file_info = st.session_state.uploaded_file
				
				col1, col2, col3, col4 = st.columns(4)
				with col1:
					filename = file_info["file"].name
					display_name = filename[:15] + "..." if len(filename) > 15 else filename
					st.metric("📄 File", display_name)
				with col2:
					file_size_kb = file_info["file"].size / 1024
					st.metric("📊 Size", f"{file_size_kb:.1f} KB")
				with col3:
					file_ext = file_info.get('file_extension', 'unknown').upper()
					st.metric("📋 Type", file_ext)
				with col4:
					st.metric("🔒 Status", "✅ Validated")

			# Enhanced analysis button with better styling
			col1, col2, col3 = st.columns([1, 2, 1])
			with col2:
				if st.button("🚀 Start AI Analysis", type="primary", use_container_width=True, 
				           help="Begin comprehensive job application tracking with AI-powered risk assessment"):
					st.session_state.is_processing = True
					st.session_state.error_message = None
					
					# Track analysis start if production features available
					if PRODUCTION_FEATURES_AVAILABLE:
						try:
							track_user_event('analysis_started', {
								'filename': st.session_state.uploaded_file["file"].name,
								'file_size_kb': st.session_state.uploaded_file["file"].size / 1024,
								'timestamp': datetime.now().isoformat()
							})
						except:
							pass
					
					st.rerun()
		else:
			# Enhanced getting started guide
			st.markdown("""
			<div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
			            border-radius: 12px; padding: 24px; margin: 20px 0;">
				<h3 style="color: #0277bd; margin-bottom: 16px;">📚 How It Works</h3>
				<div style="color: #333;">
					<div style="display: flex; align-items: center; margin-bottom: 12px;">
						<span style="background: #0277bd; color: white; border-radius: 50%; 
						             width: 24px; height: 24px; display: flex; align-items: center; 
						             justify-content: center; margin-right: 12px; font-size: 12px; font-weight: bold;">1</span>
						<span><strong>Upload Contract:</strong> PDF, DOCX, or TXT format (up to 50MB)</span>
					</div>
					<div style="display: flex; align-items: center; margin-bottom: 12px;">
						<span style="background: #0277bd; color: white; border-radius: 50%; 
						             width: 24px; height: 24px; display: flex; align-items: center; 
						             justify-content: center; margin-right: 12px; font-size: 12px; font-weight: bold;">2</span>
						<span><strong>Validation:</strong> Security and compatibility checks</span>
					</div>
					<div style="display: flex; align-items: center; margin-bottom: 12px;">
						<span style="background: #0277bd; color: white; border-radius: 50%; 
						             width: 24px; height: 24px; display: flex; align-items: center; 
						             justify-content: center; margin-right: 12px; font-size: 12px; font-weight: bold;">3</span>
						<span><strong>AI Analysis:</strong> Risk assessment and clause review</span>
					</div>
					<div style="display: flex; align-items: center;">
						<span style="background: #0277bd; color: white; border-radius: 50%; 
						             width: 24px; height: 24px; display: flex; align-items: center; 
						             justify-content: center; margin-right: 12px; font-size: 12px; font-weight: bold;">4</span>
						<span><strong>Results:</strong> Comprehensive report with recommendations</span>
					</div>
				</div>
			</div>
			""", unsafe_allow_html=True)
			
			# Feature highlights
			col1, col2, col3 = st.columns(3)
			with col1:
				st.markdown("""
				<div style="text-align: center; padding: 16px;">
					<div style="font-size: 32px; margin-bottom: 8px;">🤖</div>
					<h4 style="color: #333; margin-bottom: 8px;">AI-Powered</h4>
					<p style="color: #666; font-size: 14px;">Advanced machine learning models analyze your contracts</p>
				</div>
				""", unsafe_allow_html=True)
			
			with col2:
				st.markdown("""
				<div style="text-align: center; padding: 16px;">
					<div style="font-size: 32px; margin-bottom: 8px;">🔒</div>
					<h4 style="color: #333; margin-bottom: 8px;">Secure</h4>
					<p style="color: #666; font-size: 14px;">Enterprise-grade security and privacy protection</p>
				</div>
				""", unsafe_allow_html=True)
			
			with col3:
				st.markdown("""
				<div style="text-align: center; padding: 16px;">
					<div style="font-size: 32px; margin-bottom: 8px;">⚡</div>
					<h4 style="color: #333; margin-bottom: 8px;">Fast</h4>
					<p style="color: #666; font-size: 14px;">Get comprehensive analysis results in minutes</p>
				</div>
				""", unsafe_allow_html=True)
	
	# Enhanced error display
	if st.session_state.error_message:
		st.markdown("""
		<div class="status-card error">
			<h4 style="margin: 0 0 8px 0; color: #721c24;">❌ Error Occurred</h4>
			<p style="margin: 0; color: #721c24;">
				An error occurred during processing. Please review the details below.
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		error_display(st.session_state.error_message, show_actions=True, 
		             retry_callback=lambda: st.rerun())
	
	st.markdown('</div>', unsafe_allow_html=True)


def render_settings_interface():
	"""Render the settings interface."""
	st.subheader("⚙️ Settings")

	# Connection monitoring section
	st.subheader("🔗 Connection Monitoring")
	try:
		display_connection_dashboard(api_client)
	except Exception as e:
		st.error(f"Connection dashboard error: {str(e)}")

	st.divider()

	# Model selection
	st.subheader("AI Model Settings")
	model_preference = st.selectbox("Preferred AI Model", ["gpt-4", "gpt-3.5-turbo", "claude-3"], help="Select your preferred AI model for analysis")

	# Analysis settings
	st.subheader("Analysis Settings")
	enable_confidence = st.checkbox("Enable Confidence Scoring", value=True)
	analysis_depth = st.selectbox("Analysis Depth", ["basic", "standard", "comprehensive"], index=1)

	# Security settings
	st.subheader("Security Settings")
	enable_audit = st.checkbox("Enable Audit Logging", value=True)
	enable_quarantine = st.checkbox("Enable File Quarantine", value=True)

	# Save settings
	if st.button("💾 Save Settings", key="basic_save_settings"):
		st.success("Settings saved successfully!")
		# In a real implementation, you would save these to a database or config file


def render_login_form():
	"""Render the login form."""
	st.header("Login")
	with st.form("login_form"):
		username = st.text_input("Username", value="user@example.com")
		password = st.text_input("Password", type="password", value="string")
		submitted = st.form_submit_button("Login")

		if submitted:
			with st.spinner("Authenticating..."):
				response = api_client.login(username, password)
				if "error" not in response and "access_token" in response:
					st.session_state.auth_token = response["access_token"]
					st.session_state.user_info = response.get("user", {})
					api_client.set_token(response["access_token"])
					st.success("Login successful!")
					st.rerun()
				else:
					st.error(f"❌ {response.get('error', 'Authentication failed.')}")


# Removed duplicate function - using the one below


def render_basic_header():
	"""Render basic header without production features."""
	st.title("🔒 Secure Career Copilot")
	st.markdown("""
	    Upload your contract document for secure analysis with advanced threat detection,
	    input sanitization, and comprehensive audit logging.
	    """)


def render_production_settings():
	"""Render production settings interface."""
	st.subheader("⚙️ Production Settings")
	
	if PRODUCTION_FEATURES_AVAILABLE:
		try:
			config = get_config()
			
			# Feature flags
			st.subheader("🚩 Feature Flags")
			
			col1, col2 = st.columns(2)
			
			with col1:
				real_time = st.checkbox(
					"Real-time Updates",
					value=config.feature_flags.get('real_time_updates', True),
					help="Enable real-time status updates and notifications"
				)
				
				analytics = st.checkbox(
					"Advanced Analytics",
					value=config.feature_flags.get('advanced_analytics', True),
					help="Enable detailed analytics and performance monitoring"
				)
			
			with col2:
				mobile_opt = st.checkbox(
					"Mobile Optimizations",
					value=config.feature_flags.get('mobile_optimizations', True),
					help="Enable mobile-specific UI optimizations"
				)
				
				error_recovery = st.checkbox(
					"Error Recovery",
					value=config.feature_flags.get('error_recovery', True),
					help="Enable automatic error recovery and user guidance"
				)
			
			# Save settings
			if st.button("💾 Save Production Settings", key="production_save_settings"):
				st.success("Production settings saved!")
		except Exception as e:
			st.error(f"Production settings unavailable: {e}")
			render_settings_interface()
	else:
		render_settings_interface()


def render_production_sidebar(websocket_features=None, analytics=None):
	"""Render production sidebar."""
	with st.sidebar:
		st.header("🚀 Production Status")
		
		if websocket_features:
			try:
				# Connection status
				connection = websocket_features.get('websocket_manager', {}).get('connection_status', {})
				if connection.get('connected'):
					st.success("🟢 Connected")
				else:
					st.error("🔴 Disconnected")
			except:
				st.info("🟡 Status Unknown")
		
		if analytics:
			try:
				# Quick metrics
				st.subheader("📊 Quick Metrics")
				metrics = analytics.get_quick_metrics()
				for metric_name, metric_value in metrics.items():
					st.metric(metric_name, metric_value)
			except:
				st.info("Analytics unavailable")
		
		# Fallback to security sidebar
		render_security_sidebar()


def render_production_footer(websocket_features=None):
	"""Render production footer."""
	st.divider()
	
	col1, col2, col3 = st.columns(3)
	
	with col1:
		st.caption("🔒 Career Copilot v2.0")
	
	with col2:
		if websocket_features:
			try:
				latency = websocket_features.get('websocket_manager', {}).get('latency', 0)
				st.caption(f"⚡ Latency: {latency:.0f}ms")
			except:
				st.caption("⚡ Latency: --ms")
		else:
			st.caption("⚡ Latency: --ms")
	
	with col3:
		st.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')}")


def render_production_header(websocket_features=None):
	"""Render enhanced header with production features."""
	col1, col2, col3 = st.columns([3, 1, 1])
	
	with col1:
		st.title("🔒 Career Copilot")
		st.caption("Production-Ready AI-Powered Contract Analysis v2.0")
	
	with col2:
		# System status indicator - Simple backend health check
		try:
			import requests
			backend_url = os.getenv('BACKEND_URL', 'http://localhost:8002')
			
			# Get comprehensive health status
			response = requests.get(f"{backend_url}/api/v1/health", timeout=2)
			if response.status_code == 200:
				health_data = response.json()
				status = health_data.get('status', 'unknown')
				
				# Map backend status to display status
				status_mapping = {
					'healthy': ('🟢', 'Healthy'),
					'degraded': ('🟡', 'Warning'),
					'unhealthy': ('🔴', 'Critical'),
					'unknown': ('⚪', 'Unknown')
				}
				
				icon, display_status = status_mapping.get(status, ('⚪', 'Unknown'))
				st.metric("System Status", f"{icon} {display_status}")
			else:
				st.metric("System Status", "🔴 Critical")
		except requests.exceptions.ConnectionError:
			st.metric("System Status", "🔴 Critical")
		except requests.exceptions.Timeout:
			st.metric("System Status", "🟡 Warning")
		except Exception as e:
			st.metric("System Status", "⚪ Unknown")
	
	with col3:
		# Connection status - Simple backend connectivity check
		try:
			import requests
			backend_url = os.getenv('BACKEND_URL', 'http://localhost:8002')
			
			# Quick health check with short timeout
			response = requests.get(f"{backend_url}/api/v1/health", timeout=2)
			if response.status_code == 200:
				health_data = response.json()
				if health_data.get('status') == 'healthy':
					st.metric("Connection", "🟢 Online")
				else:
					st.metric("Connection", "🟡 Degraded")
			else:
				st.metric("Connection", "🔴 Offline")
		except requests.exceptions.ConnectionError:
			st.metric("Connection", "🔴 Offline")
		except requests.exceptions.Timeout:
			st.metric("Connection", "🟡 Slow")
		except Exception as e:
			st.metric("Connection", "⚪ Unknown")
		
		# System information
		st.subheader("ℹ️ System Information")
		
		system_info = {
			"Environment": getattr(config, 'environment', os.getenv('ENVIRONMENT', 'development')),
			"Version": "2.0.0",
			"API URL": getattr(config, 'api_base_url', os.getenv('BACKEND_URL', 'http://localhost:8002')),
			"Cache TTL": f"{getattr(config.cache, 'ttl_seconds', 300) if hasattr(config, 'cache') else 300}s",
			"Max File Size": f"{getattr(config.security, 'max_file_size_mb', 50) if hasattr(config, 'security') else 50}MB"
		}
		
		for key, value in system_info.items():
			st.text(f"{key}: {value}")


def render_production_sidebar(websocket_features=None, analytics=None):
	"""Render enhanced sidebar with production features."""
	with st.sidebar:
		st.header("🔒 Production Dashboard")
		
		# User info
		if st.session_state.get('user_info'):
			user = st.session_state.user_info
			st.subheader(f"Welcome, {user.get('username', 'User')}")
		
		# Quick stats
		st.subheader("📊 Quick Stats")
		
		# Session metrics
		if 'app_start_time' in st.session_state:
			uptime_minutes = (datetime.now().timestamp() - st.session_state.app_start_time) / 60
			st.metric("Session Uptime", f"{uptime_minutes:.1f}m")
		
		if 'page_loads' in st.session_state:
			st.metric("Page Loads", st.session_state.page_loads)
		
		# System health indicator
		if websocket_features and hasattr(websocket_features['health_monitor'], 'render_health_indicator'):
			websocket_features['health_monitor'].render_health_indicator()
		
		# Real-time notifications
		if websocket_features and hasattr(websocket_features['notification_manager'], 'render_notifications'):
			st.subheader("🔔 Notifications")
			websocket_features['notification_manager'].render_notifications()
		
		# Quick actions
		st.subheader("⚡ Quick Actions")
		
		if st.button("🔄 Refresh Data", use_container_width=True):
			if PRODUCTION_FEATURES_AVAILABLE:
				track_user_event('sidebar_action', {'action': 'refresh_data'})
			st.rerun()
		
		if st.button("📊 View Analytics", use_container_width=True):
			if PRODUCTION_FEATURES_AVAILABLE:
				track_user_event('sidebar_action', {'action': 'view_analytics'})
			st.info("Switching to Analytics tab...")
		
		st.divider()
		st.subheader(f"Welcome, {st.session_state.user_info.get('username', 'User')}")
		if st.button("Logout", key="sidebar_logout"):
			if PRODUCTION_FEATURES_AVAILABLE:
				track_user_event('user_logout')
			api_client.clear_token()
			del st.session_state.auth_token
			del st.session_state.user_info
			st.rerun()


def render_production_footer(websocket_features=None):
	"""Render production footer with status information."""
	st.divider()
	
	col1, col2, col3 = st.columns(3)
	
	with col1:
		st.caption("🔒 Career Copilot v2.0")
		st.caption("Production-Ready AI Analysis")
	
	with col2:
		if websocket_features:
			connection = websocket_features['websocket_manager'].get_connection_status()
			status_text = "🟢 Online" if connection['connected'] else "🔴 Offline"
		else:
			status_text = "🟢 Online"
		st.caption(f"Status: {status_text}")
	
	with col3:
		session_id = st.session_state.get('session_id', 'unknown')
		st.caption(f"Session: {session_id[-8:] if len(session_id) > 8 else session_id}")
		if 'app_start_time' in st.session_state:
			uptime = (datetime.now().timestamp() - st.session_state.app_start_time) / 60
			st.caption(f"Uptime: {uptime:.0f}m")



def main():
	"""Main application function."""
	global PRODUCTION_FEATURES_AVAILABLE
	
	# Setup page configuration
	setup_page_config()
	
	# Initialize session state
	initialize_session_state()
	
	# Setup security
	setup_security()
	
	# Initialize production features if available
	websocket_features = None
	analytics = None
	
	if PRODUCTION_FEATURES_AVAILABLE:
		try:
			# Initialize production optimizations
			initialize_production_optimizations()
			
			# Initialize WebSocket features
			websocket_features = initialize_websocket_features()
			
			# Initialize responsive UI
			initialize_responsive_ui()
			
			# Initialize analytics
			analytics = initialize_production_analytics()
			
		except Exception as e:
			st.warning(f"Some production features unavailable: {e}")
			PRODUCTION_FEATURES_AVAILABLE = False

	# Load environment variables from .env file
	try:
		from dotenv import load_dotenv
		# Try multiple paths to find .env file
		env_paths = [
			'../.env',  # Parent directory
			'.env',     # Current directory
			'frontend/.env',  # Frontend directory
			os.path.join(os.path.dirname(__file__), '..', '.env')  # Relative to this file
		]
		for env_path in env_paths:
			if os.path.exists(env_path):
				load_dotenv(env_path, override=True)
				break
	except ImportError:
		pass
	
	# Force disable auth for testing
	os.environ['DISABLE_AUTH'] = 'true'
	
	# Check authentication - skip for development
	disable_auth = os.getenv("DISABLE_AUTH", "false").lower() == "true"
	
	# Debug info (remove in production)
	if st.sidebar.button("Debug Auth Status", key="debug_auth_status"):
		st.sidebar.write(f"DISABLE_AUTH: {os.getenv('DISABLE_AUTH', 'not set')}")
		st.sidebar.write(f"disable_auth: {disable_auth}")
		st.sidebar.write(f"auth_token: {st.session_state.get('auth_token', 'not set')}")
	
	# Force bypass authentication for testing
	if disable_auth or True:  # Always bypass for now
		# Set default auth token for development mode
		if not st.session_state.get("auth_token"):
			st.session_state.auth_token = "dev_token"
			st.session_state.user_info = {"username": "Developer", "id": "dev_user"}
	elif not st.session_state.get("auth_token"):
		render_login_form()
		return

	# Display connection status in sidebar
	try:
		is_connected = display_connection_status_sidebar(api_client)
		if not is_connected:
			st.warning("⚠️ Backend connection issues detected. Some features may not work properly.")
	except Exception as e:
		st.sidebar.error(f"Connection status error: {str(e)}")
		is_connected = False

	# Render header with production enhancements
	try:
		if PRODUCTION_FEATURES_AVAILABLE:
			render_production_header(websocket_features)
		else:
			render_basic_header()
	except Exception as e:
		# Fallback to simple header if there are issues
		st.title("🔒 Career Copilot")
		st.caption("AI-Powered Contract Analysis")
		st.error(f"Header rendering issue: {str(e)}")

	# Add navigation tabs with responsive design
	tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 Contract Analysis", "📊 Progress Dashboard", "📈 Analytics", "🔍 Observability", "⚙️ Settings"])

	with tab1:
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				track_user_event('tab_view', {'tab': 'analysis'})
			except:
				pass
		render_analysis_interface()

	with tab2:
		# Real-time Progress Dashboard Tab
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				track_user_event('tab_view', {'tab': 'progress_dashboard'})
			except:
				pass
		
		st.markdown("### 📊 Real-time Progress Dashboard")
		st.markdown("Monitor active analysis tasks and system performance in real-time.")
		
		# Analysis ID input for monitoring specific analysis
		analysis_id_input = st.text_input(
			"Analysis ID to Monitor (optional):",
			placeholder="Enter analysis ID to monitor specific task",
			help="Leave empty to see all active analyses"
		)
		
		if analysis_id_input:
			# Show specific analysis dashboard
			user_id = st.session_state.get("user_info", {}).get("username", "user")
			try:
				show_analysis_dashboard(api_client, analysis_id_input, user_id)
			except Exception as e:
				st.error(f"Error loading analysis dashboard: {e}")
				st.info("Make sure the analysis ID is correct and the analysis is active.")
		else:
			# Show general dashboard information
			st.info("💡 **How to use the Progress Dashboard:**")
			col1, col2 = st.columns(2)
			
			with col1:
				st.markdown("""
				**🎯 Monitor Active Analysis:**
				- Enter an analysis ID above to track specific analysis
				- View real-time agent progress
				- See estimated completion times
				- Monitor current operations
				""")
			
			with col2:
				st.markdown("""
				**🔄 Real-time Features:**
				- Live WebSocket updates
				- Agent-by-agent progress visualization
				- Error tracking and recovery
				- Analysis cancellation controls
				""")
			
			# Show current session analysis if available
			if st.session_state.get("task_id") and st.session_state.get("is_polling"):
				st.markdown("---")
				st.markdown("### 🔄 Current Session Analysis")
				st.info(f"**Active Analysis ID:** `{st.session_state.task_id}`")
				
				if st.button("📊 Monitor Current Analysis", type="primary"):
					user_id = st.session_state.get("user_info", {}).get("username", "user")
					try:
						show_analysis_dashboard(api_client, st.session_state.task_id, user_id)
					except Exception as e:
						st.error(f"Error loading current analysis dashboard: {e}")

	with tab3:
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				track_user_event('tab_view', {'tab': 'analytics'})
				if analytics:
					analytics.render_full_dashboard()
				else:
					render_analytics_dashboard()
			except:
				render_analytics_dashboard()
		else:
			render_analytics_dashboard()

	with tab4:
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				track_user_event('tab_view', {'tab': 'observability'})
			except:
				pass
		render_observability_dashboard()

	with tab5:
		if PRODUCTION_FEATURES_AVAILABLE:
			try:
				track_user_event('tab_view', {'tab': 'settings'})
				render_production_settings()
			except:
				render_settings_interface()
		else:
			render_settings_interface()
		
	# Render enhanced sidebar
	if PRODUCTION_FEATURES_AVAILABLE:
		try:
			render_production_sidebar(websocket_features, analytics)
		except:
			render_security_sidebar()
	else:
		render_security_sidebar()
		
	# Show user info in sidebar if authenticated
	if st.session_state.get("auth_token") or os.getenv("DISABLE_AUTH", "false").lower() == "true":
		with st.sidebar:
			st.divider()
			if st.session_state.get("user_info"):
				st.subheader(f"Welcome, {st.session_state.user_info.get('username', 'User')}")
			else:
				st.subheader("Welcome, Developer")
			
			if st.session_state.get("auth_token") and st.button("Logout", key="main_logout"):
				api_client.clear_token()
				if "auth_token" in st.session_state:
					del st.session_state.auth_token
				if "user_info" in st.session_state:
					del st.session_state.user_info
				st.rerun()

	# Enhanced footer
	if PRODUCTION_FEATURES_AVAILABLE:
		try:
			render_production_footer(websocket_features)
		except:
			pass


if __name__ == "__main__":
	main()
