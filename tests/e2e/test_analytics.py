"""
Consolidated Analytics E2E Tests

This module consolidates all analytics-related E2E tests including:
- Analytics performance monitoring
- Analytics task execution
- Analytics data validation
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import statistics

from tests.e2e.base import BaseE2ETest


@dataclass
class PerformanceMetrics:
    """Performance metrics for analytics operations"""
    operation_name: str
    execution_time: float
    success: bool
    data_size: int
    memory_usage: Optional[float]
    cpu_usage: Optional[float]
    error_message: Optional[str]
    timestamp: datetime


@dataclass
class DataAccuracyReport:
    """Data accuracy validation report"""
    validation_type: str
    accuracy_score: float
    total_records: int
    valid_records: int
    invalid_records: int
    validation_errors: List[str]
    timestamp: datetime


@dataclass
class StorageVerificationResult:
    """Storage verification result"""
    storage_type: str
    accessible: bool
    total_records: int
    recent_records: int
    storage_size: Optional[int]
    response_time: float
    error_message: Optional[str]
    timestamp: datetime


class AnalyticsE2ETest(BaseE2ETest):
    """Consolidated analytics E2E test class"""
    
    def __init__(self):
        super().__init__()
        self.performance_history: List[PerformanceMetrics] = []
        self.accuracy_reports: List[DataAccuracyReport] = []
        self.storage_verifications: List[StorageVerificationResult] = []
    
    async def setup(self):
        """Set up analytics test environment"""
        self.logger.info("Setting up analytics test environment")
        # Initialize test data and connections
        from app.models.user import User
        self.test_user = User(id=1, username="test_user", email="test@example.com")
    
    async def teardown(self):
        """Clean up analytics test environment"""
        self.logger.info("Cleaning up analytics test environment")
        await self._run_cleanup_tasks()
    
    async def run_test(self) -> Dict[str, Any]:
        """Execute consolidated analytics tests"""
        results = {
            "performance_monitoring": await self.test_analytics_performance(),
            "task_execution": await self.test_analytics_tasks(),
            "data_validation": await self.test_analytics_data_validation(),
            "storage_verification": await self.test_analytics_storage()
        }
        
        # Calculate overall success
        overall_success = all(
            result.get("success", False) for result in results.values()
        )
        
        return {
            "test_name": "consolidated_analytics_test",
            "status": "passed" if overall_success else "failed",
            "results": results,
            "summary": {
                "total_operations": len(self.performance_history),
                "successful_operations": len([m for m in self.performance_history if m.success]),
                "average_accuracy": statistics.mean([r.accuracy_score for r in self.accuracy_reports]) if self.accuracy_reports else 0,
                "storage_accessibility": len([s for s in self.storage_verifications if s.accessible]) / len(self.storage_verifications) if self.storage_verifications else 0
            }
        }
    
    async def test_analytics_performance(self) -> Dict[str, Any]:
        """Test analytics performance monitoring"""
        try:
            from app.services.analytics_service import AnalyticsService
            from app.core.database import get_db

            db = next(get_db())
            analytics_service = AnalyticsService(db)

            # Test timing verification
            user_metrics = await self.monitor_analytics_timing("user_analytics", lambda: analytics_service.get_user_analytics(self.test_user))
            system_metrics = await self.monitor_analytics_timing("system_analytics", lambda: analytics_service.get_metrics(self.test_user.id, "last_30_days"))
            
            return {
                "success": user_metrics.success and system_metrics.success,
                "user_analytics_time": user_metrics.execution_time,
                "system_analytics_time": system_metrics.execution_time,
                "timing_compliant": user_metrics.execution_time <= 30.0 and system_metrics.execution_time <= 60.0
            }
            
        except Exception as e:
            self.logger.error(f"Analytics performance test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_analytics_tasks(self) -> Dict[str, Any]:
        """Test analytics task execution"""
        try:
            from app.services.analytics_service import AnalyticsService
            from app.core.database import get_db

            db = next(get_db())
            analytics_service = AnalyticsService(db)

            task_results = []
            
            # Simulate processing analytics for a user
            start_time = time.time()
            result = analytics_service.process_analytics()
            execution_time = time.time() - start_time
            task_results.append({
                "task_type": "process_analytics",
                "success": result.get("processed_count", 0) > 0,
                "execution_time": execution_time
            })
            
            overall_success = all(result["success"] for result in task_results)
            
            return {
                "success": overall_success,
                "task_results": task_results,
                "total_tasks": len(task_results)
            }
            
        except Exception as e:
            self.logger.error(f"Analytics tasks test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_analytics_data_validation(self) -> Dict[str, Any]:
        """Test analytics data validation"""
        try:
            from app.services.analytics_service import AnalyticsService
            from app.core.database import get_db

            db = next(get_db())
            analytics_service = AnalyticsService(db)

            # Get actual user analytics data
            user_analytics_data = analytics_service.get_user_analytics(self.test_user)
            
            accuracy_report = await self.validate_data_accuracy(user_analytics_data, "user_analytics")
            
            return {
                "success": accuracy_report.accuracy_score > 0.8,
                "accuracy_score": accuracy_report.accuracy_score,
                "validation_errors": accuracy_report.validation_errors,
                "total_records": accuracy_report.total_records
            }
            
        except Exception as e:
            self.logger.error(f"Analytics data validation test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_analytics_storage(self) -> Dict[str, Any]:
        """Test analytics storage verification"""
        try:
            from app.services.analytics_service import AnalyticsService
            from app.core.database import get_db
            from app.models.analytics import Analytics

            db = next(get_db())
            analytics_service = AnalyticsService(db)

            # Verify analytics records in the database
            total_records = db.query(Analytics).count()
            recent_records = db.query(Analytics).filter(Analytics.generated_at >= datetime.now() - timedelta(days=7)).count()
            
            storage_result = StorageVerificationResult(
                storage_type=storage_type,
                accessible=True,
                total_records=total_records,
                recent_records=recent_records,
                storage_size=None, # Not easily verifiable in E2E
                response_time=0.0,
                error_message=None,
                timestamp=datetime.now()
            )
            
            self.storage_verifications.append(storage_result)
            return storage_result
            
        except Exception as e:
            self.logger.error(f"Analytics storage test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def monitor_analytics_timing(self, operation_type: str, operation_func) -> PerformanceMetrics:
        """Monitor timing for analytics operations"""
        start_time = time.time()
        
        try:
            result = await operation_func()
            
            execution_time = time.time() - start_time
            
            metrics = PerformanceMetrics(
                operation_name=operation_type,
                execution_time=execution_time,
                success=True,
                data_size=len(str(result)) if result else 0,
                memory_usage=None,
                cpu_usage=None,
                error_message=None,
                timestamp=datetime.now()
            )
            
            self.performance_history.append(metrics)
            return metrics
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            metrics = PerformanceMetrics(
                operation_name=operation_type,
                execution_time=execution_time,
                success=False,
                data_size=0,
                memory_usage=None,
                cpu_usage=None,
                error_message=str(e),
                timestamp=datetime.now()
            )
            
            self.performance_history.append(metrics)
            return metrics
    
    async def validate_data_accuracy(self, analytics_data: Dict[str, Any], validation_type: str) -> DataAccuracyReport:
        """Validate accuracy of analytics data"""
        validation_errors = []
        total_records = 0
        valid_records = 0
        
        # Define required fields for different validation types
        required_fields = {
            "user_analytics": ["total_jobs", "total_applications", "success_rates", "recent_activity"],
            "system_analytics": ["users", "jobs", "applications"],
            "daily_analytics": ["date", "user_count", "job_count", "application_count"]
        }
        
        fields_to_check = required_fields.get(validation_type, [])
        
        for field in fields_to_check:
            total_records += 1
            if field not in analytics_data:
                validation_errors.append(f"Missing required field: {field}")
            else:
                field_value = analytics_data[field]
                if self._validate_field_value(field, field_value):
                    valid_records += 1
                else:
                    validation_errors.append(f"Invalid value for field '{field}': {field_value}")
        
        accuracy_score = valid_records / total_records if total_records > 0 else 0.0
        
        report = DataAccuracyReport(
            validation_type=validation_type,
            accuracy_score=accuracy_score,
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=total_records - valid_records,
            validation_errors=validation_errors,
            timestamp=datetime.now()
        )
        
        self.accuracy_reports.append(report)
        return report
    
    async def verify_analytics_storage(self, storage_type: str = "analytics_tables") -> StorageVerificationResult:
        """Verify analytics storage"""
        start_time = time.time()
        
        # Mock storage verification
        total_records = 150
        recent_records = 25
        response_time = time.time() - start_time
        storage_accessible = True
        
        result = StorageVerificationResult(
            storage_type=storage_type,
            accessible=storage_accessible,
            total_records=total_records,
            recent_records=recent_records,
            storage_size=None,
            response_time=response_time,
            error_message=None,
            timestamp=datetime.now()
        )
        
        self.storage_verifications.append(result)
        return result
    
    def _validate_field_value(self, field_name: str, field_value: Any) -> bool:
        """Validate individual field value"""
        # Numeric fields should be non-negative
        numeric_fields = ["total_jobs", "total_applications", "user_count", "job_count", "application_count"]
        if field_name in numeric_fields:
            return isinstance(field_value, (int, float)) and field_value >= 0
        
        # Rate fields should be between 0 and 100
        rate_fields = ["interview_rate", "offer_rate", "success_rate"]
        if field_name in rate_fields:
            return isinstance(field_value, (int, float)) and 0 <= field_value <= 100
        
        # Dictionary fields should not be empty
        dict_fields = ["success_rates", "recent_activity", "users", "jobs", "applications"]
        if field_name in dict_fields:
            return isinstance(field_value, dict) and len(field_value) > 0
        
        return field_value is not None


# Pytest test functions
import pytest


@pytest.mark.asyncio
async def test_analytics_e2e():
    """Test the consolidated analytics E2E functionality"""
    test_instance = AnalyticsE2ETest()
    await test_instance.setup()
    try:
        result = await test_instance.execute()
        
        assert result is not None
        assert result["test_class"] == "AnalyticsE2ETest"
        assert result["status"] == "completed"
    finally:
        await test_instance.teardown()


@pytest.mark.asyncio
async def test_analytics_performance_monitoring():
    """Test analytics performance monitoring specifically"""
    test_instance = AnalyticsE2ETest()
    await test_instance.setup()
    
    try:
        result = await test_instance.test_analytics_performance()
        assert result["success"] is True
        assert "user_analytics_time" in result
        assert "system_analytics_time" in result
        assert result["timing_compliant"] is True
    finally:
        await test_instance.teardown()


@pytest.mark.asyncio
async def test_analytics_data_validation():
    """Test analytics data validation specifically"""
    test_instance = AnalyticsE2ETest()
    await test_instance.setup()
    
    try:
        result = await test_instance.test_analytics_data_validation()
        assert result["success"] is True
        assert result["accuracy_score"] > 0.8
        assert result["total_records"] > 0
    finally:
        await test_instance.teardown()