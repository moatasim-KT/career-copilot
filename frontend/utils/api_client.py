"""Enhanced API Client for Backend Communication with comprehensive error handling and retry logic"""
import requests
import json
import time
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import streamlit as st
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base API error class"""
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None, 
                 suggestions: Optional[List[str]] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.suggestions = suggestions or []
        self.retry_after = retry_after

class ConnectionError(APIError):
    """Connection-related errors"""
    pass

class TimeoutError(APIError):
    """Request timeout errors"""
    pass

class AuthenticationError(APIError):
    """Authentication-related errors"""
    pass

class ValidationError(APIError):
    """Request validation errors"""
    pass

class ServerError(APIError):
    """Server-side errors"""
    pass

class RateLimitError(APIError):
    """Rate limiting errors"""
    pass

class RetryStrategy(Enum):
    """Retry strategy options"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    backoff_multiplier: float = 2.0
    jitter: bool = True

@dataclass
class RequestConfig:
    """Configuration for individual requests"""
    timeout: float = 30.0
    retry_config: Optional[RetryConfig] = None
    correlation_id: Optional[str] = None
    require_auth: bool = True

class TokenManager:
    """Manages authentication tokens with automatic refresh"""
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.refresh_callback: Optional[Callable] = None
        
    def set_tokens(self, access_token: str, refresh_token: Optional[str] = None, expires_in: int = 3600):
        """Set authentication tokens"""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 1 minute early
        
    def clear_tokens(self):
        """Clear all tokens"""
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
    def is_token_expired(self) -> bool:
        """Check if token is expired or about to expire"""
        if not self.access_token or not self.token_expires_at:
            return True
        return datetime.now() >= self.token_expires_at
        
    def get_auth_header(self) -> Optional[str]:
        """Get authorization header value"""
        if self.access_token and not self.is_token_expired():
            return f"Bearer {self.access_token}"
        return None

