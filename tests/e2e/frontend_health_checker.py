"""
Frontend application health checker for E2E testing.

This module provides health checking functionality for the Next.js frontend application,
including HTTP accessibility verification, page rendering checks, and JavaScript error detection.
"""

import asyncio
import json
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from .base import ServiceHealthTestBase


class FrontendHealthResult(BaseModel):
    """Frontend health check result model."""
    
    service: str
    healthy: bool
    response_time_ms: float
    status_code: Optional[int] = None
    message: str = ""
    details: Dict[str, Any] = {}
    error: Optional[str] = None
    timestamp: datetime = datetime.now()


class FrontendHealthChecker:
    """
    Health checker for Next.js frontend application.
    
    This class provides methods to check the health of the frontend application
    by verifying HTTP accessibility, page rendering, and JavaScript functionality.
    """
    
    def __init__(self, base_url: str = "http://localhost:3000", timeout: float = 30.0):
        """
        Initialize the frontend health checker.
        
        Args:
            base_url: Base URL of the Next.js frontend application
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.startup_timeout = 60.0  # Maximum time to wait for frontend startup
        
    async def check_frontend_accessibility(self) -> FrontendHealthResult:
        """
        Check if the frontend application is accessible via HTTP.
        
        Verifies that the frontend server is running and responding to requests
        on the expected port (localhost:3000).
        
        Returns:
            FrontendHealthResult with accessibility status
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/")
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    return FrontendHealthResult(
                        service="frontend_accessibility",
                        healthy=True,
                        response_time_ms=response_time,
                        status_code=response.status_code,
                        message="Frontend application is accessible",
                        details={
                            "url": f"{self.base_url}/",
                            "content_length": len(response.text),
                            "content_type": response.headers.get("content-type", "unknown")
                        }
                    )
                else:
                    return FrontendHealthResult(
                        service="frontend_accessibility",
                        healthy=False,
                        response_time_ms=response_time,
                        status_code=response.status_code,
                        message=f"Frontend returned status code: {response.status_code}",
                        error=f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
        except httpx.ConnectError:
            response_time = (time.time() - start_time) * 1000
            return FrontendHealthResult(
                service="frontend_accessibility",
                healthy=False,
                response_time_ms=response_time,
                message="Cannot connect to frontend application",
                error=f"Connection refused to {self.base_url}"
            )
        except httpx.TimeoutException:
            response_time = (time.time() - start_time) * 1000
            return FrontendHealthResult(
                service="frontend_accessibility",
                healthy=False,
                response_time_ms=response_time,
                message="Frontend request timed out",
                error=f"Request timeout after {self.timeout}s"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return FrontendHealthResult(
                service="frontend_accessibility",
                healthy=False,
                response_time_ms=response_time,
                message="Frontend accessibility check failed",
                error=str(e)
            )
    
    async def check_page_rendering(self) -> FrontendHealthResult:
        """
        Check if the main page renders correctly with expected content.
        
        Verifies that the homepage loads and contains expected HTML elements
        and structure indicating proper React/Next.js rendering.
        
        Returns:
            FrontendHealthResult with page rendering status
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/")
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code != 200:
                    return FrontendHealthResult(
                        service="page_rendering",
                        healthy=False,
                        response_time_ms=response_time,
                        status_code=response.status_code,
                        message="Page not accessible for rendering check",
                        error=f"HTTP {response.status_code}"
                    )
                
                html_content = response.text
                
                # Check for basic HTML structure
                rendering_checks = {
                    "has_html_tag": bool(re.search(r'<html[^>]*>', html_content, re.IGNORECASE)),
                    "has_head_tag": bool(re.search(r'<head[^>]*>', html_content, re.IGNORECASE)),
                    "has_body_tag": bool(re.search(r'<body[^>]*>', html_content, re.IGNORECASE)),
                    "has_title": bool(re.search(r'<title[^>]*>.*?</title>', html_content, re.IGNORECASE)),
                    "has_next_script": bool(re.search(r'_next/static', html_content)),
                    "has_react_root": bool(re.search(r'__next|react-root|root', html_content, re.IGNORECASE)),
                    "no_error_messages": not bool(re.search(r'error|exception|failed|500|404', html_content, re.IGNORECASE)),
                    "has_meta_viewport": bool(re.search(r'<meta[^>]*viewport[^>]*>', html_content, re.IGNORECASE))
                }
                
                # Calculate rendering score
                passed_checks = sum(1 for check in rendering_checks.values() if check)
                total_checks = len(rendering_checks)
                rendering_score = (passed_checks / total_checks) * 100
                
                # Consider healthy if most checks pass
                is_healthy = rendering_score >= 75
                
                return FrontendHealthResult(
                    service="page_rendering",
                    healthy=is_healthy,
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    message=f"Page rendering check: {rendering_score:.1f}% passed",
                    details={
                        "rendering_score": rendering_score,
                        "checks_passed": passed_checks,
                        "total_checks": total_checks,
                        "check_results": rendering_checks,
                        "content_length": len(html_content),
                        "has_next_js_markers": rendering_checks["has_next_script"]
                    }
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return FrontendHealthResult(
                service="page_rendering",
                healthy=False,
                response_time_ms=response_time,
                message="Page rendering check failed",
                error=str(e)
            )
    
    async def check_javascript_errors(self) -> FrontendHealthResult:
        """
        Check for JavaScript errors by examining console output and error indicators.
        
        Since this is a server-side check, it looks for common JavaScript error
        patterns in the HTML response and checks for error boundaries or
        error messages that might indicate client-side issues.
        
        Returns:
            FrontendHealthResult with JavaScript error detection status
        """
        start_time = time.time()
        
        try:
            # Check multiple pages for JavaScript errors
            pages_to_check = [
                "/",
                "/health",
                "/dashboard"
            ]
            
            error_indicators = []
            total_pages_checked = 0
            pages_with_errors = 0
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for page_path in pages_to_check:
                    try:
                        response = await client.get(f"{self.base_url}{page_path}")
                        total_pages_checked += 1
                        
                        if response.status_code == 200:
                            html_content = response.text
                            
                            # Look for JavaScript error indicators in HTML
                            js_error_patterns = [
                                r'<script[^>]*>.*?error.*?</script>',
                                r'console\.error',
                                r'uncaught.*?error',
                                r'javascript.*?error',
                                r'react.*?error',
                                r'next.*?error',
                                r'hydration.*?error',
                                r'chunk.*?load.*?error'
                            ]
                            
                            page_errors = []
                            for pattern in js_error_patterns:
                                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                                if matches:
                                    page_errors.extend(matches[:3])  # Limit to first 3 matches
                            
                            if page_errors:
                                pages_with_errors += 1
                                error_indicators.append({
                                    "page": page_path,
                                    "errors": page_errors[:5]  # Limit errors per page
                                })
                        
                        # Small delay between requests
                        await asyncio.sleep(0.1)
                        
                    except Exception as page_error:
                        # If a specific page fails, note it but continue
                        error_indicators.append({
                            "page": page_path,
                            "errors": [f"Page check failed: {str(page_error)}"]
                        })
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine health status
            error_rate = (pages_with_errors / total_pages_checked * 100) if total_pages_checked > 0 else 100
            is_healthy = error_rate < 25  # Healthy if less than 25% of pages have errors
            
            message = f"JavaScript error check: {len(error_indicators)} issues found"
            if not error_indicators:
                message = "No JavaScript errors detected"
            
            return FrontendHealthResult(
                service="javascript_errors",
                healthy=is_healthy,
                response_time_ms=response_time,
                message=message,
                details={
                    "pages_checked": total_pages_checked,
                    "pages_with_errors": pages_with_errors,
                    "error_rate_percent": round(error_rate, 2),
                    "error_indicators": error_indicators[:10],  # Limit total errors reported
                    "total_errors_found": len(error_indicators)
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return FrontendHealthResult(
                service="javascript_errors",
                healthy=False,
                response_time_ms=response_time,
                message="JavaScript error detection failed",
                error=str(e)
            )
    
    async def check_health_endpoint(self) -> FrontendHealthResult:
        """
        Check the frontend's own health endpoint if available.
        
        Attempts to access /health or /api/health endpoints that might
        be provided by the Next.js application.
        
        Returns:
            FrontendHealthResult with health endpoint status
        """
        start_time = time.time()
        
        health_endpoints = [
            "/health",
            "/api/health",
            "/api/v1/health"
        ]
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for endpoint in health_endpoints:
                    try:
                        response = await client.get(f"{self.base_url}{endpoint}")
                        
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status_code == 200:
                            # Try to parse as JSON
                            try:
                                health_data = response.json()
                                return FrontendHealthResult(
                                    service="frontend_health_endpoint",
                                    healthy=True,
                                    response_time_ms=response_time,
                                    status_code=response.status_code,
                                    message=f"Frontend health endpoint accessible at {endpoint}",
                                    details={
                                        "endpoint": endpoint,
                                        "health_data": health_data
                                    }
                                )
                            except json.JSONDecodeError:
                                # Health endpoint exists but doesn't return JSON
                                return FrontendHealthResult(
                                    service="frontend_health_endpoint",
                                    healthy=True,
                                    response_time_ms=response_time,
                                    status_code=response.status_code,
                                    message=f"Frontend health endpoint accessible at {endpoint} (non-JSON)",
                                    details={
                                        "endpoint": endpoint,
                                        "response_text": response.text[:200]
                                    }
                                )
                    
                    except httpx.HTTPStatusError:
                        continue  # Try next endpoint
                    except Exception:
                        continue  # Try next endpoint
            
            # No health endpoint found
            response_time = (time.time() - start_time) * 1000
            return FrontendHealthResult(
                service="frontend_health_endpoint",
                healthy=False,
                response_time_ms=response_time,
                message="No frontend health endpoint found",
                details={
                    "attempted_endpoints": health_endpoints,
                    "note": "This is not necessarily an error - frontend may not have dedicated health endpoint"
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return FrontendHealthResult(
                service="frontend_health_endpoint",
                healthy=False,
                response_time_ms=response_time,
                message="Frontend health endpoint check failed",
                error=str(e)
            )
    
    async def verify_frontend_startup(self, max_attempts: int = 12, retry_delay: float = 5.0) -> FrontendHealthResult:
        """
        Verify that the frontend application has started up successfully.
        
        Attempts to connect to the frontend with retries and timeout handling
        to ensure the application is fully operational before running tests.
        
        Args:
            max_attempts: Maximum number of connection attempts
            retry_delay: Delay between retry attempts in seconds
            
        Returns:
            FrontendHealthResult with startup verification status
        """
        start_time = time.time()
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Check if frontend is responding
                accessibility_result = await self.check_frontend_accessibility()
                
                if accessibility_result.healthy:
                    # Frontend is accessible, now check rendering
                    rendering_result = await self.check_page_rendering()
                    response_time = (time.time() - start_time) * 1000
                    
                    if rendering_result.healthy:
                        return FrontendHealthResult(
                            service="frontend_startup",
                            healthy=True,
                            response_time_ms=response_time,
                            message=f"Frontend startup verified successfully (attempt {attempt})",
                            details={
                                "attempts": attempt,
                                "startup_time_ms": response_time,
                                "accessibility_status": accessibility_result.dict(),
                                "rendering_status": rendering_result.dict()
                            }
                        )
                    else:
                        # Frontend accessible but not rendering properly
                        if attempt < max_attempts:
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            return FrontendHealthResult(
                                service="frontend_startup",
                                healthy=False,
                                response_time_ms=(time.time() - start_time) * 1000,
                                message=f"Frontend accessible but not rendering properly after {attempt} attempts",
                                error=rendering_result.error
                            )
                else:
                    # Frontend not accessible, retry
                    if attempt < max_attempts:
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        return FrontendHealthResult(
                            service="frontend_startup",
                            healthy=False,
                            response_time_ms=(time.time() - start_time) * 1000,
                            message=f"Frontend not accessible after {attempt} attempts",
                            error=accessibility_result.error
                        )
                        
            except Exception as e:
                if attempt < max_attempts:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    return FrontendHealthResult(
                        service="frontend_startup",
                        healthy=False,
                        response_time_ms=(time.time() - start_time) * 1000,
                        message=f"Frontend startup verification failed after {attempt} attempts",
                        error=str(e)
                    )
        
        # Should not reach here, but just in case
        return FrontendHealthResult(
            service="frontend_startup",
            healthy=False,
            response_time_ms=(time.time() - start_time) * 1000,
            message="Frontend startup verification failed - unexpected error"
        )
    
    async def comprehensive_frontend_check(self) -> Dict[str, FrontendHealthResult]:
        """
        Perform comprehensive health check of all frontend components.
        
        Checks accessibility, page rendering, JavaScript errors, and health endpoints.
        
        Returns:
            Dictionary mapping component names to their health check results
        """
        results = {}
        
        # Run all health checks concurrently where possible
        health_tasks = {
            "accessibility": self.check_frontend_accessibility(),
            "page_rendering": self.check_page_rendering(),
            "javascript_errors": self.check_javascript_errors(),
            "health_endpoint": self.check_health_endpoint()
        }
        
        # Wait for all checks to complete
        completed_tasks = await asyncio.gather(*health_tasks.values(), return_exceptions=True)
        
        # Process results
        for component, result in zip(health_tasks.keys(), completed_tasks):
            if isinstance(result, Exception):
                results[component] = FrontendHealthResult(
                    service=component,
                    healthy=False,
                    response_time_ms=0.0,
                    message=f"Health check failed with exception",
                    error=str(result)
                )
            else:
                results[component] = result
        
        return results
    
    def get_health_summary(self, results: Dict[str, FrontendHealthResult]) -> Dict[str, Any]:
        """
        Generate a summary of frontend health check results.
        
        Args:
            results: Dictionary of health check results
            
        Returns:
            Summary dictionary with overall status and component details
        """
        healthy_count = sum(1 for result in results.values() if result.healthy)
        total_count = len(results)
        
        overall_healthy = healthy_count == total_count
        success_rate = (healthy_count / total_count * 100) if total_count > 0 else 0
        
        unhealthy_components = [
            name for name, result in results.items() 
            if not result.healthy
        ]
        
        return {
            "overall_healthy": overall_healthy,
            "healthy_components": healthy_count,
            "total_components": total_count,
            "success_rate": round(success_rate, 2),
            "unhealthy_components": unhealthy_components,
            "timestamp": datetime.now().isoformat(),
            "details": {name: result.dict() for name, result in results.items()}
        }


class FrontendHealthTest(ServiceHealthTestBase):
    """
    E2E test class for frontend application health checking.
    
    This class extends ServiceHealthTestBase to provide specific
    frontend health testing functionality for the E2E test suite.
    """
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        """Initialize frontend health test."""
        super().__init__()
        self.base_url = base_url
        self.health_checker = FrontendHealthChecker(base_url)
    
    async def setup(self):
        """Set up frontend health test environment."""
        await super().setup()
        self.logger.info(f"Setting up frontend health test for {self.base_url}")
        
        # Add service endpoints specific to frontend
        self.service_endpoints.update({
            "frontend_root": f"{self.base_url}/",
            "frontend_health": f"{self.base_url}/health",
            "frontend_dashboard": f"{self.base_url}/dashboard"
        })
    
    async def run_test(self) -> Dict[str, Any]:
        """
        Execute frontend health test.
        
        Performs comprehensive health checks and returns results.
        """
        self.logger.info("Running frontend health test")
        
        try:
            # Perform comprehensive health check
            health_results = await self.health_checker.comprehensive_frontend_check()
            
            # Add results to base class tracking
            for service_name, result in health_results.items():
                self.add_health_result(
                    service=service_name,
                    is_healthy=result.healthy,
                    response_time=result.response_time_ms / 1000,  # Convert to seconds
                    details=result.dict()
                )
            
            # Generate summary
            summary = self.health_checker.get_health_summary(health_results)
            
            # Determine test status
            test_status = "passed" if summary["overall_healthy"] else "failed"
            
            return {
                "test_name": "frontend_health_check",
                "status": test_status,
                "message": f"Frontend health check completed - {summary['success_rate']}% healthy",
                "summary": summary,
                "health_results": self.health_results,
                "unhealthy_components": self.get_unhealthy_services()
            }
            
        except Exception as e:
            self.logger.error(f"Frontend health test failed: {e}")
            return {
                "test_name": "frontend_health_check",
                "status": "failed",
                "message": f"Frontend health test failed: {str(e)}",
                "error": str(e)
            }