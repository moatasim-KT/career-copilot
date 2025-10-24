"""
Demo script for notification delivery verification testing

This script demonstrates the notification delivery verification capabilities including:
- Email delivery verification system
- In-app notification checking  
- Deadline reminder testing (requirement 6.4)
"""

import asyncio
import json
from datetime import datetime
from tests.e2e.notification_delivery_verification import NotificationDeliveryVerificationFramework


async def demo_notification_delivery_verification():
    """Demonstrate notification delivery verification capabilities"""
    
    print("📧 Notification Delivery Verification Demo")
    print("=" * 60)
    print()
    
    framework = NotificationDeliveryVerificationFramework()
    
    try:
        # Setup test environment
        print("📋 Setting up test environment...")
        setup_success = await framework.setup_test_environment()
        
        if not setup_success:
            print("❌ Failed to setup test environment")
            return
        
        print(f"✅ Created {len(framework.test_users)} test users with different notification preferences")
        print(f"✅ Created {len(framework.test_applications)} test applications with various deadlines")
        
        # Display test users and their preferences
        print("\n👥 Test Users for Delivery Verification:")
        for i, user in enumerate(framework.test_users, 1):
            # Mock preferences for demo
            prefs = {
                "email_notifications": True,
                "in_app_notifications": True,
                "push_notifications": False,
                "deadline_reminders": True
            }
            print(f"  {i}. {user.username}")
            print(f"     Email: {user.email}")
            print(f"     Email notifications: {prefs.get('email_notifications', True)}")
            print(f"     In-app notifications: {prefs.get('in_app_notifications', True)}")
            print(f"     Push notifications: {prefs.get('push_notifications', False)}")
            print(f"     Deadline reminders: {prefs.get('deadline_reminders', True)}")
            print()
        
        # Display test applications with deadlines
        print("📅 Test Applications with Deadlines:")
        for i, app in enumerate(framework.test_applications, 1):
            deadline_datetime = datetime.combine(app.follow_up_date, datetime.min.time())
            hours_until = (deadline_datetime - datetime.now()).total_seconds() / 3600
            print(f"  {i}. Application ID {app.id}")
            print(f"     User ID: {app.user_id}")
            print(f"     Deadline: {deadline_datetime.strftime('%Y-%m-%d %H:%M')}")
            print(f"     Hours until deadline: {hours_until:.1f}")
            print(f"     Notes: {app.notes}")
            print()
        
        # Test email delivery verification
        print("📧 Testing Email Delivery Verification...")
        print("-" * 50)
        
        email_results = await framework.test_email_delivery_verification()
        
        if "error" in email_results:
            print(f"❌ Email delivery verification test failed: {email_results['error']}")
        else:
            # Display email delivery results
            delivery_tests = email_results.get("delivery_tests", [])
            print(f"📊 Email Delivery Test Results ({len(delivery_tests)} users):")
            
            for test in delivery_tests:
                user_email = test.get("user_email", "Unknown")
                if test.get("skipped"):
                    print(f"  {user_email}: ⏭️ SKIPPED - {test.get('reason', 'Unknown reason')}")
                elif "result" in test:
                    result = test["result"]
                    status = "✅ DELIVERED" if result.success else "❌ FAILED"
                    timing = f"{result.delivery_time:.3f}s"
                    provider = result.provider_used or "unknown"
                    verification = result.verification_method
                    
                    print(f"  {user_email}: {status} ({timing}) via {provider}")
                    print(f"    Verification: {verification}")
                    if result.tracking_id:
                        print(f"    Tracking ID: {result.tracking_id}")
                    if not result.success and result.error_message:
                        print(f"    Error: {result.error_message}")
                elif "error" in test:
                    print(f"  {user_email}: ❌ ERROR - {test['error']}")
            
            # Display provider performance
            provider_performance = email_results.get("provider_performance", {})
            if provider_performance:
                print(f"\n📈 Email Provider Performance:")
                for provider, stats in provider_performance.items():
                    success_rate = stats.get("success_rate", 0)
                    avg_time = stats.get("average_delivery_time", 0)
                    total_attempts = stats.get("total_attempts", 0)
                    
                    print(f"  {provider.upper()}:")
                    print(f"    Success rate: {success_rate:.2%} ({stats.get('successful_deliveries', 0)}/{total_attempts})")
                    print(f"    Average delivery time: {avg_time:.3f}s")
                    print(f"    Max delivery time: {stats.get('max_delivery_time', 0):.3f}s")
            
            # Display delivery timing metrics
            delivery_timing = email_results.get("delivery_timing", {})
            if delivery_timing:
                print(f"\n⏱️ Overall Email Delivery Timing:")
                print(f"  Total emails sent: {delivery_timing.get('total_emails_sent', 0)}")
                print(f"  Successful deliveries: {delivery_timing.get('successful_deliveries', 0)}")
                print(f"  Success rate: {delivery_timing.get('delivery_success_rate', 0):.2%}")
                print(f"  Average delivery time: {delivery_timing.get('average_delivery_time', 0):.3f}s")
        
        print()
        
        # Test in-app notification checking
        print("📱 Testing In-App Notification Checking...")
        print("-" * 50)
        
        in_app_results = await framework.test_in_app_notification_checking()
        
        if "error" in in_app_results:
            print(f"❌ In-app notification test failed: {in_app_results['error']}")
        else:
            notification_tests = in_app_results.get("notification_tests", [])
            print(f"📊 In-App Notification Test Results ({len(notification_tests)} users):")
            
            for test in notification_tests:
                username = test.get("username", "Unknown")
                if test.get("skipped"):
                    print(f"  {username}: ⏭️ SKIPPED - {test.get('reason', 'Unknown reason')}")
                elif "result" in test:
                    result = test["result"]
                    status = "✅ SUCCESS" if result.success else "❌ FAILED"
                    timing = f"{result.delivery_time:.3f}s"
                    display_ok = "📱 DISPLAYED" if result.display_verification else "❌ NOT DISPLAYED"
                    read_status = "👁️ READ" if result.read_status else "📬 UNREAD"
                    
                    print(f"  {username}: {status} ({timing}) {display_ok} {read_status}")
                    if result.notification_id:
                        print(f"    Notification ID: {result.notification_id}")
                    if not result.success and result.error_message:
                        print(f"    Error: {result.error_message}")
                elif "error" in test:
                    print(f"  {username}: ❌ ERROR - {test['error']}")
            
            # Display system test results
            display_verification = in_app_results.get("display_verification", {})
            if display_verification:
                print(f"\n📱 In-App Notification System Tests:")
                for test_name, test_result in display_verification.items():
                    if test_result.get("tested", False):
                        success_rate = test_result.get("success_rate", 0)
                        status = "✅" if success_rate >= 0.9 else "⚠️" if success_rate >= 0.7 else "❌"
                        print(f"  {test_name.replace('_', ' ').title()}: {status} {success_rate:.2%}")
                    else:
                        reason = test_result.get("reason", "Not tested")
                        print(f"  {test_name.replace('_', ' ').title()}: ⏭️ SKIPPED - {reason}")
        
        print()
        
        # Test deadline reminder testing
        print("⏰ Testing Deadline Reminder System...")
        print("-" * 50)
        
        deadline_results = await framework.test_deadline_reminder_testing()
        
        if "error" in deadline_results:
            print(f"❌ Deadline reminder test failed: {deadline_results['error']}")
        else:
            reminder_tests = deadline_results.get("reminder_tests", [])
            print(f"📊 Deadline Reminder Test Results ({len(reminder_tests)} applications):")
            
            for test in reminder_tests:
                app_id = test.get("application_id", "Unknown")
                user_id = test.get("user_id", "Unknown")
                
                if test.get("skipped"):
                    print(f"  App {app_id} (User {user_id}): ⏭️ SKIPPED - {test.get('reason', 'Unknown reason')}")
                elif "result" in test:
                    result = test["result"]
                    status = "✅ SUCCESS" if result.success else "❌ FAILED"
                    hours_before = result.hours_before_deadline
                    channels = ", ".join(result.notification_channels) if result.notification_channels else "none"
                    
                    print(f"  App {app_id} (User {user_id}): {status}")
                    print(f"    Hours before deadline: {hours_before:.1f}")
                    print(f"    Notification channels: {channels}")
                    print(f"    Deadline: {result.deadline_date.strftime('%Y-%m-%d %H:%M')}")
                    
                    # Show timing verification
                    if "timing_verification" in test:
                        timing = test["timing_verification"]
                        timing_ok = "⏱️ ON TIME" if timing.get("timing_accurate", False) else "⏰ OFF TIME"
                        deviation = timing.get("timing_deviation", 0)
                        print(f"    Timing: {timing_ok} (deviation: {deviation:.1f}h)")
                    
                    if not result.success and result.error_message:
                        print(f"    Error: {result.error_message}")
                elif "error" in test:
                    print(f"  App {app_id} (User {user_id}): ❌ ERROR - {test['error']}")
            
            # Display timing accuracy analysis
            timing_accuracy = deadline_results.get("timing_accuracy", {})
            if timing_accuracy:
                print(f"\n⏱️ Deadline Reminder Timing Analysis:")
                print(f"  Total tests: {timing_accuracy.get('total_tests', 0)}")
                print(f"  Successful tests: {timing_accuracy.get('successful_tests', 0)}")
                print(f"  Accurate timing: {timing_accuracy.get('accurate_timing_count', 0)}")
                print(f"  Timing accuracy rate: {timing_accuracy.get('timing_accuracy_rate', 0):.2%}")
                print(f"  Average deviation: {timing_accuracy.get('average_timing_deviation', 0):.1f} hours")
                print(f"  Max deviation: {timing_accuracy.get('max_timing_deviation', 0):.1f} hours")
            
            # Display notification channel tests
            notification_channels = deadline_results.get("notification_channels", {})
            if notification_channels:
                print(f"\n📢 Notification Channel Performance:")
                for channel, stats in notification_channels.items():
                    success_rate = stats.get("success_rate", 0)
                    avg_time = stats.get("average_delivery_time", 0)
                    features = ", ".join(stats.get("features", []))
                    
                    print(f"  {channel.replace('_', ' ').title()}:")
                    print(f"    Success rate: {success_rate:.2%}")
                    print(f"    Average delivery time: {avg_time:.1f}s")
                    print(f"    Features: {features}")
            
            # Display deadline scenario tests
            deadline_scenarios = deadline_results.get("deadline_scenarios", {})
            if deadline_scenarios:
                print(f"\n📅 Deadline Scenario Tests:")
                for scenario, result in deadline_scenarios.items():
                    should_trigger = result.get("should_trigger", False)
                    success_rate = result.get("success_rate", 0)
                    trigger_text = "SHOULD trigger" if should_trigger else "should NOT trigger"
                    status = "✅" if success_rate >= 0.9 else "⚠️" if success_rate >= 0.7 else "❌"
                    
                    print(f"  {scenario.replace('_', ' ').title()}: {status} {success_rate:.2%} ({trigger_text})")
        
        print()
        
        # Run comprehensive test
        print("🔍 Running Comprehensive Delivery Verification Test...")
        print("-" * 50)
        
        comprehensive_results = await framework.run_comprehensive_delivery_verification_test()
        
        if "error" in comprehensive_results:
            print(f"❌ Comprehensive test failed: {comprehensive_results['error']}")
        else:
            summary = comprehensive_results.get("test_summary", {})
            print(f"📋 Test Summary:")
            print(f"  Total execution time: {summary.get('total_execution_time', 0):.2f}s")
            print(f"  Test users created: {summary.get('test_users_created', 0)}")
            print(f"  Test applications created: {summary.get('test_applications_created', 0)}")
            print(f"  Overall success: {'✅ PASSED' if summary.get('overall_success', False) else '❌ FAILED'}")
            
            # Display requirements validation
            req_validation = comprehensive_results.get("requirements_validation", {})
            print(f"\n📋 Requirements Validation:")
            
            for req_id, validation in req_validation.items():
                req_name = {
                    "req_6_4_deadline_reminders": "6.4 Deadline Reminder Notifications (24h advance)"
                }.get(req_id, req_id)
                
                if validation.get("validated", False):
                    compliance = validation.get("compliance_status", "PASSED")
                    print(f"  ✅ {req_name}: {compliance}")
                    if "timing_accuracy_rate" in validation:
                        print(f"     Timing accuracy: {validation['timing_accuracy_rate']:.2%}")
                    if "average_timing_deviation" in validation:
                        print(f"     Average deviation: {validation['average_timing_deviation']:.1f} hours")
                else:
                    compliance = validation.get("compliance_status", "FAILED")
                    print(f"  ❌ {req_name}: {compliance}")
                    if "error" in validation:
                        print(f"     Error: {validation['error']}")
        
        print()
        print("🎉 Notification delivery verification demo completed!")
        
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
    asyncio.run(demo_notification_delivery_verification())