class APIClient:
    """Enhanced client for communicating with the backend API with comprehensive error handling."""
    
    def __init__(self, base_url: str, default_retry_config: Optional[RetryConfig] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token_manager = TokenManager()
        self.default_retry_config = default_retry_config or RetryConfig()
        
        # Request tracking
        self.request_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        
        # Circuit breaker state
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = None
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 60  # seconds
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ContractAnalyzer-Frontend/2.0',
            'Accept': 'application/json'
        })
        
        logger.info(f"API Client initialized for {self.base_url}")
    
    def set_token(self, token: str, refresh_token: Optional[str] = None, expires_in: int = 3600):
        """Set authentication token with automatic refresh support."""
        self.token_manager.set_tokens(token, refresh_token, expires_in)
        self._update_auth_header()
        logger.info("Authentication token set successfully")
    
    def clear_token(self):
        """Clear authentication token."""
        self.token_manager.clear_tokens()
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        logger.info("Authentication token cleared")
    
    def _update_auth_header(self):
        """Update authorization header with current token"""
        auth_header = self.token_manager.get_auth_header()
        if auth_header:
            self.session.headers['Authorization'] = auth_header
        elif 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.circuit_breaker_failures < self.circuit_breaker_threshold:
            return False
            
        if self.circuit_breaker_last_failure:
            time_since_failure = (datetime.now() - self.circuit_breaker_last_failure).total_seconds()
            if time_since_failure > self.circuit_breaker_timeout:
                # Reset circuit breaker
                self.circuit_breaker_failures = 0
                self.circuit_breaker_last_failure = None
                return False
                
        return True
    
    def _record_failure(self):
        """Record a failure for circuit breaker"""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = datetime.now()
        
    def _record_success(self):
        """Record a success for circuit breaker"""
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = None
    
    def _calculate_delay(self, attempt: int, retry_config: RetryConfig) -> float:
        """Calculate delay for retry attempt"""
        if retry_config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = retry_config.base_delay * (retry_config.backoff_multiplier ** (attempt - 1))
        elif retry_config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = retry_config.base_delay * attempt
        else:  # FIXED_DELAY
            delay = retry_config.base_delay
            
        # Apply jitter if enabled
        if retry_config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
            
        return min(delay, retry_config.max_delay)
    
    def _should_retry(self, response: Optional[requests.Response], exception: Optional[Exception]) -> bool:
        """Determine if request should be retried"""
        if exception:
            # Retry on connection errors, timeouts, and server errors
            if isinstance(exception, requests.exceptions.ConnectionError):
                logger.warning("Connection error detected - will retry")
                return True
            elif isinstance(exception, requests.exceptions.Timeout):
                logger.warning("Timeout error detected - will retry")
                return True
            elif isinstance(exception, requests.exceptions.HTTPError):
                # Only retry on server errors
                if hasattr(exception, 'response') and exception.response:
                    return exception.response.status_code >= 500
                return True
            elif isinstance(exception, requests.exceptions.RequestException):
                logger.warning("Request exception detected - will retry")
                return True
            
        if response:
            # Retry on server errors (5xx) and some client errors
            if response.status_code >= 500:
                logger.warning(f"Server error {response.status_code} - will retry")
                return True
            elif response.status_code in [408, 429, 502, 503, 504]:
                logger.warning(f"Retryable client error {response.status_code} - will retry")
                return True
            
        return False
    
    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID for request tracking"""
        return str(uuid.uuid4())
    
    def _log_request(self, method: str, url: str, correlation_id: str, 
                    response_status: Optional[int] = None, error: Optional[str] = None,
                    duration: Optional[float] = None):
        """Log request details for debugging"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'url': url,
            'correlation_id': correlation_id,
            'response_status': response_status,
            'error': error,
            'duration_ms': int(duration * 1000) if duration else None
        }
        
        # Add to history
        self.request_history.append(log_entry)
        if len(self.request_history) > self.max_history_size:
            self.request_history.pop(0)
            
        # Log to console
        if error:
            logger.error(f"Request failed [{correlation_id}]: {method} {url} - {error}")
        else:
            logger.info(f"Request completed [{correlation_id}]: {method} {url} - {response_status} ({duration:.2f}s)")
    
    async def _refresh_token_if_needed(self) -> bool:
        """Refresh token if needed and possible"""
        if not self.token_manager.is_token_expired():
            return True
            
        if not self.token_manager.refresh_token:
            logger.warning("Token expired and no refresh token available")
            return False
            
        try:
            # Attempt to refresh token
            refresh_response = await self._make_request_internal(
                'POST', '/api/v1/auth/refresh',
                json={'refresh_token': self.token_manager.refresh_token},
                config=RequestConfig(require_auth=False)
            )
            
            if 'error' not in refresh_response and 'access_token' in refresh_response:
                self.set_token(
                    refresh_response['access_token'],
                    refresh_response.get('refresh_token'),
                    refresh_response.get('expires_in', 3600)
                )
                logger.info("Token refreshed successfully")
                return True
            else:
                logger.error(f"Token refresh failed: {refresh_response.get('error', 'Unknown error')}")
                self.clear_token()
                return False
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            self.clear_token()
            return False
    
    async def _make_request_internal(self, method: str, endpoint: str, 
                                   config: Optional[RequestConfig] = None, **kwargs) -> Dict[str, Any]:
        """Internal method to make HTTP request with comprehensive error handling and retry logic."""
        config = config or RequestConfig()
        retry_config = config.retry_config or self.default_retry_config
        correlation_id = config.correlation_id or self._generate_correlation_id()
        
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            error_msg = "Circuit breaker is open - service appears to be down"
            self._log_request(method, endpoint, correlation_id, error=error_msg)
            return {'error': error_msg, 'correlation_id': correlation_id}
        
        # Refresh token if needed
        if config.require_auth:
            token_valid = await self._refresh_token_if_needed()
            if not token_valid:
                return {'error': 'Authentication required - please login', 'correlation_id': correlation_id}
        
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        # Add correlation ID to headers
        headers = kwargs.get('headers', {})
        headers['X-Correlation-ID'] = correlation_id
        kwargs['headers'] = headers
        
        last_exception = None
        last_response = None
        
        for attempt in range(1, retry_config.max_attempts + 1):
            start_time = time.time()
            
            try:
                # Update auth header before each request
                if config.require_auth:
                    self._update_auth_header()
                
                response = self.session.request(
                    method, url, 
                    timeout=config.timeout, 
                    **kwargs
                )
                
                duration = time.time() - start_time
                last_response = response
                
                # Handle successful responses
                if response.status_code < 400:
                    self._record_success()
                    
                    # Parse response
                    if response.headers.get('content-type', '').startswith('application/json'):
                        try:
                            result = response.json()
                            result['correlation_id'] = correlation_id
                            self._log_request(method, url, correlation_id, response.status_code, duration=duration)
                            return result
                        except json.JSONDecodeError:
                            error_msg = 'Invalid JSON response from server'
                            self._log_request(method, url, correlation_id, response.status_code, error_msg, duration)
                            return {'error': error_msg, 'correlation_id': correlation_id}
                    else:
                        # Non-JSON response
                        result = {
                            'data': response.text,
                            'status_code': response.status_code,
                            'correlation_id': correlation_id
                        }
                        self._log_request(method, url, correlation_id, response.status_code, duration=duration)
                        return result
                
                # Handle client/server errors
                error_msg = f"HTTP {response.status_code}: {response.reason}"
                
                # Try to get error details from response
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_data = response.json()
                        if 'detail' in error_data:
                            error_msg = error_data['detail']
                        elif 'message' in error_data:
                            error_msg = error_data['message']
                        elif 'error' in error_data:
                            error_msg = error_data['error']
                except:
                    pass
                
                # Handle authentication errors
                if response.status_code == 401:
                    self.clear_token()
                    error_msg = "Authentication failed - please login again"
                    self._log_request(method, url, correlation_id, response.status_code, error_msg, duration)
                    return {'error': error_msg, 'correlation_id': correlation_id, 'requires_login': True}
                
                # Check if we should retry
                if not self._should_retry(response, None) or attempt == retry_config.max_attempts:
                    self._record_failure()
                    self._log_request(method, url, correlation_id, response.status_code, error_msg, duration)
                    return {'error': error_msg, 'correlation_id': correlation_id}
                
                # Log retry attempt
                logger.warning(f"Request failed [{correlation_id}], attempt {attempt}/{retry_config.max_attempts}: {error_msg}")
                
            except Exception as e:
                duration = time.time() - start_time
                last_exception = e
                
                error_details = self._format_exception_message(e)
                
                # Check if we should retry
                if not self._should_retry(None, e) or attempt == retry_config.max_attempts:
                    self._record_failure()
                    self._log_request(method, url, correlation_id, error=error_details.get('message', str(e)), duration=duration)
                    
                    # Return structured error response
                    result = {
                        'correlation_id': correlation_id,
                        **error_details
                    }
                    return result
                
                # Log retry attempt
                logger.warning(f"Request failed [{correlation_id}], attempt {attempt}/{retry_config.max_attempts}: {error_details.get('message', str(e))}")
            
            # Wait before retry (except on last attempt)
            if attempt < retry_config.max_attempts:
                delay = self._calculate_delay(attempt, retry_config)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
        
        # All attempts failed
        self._record_failure()
        
        if last_exception:
            error_details = self._format_exception_message(last_exception)
        elif last_response:
            error_details = {
                'error': 'Request Failed',
                'message': f"HTTP {last_response.status_code}: {last_response.reason}",
                'suggestions': [
                    'Check your request and try again',
                    'Contact support if the problem persists'
                ],
                'category': 'http_error'
            }
        else:
            error_details = {
                'error': 'Request Failed',
                'message': 'All retry attempts failed',
                'suggestions': [
                    'Check your internet connection',
                    'Try again later',
                    'Contact support if the problem persists'
                ],
                'category': 'retry_exhausted'
            }
            
        result = {
            'correlation_id': correlation_id,
            **error_details
        }
        return result
    
    def _format_exception_message(self, exception: Exception) -> str:
        """Format exception message for user display with detailed error information"""
        if isinstance(exception, requests.exceptions.ConnectionError):
            return {
                'error': 'Connection Error',
                'message': 'Unable to connect to the backend service',
                'suggestions': [
                    'Check if the backend service is running',
                    'Verify your internet connection',
                    'Try refreshing the page'
                ],
                'category': 'connection'
            }
        elif isinstance(exception, requests.exceptions.Timeout):
            return {
                'error': 'Request Timeout',
                'message': 'The server is taking too long to respond',
                'suggestions': [
                    'Try again in a moment',
                    'Check your internet connection',
                    'The server may be experiencing high load'
                ],
                'category': 'timeout'
            }
        elif isinstance(exception, requests.exceptions.HTTPError):
            status_code = getattr(exception.response, 'status_code', None) if hasattr(exception, 'response') else None
            if status_code == 401:
                return {
                    'error': 'Authentication Error',
                    'message': 'Your session has expired or credentials are invalid',
                    'suggestions': [
                        'Please log in again',
                        'Check your username and password'
                    ],
                    'category': 'authentication',
                    'requires_login': True
                }
            elif status_code == 403:
                return {
                    'error': 'Access Denied',
                    'message': 'You do not have permission to perform this action',
                    'suggestions': [
                        'Contact your administrator for access',
                        'Verify your account permissions'
                    ],
                    'category': 'authorization'
                }
            elif status_code == 429:
                return {
                    'error': 'Rate Limit Exceeded',
                    'message': 'Too many requests. Please wait before trying again',
                    'suggestions': [
                        'Wait a moment before retrying',
                        'Reduce the frequency of your requests'
                    ],
                    'category': 'rate_limit',
                    'retry_after': 60
                }
            elif status_code and status_code >= 500:
                return {
                    'error': 'Server Error',
                    'message': 'The server encountered an internal error',
                    'suggestions': [
                        'Try again in a few moments',
                        'Contact support if the problem persists'
                    ],
                    'category': 'server_error'
                }
            else:
                return {
                    'error': 'HTTP Error',
                    'message': f'Request failed with status {status_code}',
                    'suggestions': [
                        'Check your request and try again',
                        'Contact support if the problem persists'
                    ],
                    'category': 'http_error'
                }
        elif isinstance(exception, requests.exceptions.RequestException):
            return {
                'error': 'Request Error',
                'message': 'Failed to complete the request',
                'suggestions': [
                    'Check your internet connection',
                    'Try again in a moment',
                    'Contact support if the problem persists'
                ],
                'category': 'request_error'
            }
        elif isinstance(exception, json.JSONDecodeError):
            return {
                'error': 'Invalid Response',
                'message': 'Received invalid data from the server',
                'suggestions': [
                    'Try refreshing the page',
                    'Contact support if the problem persists'
                ],
                'category': 'json_error'
            }
        else:
            return {
                'error': 'Unexpected Error',
                'message': f'An unexpected error occurred: {str(exception)}',
                'suggestions': [
                    'Try refreshing the page',
                    'Contact support with the error details'
                ],
                'category': 'unexpected_error'
            }
    
    def _make_request(self, method: str, endpoint: str, config: Optional[RequestConfig] = None, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for _make_request_internal"""
        try:
            # Run async method in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._make_request_internal(method, endpoint, config, **kwargs))
            finally:
                loop.close()
        except Exception as e:
            correlation_id = config.correlation_id if config else self._generate_correlation_id()
            error_msg = f"Request execution failed: {str(e)}"
            self._log_request(method, endpoint, correlation_id, error=error_msg)
            return {'error': error_msg, 'correlation_id': correlation_id}
    
    def health_check(self) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('GET', get_endpoint('health'), RequestConfig(require_auth=False, timeout=10.0))
    
    def connection_test(self) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('GET', get_endpoint('connection_test'), RequestConfig(require_auth=False, timeout=5.0))
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status information."""
        try:
            # Test basic connectivity first
            connection_result = self.connection_test()
            if 'error' in connection_result:
                return {
                    'connected': False,
                    'status': 'offline',
                    'error': connection_result['error'],
                    'last_check': datetime.now().isoformat(),
                    'suggestions': connection_result.get('suggestions', [])
                }
            
            # Test health endpoint
            health_result = self.health_check()
            if 'error' in health_result:
                return {
                    'connected': True,
                    'status': 'degraded',
                    'error': health_result['error'],
                    'last_check': datetime.now().isoformat(),
                    'connection_info': connection_result
                }
            
            return {
                'connected': True,
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'connection_info': connection_result,
                'health_info': health_result
            }
            
        except Exception as e:
            return {
                'connected': False,
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat(),
                'suggestions': [
                    'Check if the backend service is running',
                    'Verify the backend URL configuration',
                    'Check your network connection'
                ]
            }
    
    def login(self, username: str, password: str, mfa_code: Optional[str] = None) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        data = {'username': username, 'password': password}
        if mfa_code:
            data['mfa_code'] = mfa_code
        
        result = self._make_request('POST', get_endpoint('login'), RequestConfig(require_auth=False, timeout=10.0), json=data)
        if 'error' not in result and 'access_token' in result:
            self.set_token(result['access_token'], result.get('refresh_token'), result.get('expires_in', 3600))
        return result
    
    def logout(self) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        result = self._make_request('POST', get_endpoint('logout'), RequestConfig(timeout=5.0))
        self.clear_token()
        return result
    
    def refresh_token(self) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        if not self.token_manager.refresh_token:
            return {'error': 'No refresh token available'}
        
        result = self._make_request('POST', get_endpoint('refresh_token'), RequestConfig(require_auth=False, timeout=10.0), json={'refresh_token': self.token_manager.refresh_token})
        if 'error' not in result and 'access_token' in result:
            self.set_token(result['access_token'], result.get('refresh_token'), result.get('expires_in', 3600))
        return result
    
    def analyze_contract_async(self, uploaded_file, analysis_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Start asynchronous job application tracking."""
        from ..api.endpoints_config import get_endpoint
        
        try:
            files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = analysis_options or {}
            
            config = RequestConfig(timeout=120.0, retry_config=RetryConfig(max_attempts=2, base_delay=2.0))
            original_content_type = self.session.headers.get('Content-Type')
            if 'Content-Type' in self.session.headers:
                del self.session.headers['Content-Type']
            
            try:
                correlation_id = self._generate_correlation_id()
                headers = {'X-Correlation-ID': correlation_id}
                
                if config.require_auth:
                    self._update_auth_header()
                    if 'Authorization' in self.session.headers:
                        headers['Authorization'] = self.session.headers['Authorization']
                
                url = urljoin(self.base_url, get_endpoint('analyze_contract'))
                start_time = time.time()
                response = self.session.post(url, files=files, data=data, headers=headers, timeout=config.timeout)
                duration = time.time() - start_time
                
                if original_content_type:
                    self.session.headers['Content-Type'] = original_content_type
                
                if response.status_code < 400:
                    self._record_success()
                    if response.headers.get('content-type', '').startswith('application/json'):
                        result = response.json()
                        result['correlation_id'] = correlation_id
                        self._log_request('POST', url, correlation_id, response.status_code, duration=duration)
                        return result
                    return {'error': f'Unexpected response format', 'correlation_id': correlation_id}
                else:
                    error_msg = f"HTTP {response.status_code}: {response.reason}"
                    try:
                        if response.headers.get('content-type', '').startswith('application/json'):
                            error_data = response.json()
                            error_msg = error_data.get('detail') or error_data.get('message') or error_msg
                    except:
                        pass
                    self._record_failure()
                    self._log_request('POST', url, correlation_id, response.status_code, error_msg, duration)
                    return {'error': error_msg, 'correlation_id': correlation_id}
            finally:
                if original_content_type:
                    self.session.headers['Content-Type'] = original_content_type
        except requests.exceptions.ConnectionError:
            return {'error': 'Connection failed. Please check if the backend service is running.'}
        except requests.exceptions.Timeout:
            return {'error': 'Upload timeout. The file might be too large or the server is busy.'}
        except Exception as e:
            return {'error': f'Upload failed: {str(e)}'}
    
    def get_analysis_status(self, task_id: str) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('GET', get_endpoint('analysis_status', task_id=task_id), RequestConfig(timeout=10.0))
    
    def get_analysis_results(self, task_id: str) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('GET', get_endpoint('analysis_result', task_id=task_id), RequestConfig(timeout=30.0))
    
    def get_analysis_history(self, limit: int = 10) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('GET', f"{get_endpoint('contracts_list')}?limit={limit}", RequestConfig(timeout=15.0))
    
    def delete_analysis(self, task_id: str) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('DELETE', get_endpoint('cancel_analysis', task_id=task_id), RequestConfig(timeout=10.0))
    
    def get_contract_redlines(self, contract_id: str) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('GET', get_endpoint('analysis_redlines', analysis_id=contract_id), RequestConfig(timeout=20.0))
    
    def accept_redline(self, contract_id: str, redline_id: str) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('POST', get_endpoint('accept_redline', analysis_id=contract_id, redline_id=redline_id), RequestConfig(timeout=10.0))
    
    def reject_redline(self, contract_id: str, redline_id: str) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('POST', get_endpoint('accept_redline', analysis_id=contract_id, redline_id=redline_id), RequestConfig(timeout=10.0), json={"action": "reject"})
    
    def generate_revised_contract(self, contract_id: str) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('POST', get_endpoint('generate_revised_contract', analysis_id=contract_id), RequestConfig(timeout=30.0))
    
    def get_user_profile(self) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('GET', get_endpoint('user_profile'), RequestConfig(timeout=10.0))
    
    def update_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('PUT', get_endpoint('user_profile'), RequestConfig(timeout=15.0), json=profile_data)
    
    def get_user_settings(self) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('GET', get_endpoint('user_settings'), RequestConfig(timeout=10.0))
    
    def update_user_settings(self, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        from ..api.endpoints_config import get_endpoint
        return self._make_request('PUT', get_endpoint('user_settings'), RequestConfig(timeout=15.0), json=settings_data)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        config = RequestConfig(timeout=10.0)
        return self._make_request('GET', '/api/v1/monitoring/services', config)
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """Get API usage metrics."""
        config = RequestConfig(timeout=10.0)
        return self._make_request('GET', '/api/v1/monitoring/alerts', config)
    
    def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email through the backend service."""
        config = RequestConfig(timeout=30.0)
        return self._make_request('POST', '/api/v1/email/send', config, json=email_data)
    
    def send_slack_message(self, slack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send Slack message through the backend service."""
        config = RequestConfig(timeout=20.0)
        return self._make_request('POST', '/api/v1/slack/send-notification', config, json=slack_data)
    
    def get_communication_history(self, contract_id: Optional[str] = None) -> Dict[str, Any]:
        """Get communication history."""
        # Note: Communications endpoint not implemented in backend yet
        return {
            "success": False,
            "error": "Communication history endpoint not yet implemented",
            "data": []
        }
    
    def get_request_history(self) -> List[Dict[str, Any]]:
        """Get recent request history for debugging."""
        return self.request_history.copy()
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get API client status information."""
        return {
            'base_url': self.base_url,
            'authenticated': self.token_manager.access_token is not None,
            'token_expired': self.token_manager.is_token_expired(),
            'circuit_breaker_failures': self.circuit_breaker_failures,
            'circuit_breaker_open': self._is_circuit_breaker_open(),
            'request_history_count': len(self.request_history)
        }

# Utility functions for Streamlit integration
def check_backend_connection(api_client: APIClient) -> bool:
    """Check if backend is accessible and display status."""
    health = api_client.health_check()
    
    if 'error' in health:
        st.error(f"❌ Backend connection failed: {health['error']}")
        st.info("💡 Make sure the backend service is running on http://localhost:8000")
        
        # Show additional debugging info
        with st.expander("🔍 Connection Details"):
            status = api_client.get_connection_status()
            st.json(status)
            
            if api_client.request_history:
                st.subheader("Recent Requests")
                for req in api_client.request_history[-3:]:
                    st.text(f"{req['timestamp']}: {req['method']} {req['url']} - {req.get('error', 'OK')}")
        
        return False
    else:
        st.success("✅ Backend connection successful")
        if 'correlation_id' in health:
            st.caption(f"Request ID: {health['correlation_id']}")
        return True

def handle_api_response(response: Dict[str, Any], success_message: str = None) -> bool:
    """Handle API response and display appropriate messages."""
    if 'error' in response:
        error_msg = response['error']
        st.error(f"❌ {error_msg}")
        
        # Show correlation ID for debugging
        if 'correlation_id' in response:
            st.caption(f"Request ID: {response['correlation_id']}")
        
        # Handle specific error types
        if response.get('requires_login'):
            st.warning("🔐 Please login to continue")
            return False
        
        # Show retry suggestion for transient errors
        if any(keyword in error_msg.lower() for keyword in ['connection', 'timeout', 'server']):
            st.info("💡 This appears to be a temporary issue. Please try again.")
        
        return False
    else:
        if success_message:
            st.success(f"✅ {success_message}")
        
        # Show correlation ID for successful requests too
        if 'correlation_id' in response:
            st.caption(f"Request ID: {response['correlation_id']}")
        
        return True

def poll_task_status(api_client: APIClient, task_id: str, max_attempts: int = 60) -> Optional[Dict[str, Any]]:
    """Poll task status until completion or timeout with enhanced error handling."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    correlation_ids = []
    
    for attempt in range(max_attempts):
        status_response = api_client.get_analysis_status(task_id)
        
        # Track correlation IDs for debugging
        if 'correlation_id' in status_response:
            correlation_ids.append(status_response['correlation_id'])
        
        if 'error' in status_response:
            error_msg = status_response['error']
            st.error(f"❌ Error checking status: {error_msg}")
            
            # Show debugging info
            with st.expander("🔍 Debugging Information"):
                st.text(f"Task ID: {task_id}")
                st.text(f"Attempt: {attempt + 1}/{max_attempts}")
                if correlation_ids:
                    st.text(f"Request IDs: {', '.join(correlation_ids[-3:])}")
            
            # For authentication errors, stop polling
            if status_response.get('requires_login'):
                progress_bar.empty()
                status_text.empty()
                return None
            
            # For other errors, continue polling (might be transient)
            if attempt < max_attempts - 1:
                status_text.text(f"⚠️ Error occurred, retrying... ({attempt + 1}/{max_attempts})")
                time.sleep(5)
                continue
            else:
                progress_bar.empty()
                status_text.empty()
                return None
        
        status = status_response.get('status', 'unknown')
        progress = status_response.get('progress', 0)
        
        progress_bar.progress(min(progress / 100.0, 1.0))
        status_text.text(f"Status: {status} ({progress}%)")
        
        if status == 'completed':
            progress_bar.empty()
            status_text.empty()
            
            # Get final results
            results = api_client.get_analysis_results(task_id)
            if 'error' not in results:
                st.success("✅ Analysis completed successfully!")
                return results
            else:
                st.error(f"❌ Error retrieving results: {results['error']}")
                return None
                
        elif status in ['failed', 'timeout', 'error']:
            error_detail = status_response.get('error', f'Analysis {status}')
            st.error(f"❌ {error_detail}")
            
            # Show debugging info for failed tasks
            with st.expander("🔍 Task Details"):
                st.json(status_response)
            
            progress_bar.empty()
            status_text.empty()
            return None
        
        # Wait before next poll
        time.sleep(5)
    
    # Timeout reached
    st.error("❌ Analysis timeout - task is taking too long")
    st.info("💡 The analysis may still be running. You can check back later.")
    
    with st.expander("🔍 Timeout Details"):
        st.text(f"Task ID: {task_id}")
        st.text(f"Max attempts: {max_attempts}")
        st.text(f"Total time: {max_attempts * 5} seconds")
        if correlation_ids:
            st.text(f"Request IDs: {', '.join(correlation_ids)}")
    
    progress_bar.empty()
    status_text.empty()
    return None

def create_api_client_with_config() -> APIClient:
    """Create API client with production-ready configuration."""
    retry_config = RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        backoff_multiplier=2.0,
        jitter=True
    )
    
    # Use localhost for browser access, backend for container-to-container communication
    backend_url = "http://localhost:8002"
    
    return APIClient(backend_url, retry_config)

def display_api_debug_info(api_client: APIClient):
    """Display API client debugging information."""
    st.subheader("🔍 API Client Debug Info")
    
    status = api_client.get_connection_status()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Backend URL", status['base_url'])
        st.metric("Authenticated", "✅" if status['authenticated'] else "❌")
        st.metric("Token Status", "Valid" if not status['token_expired'] else "Expired")
    
    with col2:
        st.metric("Circuit Breaker", "Open" if status['circuit_breaker_open'] else "Closed")
        st.metric("Failures", status['circuit_breaker_failures'])
        st.metric("Request History", status['request_history_count'])
    
    # Show recent requests
    if api_client.request_history:
        st.subheader("Recent Requests")
        history_df = []
        for req in api_client.request_history[-10:]:
            history_df.append({
                'Time': req['timestamp'][-8:],  # Show only time part
                'Method': req['method'],
                'URL': req['url'].split('/')[-1] if '/' in req['url'] else req['url'],
                'Status': req.get('response_status', 'Error'),
                'Duration': f"{req.get('duration_ms', 0)}ms",
                'Error': req.get('error', '')[:50] if req.get('error') else ''
            })
        
        if history_df:
            import pandas as pd
            st.dataframe(pd.DataFrame(history_df), use_container_width=True)