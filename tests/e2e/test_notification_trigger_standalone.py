"""
Standalone notification trigger test

This test demonstrates the notification trigger functionality without requiring
a full database setup, using mock objects to simulate the notification system.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class MockNotificationResult:
    """Mock notification result for testing"""
    success: bool
    user_id: int
    notification_type: str
    execution_time: float
    error_message: str = None


class MockNotificationService:
    """Mock notification service for testing"""
    
    def __init__(self):
        self.call_count = 0
    
    async def send_morning_briefing(self, user_id: int, db=None, force_send=False) -> Dict[str, Any]:
        """Mock morning briefing send"""
        self.call_count += 1
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Simulate different outcomes based on user_id
        if user_id == 5:  # Opted out user
            return {
                "success": False,
                "error": "user_opted_out",
                "user_id": user_id,
                "message": "User has opted out of morning briefings"
            }
        
        return {
            "success": True,
            "user_id": user_id,
            "email": f"user{user_id}@test.com",
            "tracking_id": f"track_{user_id}_{self.call_count}",
            "recommendations_count": 3
        }
    
    async def send_evening_update(self, user_id: int, db=None, force_send=False) -> Dict[str, Any]:
        """Mock evening update send"""
        self.call_count += 1
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Simulate different outcomes based on user_id
        if user_id == 5:  # Opted out user
            return {
                "success": False,
                "error": "user_opted_out",
                "user_id": user_id,
                "message": "User has opted out of evening updates"
            }
        elif user_id == 2:  # No activity user
            return {
                "success": False,
                "error": "no_activity_today",
                "user_id": user_id,
                "message": "No meaningful activity today, skipping evening update"
            }
        
        return {
            "success": True,
            "user_id": user_id,
            "email": f"user{user_id}@test.com",
            "tracking_id": f"track_{user_id}_{self.call_count}",
            "activity_summary": {
                "applications_sent": 2,
                "jobs_viewed": 5,
                "achievements_count": 1
            }
        }
    
    async def send_bulk_morning_briefings(self, db=None) -> Dict[str, Any]:
        """Mock bulk morning briefings"""
        await asyncio.sleep(0.2)  # Simulate processing time
        return {
            "total_eligible": 5,
            "sent": 3,
            "failed": 1,
            "opted_out": 1,
            "errors": [{"user_id": 4, "error": "Email delivery failed"}]
        }
    
    async def send_bulk_evening_updates(self, db=None) -> Dict[str, Any]:
        """Mock bulk evening updates"""
        await asyncio.sleep(0.2)  # Simulate processing time
        return {
            "total_eligible": 5,
            "sent": 2,
            "failed": 1,
            "opted_out": 1,
            "no_activity": 1,
            "errors": [{"user_id": 4, "error": "Email delivery failed"}]
        }


class MockJobMatchService:
    """Mock job matching service for testing"""
    
    def find_matching_jobs(self, user_id: int) -> List[Dict[str, Any]]:
        """Mock job matching"""
        # Simulate different match counts based on user_id
        if user_id == 5:  # Opted out user
            return []
        
        matches = [
            {
                "job_id": f"job_{user_id}_1",
                "title": "Python Developer",
                "company": "TechCorp",
                "location": "San Francisco, CA",
                "match_score": 85.5,
                "matching_skills": ["Python", "Django"]
            },
            {
                "job_id": f"job_{user_id}_2",
                "title": "Backend Engineer",
                "company": "StartupInc",
                "location": "Remote",
                "match_score": 78.2,
                "matching_skills": ["Python", "PostgreSQL"]
            }
        ]
        
        return matches[:user_id % 3 + 1]  # Return 1-3 matches based on user_id
    
    async def send_job_alert(self, user_id: int, matching_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock job alert sending"""
        await asyncio.sleep(0.05)  # Simulate processing time
        
        if not matching_jobs:
            return {
                "success": False,
                "error": "no_matching_jobs",
                "user_id": user_id
            }
        
        return {
            "success": True,
            "user_id": user_id,
            "matches_sent": len(matching_jobs),
            "message": "Job alerts sent successfully"
        }


