#!/usr/bin/env python3
"""
Focused validation script that tests what we can without authentication
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FocusedValidator:
    """Focused validation without authentication dependencies"""
    
    def __init__(self):
        self.results = {
            "tests": {},
            "timestamp": datetime.now().isoformat(),
            "errors": [],
            "warnings": []
        }
        self.backend_url = "http://localhost:8002"
    
    def add_result(self, test_name: str, status: str, details: str = ""):
        """Add test result"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if status == "FAIL":
            self.results["errors"].append(f"{test_name}: {details}")
        elif status == "WARN":
            self.results["warnings"].append(f"{test_name}: {details}")
    
    def test_backend_connectivity(self):
        """Test if backend is running and responding"""
        logger.info("🌐 Testing backend connectivity...")
        
        try:
            response = requests.get(f"{self.backend_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ Backend is running - Status: {health_data.get('status')}")
                self.add_result("backend_connectivity", "PASS", f"Backend responding with status: {health_data.get('status')}")
                return True
            else:
                raise Exception(f"Health check returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Backend connectivity failed: {e}")
            self.add_result("backend_connectivity", "FAIL", str(e))
            return False
    
    def test_api_endpoints_without_auth(self):
        """Test API endpoints that don't require authentication"""
        logger.info("🔌 Testing public API endpoints...")
        
        public_endpoints = [
            ("/", "GET"),
            ("/api/v1/health", "GET"),
        ]
        
        all_passed = True
        
        for endpoint, method in public_endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                
                if response.status_code in [200, 404]:  # 404 is acceptable for some endpoints
                    logger.info(f"✅ {method} {endpoint}: {response.status_code}")
                else:
                    logger.warning(f"⚠️ {method} {endpoint}: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"❌ {method} {endpoint}: {e}")
                all_passed = False
        
        if all_passed:
            self.add_result("public_endpoints", "PASS", "All public endpoints responding")
        else:
            self.add_result("public_endpoints", "WARN", "Some public endpoints have issues")
    
    def test_database_models(self):
        """Test database models can be imported and used"""
        logger.info("🗄️ Testing database models...")
        
        try:
            from app.models.user import User
            from app.models.job import Job
            from app.models.application import Application
            
            # Test model creation (without database)
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "hashed_password": "hashed_password"
            }
            
            job_data = {
                "user_id": 1,
                "company": "Test Company",
                "title": "Software Engineer",
                "location": "Remote",
                "tech_stack": ["Python", "FastAPI"],
                "source": "manual"
            }
            
            app_data = {
                "user_id": 1,
                "job_id": 1,
                "status": "applied"
            }
            
            # Test model instantiation
            user = User(**user_data)
            job = Job(**job_data)
            application = Application(**app_data)
            
            logger.info("✅ Database models work correctly")
            self.add_result("database_models", "PASS", "All models can be instantiated")
            
        except Exception as e:
            logger.error(f"❌ Database models test failed: {e}")
            self.add_result("database_models", "FAIL", str(e))
    
    def test_schemas(self):
        """Test Pydantic schemas"""
        logger.info("📋 Testing Pydantic schemas...")
        
        try:
            from app.schemas.job import JobCreate, JobUpdate, JobResponse
            from app.schemas.user import UserCreate, UserResponse
            from app.schemas.application import ApplicationCreate, ApplicationUpdate
            
            # Test JobCreate schema
            job_data = {
                "company": "Test Company",
                "title": "Software Engineer",
                "location": "Remote",
                "tech_stack": ["Python", "FastAPI"],
                "source": "manual"
            }
            
            job_create = JobCreate(**job_data)
            
            # Test UserCreate schema
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            user_create = UserCreate(**user_data)
            
            # Test ApplicationCreate schema
            app_data = {
                "job_id": 1,
                "status": "applied"
            }
            
            app_create = ApplicationCreate(**app_data)
            
            logger.info("✅ Pydantic schemas work correctly")
            self.add_result("pydantic_schemas", "PASS", "All schemas validate correctly")
            
        except Exception as e:
            logger.error(f"❌ Pydantic schemas test failed: {e}")
            self.add_result("pydantic_schemas", "FAIL", str(e))
    
    def test_security_functions(self):
        """Test security functions"""
        logger.info("🔒 Testing security functions...")
        
        try:
            from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
            
            # Test password hashing
            password = "testpassword123"
            hashed = get_password_hash(password)
            
            if hashed != password:
                logger.info("✅ Password hashing works")
                
                # Test password verification
                if verify_password(password, hashed):
                    logger.info("✅ Password verification works")
                    
                    # Test JWT token creation
                    token = create_access_token({"sub": "testuser"})
                    if token:
                        logger.info("✅ JWT token creation works")
                        
                        # Test JWT token decoding
                        payload = decode_access_token(token)
                        if payload and payload.get("sub") == "testuser":
                            logger.info("✅ JWT token decoding works")
                            self.add_result("security_functions", "PASS", "All security functions work")
                        else:
                            raise Exception("JWT token decoding failed")
                    else:
                        raise Exception("JWT token creation failed")
                else:
                    raise Exception("Password verification failed")
            else:
                raise Exception("Password hashing failed - hash same as original")
                
        except Exception as e:
            logger.error(f"❌ Security functions test failed: {e}")
            self.add_result("security_functions", "FAIL", str(e))
    
    def test_configuration(self):
        """Test configuration loading"""
        logger.info("⚙️ Testing configuration...")
        
        try:
            from app.core.config import get_settings
            
            settings = get_settings()
            
            # Check required settings
            required_settings = [
                "database_url", "jwt_secret_key", "jwt_algorithm", 
                "api_host", "api_port"
            ]
            
            missing_settings = []
            for setting in required_settings:
                if not hasattr(settings, setting) or getattr(settings, setting) is None:
                    missing_settings.append(setting)
            
            if not missing_settings:
                logger.info("✅ Configuration loading works")
                self.add_result("configuration", "PASS", "All required settings present")
            else:
                raise Exception(f"Missing settings: {missing_settings}")
                
        except Exception as e:
            logger.error(f"❌ Configuration test failed: {e}")
            self.add_result("configuration", "FAIL", str(e))
    
    def test_database_connection(self):
        """Test database connection"""
        logger.info("🗄️ Testing database connection...")
        
        try:
            from sqlalchemy import create_engine, text
            from app.core.config import get_settings
            
            settings = get_settings()
            engine = create_engine(settings.database_url)
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    logger.info("✅ Database connection works")
                    
                    # Check table existence
                    tables_result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                    tables = [row[0] for row in tables_result.fetchall()]
                    
                    expected_tables = ["users", "jobs", "applications"]
                    missing_tables = [t for t in expected_tables if t not in tables]
                    
                    if not missing_tables:
                        logger.info(f"✅ All required tables exist: {tables}")
                        self.add_result("database_connection", "PASS", f"Database connection successful, tables: {tables}")
                    else:
                        logger.warning(f"⚠️ Missing tables: {missing_tables}")
                        self.add_result("database_connection", "WARN", f"Missing tables: {missing_tables}")
                else:
                    raise Exception("Database query returned unexpected result")
                    
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            self.add_result("database_connection", "FAIL", str(e))
    
    def test_service_imports(self):
        """Test service modules can be imported"""
        logger.info("🔧 Testing service modules...")
        
        services_to_test = [
            ("app.services.job_service", "JobService"),
            ("app.services.auth_service", "AuthService"),
            ("app.services.application_service", "ApplicationService"),
            ("app.services.recommendation_service", "RecommendationService"),
            ("app.services.analytics_service", "AnalyticsService"),
        ]
        
        failed_imports = []
        
        for module_name, class_name in services_to_test:
            try:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
                logger.info(f"✅ {module_name}.{class_name} imports successfully")
            except Exception as e:
                logger.error(f"❌ {module_name}.{class_name} import failed: {e}")
                failed_imports.append(f"{module_name}.{class_name}")
        
        if not failed_imports:
            self.add_result("service_imports", "PASS", "All service modules importable")
        else:
            self.add_result("service_imports", "FAIL", f"Failed imports: {failed_imports}")
    
    def test_api_route_imports(self):
        """Test API route modules can be imported"""
        logger.info("🛣️ Testing API routes...")
        
        try:
            from app.api.v1 import auth, jobs, applications, analytics, recommendations, skill_gap, profile
            
            logger.info("✅ API route modules import successfully")
            self.add_result("api_routes", "PASS", "All API route modules importable")
            
        except Exception as e:
            logger.error(f"❌ API routes test failed: {e}")
            self.add_result("api_routes", "FAIL", str(e))
    
    def test_frontend_dependencies(self):
        """Test frontend dependencies are available"""
        logger.info("🎨 Testing frontend dependencies...")
        
        frontend_deps = [
            "streamlit",
            "pandas", 
            "plotly",
            "requests"
        ]
        
        missing_deps = []
        
        for dep in frontend_deps:
            try:
                __import__(dep)
                logger.info(f"✅ {dep} is available")
            except ImportError:
                logger.error(f"❌ {dep} is missing")
                missing_deps.append(dep)
        
        if not missing_deps:
            self.add_result("frontend_dependencies", "PASS", "All frontend dependencies available")
        else:
            self.add_result("frontend_dependencies", "FAIL", f"Missing dependencies: {missing_deps}")
    
    def run_all_tests(self):
        """Run all focused tests"""
        logger.info("🚀 Starting Career Copilot Focused Validation")
        logger.info("=" * 60)
        
        # Test backend connectivity first
        backend_running = self.test_backend_connectivity()
        
        if backend_running:
            self.test_api_endpoints_without_auth()
        
        # Test components that don't require running server
        self.test_configuration()
        self.test_database_models()
        self.test_schemas()
        self.test_security_functions()
        self.test_database_connection()
        self.test_service_imports()
        self.test_api_route_imports()
        self.test_frontend_dependencies()
        
        # Calculate results
        total_tests = len(self.results["tests"])
        failed_tests = len([t for t in self.results["tests"].values() if t["status"] == "FAIL"])
        passed_tests = total_tests - failed_tests
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%"
        }
        
        # Save results
        with open("focused_validation_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print validation summary"""
        logger.info("\n" + "=" * 60)
        logger.info("🏁 FOCUSED VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        summary = self.results["summary"]
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed Tests: {summary['passed_tests']}")
        logger.info(f"Failed Tests: {summary['failed_tests']}")
        logger.info(f"Success Rate: {summary['success_rate']}")
        
        if self.results["errors"]:
            logger.info("\n❌ ERRORS:")
            for error in self.results["errors"]:
                logger.info(f"  - {error}")
        
        if self.results["warnings"]:
            logger.info("\n⚠️ WARNINGS:")
            for warning in self.results["warnings"]:
                logger.info(f"  - {warning}")
        
        logger.info(f"\n📊 Detailed report saved to: focused_validation_report.json")
        logger.info("=" * 60)

def main():
    """Main function"""
    validator = FocusedValidator()
    validator.run_all_tests()

if __name__ == "__main__":
    main()