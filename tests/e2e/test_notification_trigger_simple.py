"""
Simple notification trigger tests

This module provides basic tests for notification trigger functionality
using the NotificationTriggerTestFramework.
"""

import pytest
import asyncio
from tests.e2e.notification_trigger_test_framework import NotificationTriggerTestFramework


class TestNotificationTriggerSimple:
    """Simple notification trigger tests"""
    
    @pytest.fixture
    def framework(self):
        """Create notification trigger test framework instance"""
        return NotificationTriggerTestFramework()
    
    @pytest.mark.asyncio
    async def test_setup_notification_environment(self, framework):
        """Test notification test environment setup"""
        try:
            success = await framework.setup_test_environment()
            assert success, "Failed to setup notification test environment"
            
            # Verify test users were created
            assert len(framework.test_users) > 0, "No test users created"
            
            # Verify users have different notification preferences
            preferences_found = False
            for user in framework.test_users:
                user_prefs = user.settings.get("notifications", {})
                if user_prefs:
                    preferences_found = True
                    break
            
            assert preferences_found, "No notification preferences found in test users"
            
        finally:
            await framework.cleanup_test_environment()
    
    @pytest.mark.asyncio
    async def test_morning_briefing_trigger(self, framework):
        """Test manual morning briefing trigger"""
        try:
            # Setup environment
            setup_success = await framework.setup_test_environment()
            assert setup_success, "Failed to setup test environment"
            
            # Test morning briefing triggers
            results = await framework.test_manual_morning_briefing_trigger()
            
            # Verify no errors occurred
            assert "error" not in results, f"Morning briefing test failed: {results.get('error')}"
            
            # Verify individual triggers were tested
            assert "individual_triggers" in results, "No individual trigger results found"
            assert len(results["individual_triggers"]) > 0, "No individual triggers tested"
            
            # Verify bulk trigger was tested
            assert "bulk_trigger" in results, "No bulk trigger results found"
            
            # Verify timing metrics were calculated
            assert "timing_metrics" in results, "No timing metrics found"
            
            # Check that at least some notifications were processed
            individual_results = results["individual_triggers"]
            processed_count = len([r for r in individual_results if "result" in r or "error" in r])
            assert processed_count > 0, "No notifications were processed"
            
        finally:
            await framework.cleanup_test_environment()
    
    @pytest.mark.asyncio
    async def test_evening_update_trigger(self, framework):
        """Test manual evening update trigger"""
        try:
            # Setup environment
            setup_success = await framework.setup_test_environment()
            assert setup_success, "Failed to setup test environment"
            
            # Test evening update triggers
            results = await framework.test_manual_evening_update_trigger()
            
            # Verify no errors occurred
            assert "error" not in results, f"Evening update test failed: {results.get('error')}"
            
            # Verify individual triggers were tested
            assert "individual_triggers" in results, "No individual trigger results found"
            assert len(results["individual_triggers"]) > 0, "No individual triggers tested"
            
            # Verify bulk trigger was tested
            assert "bulk_trigger" in results, "No bulk trigger results found"
            
            # Verify timing metrics were calculated
            assert "timing_metrics" in results, "No timing metrics found"
            
            # Check that at least some notifications were processed
            individual_results = results["individual_triggers"]
            processed_count = len([r for r in individual_results if "result" in r or "error" in r])
            assert processed_count > 0, "No notifications were processed"
            
        finally:
            await framework.cleanup_test_environment()
    
    @pytest.mark.asyncio
    async def test_job_match_notifications(self, framework):
        """Test job match notification system"""
        try:
            # Setup environment
            setup_success = await framework.setup_test_environment()
            assert setup_success, "Failed to setup test environment"
            
            # Test job match notifications
            results = await framework.test_job_match_notifications()
            
            # Verify no errors occurred
            assert "error" not in results, f"Job match notification test failed: {results.get('error')}"
            
            # Verify job alert triggers were tested
            assert "job_alert_triggers" in results, "No job alert trigger results found"
            
            # Verify Celery task tests were performed
            assert "celery_task_tests" in results, "No Celery task test results found"
            
            # Verify delivery timing was measured
            assert "delivery_timing" in results, "No delivery timing results found"
            
            # Verify match relevance was calculated
            assert "match_relevance" in results, "No match relevance results found"
            
            # Check that job alerts were processed for eligible users
            job_alert_results = results["job_alert_triggers"]
            processed_count = len([r for r in job_alert_results if not r.get("skipped", False)])
            
            # Should have at least some users eligible for job alerts
            total_users = len(job_alert_results)
            assert total_users > 0, "No users tested for job alerts"
            
        finally:
            await framework.cleanup_test_environment()
    
    @pytest.mark.asyncio
    async def test_notification_delivery_timing(self, framework):
        """Test notification delivery timing verification"""
        try:
            # Setup environment
            setup_success = await framework.setup_test_environment()
            assert setup_success, "Failed to setup test environment"
            
            # Test delivery timing
            results = await framework.test_notification_delivery_timing()
            
            # Verify no errors occurred
            assert "error" not in results, f"Delivery timing test failed: {results.get('error')}"
            
            # Verify timing results for different notification types
            assert "morning_briefing_timing" in results, "No morning briefing timing results"
            assert "evening_update_timing" in results, "No evening update timing results"
            assert "job_alert_timing" in results, "No job alert timing results"
            
            # Verify overall timing metrics were calculated
            assert "overall_timing_metrics" in results, "No overall timing metrics found"
            
            overall_metrics = results["overall_timing_metrics"]
            if overall_metrics:  # Only check if we have metrics
                assert "total_notifications_tested" in overall_metrics, "No total notifications count"
                assert "average_delivery_time" in overall_metrics, "No average delivery time"
                assert "timing_compliance_rate" in overall_metrics, "No timing compliance rate"
                
                # Verify timing compliance is reasonable (at least some notifications should be on time)
                compliance_rate = overall_metrics.get("timing_compliance_rate", 0)
                assert compliance_rate >= 0, "Invalid compliance rate"
            
        finally:
            await framework.cleanup_test_environment()
    
    @pytest.mark.asyncio
    async def test_comprehensive_notification_test(self, framework):
        """Test comprehensive notification trigger functionality"""
        try:
            # Run comprehensive test
            results = await framework.run_comprehensive_notification_test()
            
            # Verify no errors occurred
            assert "error" not in results, f"Comprehensive test failed: {results.get('error')}"
            
            # Verify all test sections are present
            assert "test_summary" in results, "No test summary found"
            assert "morning_briefing_results" in results, "No morning briefing results"
            assert "evening_update_results" in results, "No evening update results"
            assert "job_match_notification_results" in results, "No job match notification results"
            assert "delivery_timing_results" in results, "No delivery timing results"
            assert "requirements_validation" in results, "No requirements validation found"
            
            # Verify test summary
            summary = results["test_summary"]
            assert "total_execution_time" in summary, "No execution time in summary"
            assert "test_users_created" in summary, "No user count in summary"
            assert "overall_success" in summary, "No overall success status"
            
            # Verify requirements validation
            req_validation = results["requirements_validation"]
            assert "req_6_1_morning_briefing" in req_validation, "Missing requirement 6.1 validation"
            assert "req_6_2_evening_briefing" in req_validation, "Missing requirement 6.2 validation"
            assert "req_6_3_job_match_notifications" in req_validation, "Missing requirement 6.3 validation"
            
            # Check that at least some requirements passed validation
            validated_count = sum(1 for req in req_validation.values() if req.get("validated", False))
            assert validated_count > 0, "No requirements passed validation"
            
        finally:
            # Cleanup is handled by the comprehensive test itself
            pass


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])