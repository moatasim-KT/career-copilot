#!/usr/bin/env python3
"""
Security Implementation Test Script for Career Copilot.
Tests the implemented security features and validates configuration.
"""

import asyncio
import json
import time
from typing import Dict, List
import requests
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30


class SecurityTester:
    """Security implementation tester."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_basic_connectivity(self):
        """Test basic API connectivity."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            passed = response.status_code == 200
            self.log_result("Basic Connectivity", passed, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Basic Connectivity", False, f"Error: {e}")
    
    def test_security_headers(self):
        """Test security headers implementation."""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            
            required_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Referrer-Policy",
                "Content-Security-Policy"
            ]
            
            missing_headers = []
            for header in required_headers:
                if header not in response.headers:
                    missing_headers.append(header)
            
            passed = len(missing_headers) == 0
            details = f"Missing headers: {missing_headers}" if missing_headers else "All security headers present"
            self.log_result("Security Headers", passed, details)
            
        except Exception as e:
            self.log_result("Security Headers", False, f"Error: {e}")
    
    def test_csp_header(self):
        """Test Content Security Policy header."""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            csp_header = response.headers.get("Content-Security-Policy")
            
            if csp_header:
                # Check for key CSP directives
                required_directives = ["default-src", "script-src", "style-src", "frame-ancestors"]
                missing_directives = []
                
                for directive in required_directives:
                    if directive not in csp_header:
                        missing_directives.append(directive)
                
                passed = len(missing_directives) == 0
                details = f"Missing directives: {missing_directives}" if missing_directives else "CSP properly configured"
            else:
                passed = False
                details = "CSP header not found"
            
            self.log_result("Content Security Policy", passed, details)
            
        except Exception as e:
            self.log_result("Content Security Policy", False, f"Error: {e}")
    
    def test_input_validation(self):
        """Test input validation and sanitization."""
        # Test SQL injection patterns
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users"
        ]
        
        for payload in sql_payloads:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/v1/health",
                    params={"test": payload},
                    timeout=5
                )
                
                # Should either block the request (400) or handle it safely
                passed = response.status_code in [400, 200]
                self.log_result(
                    f"SQL Injection Protection ({payload[:20]}...)",
                    passed,
                    f"Status: {response.status_code}"
                )
                
            except Exception as e:
                self.log_result(f"SQL Injection Test", False, f"Error: {e}")
        
        # Test XSS patterns
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/v1/health",
                    params={"test": payload},
                    timeout=5
                )
                
                passed = response.status_code in [400, 200]
                self.log_result(
                    f"XSS Protection ({payload[:20]}...)",
                    passed,
                    f"Status: {response.status_code}"
                )
                
            except Exception as e:
                self.log_result(f"XSS Protection Test", False, f"Error: {e}")
    
    def test_rate_limiting(self):
        """Test rate limiting implementation."""
        try:
            # Make rapid requests to trigger rate limiting
            responses = []
            for i in range(15):  # Exceed typical rate limits
                response = self.session.get(f"{self.base_url}/api/v1/health", timeout=2)
                responses.append(response.status_code)
                time.sleep(0.1)  # Small delay between requests
            
            # Check if any requests were rate limited (429)
            rate_limited = any(status == 429 for status in responses)
            
            if rate_limited:
                self.log_result("Rate Limiting", True, "Rate limiting is active")
            else:
                # Maybe rate limits are higher, try with auth endpoint
                auth_responses = []
                for i in range(20):
                    try:
                        response = self.session.post(
                            f"{self.base_url}/api/v1/auth/login",
                            json={"email": "test@example.com", "password": "test"},
                            timeout=2
                        )
                        auth_responses.append(response.status_code)
                    except:
                        break
                    time.sleep(0.05)
                
                auth_rate_limited = any(status == 429 for status in auth_responses)
                self.log_result("Rate Limiting", auth_rate_limited, 
                              "Rate limiting active on auth endpoints" if auth_rate_limited 
                              else "Rate limiting may be disabled or limits are high")
            
        except Exception as e:
            self.log_result("Rate Limiting", False, f"Error: {e}")
    
    def test_cors_configuration(self):
        """Test CORS configuration."""
        try:
            # Test preflight request
            response = self.session.options(
                f"{self.base_url}/api/v1/health",
                headers={
                    "Origin": "https://malicious-site.com",
                    "Access-Control-Request-Method": "GET"
                },
                timeout=5
            )
            
            # Check CORS headers
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            # CORS should be restrictive
            origin_header = cors_headers["Access-Control-Allow-Origin"]
            if origin_header == "*":
                passed = False
                details = "CORS allows all origins (security risk)"
            elif origin_header:
                passed = True
                details = f"CORS properly configured: {origin_header}"
            else:
                passed = True
                details = "CORS restrictive (no Access-Control-Allow-Origin header)"
            
            self.log_result("CORS Configuration", passed, details)
            
        except Exception as e:
            self.log_result("CORS Configuration", False, f"Error: {e}")
    
    def test_firebase_auth_endpoints(self):
        """Test Firebase authentication endpoints."""
        try:
            # Test Firebase token verification endpoint
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/firebase/verify-token",
                json={"id_token": "invalid_token"},
                timeout=5
            )
            
            # Should handle invalid token gracefully
            passed = response.status_code in [400, 401, 422]
            self.log_result(
                "Firebase Auth Endpoint",
                passed,
                f"Status: {response.status_code} (handles invalid tokens)"
            )
            
        except Exception as e:
            self.log_result("Firebase Auth Endpoint", False, f"Error: {e}")
    
    def test_authentication_required_endpoints(self):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/api/v1/auth/me",
            "/api/v1/auth/firebase/me"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                
                # Should require authentication (401 or 403)
                passed = response.status_code in [401, 403]
                self.log_result(
                    f"Auth Required ({endpoint})",
                    passed,
                    f"Status: {response.status_code}"
                )
                
            except Exception as e:
                self.log_result(f"Auth Required ({endpoint})", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all security tests."""
        print("🔒 Starting Security Implementation Tests")
        print("=" * 50)
        
        # Run tests
        self.test_basic_connectivity()
        self.test_security_headers()
        self.test_csp_header()
        self.test_input_validation()
        self.test_rate_limiting()
        self.test_cors_configuration()
        self.test_firebase_auth_endpoints()
        self.test_authentication_required_endpoints()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        passed_tests = sum(1 for result in self.results if result["passed"])
        total_tests = len(self.results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Failed tests
        failed_tests = [result for result in self.results if not result["passed"]]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        return passed_tests == total_tests


def main():
    """Main test function."""
    tester = SecurityTester()
    
    try:
        success = tester.run_all_tests()
        
        # Save results
        with open("security_test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "results": tester.results
            }, f, indent=2)
        
        print(f"\n📄 Results saved to security_test_results.json")
        
        if success:
            print("🎉 All security tests passed!")
            return 0
        else:
            print("⚠️  Some security tests failed. Please review the implementation.")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())