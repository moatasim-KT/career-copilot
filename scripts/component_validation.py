#!/usr/bin/env python3
"""
Career Copilot MVP - Component Validation Script
Tests individual components without requiring running servers
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComponentValidator:
    """Validate individual components"""
    
    def __init__(self):
        self.results = {
            "component_tests": {},
            "timestamp": datetime.now().isoformat(),
            "errors": [],
            "warnings": []
        }
    
    def add_result(self, test_name: str, status: str, details: str = ""):
        """Add test result"""
        self.results["component_tests"][test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if status == "FAIL":
            self.results["errors"].append(f"{test_name}: {details}")
        elif status == "WARN":
            self.results["warnings"].append(f"{test_name}: {details}")
    
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
                    self.add_result("database_connection", "PASS", "Database connection successful")
                else:
                    raise Exception("Database query returned unexpected result")
                    
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            self.add_result("database_connection", "FAIL", str(e))
    
    def test_services(self):
        """Test service modules can be imported"""
        logger.info("🔧 Testing service modules...")
        
        try:
            # Test service imports
            from app.services.job_service import JobService
            from app.services.user_service import UserService
            from app.services.application_service import ApplicationService
            from app.services.recommendation_service import RecommendationService
            from app.services.analytics_service import AnalyticsService
            
            logger.info("✅ Service modules import successfully")
            self.add_result("service_modules", "PASS", "All service modules importable")
            
        except Exception as e:
            logger.error(f"❌ Service modules test failed: {e}")
            self.add_result("service_modules", "FAIL", str(e))
    
    def test_api_routes(self):
        """Test API route modules can be imported"""
        logger.info("🛣️ Testing API routes...")
        
        try:
            from app.api.v1 import auth, jobs, applications, analytics, recommendations, skill_gap, profile
            
            logger.info("✅ API route modules import successfully")
            self.add_result("api_routes", "PASS", "All API route modules importable")
            
        except Exception as e:
            logger.error(f"❌ API routes test failed: {e}")
            self.add_result("api_routes", "FAIL", str(e))
    
    def test_frontend_imports(self):
        """Test frontend can import required modules"""
        logger.info("🎨 Testing frontend imports...")
        
        try:
            # Add frontend to path
            frontend_dir = Path(__file__).parent.parent / "frontend"
            sys.path.insert(0, str(frontend_dir))
            
            # Test basic imports that frontend needs
            import streamlit as st
            import pandas as pd
            import plotly.express as px
            import requests
            
            logger.info("✅ Frontend dependencies available")
            self.add_result("frontend_imports", "PASS", "All frontend dependencies importable")
            
        except Exception as e:
            logger.error(f"❌ Frontend imports test failed: {e}")
            self.add_result("frontend_imports", "FAIL", str(e))
    
    def test_data_directory(self):
        """Test data directory structure"""
        logger.info("📁 Testing data directory structure...")
        
        try:
            data_dir = Path("data")
            
            # Create data directory if it doesn't exist
            data_dir.mkdir(exist_ok=True)
            
            # Check if database file exists or can be created
            db_file = data_dir / "career_copilot.db"
            if db_file.exists():
                logger.info("✅ Database file exists")
            else:
                logger.info("ℹ️ Database file will be created when needed")
            
            # Check write permissions
            test_file = data_dir / "test_write.txt"
            test_file.write_text("test")
            test_file.unlink()
            
            logger.info("✅ Data directory structure is correct")
            self.add_result("data_directory", "PASS", "Data directory accessible and writable")
            
        except Exception as e:
            logger.error(f"❌ Data directory test failed: {e}")
            self.add_result("data_directory", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run all component tests"""
        logger.info("🚀 Starting Career Copilot Component Validation")
        logger.info("=" * 60)
        
        # Run all tests
        self.test_configuration()
        self.test_database_models()
        self.test_schemas()
        self.test_security_functions()
        self.test_database_connection()
        self.test_services()
        self.test_api_routes()
        self.test_frontend_imports()
        self.test_data_directory()
        
        # Calculate results
        total_tests = len(self.results["component_tests"])
        failed_tests = len([t for t in self.results["component_tests"].values() if t["status"] == "FAIL"])
        passed_tests = total_tests - failed_tests
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%"
        }
        
        # Save results
        with open("component_validation_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print validation summary"""
        logger.info("\n" + "=" * 60)
        logger.info("🏁 COMPONENT VALIDATION SUMMARY")
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
        
        logger.info(f"\n📊 Detailed report saved to: component_validation_report.json")
        logger.info("=" * 60)

def main():
    """Main function"""
    validator = ComponentValidator()
    validator.run_all_tests()

if __name__ == "__main__":
    main()