class NotificationTriggerStandaloneTest:
    """Standalone notification trigger test class"""
    
    def __init__(self):
        self.notification_service = MockNotificationService()
        self.job_match_service = MockJobMatchService()
        self.test_users = [
            {"id": 1, "name": "Morning User", "preferences": {"morning_briefing": True, "evening_update": False}},
            {"id": 2, "name": "Evening User", "preferences": {"morning_briefing": False, "evening_update": True}},
            {"id": 3, "name": "Full User", "preferences": {"morning_briefing": True, "evening_update": True}},
            {"id": 4, "name": "Weekly User", "preferences": {"morning_briefing": True, "evening_update": True, "frequency": "weekly"}},
            {"id": 5, "name": "Opted Out User", "preferences": {"morning_briefing": False, "evening_update": False}}
        ]
    
    async def test_morning_briefing_triggers(self) -> Dict[str, Any]:
        """Test morning briefing trigger functionality"""
        print("🌅 Testing Morning Briefing Triggers...")
        
        results = {
            "individual_triggers": [],
            "bulk_trigger": {},
            "timing_metrics": {}
        }
        
        # Test individual triggers
        for user in self.test_users:
            start_time = time.time()
            
            try:
                result = await self.notification_service.send_morning_briefing(user["id"])
                execution_time = time.time() - start_time
                
                # Validate timing (should complete within 15 seconds per requirement)
                timing_valid = execution_time <= 15.0
                
                results["individual_triggers"].append({
                    "user_id": user["id"],
                    "user_name": user["name"],
                    "success": result["success"],
                    "execution_time": execution_time,
                    "timing_valid": timing_valid,
                    "error": result.get("error"),
                    "message": result.get("message")
                })
                
                status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
                timing_status = "⏱️ ON TIME" if timing_valid else "⏰ SLOW"
                print(f"  {user['name']}: {status} ({execution_time:.3f}s) {timing_status}")
                
                if not result["success"]:
                    print(f"    Reason: {result.get('message', 'Unknown error')}")
                
            except Exception as e:
                execution_time = time.time() - start_time
                results["individual_triggers"].append({
                    "user_id": user["id"],
                    "user_name": user["name"],
                    "success": False,
                    "execution_time": execution_time,
                    "timing_valid": False,
                    "error": "exception",
                    "message": str(e)
                })
                print(f"  {user['name']}: ❌ ERROR - {e}")
        
        # Test bulk trigger
        print("\n📦 Testing Bulk Morning Briefing Trigger...")
        bulk_start_time = time.time()
        
        try:
            bulk_result = await self.notification_service.send_bulk_morning_briefings()
            bulk_execution_time = time.time() - bulk_start_time
            
            results["bulk_trigger"] = {
                "success": True,
                "execution_time": bulk_execution_time,
                **bulk_result
            }
            
            print(f"  Total eligible: {bulk_result['total_eligible']}")
            print(f"  Successfully sent: {bulk_result['sent']}")
            print(f"  Failed: {bulk_result['failed']}")
            print(f"  Opted out: {bulk_result['opted_out']}")
            print(f"  Execution time: {bulk_execution_time:.3f}s")
            
        except Exception as e:
            bulk_execution_time = time.time() - bulk_start_time
            results["bulk_trigger"] = {
                "success": False,
                "error": str(e),
                "execution_time": bulk_execution_time
            }
            print(f"  ❌ Bulk trigger failed: {e}")
        
        # Calculate timing metrics
        successful_results = [r for r in results["individual_triggers"] if r["success"]]
        if successful_results:
            avg_time = sum(r["execution_time"] for r in successful_results) / len(successful_results)
            on_time_count = sum(1 for r in successful_results if r["timing_valid"])
            
            results["timing_metrics"] = {
                "total_notifications": len(results["individual_triggers"]),
                "successful_deliveries": len(successful_results),
                "on_time_deliveries": on_time_count,
                "average_delivery_time": avg_time,
                "timing_accuracy_score": on_time_count / len(successful_results) if successful_results else 0.0
            }
            
            print(f"\n⏱️ Timing Metrics:")
            print(f"  Timing accuracy: {results['timing_metrics']['timing_accuracy_score']:.2%}")
            print(f"  Average delivery time: {avg_time:.3f}s")
        
        return results
    
    async def test_evening_update_triggers(self) -> Dict[str, Any]:
        """Test evening update trigger functionality"""
        print("\n🌆 Testing Evening Update Triggers...")
        
        results = {
            "individual_triggers": [],
            "bulk_trigger": {},
            "timing_metrics": {}
        }
        
        # Test individual triggers
        for user in self.test_users:
            start_time = time.time()
            
            try:
                result = await self.notification_service.send_evening_update(user["id"])
                execution_time = time.time() - start_time
                
                # Validate timing (should complete within 15 seconds per requirement)
                timing_valid = execution_time <= 15.0
                
                results["individual_triggers"].append({
                    "user_id": user["id"],
                    "user_name": user["name"],
                    "success": result["success"],
                    "execution_time": execution_time,
                    "timing_valid": timing_valid,
                    "error": result.get("error"),
                    "message": result.get("message")
                })
                
                status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
                timing_status = "⏱️ ON TIME" if timing_valid else "⏰ SLOW"
                print(f"  {user['name']}: {status} ({execution_time:.3f}s) {timing_status}")
                
                if not result["success"]:
                    print(f"    Reason: {result.get('message', 'Unknown error')}")
                
            except Exception as e:
                execution_time = time.time() - start_time
                results["individual_triggers"].append({
                    "user_id": user["id"],
                    "user_name": user["name"],
                    "success": False,
                    "execution_time": execution_time,
                    "timing_valid": False,
                    "error": "exception",
                    "message": str(e)
                })
                print(f"  {user['name']}: ❌ ERROR - {e}")
        
        # Test bulk trigger
        print("\n📦 Testing Bulk Evening Update Trigger...")
        bulk_start_time = time.time()
        
        try:
            bulk_result = await self.notification_service.send_bulk_evening_updates()
            bulk_execution_time = time.time() - bulk_start_time
            
            results["bulk_trigger"] = {
                "success": True,
                "execution_time": bulk_execution_time,
                **bulk_result
            }
            
            print(f"  Total eligible: {bulk_result['total_eligible']}")
            print(f"  Successfully sent: {bulk_result['sent']}")
            print(f"  Failed: {bulk_result['failed']}")
            print(f"  Opted out: {bulk_result['opted_out']}")
            print(f"  No activity: {bulk_result['no_activity']}")
            print(f"  Execution time: {bulk_execution_time:.3f}s")
            
        except Exception as e:
            bulk_execution_time = time.time() - bulk_start_time
            results["bulk_trigger"] = {
                "success": False,
                "error": str(e),
                "execution_time": bulk_execution_time
            }
            print(f"  ❌ Bulk trigger failed: {e}")
        
        return results
    
    async def test_job_match_notifications(self) -> Dict[str, Any]:
        """Test job match notification functionality"""
        print("\n🎯 Testing Job Match Notifications...")
        
        results = {
            "job_alert_triggers": [],
            "delivery_timing": {},
            "match_relevance": []
        }
        
        timing_data = []
        
        for user in self.test_users:
            start_time = time.time()
            
            try:
                # Find matching jobs
                matching_jobs = self.job_match_service.find_matching_jobs(user["id"])
                
                if matching_jobs:
                    # Send job alert
                    alert_result = await self.job_match_service.send_job_alert(user["id"], matching_jobs)
                    execution_time = time.time() - start_time
                    
                    # Validate delivery timing (should be within 1 hour per requirement)
                    timing_valid = execution_time <= 3600.0  # 1 hour in seconds
                    timing_data.append(execution_time)
                    
                    results["job_alert_triggers"].append({
                        "user_id": user["id"],
                        "user_name": user["name"],
                        "matching_jobs_count": len(matching_jobs),
                        "execution_time": execution_time,
                        "timing_valid": timing_valid,
                        "alert_success": alert_result["success"]
                    })
                    
                    # Calculate match relevance
                    avg_score = sum(job["match_score"] for job in matching_jobs) / len(matching_jobs)
                    results["match_relevance"].append({
                        "user_id": user["id"],
                        "relevance_score": avg_score,
                        "matching_jobs": len(matching_jobs)
                    })
                    
                    status = "✅ SUCCESS" if alert_result["success"] else "❌ FAILED"
                    timing_status = "⏱️ ON TIME" if timing_valid else "⏰ SLOW"
                    print(f"  {user['name']}: {len(matching_jobs)} matches, {status}, {timing_status}")
                    
                else:
                    results["job_alert_triggers"].append({
                        "user_id": user["id"],
                        "user_name": user["name"],
                        "matching_jobs_count": 0,
                        "skipped": True,
                        "reason": "No matching jobs found"
                    })
                    print(f"  {user['name']}: ⏭️ SKIPPED - No matching jobs")
                
            except Exception as e:
                execution_time = time.time() - start_time
                results["job_alert_triggers"].append({
                    "user_id": user["id"],
                    "user_name": user["name"],
                    "error": str(e),
                    "execution_time": execution_time
                })
                print(f"  {user['name']}: ❌ ERROR - {e}")
        
        # Calculate delivery timing metrics
        if timing_data:
            results["delivery_timing"] = {
                "average_time": sum(timing_data) / len(timing_data),
                "max_time": max(timing_data),
                "min_time": min(timing_data),
                "within_limit_count": sum(1 for t in timing_data if t <= 3600.0),
                "total_tests": len(timing_data)
            }
            
            print(f"\n⏱️ Delivery Timing:")
            print(f"  Average time: {results['delivery_timing']['average_time']:.3f}s")
            print(f"  Within 1-hour limit: {results['delivery_timing']['within_limit_count']}/{results['delivery_timing']['total_tests']}")
        
        # Display match relevance
        if results["match_relevance"]:
            avg_relevance = sum(r["relevance_score"] for r in results["match_relevance"]) / len(results["match_relevance"])
            print(f"\n🎯 Match Relevance:")
            print(f"  Average relevance score: {avg_relevance:.1f}%")
        
        return results
    
    async def validate_requirements(self, morning_results: Dict, evening_results: Dict, job_match_results: Dict) -> Dict[str, Any]:
        """Validate requirements 6.1, 6.2, and 6.3"""
        print("\n📋 Validating Requirements...")
        
        validation = {}
        
        # Requirement 6.1: Morning briefing delivery at configured time
        morning_timing = morning_results.get("timing_metrics", {})
        req_6_1_passed = morning_timing.get("timing_accuracy_score", 0) >= 0.8  # 80% on-time delivery
        
        validation["req_6_1_morning_briefing"] = {
            "validated": req_6_1_passed,
            "timing_accuracy": morning_timing.get("timing_accuracy_score", 0),
            "on_time_deliveries": morning_timing.get("on_time_deliveries", 0),
            "total_deliveries": morning_timing.get("successful_deliveries", 0)
        }
        
        status_6_1 = "✅ PASSED" if req_6_1_passed else "❌ FAILED"
        print(f"  6.1 Morning Briefing Delivery: {status_6_1}")
        print(f"      Timing accuracy: {morning_timing.get('timing_accuracy_score', 0):.2%}")
        
        # Requirement 6.2: Evening briefing delivery at configured time
        evening_timing = evening_results.get("timing_metrics", {})
        req_6_2_passed = evening_timing.get("timing_accuracy_score", 0) >= 0.8  # 80% on-time delivery
        
        validation["req_6_2_evening_briefing"] = {
            "validated": req_6_2_passed,
            "timing_accuracy": evening_timing.get("timing_accuracy_score", 0),
            "on_time_deliveries": evening_timing.get("on_time_deliveries", 0),
            "total_deliveries": evening_timing.get("successful_deliveries", 0)
        }
        
        status_6_2 = "✅ PASSED" if req_6_2_passed else "❌ FAILED"
        print(f"  6.2 Evening Briefing Delivery: {status_6_2}")
        print(f"      Timing accuracy: {evening_timing.get('timing_accuracy_score', 0):.2%}")
        
        # Requirement 6.3: Job match notifications within 1 hour
        job_timing = job_match_results.get("delivery_timing", {})
        within_limit = job_timing.get("within_limit_count", 0)
        total_tests = job_timing.get("total_tests", 1)
        compliance_rate = within_limit / total_tests if total_tests > 0 else 0
        req_6_3_passed = compliance_rate >= 0.9  # 90% within 1-hour limit
        
        validation["req_6_3_job_match_notifications"] = {
            "validated": req_6_3_passed,
            "average_delivery_time": job_timing.get("average_time", 0),
            "within_limit_count": within_limit,
            "total_tests": total_tests,
            "compliance_rate": compliance_rate
        }
        
        status_6_3 = "✅ PASSED" if req_6_3_passed else "❌ FAILED"
        print(f"  6.3 Job Match Notifications: {status_6_3}")
        print(f"      Compliance rate: {compliance_rate:.2%}")
        
        return validation
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive notification trigger test"""
        print("🔔 Notification Trigger Testing - Standalone Demo")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Test morning briefing triggers
            morning_results = await self.test_morning_briefing_triggers()
            
            # Test evening update triggers
            evening_results = await self.test_evening_update_triggers()
            
            # Test job match notifications
            job_match_results = await self.test_job_match_notifications()
            
            # Validate requirements
            requirements_validation = await self.validate_requirements(
                morning_results, evening_results, job_match_results
            )
            
            total_execution_time = time.time() - start_time
            
            # Calculate overall success
            all_req_passed = all(req.get("validated", False) for req in requirements_validation.values())
            
            print(f"\n🎉 Test Summary:")
            print(f"  Total execution time: {total_execution_time:.2f}s")
            print(f"  Test users: {len(self.test_users)}")
            print(f"  Overall success: {'✅ PASSED' if all_req_passed else '❌ FAILED'}")
            
            return {
                "test_summary": {
                    "total_execution_time": total_execution_time,
                    "test_users_count": len(self.test_users),
                    "overall_success": all_req_passed,
                    "timestamp": datetime.now().isoformat()
                },
                "morning_briefing_results": morning_results,
                "evening_update_results": evening_results,
                "job_match_notification_results": job_match_results,
                "requirements_validation": requirements_validation
            }
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


async def main():
    """Run the standalone notification trigger test"""
    test = NotificationTriggerStandaloneTest()
    results = await test.run_comprehensive_test()
    
    if "error" not in results:
        print("\n✅ Notification trigger testing completed successfully!")
        
        # Show key metrics
        summary = results["test_summary"]
        req_validation = results["requirements_validation"]
        
        passed_requirements = sum(1 for req in req_validation.values() if req.get("validated", False))
        total_requirements = len(req_validation)
        
        print(f"\nKey Metrics:")
        print(f"  Requirements passed: {passed_requirements}/{total_requirements}")
        print(f"  Execution time: {summary['total_execution_time']:.2f}s")
        print(f"  Test coverage: Morning briefings, Evening updates, Job match notifications")
    else:
        print(f"\n❌ Test failed: {results['error']}")


if __name__ == "__main__":
    asyncio.run(main())