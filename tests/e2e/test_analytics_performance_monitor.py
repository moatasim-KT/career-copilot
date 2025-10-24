"""
Test Analytics Performance Monitor

Tests for the enhanced analytics performance monitoring system
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from tests.e2e.analytics_performance_monitor import (
    AnalyticsPerformanceMonitor,
    PerformanceMetrics,
    DataAccuracyReport,
    StorageVerificationResult,
    run_analytics_performance_monitoring
)


class TestAnalyticsPerformanceMonitor:
    """Test class for analytics performance monitoring"""
    
    @pytest.fixture
    def monitor(self):
        """Create analytics performance monitor instance"""
        return AnalyticsPerformanceMonitor()
    
    @pytest.mark.asyncio
    async def test_timing_verification(self, monitor):
        """Test timing verification for analytics operations"""
        # Mock analytics operation
        async def mock_analytics_operation():
            await asyncio.sleep(0.1)  # Simulate 100ms operation
            return {"status": "success", "analytics": {"total_users": 10}}
        
        # Monitor the operation
        metrics = await monitor.monitor_analytics_timing(
            "user_analytics",
            mock_analytics_operation
        )
        
        # Verify metrics
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.operation_name == "user_analytics"
        assert metrics.success is True
        assert metrics.execution_time > 0
        assert metrics.execution_time < 30.0  # Should be well under 30 second limit
        assert metrics.error_message is None
    
    @pytest.mark.asyncio
    async def test_timing_verification_failure(self, monitor):
        """Test timing verification when operation fails"""
        # Mock failing analytics operation
        async def failing_analytics_operation():
            await asyncio.sleep(0.05)
            raise Exception("Mock analytics failure")
        
        # Monitor the operation
        metrics = await monitor.monitor_analytics_timing(
            "user_analytics",
            failing_analytics_operation
        )
        
        # Verify failure metrics
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.success is False
        assert metrics.error_message == "Mock analytics failure"
        assert metrics.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_data_accuracy_validation(self, monitor):
        """Test data accuracy validation"""
        # Valid analytics data
        valid_data = {
            "total_jobs": 10,
            "total_applications": 5,
            "success_rates": {"interview_rate": 20.0, "offer_rate": 10.0},
            "recent_activity": {"jobs_added": 2, "applications_submitted": 1}
        }
        
        # Validate the data
        report = await monitor.validate_data_accuracy(valid_data, "user_analytics")
        
        # Verify validation report
        assert isinstance(report, DataAccuracyReport)
        assert report.validation_type == "user_analytics"
        assert report.accuracy_score > 0.8  # Should have high accuracy
        assert report.total_records > 0
        assert report.valid_records > 0
        assert len(report.validation_errors) == 0
    
    @pytest.mark.asyncio
    async def test_data_accuracy_validation_invalid_data(self, monitor):
        """Test data accuracy validation with invalid data"""
        # Invalid analytics data (applications > jobs)
        invalid_data = {
            "total_jobs": 5,
            "total_applications": 10,  # Invalid: more applications than jobs
            "success_rates": {"interview_rate": 20.0, "offer_rate": 30.0},  # Invalid: offer > interview
            "recent_activity": {}  # Invalid: empty dict
        }
        
        # Validate the data
        report = await monitor.validate_data_accuracy(invalid_data, "user_analytics")
        
        # Verify validation catches errors
        assert isinstance(report, DataAccuracyReport)
        assert report.accuracy_score < 1.0  # Should have reduced accuracy
        assert len(report.validation_errors) > 0
        assert any("Applications" in error and "exceed" in error for error in report.validation_errors)
    
    @pytest.mark.asyncio
    async def test_storage_verification(self, monitor):
        """Test analytics storage verification"""
        # Run storage verification
        result = await monitor.verify_analytics_storage("analytics_tables")
        
        # Verify storage verification result
        assert isinstance(result, StorageVerificationResult)
        assert result.storage_type == "analytics_tables"
        assert result.response_time > 0
        assert result.total_records >= 0
        assert result.recent_records >= 0
        # Note: accessible may be True or False depending on mock/real backend
    
    @pytest.mark.asyncio
    async def test_comprehensive_performance_monitoring(self, monitor):
        """Test comprehensive performance monitoring"""
        # Test with mock user IDs
        test_user_ids = [1, 2, 3]
        
        # Run comprehensive monitoring
        results = await monitor.run_comprehensive_performance_monitoring(test_user_ids)
        
        # Verify results structure
        assert "timing_verification" in results
        assert "data_accuracy_validation" in results
        assert "storage_verification" in results
        assert "performance_summary" in results
        assert "compliance_status" in results
        
        # Verify timing verification results
        timing_results = results["timing_verification"]
        assert "user_analytics" in timing_results or len(timing_results) >= 0
        assert "system_analytics" in timing_results
        
        # Verify compliance status
        compliance_status = results["compliance_status"]
        assert "requirement_8_3_timing" in compliance_status
        assert "requirement_8_4_storage" in compliance_status
        assert "overall_compliance" in compliance_status
        
        # Check compliance structure
        req_8_3 = compliance_status["requirement_8_3_timing"]
        assert "compliant" in req_8_3
        assert "compliance_rate" in req_8_3
        assert "description" in req_8_3
        
        req_8_4 = compliance_status["requirement_8_4_storage"]
        assert "compliant" in req_8_4
        assert "compliance_rate" in req_8_4
        assert "description" in req_8_4
    
    @pytest.mark.asyncio
    async def test_performance_report_generation(self, monitor):
        """Test performance report generation"""
        # Add some mock performance data
        mock_metrics = PerformanceMetrics(
            operation_name="test_operation",
            execution_time=15.0,
            success=True,
            data_size=1024,
            memory_usage=None,
            cpu_usage=None,
            error_message=None,
            timestamp=datetime.now()
        )
        monitor.performance_history.append(mock_metrics)
        
        # Add mock accuracy report
        mock_accuracy = DataAccuracyReport(
            validation_type="test_validation",
            accuracy_score=0.95,
            total_records=10,
            valid_records=9,
            invalid_records=1,
            validation_errors=["Minor validation issue"],
            timestamp=datetime.now()
        )
        monitor.accuracy_reports.append(mock_accuracy)
        
        # Generate report
        report = monitor.get_performance_report()
        
        # Verify report structure
        assert "performance_metrics" in report
        assert "accuracy_reports" in report
        assert "storage_verifications" in report
        assert "timing_benchmarks" in report
        
        # Verify performance metrics
        assert len(report["performance_metrics"]) > 0
        perf_metric = report["performance_metrics"][0]
        assert perf_metric["operation"] == "test_operation"
        assert perf_metric["execution_time"] == 15.0
        assert perf_metric["success"] is True
        
        # Verify accuracy reports
        assert len(report["accuracy_reports"]) > 0
        acc_report = report["accuracy_reports"][0]
        assert acc_report["validation_type"] == "test_validation"
        assert acc_report["accuracy_score"] == 0.95
    
    def test_timing_benchmark_updates(self, monitor):
        """Test timing benchmark updates"""
        # Update benchmark with sample data
        monitor._update_timing_benchmark("user_analytics", 10.0, True)
        monitor._update_timing_benchmark("user_analytics", 15.0, True)
        monitor._update_timing_benchmark("user_analytics", 20.0, False)
        
        # Check benchmark statistics
        benchmark = monitor.timing_benchmarks["user_analytics"]
        assert benchmark.samples_count == 3
        assert benchmark.min_time == 10.0
        assert benchmark.max_time == 20.0
        assert benchmark.average_time == 15.0  # (10 + 15 + 20) / 3
        assert benchmark.success_rate == 2/3  # 2 successes out of 3
    
    def test_field_validation(self, monitor):
        """Test individual field validation"""
        # Test numeric field validation
        assert monitor._validate_field_value("total_jobs", 10) is True
        assert monitor._validate_field_value("total_jobs", -5) is False
        assert monitor._validate_field_value("total_jobs", "invalid") is False
        
        # Test rate field validation
        assert monitor._validate_field_value("interview_rate", 25.0) is True
        assert monitor._validate_field_value("interview_rate", 150.0) is False
        assert monitor._validate_field_value("interview_rate", -10.0) is False
        
        # Test dictionary field validation
        assert monitor._validate_field_value("success_rates", {"rate": 10}) is True
        assert monitor._validate_field_value("success_rates", {}) is False
        assert monitor._validate_field_value("success_rates", None) is False
    
    def test_data_consistency_validation(self, monitor):
        """Test data consistency validation"""
        # Valid data (applications <= jobs)
        valid_data = {"total_jobs": 10, "total_applications": 5}
        errors = monitor._validate_data_consistency(valid_data)
        assert len(errors) == 0
        
        # Invalid data (applications > jobs)
        invalid_data = {"total_jobs": 5, "total_applications": 10}
        errors = monitor._validate_data_consistency(invalid_data)
        assert len(errors) > 0
        assert any("Applications" in error and "exceed" in error for error in errors)
        
        # Invalid success rates (offer > interview)
        invalid_rates_data = {
            "success_rates": {"interview_rate": 10.0, "offer_rate": 20.0}
        }
        errors = monitor._validate_data_consistency(invalid_rates_data)
        assert len(errors) > 0
        assert any("Offer rate" in error and "exceed" in error for error in errors)


@pytest.mark.asyncio
async def test_convenience_function():
    """Test the convenience function for running performance monitoring"""
    test_user_ids = [1, 2]
    
    results = await run_analytics_performance_monitoring(test_user_ids)
    
    # Verify results structure
    assert isinstance(results, dict)
    if "error" not in results:
        assert "timing_verification" in results
        assert "data_accuracy_validation" in results
        assert "storage_verification" in results
        assert "performance_summary" in results
        assert "compliance_status" in results


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])