"""
Demo script for notification trigger testing

This script demonstrates the notification trigger test framework capabilities
including manual triggers, timing verification, and job match notifications.
"""

import asyncio
import json
from datetime import datetime
from tests.e2e.notification_trigger_test_framework import NotificationTriggerTestFramework


async def demo_notification_trigger_testing():
    """Demonstrate notification trigger testing capabilities"""
    
    print("🔔 Notification Trigger Testing Demo")
    print("=" * 60)
    print()
    
    framework = NotificationTriggerTestFramework()
    
    try:
        # Setup test environment
        print("📋 Setting up test environment...")
        setup_success = await framework.setup_test_environment()
        
        if not setup_success:
            print("❌ Failed to setup test environment")
            return
        
        print(f"✅ Created {len(framework.test_users)} test users with different notification preferences")
        
        # Display test users and their preferences
        print("\n👥 Test Users:")
        for i, user in enumerate(framework.test_users, 1):
            prefs = user.settings.get("notifications", {})
            print(f"  {i}. {user.username}")
            print(f"     Email: {user.email}")
            print(f"     Morning briefing: {prefs.get('morning_briefing', True)}")
            print(f"     Evening update: {prefs.get('evening_update', True)}")
            print(f"     Job alerts: {prefs.get('job_alerts', True)}")
            print(f"     Frequency: {prefs.get('frequency', 'daily')}")
            print()
        
        # Test morning briefing triggers
        print("🌅 Testing Morning Briefing Triggers...")
        print("-" * 40)
        
        morning_results = await framework.test_manual_morning_briefing_trigger()
        
        if "error" in morning_results:
            print(f"❌ Morning briefing test failed: {morning_results['error']}")
        else:
            # Display individual trigger results
            individual_results = morning_results.get("individual_triggers", [])
            print(f"📊 Individual Trigger Results ({len(individual_results)} users):")
            
            for result in individual_results:
                user_name = result.get("user_name", "Unknown")
                if "result" in result:
                    test_result = result["result"]
                    status = "✅ SUCCESS" if test_result.success else "❌ FAILED"
                    timing = f"{test_result.execution_time:.3f}s"
                    timing_ok = "⏱️ ON TIME" if test_result.timing_validation["within_limit"] else "⏰ SLOW"
                    
                    print(f"  {user_name}: {status} ({timing}) {timing_ok}")
                    if not test_result.success and test_result.error_message:
                        print(f"    Error: {test_result.error_message}")
                elif "error" in result:
                    print(f"  {user_name}: ❌ ERROR - {result['error']}")
            
            # Display bulk trigger results
            bulk_result = morning_results.get("bulk_trigger", {})
            if bulk_result.get("success"):
                print(f"\n📦 Bulk Trigger Results:")
                print(f"  Total eligible: {bulk_result.get('total_eligible', 0)}")
                print(f"  Successfully sent: {bulk_result.get('sent', 0)}")
                print(f"  Failed: {bulk_result.get('failed', 0)}")
                print(f"  Opted out: {bulk_result.get('opted_out', 0)}")
                print(f"  Execution time: {bulk_result.get('execution_time', 0):.3f}s")
            
            # Display timing metrics
            timing_metrics = morning_results.get("timing_metrics", {})
            if hasattr(timing_metrics, "timing_accuracy_score"):
                print(f"\n⏱️ Timing Metrics:")
                print(f"  Timing accuracy: {timing_metrics.timing_accuracy_score:.2%}")
                print(f"  On-time deliveries: {timing_metrics.on_time_deliveries}")
                print(f"  Average delivery time: {timing_metrics.average_delivery_time:.3f}s")
        
        print()
        
        # Test evening update triggers
        print("🌆 Testing Evening Update Triggers...")
        print("-" * 40)
        
        evening_results = await framework.test_manual_evening_update_trigger()
        
        if "error" in evening_results:
            print(f"❌ Evening update test failed: {evening_results['error']}")
        else:
            individual_results = evening_results.get("individual_triggers", [])
            print(f"📊 Individual Trigger Results ({len(individual_results)} users):")
            
            for result in individual_results:
                user_name = result.get("user_name", "Unknown")
                if "result" in result:
                    test_result = result["result"]
                    status = "✅ SUCCESS" if test_result.success else "❌ FAILED"
                    timing = f"{test_result.execution_time:.3f}s"
                    timing_ok = "⏱️ ON TIME" if test_result.timing_validation["within_limit"] else "⏰ SLOW"
                    
                    print(f"  {user_name}: {status} ({timing}) {timing_ok}")
                    if not test_result.success and test_result.error_message:
                        print(f"    Error: {test_result.error_message}")
                elif "error" in result:
                    print(f"  {user_name}: ❌ ERROR - {result['error']}")
            
            bulk_result = evening_results.get("bulk_trigger", {})
            if bulk_result.get("success"):
                print(f"\n📦 Bulk Trigger Results:")
                print(f"  Total eligible: {bulk_result.get('total_eligible', 0)}")
                print(f"  Successfully sent: {bulk_result.get('sent', 0)}")
                print(f"  Failed: {bulk_result.get('failed', 0)}")
                print(f"  Opted out: {bulk_result.get('opted_out', 0)}")
                print(f"  No activity: {bulk_result.get('no_activity', 0)}")
        
        print()
        
        # Test job match notifications
        print("🎯 Testing Job Match Notifications...")
        print("-" * 40)
        
        job_match_results = await framework.test_job_match_notifications()
        
        if "error" in job_match_results:
            print(f"❌ Job match notification test failed: {job_match_results['error']}")
        else:
            job_alert_results = job_match_results.get("job_alert_triggers", [])
            print(f"📊 Job Alert Results ({len(job_alert_results)} users):")
            
            for result in job_alert_results:
                user_name = result.get("user_name", "Unknown")
                if result.get("skipped"):
                    print(f"  {user_name}: ⏭️ SKIPPED - {result.get('reason', 'Unknown reason')}")
                elif "error" in result:
                    print(f"  {user_name}: ❌ ERROR - {result['error']}")
                else:
                    matching_jobs = result.get("matching_jobs_count", 0)
                    timing_valid = "⏱️ ON TIME" if result.get("timing_valid", False) else "⏰ SLOW"
                    celery_success = "✅" if result.get("celery_task_success", False) else "❌"
                    
                    print(f"  {user_name}: {matching_jobs} matches, {timing_valid}, Celery: {celery_success}")
            
            # Display Celery task results
            celery_results = job_match_results.get("celery_task_tests", [])
            successful_tasks = [r for r in celery_results if r.get("success", False)]
            print(f"\n🔄 Celery Task Results:")
            print(f"  Total tasks: {len(celery_results)}")
            print(f"  Successful: {len(successful_tasks)}")
            print(f"  Failed: {len(celery_results) - len(successful_tasks)}")
            
            # Display delivery timing
            delivery_timing = job_match_results.get("delivery_timing", {})
            if delivery_timing:
                print(f"\n⏱️ Delivery Timing:")
                print(f"  Average time: {delivery_timing.get('average_time', 0):.3f}s")
                print(f"  Within limit: {delivery_timing.get('within_limit_count', 0)}/{delivery_timing.get('total_tests', 0)}")
            
            # Display match relevance
            match_relevance = job_match_results.get("match_relevance", [])
            if match_relevance:
                avg_relevance = sum(r["relevance_score"] for r in match_relevance) / len(match_relevance)
                print(f"\n🎯 Match Relevance:")
                print(f"  Average relevance score: {avg_relevance:.1f}%")
        
        print()
        
        # Test delivery timing verification
        print("⏰ Testing Delivery Timing Verification...")
        print("-" * 40)
        
        timing_results = await framework.test_notification_delivery_timing()
        
        if "error" in timing_results:
            print(f"❌ Timing verification test failed: {timing_results['error']}")
        else:
            overall_metrics = timing_results.get("overall_timing_metrics", {})
            if overall_metrics:
                print(f"📊 Overall Timing Metrics:")
                print(f"  Total notifications tested: {overall_metrics.get('total_notifications_tested', 0)}")
                print(f"  Average delivery time: {overall_metrics.get('average_delivery_time', 0):.3f}s")
                print(f"  Max delivery time: {overall_metrics.get('max_delivery_time', 0):.3f}s")
                print(f"  Min delivery time: {overall_metrics.get('min_delivery_time', 0):.3f}s")
                print(f"  Within 15s limit: {overall_metrics.get('within_15_second_limit', 0)}")
                print(f"  Timing compliance: {overall_metrics.get('timing_compliance_rate', 0):.2%}")
        
        print()
        
        # Run comprehensive test
        print("🔍 Running Comprehensive Notification Test...")
        print("-" * 40)
        
        comprehensive_results = await framework.run_comprehensive_notification_test()
        
        if "error" in comprehensive_results:
            print(f"❌ Comprehensive test failed: {comprehensive_results['error']}")
        else:
            summary = comprehensive_results.get("test_summary", {})
            print(f"📋 Test Summary:")
            print(f"  Total execution time: {summary.get('total_execution_time', 0):.2f}s")
            print(f"  Test users created: {summary.get('test_users_created', 0)}")
            print(f"  Overall success: {'✅ PASSED' if summary.get('overall_success', False) else '❌ FAILED'}")
            
            # Display requirements validation
            req_validation = comprehensive_results.get("requirements_validation", {})
            print(f"\n📋 Requirements Validation:")
            
            for req_id, validation in req_validation.items():
                req_name = {
                    "req_6_1_morning_briefing": "6.1 Morning Briefing Delivery",
                    "req_6_2_evening_briefing": "6.2 Evening Briefing Delivery", 
                    "req_6_3_job_match_notifications": "6.3 Job Match Notifications"
                }.get(req_id, req_id)
                
                if validation.get("validated", False):
                    print(f"  ✅ {req_name}: PASSED")
                    if "compliance_rate" in validation:
                        print(f"     Compliance rate: {validation['compliance_rate']:.2%}")
                    if "timing_accuracy" in validation:
                        print(f"     Timing accuracy: {validation['timing_accuracy']:.2%}")
                else:
                    print(f"  ❌ {req_name}: FAILED")
                    if "error" in validation:
                        print(f"     Error: {validation['error']}")
        
        print()
        print("🎉 Notification trigger testing demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up test environment...")
        cleanup_success = await framework.cleanup_test_environment()
        if cleanup_success:
            print("✅ Cleanup completed successfully")
        else:
            print("⚠️ Cleanup completed with warnings")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_notification_trigger_testing())