"""
Analytics Performance Monitor

Enhanced performance monitoring for analytics processing including:
- Timing verification for analytics processing (Requirement 8.3)
- Data accuracy validation for reports
- Analytics storage verification (Requirement 8.4)
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics
import logging

try:
    from backend.app.core.database import get_db
    from backend.app.models.analytics import Analytics
    from backend.app.tasks.analytics_tasks import (
        generate_user_analytics,
        generate_system_analytics,
        generate_batch_analytics
    )
    from sqlalchemy.orm import Session
    from sqlalchemy import func, and_
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Backend imports not available: {e}")
    BACKEND_AVAILABLE = False
    
    # Mock classes for testing when backend is not available
    class MockSession:
        def query(self, model):
            return MockQuery()
        def add(self, obj):
            pass
        def commit(self):
            pass
        def close(self):
            pass
    
    class MockQuery:
        def filter(self, *args):
            return self
        def count(self):
            return 10
        def all(self):
            return []
        def first(self):
            return None
    
    def get_db():
        return MockSession()
    
    class MockAnalytics:
        def __init__(self, **kwargs):
            self.id = 1
            self.type = "user_analytics"
            self.data = {}
            self.generated_at = datetime.now()
    
    Analytics = MockAnalytics


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
class TimingBenchmark:
    """Timing benchmark for analytics operations"""
    operation_type: str
    max_allowed_time: float  # seconds
    average_time: float
    min_time: float
    max_time: float
    success_rate: float
    samples_count: int


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


class AnalyticsPerformanceMonitor:
    """
    Enhanced analytics performance monitoring system
    
    Provides comprehensive monitoring for:
    - Timing verification (Requirement 8.3: 30-minute completion)
    - Data accuracy validation
    - Storage verification (Requirement 8.4: designated reporting tables)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if BACKEND_AVAILABLE:
            self.db: Session = next(get_db())
        else:
            self.db = MockSession()
        
        # Performance benchmarks (Requirement 8.3: 30 minutes = 1800 seconds)
        self.timing_benchmarks = {
            "user_analytics": TimingBenchmark("user_analytics", 30.0, 0.0, 0.0, 0.0, 0.0, 0),
            "system_analytics": TimingBenchmark("system_analytics", 60.0, 0.0, 0.0, 0.0, 0.0, 0),
            "batch_analytics": TimingBenchmark("batch_analytics", 1800.0, 0.0, 0.0, 0.0, 0.0, 0),  # 30 minutes
            "daily_analytics": TimingBenchmark("daily_analytics", 1800.0, 0.0, 0.0, 0.0, 0.0, 0)   # 30 minutes
        }
        
        self.performance_history: List[PerformanceMetrics] = []
        self.accuracy_reports: List[DataAccuracyReport] = []
        self.storage_verifications: List[StorageVerificationResult] = []
    
    async def monitor_analytics_timing(self, operation_type: str, operation_func, *args, **kwargs) -> PerformanceMetrics:
        """
        Monitor timing for analytics operations (Requirement 8.3)
        
        Args:
            operation_type: Type of analytics operation
            operation_func: Function to execute and monitor
            *args, **kwargs: Arguments for the operation function
            
        Returns:
            PerformanceMetrics: Detailed performance metrics
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            # Execute the analytics operation
            if asyncio.iscoroutinefunction(operation_func):
                result = await operation_func(*args, **kwargs)
            else:
                result = operation_func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            end_memory = self._get_memory_usage()
            memory_delta = end_memory - start_memory if start_memory and end_memory else None
            
            # Determine data size from result
            data_size = self._calculate_data_size(result)
            
            # Check if timing meets requirements (8.3: 30 minutes max)
            benchmark = self.timing_benchmarks.get(operation_type)
            timing_compliant = execution_time <= benchmark.max_allowed_time if benchmark else True
            
            metrics = PerformanceMetrics(
                operation_name=operation_type,
                execution_time=execution_time,
                success=True,
                data_size=data_size,
                memory_usage=memory_delta,
                cpu_usage=None,  # Could be enhanced with psutil
                error_message=None,
                timestamp=datetime.now()
            )
            
            # Update benchmark statistics
            self._update_timing_benchmark(operation_type, execution_time, True)
            
            self.logger.info(
                f"Analytics operation '{operation_type}' completed in {execution_time:.2f}s "
                f"(Compliant: {timing_compliant}, Max allowed: {benchmark.max_allowed_time if benchmark else 'N/A'}s)"
            )
            
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
            
            # Update benchmark with failure
            self._update_timing_benchmark(operation_type, execution_time, False)
            
            self.logger.error(f"Analytics operation '{operation_type}' failed after {execution_time:.2f}s: {e}")
            return metrics
        
        finally:
            self.performance_history.append(metrics)
    
    async def validate_data_accuracy(self, analytics_data: Dict[str, Any], validation_type: str) -> DataAccuracyReport:
        """
        Validate accuracy of analytics data
        
        Args:
            analytics_data: Analytics data to validate
            validation_type: Type of validation being performed
            
        Returns:
            DataAccuracyReport: Detailed accuracy validation report
        """
        validation_errors = []
        total_records = 0
        valid_records = 0
        
        try:
            # Validate data structure and completeness
            if not analytics_data:
                validation_errors.append("Analytics data is empty or None")
            else:
                # Check for required fields based on validation type
                required_fields = self._get_required_fields(validation_type)
                
                for field in required_fields:
                    if field not in analytics_data:
                        validation_errors.append(f"Missing required field: {field}")
                    else:
                        total_records += 1
                        
                        # Validate field data quality
                        field_value = analytics_data[field]
                        if self._validate_field_value(field, field_value):
                            valid_records += 1
                        else:
                            validation_errors.append(f"Invalid value for field '{field}': {field_value}")
                
                # Validate data consistency
                consistency_errors = self._validate_data_consistency(analytics_data)
                validation_errors.extend(consistency_errors)
                
                # Validate data ranges and business logic
                business_logic_errors = self._validate_business_logic(analytics_data, validation_type)
                validation_errors.extend(business_logic_errors)
            
            # Calculate accuracy score
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
            
            self.logger.info(
                f"Data accuracy validation '{validation_type}': "
                f"{accuracy_score:.2f} accuracy ({valid_records}/{total_records} valid)"
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error validating data accuracy for '{validation_type}': {e}")
            return DataAccuracyReport(
                validation_type=validation_type,
                accuracy_score=0.0,
                total_records=0,
                valid_records=0,
                invalid_records=0,
                validation_errors=[f"Validation error: {str(e)}"],
                timestamp=datetime.now()
            )
    
    async def verify_analytics_storage(self, storage_type: str = "analytics_tables") -> StorageVerificationResult:
        """
        Verify analytics storage in designated reporting tables (Requirement 8.4)
        
        Args:
            storage_type: Type of storage to verify
            
        Returns:
            StorageVerificationResult: Storage verification results
        """
        start_time = time.time()
        
        try:
            # Verify analytics table accessibility and data
            total_records = self.db.query(Analytics).count()
            
            # Check recent analytics records (last 24 hours)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_records = self.db.query(Analytics).filter(
                Analytics.generated_at >= recent_cutoff
            ).count()
            
            # Verify different types of analytics are stored
            analytics_types = self.db.query(Analytics.type).distinct().all()
            stored_types = [t[0] for t in analytics_types] if analytics_types else []
            
            response_time = time.time() - start_time
            
            # Check if required analytics types are present
            required_types = ["user_analytics", "system_analytics", "daily_analytics"]
            missing_types = [t for t in required_types if t not in stored_types]
            
            # Determine if storage is properly functioning
            storage_accessible = (
                total_records > 0 and
                recent_records >= 0 and
                len(missing_types) == 0
            )
            
            result = StorageVerificationResult(
                storage_type=storage_type,
                accessible=storage_accessible,
                total_records=total_records,
                recent_records=recent_records,
                storage_size=None,  # Could be enhanced with actual size calculation
                response_time=response_time,
                error_message=f"Missing analytics types: {missing_types}" if missing_types else None,
                timestamp=datetime.now()
            )
            
            self.storage_verifications.append(result)
            
            self.logger.info(
                f"Storage verification '{storage_type}': "
                f"{'✅ Accessible' if storage_accessible else '❌ Issues detected'} "
                f"({total_records} total, {recent_records} recent records)"
            )
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            
            result = StorageVerificationResult(
                storage_type=storage_type,
                accessible=False,
                total_records=0,
                recent_records=0,
                storage_size=None,
                response_time=response_time,
                error_message=str(e),
                timestamp=datetime.now()
            )
            
            self.storage_verifications.append(result)
            self.logger.error(f"Storage verification failed for '{storage_type}': {e}")
            return result 
   
    async def run_comprehensive_performance_monitoring(self, user_ids: List[int] = None) -> Dict[str, Any]:
        """
        Run comprehensive performance monitoring for all analytics operations
        
        Args:
            user_ids: List of user IDs to test (optional)
            
        Returns:
            Dict containing comprehensive performance monitoring results
        """
        monitoring_results = {
            "timing_verification": {},
            "data_accuracy_validation": {},
            "storage_verification": {},
            "performance_summary": {},
            "compliance_status": {}
        }
        
        try:
            # 1. Timing Verification (Requirement 8.3)
            timing_results = await self._run_timing_verification_tests(user_ids)
            monitoring_results["timing_verification"] = timing_results
            
            # 2. Data Accuracy Validation
            accuracy_results = await self._run_data_accuracy_tests(user_ids)
            monitoring_results["data_accuracy_validation"] = accuracy_results
            
            # 3. Storage Verification (Requirement 8.4)
            storage_results = await self._run_storage_verification_tests()
            monitoring_results["storage_verification"] = storage_results
            
            # 4. Generate Performance Summary
            performance_summary = self._generate_performance_summary()
            monitoring_results["performance_summary"] = performance_summary
            
            # 5. Check Compliance Status
            compliance_status = self._check_compliance_status()
            monitoring_results["compliance_status"] = compliance_status
            
            return monitoring_results
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive performance monitoring: {e}")
            return {"error": str(e)}
    
    async def _run_timing_verification_tests(self, user_ids: List[int] = None) -> Dict[str, Any]:
        """Run timing verification tests for all analytics operations"""
        timing_results = {}
        
        # Test user analytics timing
        if user_ids:
            user_timing_results = []
            for user_id in user_ids[:3]:  # Limit to 3 users for testing
                if BACKEND_AVAILABLE:
                    metrics = await self.monitor_analytics_timing(
                        "user_analytics",
                        lambda uid: generate_user_analytics.delay(uid).get(timeout=60),
                        user_id
                    )
                else:
                    # Mock timing test
                    metrics = PerformanceMetrics(
                        operation_name="user_analytics",
                        execution_time=15.0,
                        success=True,
                        data_size=1024,
                        memory_usage=None,
                        cpu_usage=None,
                        error_message=None,
                        timestamp=datetime.now()
                    )
                
                user_timing_results.append({
                    "user_id": user_id,
                    "metrics": metrics,
                    "compliant": metrics.execution_time <= 30.0  # 30 seconds for user analytics
                })
            
            timing_results["user_analytics"] = user_timing_results
        
        # Test system analytics timing
        if BACKEND_AVAILABLE:
            system_metrics = await self.monitor_analytics_timing(
                "system_analytics",
                lambda: generate_system_analytics.delay().get(timeout=120)
            )
        else:
            system_metrics = PerformanceMetrics(
                operation_name="system_analytics",
                execution_time=45.0,
                success=True,
                data_size=2048,
                memory_usage=None,
                cpu_usage=None,
                error_message=None,
                timestamp=datetime.now()
            )
        
        timing_results["system_analytics"] = {
            "metrics": system_metrics,
            "compliant": system_metrics.execution_time <= 60.0  # 1 minute for system analytics
        }
        
        # Test batch analytics timing (Requirement 8.3: 30 minutes)
        if user_ids:
            if BACKEND_AVAILABLE:
                batch_metrics = await self.monitor_analytics_timing(
                    "batch_analytics",
                    lambda uids: generate_batch_analytics.delay(uids).get(timeout=1800),
                    user_ids
                )
            else:
                batch_metrics = PerformanceMetrics(
                    operation_name="batch_analytics",
                    execution_time=300.0,  # 5 minutes
                    success=True,
                    data_size=4096,
                    memory_usage=None,
                    cpu_usage=None,
                    error_message=None,
                    timestamp=datetime.now()
                )
            
            timing_results["batch_analytics"] = {
                "metrics": batch_metrics,
                "compliant": batch_metrics.execution_time <= 1800.0,  # 30 minutes (Requirement 8.3)
                "user_count": len(user_ids)
            }
        
        return timing_results
    
    async def _run_data_accuracy_tests(self, user_ids: List[int] = None) -> Dict[str, Any]:
        """Run data accuracy validation tests"""
        accuracy_results = {}
        
        # Test user analytics data accuracy
        if user_ids:
            user_accuracy_results = []
            for user_id in user_ids[:2]:  # Limit for testing
                # Generate analytics data
                if BACKEND_AVAILABLE:
                    task = generate_user_analytics.delay(user_id)
                    result = task.get(timeout=60)
                    analytics_data = result.get("analytics", {})
                else:
                    analytics_data = {
                        "total_jobs": 10,
                        "total_applications": 5,
                        "success_rates": {"interview_rate": 20.0, "offer_rate": 10.0},
                        "recent_activity": {"jobs_added": 2, "applications_submitted": 1}
                    }
                
                # Validate accuracy
                accuracy_report = await self.validate_data_accuracy(analytics_data, "user_analytics")
                user_accuracy_results.append({
                    "user_id": user_id,
                    "report": accuracy_report,
                    "data_sample": analytics_data
                })
            
            accuracy_results["user_analytics"] = user_accuracy_results
        
        # Test system analytics data accuracy
        if BACKEND_AVAILABLE:
            system_task = generate_system_analytics.delay()
            system_result = system_task.get(timeout=60)
            system_analytics_data = system_result.get("analytics", {})
        else:
            system_analytics_data = {
                "users": {"total": 100, "active_30_days": 80},
                "jobs": {"total": 500, "added_last_week": 25},
                "applications": {"total": 200, "submitted_last_week": 15}
            }
        
        system_accuracy_report = await self.validate_data_accuracy(system_analytics_data, "system_analytics")
        accuracy_results["system_analytics"] = {
            "report": system_accuracy_report,
            "data_sample": system_analytics_data
        }
        
        return accuracy_results
    
    async def _run_storage_verification_tests(self) -> Dict[str, Any]:
        """Run storage verification tests (Requirement 8.4)"""
        storage_results = {}
        
        # Verify main analytics tables
        main_storage_result = await self.verify_analytics_storage("analytics_tables")
        storage_results["analytics_tables"] = main_storage_result
        
        # Verify specific analytics types are stored
        analytics_types = ["user_analytics", "system_analytics", "daily_analytics"]
        for analytics_type in analytics_types:
            type_result = await self.verify_analytics_storage(f"{analytics_type}_storage")
            storage_results[f"{analytics_type}_storage"] = type_result
        
        return storage_results
    
    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary from collected metrics"""
        if not self.performance_history:
            return {"message": "No performance data available"}
        
        # Calculate timing statistics
        execution_times = [m.execution_time for m in self.performance_history if m.success]
        timing_stats = {
            "average_execution_time": statistics.mean(execution_times) if execution_times else 0,
            "median_execution_time": statistics.median(execution_times) if execution_times else 0,
            "min_execution_time": min(execution_times) if execution_times else 0,
            "max_execution_time": max(execution_times) if execution_times else 0,
            "total_operations": len(self.performance_history),
            "successful_operations": len(execution_times),
            "success_rate": len(execution_times) / len(self.performance_history) if self.performance_history else 0
        }
        
        # Calculate accuracy statistics
        accuracy_scores = [r.accuracy_score for r in self.accuracy_reports]
        accuracy_stats = {
            "average_accuracy": statistics.mean(accuracy_scores) if accuracy_scores else 0,
            "min_accuracy": min(accuracy_scores) if accuracy_scores else 0,
            "max_accuracy": max(accuracy_scores) if accuracy_scores else 0,
            "total_validations": len(self.accuracy_reports)
        }
        
        # Calculate storage statistics
        storage_accessible_count = sum(1 for s in self.storage_verifications if s.accessible)
        storage_stats = {
            "accessible_storages": storage_accessible_count,
            "total_storages_checked": len(self.storage_verifications),
            "storage_accessibility_rate": storage_accessible_count / len(self.storage_verifications) if self.storage_verifications else 0
        }
        
        return {
            "timing_statistics": timing_stats,
            "accuracy_statistics": accuracy_stats,
            "storage_statistics": storage_stats,
            "summary_timestamp": datetime.now().isoformat()
        }
    
    def _check_compliance_status(self) -> Dict[str, Any]:
        """Check compliance with requirements 8.3 and 8.4"""
        compliance_status = {}
        
        # Requirement 8.3: 30-minute completion time
        timing_compliant_operations = []
        for metrics in self.performance_history:
            benchmark = self.timing_benchmarks.get(metrics.operation_name)
            if benchmark and metrics.success:
                compliant = metrics.execution_time <= benchmark.max_allowed_time
                timing_compliant_operations.append(compliant)
        
        timing_compliance_rate = sum(timing_compliant_operations) / len(timing_compliant_operations) if timing_compliant_operations else 0
        
        compliance_status["requirement_8_3_timing"] = {
            "compliant": timing_compliance_rate >= 0.9,  # 90% compliance threshold
            "compliance_rate": timing_compliance_rate,
            "total_operations_checked": len(timing_compliant_operations),
            "description": "Analytics processing within 30 minutes"
        }
        
        # Requirement 8.4: Storage in designated reporting tables
        storage_accessible_count = sum(1 for s in self.storage_verifications if s.accessible)
        storage_compliance_rate = storage_accessible_count / len(self.storage_verifications) if self.storage_verifications else 0
        
        compliance_status["requirement_8_4_storage"] = {
            "compliant": storage_compliance_rate >= 0.9,  # 90% compliance threshold
            "compliance_rate": storage_compliance_rate,
            "total_storages_checked": len(self.storage_verifications),
            "description": "Analytics stored in designated reporting tables"
        }
        
        # Overall compliance
        overall_compliant = (
            compliance_status["requirement_8_3_timing"]["compliant"] and
            compliance_status["requirement_8_4_storage"]["compliant"]
        )
        
        compliance_status["overall_compliance"] = {
            "compliant": overall_compliant,
            "requirements_met": sum(1 for req in ["requirement_8_3_timing", "requirement_8_4_storage"] 
                                  if compliance_status[req]["compliant"]),
            "total_requirements": 2
        }
        
        return compliance_status    

    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage (could be enhanced with psutil)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return None
    
    def _calculate_data_size(self, data: Any) -> int:
        """Calculate approximate data size"""
        if isinstance(data, dict):
            return len(str(data))
        elif isinstance(data, (list, tuple)):
            return sum(len(str(item)) for item in data)
        else:
            return len(str(data))
    
    def _update_timing_benchmark(self, operation_type: str, execution_time: float, success: bool):
        """Update timing benchmark statistics"""
        if operation_type not in self.timing_benchmarks:
            return
        
        benchmark = self.timing_benchmarks[operation_type]
        
        # Update statistics
        if benchmark.samples_count == 0:
            benchmark.min_time = execution_time
            benchmark.max_time = execution_time
            benchmark.average_time = execution_time
        else:
            benchmark.min_time = min(benchmark.min_time, execution_time)
            benchmark.max_time = max(benchmark.max_time, execution_time)
            # Running average
            benchmark.average_time = (
                (benchmark.average_time * benchmark.samples_count + execution_time) / 
                (benchmark.samples_count + 1)
            )
        
        benchmark.samples_count += 1
        
        # Update success rate
        if success:
            successful_samples = int(benchmark.success_rate * (benchmark.samples_count - 1))
            benchmark.success_rate = (successful_samples + 1) / benchmark.samples_count
        else:
            successful_samples = int(benchmark.success_rate * (benchmark.samples_count - 1))
            benchmark.success_rate = successful_samples / benchmark.samples_count
    
    def _get_required_fields(self, validation_type: str) -> List[str]:
        """Get required fields for validation type"""
        field_mappings = {
            "user_analytics": ["total_jobs", "total_applications", "success_rates", "recent_activity"],
            "system_analytics": ["users", "jobs", "applications"],
            "daily_analytics": ["date", "user_count", "job_count", "application_count"],
            "batch_analytics": ["processed_users", "successful_operations", "failed_operations"]
        }
        return field_mappings.get(validation_type, [])
    
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
        
        # Default validation: not None
        return field_value is not None
    
    def _validate_data_consistency(self, analytics_data: Dict[str, Any]) -> List[str]:
        """Validate data consistency and logical relationships"""
        errors = []
        
        # Check logical relationships
        total_jobs = analytics_data.get("total_jobs", 0)
        total_applications = analytics_data.get("total_applications", 0)
        
        if isinstance(total_jobs, (int, float)) and isinstance(total_applications, (int, float)):
            if total_applications > total_jobs:
                errors.append(f"Applications ({total_applications}) cannot exceed jobs ({total_jobs})")
        
        # Check success rates are reasonable
        success_rates = analytics_data.get("success_rates", {})
        if isinstance(success_rates, dict):
            interview_rate = success_rates.get("interview_rate", 0)
            offer_rate = success_rates.get("offer_rate", 0)
            
            if isinstance(interview_rate, (int, float)) and isinstance(offer_rate, (int, float)):
                if offer_rate > interview_rate:
                    errors.append(f"Offer rate ({offer_rate}%) cannot exceed interview rate ({interview_rate}%)")
        
        return errors
    
    def _validate_business_logic(self, analytics_data: Dict[str, Any], validation_type: str) -> List[str]:
        """Validate business logic rules"""
        errors = []
        
        if validation_type == "user_analytics":
            # User analytics should have reasonable ranges
            total_jobs = analytics_data.get("total_jobs", 0)
            if isinstance(total_jobs, (int, float)) and total_jobs > 10000:
                errors.append(f"Unusually high job count: {total_jobs}")
            
            total_applications = analytics_data.get("total_applications", 0)
            if isinstance(total_applications, (int, float)) and total_applications > 1000:
                errors.append(f"Unusually high application count: {total_applications}")
        
        elif validation_type == "system_analytics":
            # System analytics should have reasonable user counts
            users_data = analytics_data.get("users", {})
            if isinstance(users_data, dict):
                total_users = users_data.get("total", 0)
                active_users = users_data.get("active_30_days", 0)
                
                if isinstance(total_users, (int, float)) and isinstance(active_users, (int, float)):
                    if active_users > total_users:
                        errors.append(f"Active users ({active_users}) cannot exceed total users ({total_users})")
        
        return errors
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance monitoring report"""
        return {
            "performance_metrics": [
                {
                    "operation": m.operation_name,
                    "execution_time": m.execution_time,
                    "success": m.success,
                    "data_size": m.data_size,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.performance_history
            ],
            "accuracy_reports": [
                {
                    "validation_type": r.validation_type,
                    "accuracy_score": r.accuracy_score,
                    "total_records": r.total_records,
                    "valid_records": r.valid_records,
                    "errors": r.validation_errors,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.accuracy_reports
            ],
            "storage_verifications": [
                {
                    "storage_type": s.storage_type,
                    "accessible": s.accessible,
                    "total_records": s.total_records,
                    "recent_records": s.recent_records,
                    "response_time": s.response_time,
                    "timestamp": s.timestamp.isoformat()
                }
                for s in self.storage_verifications
            ],
            "timing_benchmarks": {
                op_type: {
                    "max_allowed_time": benchmark.max_allowed_time,
                    "average_time": benchmark.average_time,
                    "min_time": benchmark.min_time,
                    "max_time": benchmark.max_time,
                    "success_rate": benchmark.success_rate,
                    "samples_count": benchmark.samples_count
                }
                for op_type, benchmark in self.timing_benchmarks.items()
            }
        }
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self.db, 'close'):
            self.db.close()


# Convenience function for running performance monitoring
async def run_analytics_performance_monitoring(user_ids: List[int] = None) -> Dict[str, Any]:
    """
    Convenience function to run analytics performance monitoring
    
    Args:
        user_ids: List of user IDs to test (optional)
        
    Returns:
        Dict containing performance monitoring results
    """
    monitor = AnalyticsPerformanceMonitor()
    try:
        results = await monitor.run_comprehensive_performance_monitoring(user_ids)
        return results
    finally:
        monitor.cleanup()


if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("Running Analytics Performance Monitoring...")
        
        # Test with mock user IDs
        test_user_ids = [1, 2, 3, 4]
        
        results = await run_analytics_performance_monitoring(test_user_ids)
        
        print("\n" + "="*60)
        print("ANALYTICS PERFORMANCE MONITORING RESULTS")
        print("="*60)
        
        if "error" in results:
            print(f"❌ Monitoring failed: {results['error']}")
        else:
            # Print timing verification results
            timing_results = results.get("timing_verification", {})
            print("\n📊 TIMING VERIFICATION (Requirement 8.3):")
            
            for operation, data in timing_results.items():
                if isinstance(data, dict) and "metrics" in data:
                    metrics = data["metrics"]
                    compliant = data.get("compliant", False)
                    print(f"  {operation}: {metrics.execution_time:.2f}s {'✅' if compliant else '❌'}")
                elif isinstance(data, list):
                    for item in data:
                        metrics = item["metrics"]
                        compliant = item.get("compliant", False)
                        print(f"  {operation} (User {item.get('user_id', 'N/A')}): {metrics.execution_time:.2f}s {'✅' if compliant else '❌'}")
            
            # Print data accuracy results
            accuracy_results = results.get("data_accuracy_validation", {})
            print("\n🎯 DATA ACCURACY VALIDATION:")
            
            for validation_type, data in accuracy_results.items():
                if isinstance(data, dict) and "report" in data:
                    report = data["report"]
                    print(f"  {validation_type}: {report.accuracy_score:.2f} accuracy ({report.valid_records}/{report.total_records})")
                elif isinstance(data, list):
                    for item in data:
                        report = item["report"]
                        print(f"  {validation_type} (User {item.get('user_id', 'N/A')}): {report.accuracy_score:.2f} accuracy")
            
            # Print storage verification results
            storage_results = results.get("storage_verification", {})
            print("\n💾 STORAGE VERIFICATION (Requirement 8.4):")
            
            for storage_type, result in storage_results.items():
                accessible = result.accessible
                print(f"  {storage_type}: {'✅ Accessible' if accessible else '❌ Issues'} ({result.total_records} records)")
            
            # Print compliance status
            compliance_status = results.get("compliance_status", {})
            print("\n📋 COMPLIANCE STATUS:")
            
            req_8_3 = compliance_status.get("requirement_8_3_timing", {})
            req_8_4 = compliance_status.get("requirement_8_4_storage", {})
            overall = compliance_status.get("overall_compliance", {})
            
            print(f"  Requirement 8.3 (Timing): {'✅' if req_8_3.get('compliant') else '❌'} ({req_8_3.get('compliance_rate', 0):.1%})")
            print(f"  Requirement 8.4 (Storage): {'✅' if req_8_4.get('compliant') else '❌'} ({req_8_4.get('compliance_rate', 0):.1%})")
            print(f"  Overall Compliance: {'✅' if overall.get('compliant') else '❌'} ({overall.get('requirements_met', 0)}/{overall.get('total_requirements', 2)})")
    
    asyncio.run(main())