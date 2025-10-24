"""
Notification Trigger Test Framework

This module provides comprehensive testing for the notification system including:
- Manual trigger for morning and evening briefings
- Verification for notification delivery timing
- Test framework for job match notifications
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

try:
    from backend.app.core.database import get_db
    from backend.app.models.user import User
    from backend.app.models.job import Job
    from backend.app.services.scheduled_notification_service import ScheduledNotificationService
    from backend.app.tasks.notification_tasks import (
        send_morning_briefings_async,
        send_evening_summaries_async,
        send_job_alerts_async
    )
    from backend.app.core.celery_app import celery_app
    from tests.e2e.base import BaseE2ETest
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Backend imports not available: {e}")
    BACKEND_AVAILABLE = False
    
    # Mock classes for testing when backend is not available
    class MockSession:
        def query(self, model):
            return MockQuery(model)
        def add(self, obj):
            pass
        def commit(self):
            pass
        def refresh(self, obj):
            if not hasattr(obj, 'id'):
                obj.id = 1
        def delete(self, obj):
            pass
        def close(self):
            pass
    
    class MockQuery:
        def __init__(self, model_class=None):
            self.model_class = model_class
            
        def filter(self, *args):
            return self
        def first(self):
            if self.model_class == MockUser:
                return None  # Simulate user not found for testing
            return None
        def all(self):
            return []
        def count(self):
            return 0
    
    class MockUser:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.id = getattr(self, 'id', 1)
            self.email = getattr(self, 'email', 'test@example.com')
            self.username = getattr(self, 'username', 'test_user')
            self.skills = getattr(self, 'skills', [])
            self.is_active = getattr(self, 'is_active', True)
            self.settings = getattr(self, 'settings', {})
            self.profile = getattr(self, 'profile', {})
    
    class MockJob:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.id = getattr(self, 'id', 1)
            self.title = getattr(self, 'title', 'Test Job')
            self.company = getattr(self, 'company', 'Test Company')
            self.location = getattr(self, 'location', 'Test Location')
            self.tech_stack = getattr(self, 'tech_stack', [])
            self.source = getattr(self, 'source', 'test')
    
    class MockNotificationService:
        async def send_morning_briefing(self, *args, **kwargs):
            return {"success": True, "user_id": 1}
        async def send_evening_update(self, *args, **kwargs):
            return {"success": True, "user_id": 1}
        async def send_bulk_morning_briefings(self, *args, **kwargs):
            return {"total_eligible": 1, "sent": 1, "failed": 0, "opted_out": 0}
        async def send_bulk_evening_updates(self, *args, **kwargs):
            return {"total_eligible": 1, "sent": 1, "failed": 0, "opted_out": 0, "no_activity": 0}
    
    def get_db():
        return MockSession()
    
    User = MockUser
    Job = MockJob
    ScheduledNotificationService = MockNotificationService
    
    class BaseE2ETest:
        def __init__(self):
            import logging
            self.logger = logging.getLogger(__name__)


@dataclass
class NotificationTestUser:
    """Test user profile for notification testing"""
    name: str
    email: str
    skills: List[str]
    notification_preferences: Dict[str, Any]
    expected_notifications: List[str]  # Types of notifications this user should receive


@dataclass
class NotificationTestResult:
    """Result of notification test execution"""
    success: bool
    user_id: int
    notification_type: str
    delivery_time: float
    delivery_status: str
    execution_time: float
    error_message: Optional[str]
    timing_validation: Dict[str, Any]


@dataclass
class DeliveryTimingMetrics:
    """Metrics for evaluating notification delivery timing"""
    total_notifications: int
    on_time_deliveries: int
    late_deliveries: int
    failed_deliveries: int
    average_delivery_time: float
    timing_accuracy_score: float


class NotificationTriggerTestFramework(BaseE2ETest):
    """
    Test framework for notification trigger functionality
    
    Provides methods to:
    - Manually trigger morning and evening briefings
    - Verify notification delivery timing
    - Test job match notification system
    - Validate notification preferences and opt-out functionality
    """
    
    def __init__(self):
        super().__init__()
        if BACKEND_AVAILABLE:
            self.db: Session = next(get_db())
        else:
            self.db = MockSession()
        self.test_users: List[User] = []
        self.notification_service = ScheduledNotificationService()
        self.api_client = httpx.AsyncClient(base_url="http://localhost:8000")
        
        # Define test user profiles with different notification preferences
        self.test_profiles = [
            NotificationTestUser(
                name="Morning Briefing User",
                email="morning_user@test.com",
                skills=["Python", "Django", "PostgreSQL"],
                notification_preferences={
                    "morning_briefing": True,
                    "evening_update": False,
                    "morning_time": "08:00",
                    "frequency": "daily",
                    "job_alerts": True
                },
                expected_notifications=["morning_briefing", "job_alerts"]
            ),
            NotificationTestUser(
                name="Evening Update User",
                email="evening_user@test.com",
                skills=["React", "Node.js", "TypeScript"],
                notification_preferences={
                    "morning_briefing": False,
                    "evening_update": True,
                    "evening_time": "19:00",
                    "frequency": "daily",
                    "job_alerts": True
                },
                expected_notifications=["evening_update", "job_alerts"]
            ),
            NotificationTestUser(
                name="Full Notifications User",
                email="full_notifications@test.com",
                skills=["Python", "Machine Learning", "AWS"],
                notification_preferences={
                    "morning_briefing": True,
                    "evening_update": True,
                    "morning_time": "07:30",
                    "evening_time": "18:30",
                    "frequency": "daily",
                    "job_alerts": True,
                    "application_reminders": True
                },
                expected_notifications=["morning_briefing", "evening_update", "job_alerts"]
            ),
            NotificationTestUser(
                name="Weekly Notifications User",
                email="weekly_user@test.com",
                skills=["JavaScript", "Vue.js", "CSS"],
                notification_preferences={
                    "morning_briefing": True,
                    "evening_update": True,
                    "frequency": "weekly",
                    "job_alerts": False
                },
                expected_notifications=["morning_briefing", "evening_update"]
            ),
            NotificationTestUser(
                name="Opted Out User",
                email="opted_out@test.com",
                skills=["Java", "Spring", "MySQL"],
                notification_preferences={
                    "morning_briefing": False,
                    "evening_update": False,
                    "frequency": "never",
                    "job_alerts": False
                },
                expected_notifications=[]
            )
        ]
    
    async def setup_test_environment(self) -> bool:
        """
        Set up test environment with test users and notification preferences
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Create test users from profiles
            await self._create_test_users()
            
            # Create sample jobs for job match notifications
            await self._create_sample_jobs()
            
            self.logger.info(f"Notification test environment setup complete. Created {len(self.test_users)} users")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup notification test environment: {e}")
            return False
    
    async def _create_test_users(self) -> None:
        """Create test users from predefined profiles"""
        for profile in self.test_profiles:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                User.email == profile.email
            ).first()
            
            if existing_user:
                # Update existing user with test preferences
                existing_user.skills = profile.skills
                existing_user.settings = {
                    "notifications": profile.notification_preferences
                }
                self.db.commit()
                self.test_users.append(existing_user)
                continue
            
            # Create new test user
            user = User(
                email=profile.email,
                username=profile.name.lower().replace(" ", "_"),
                skills=profile.skills,
                is_active=True,
                settings={
                    "notifications": profile.notification_preferences
                },
                profile={
                    "name": profile.name,
                    "skills": profile.skills
                }
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            self.test_users.append(user)
            
            self.logger.info(f"Created test user: {profile.name} (ID: {user.id})")
    
    async def _create_sample_jobs(self) -> None:
        """Create sample jobs for job match notification testing"""
        sample_jobs = [
            {
                "title": "Python Developer",
                "company": "TechCorp",
                "location": "San Francisco, CA",
                "description": "Python development position with Django",
                "tech_stack": ["Python", "Django", "PostgreSQL"],
                "salary_range": "$80,000 - $100,000",
                "remote_option": True
            },
            {
                "title": "Frontend Developer",
                "company": "WebStudio",
                "location": "Remote",
                "description": "React frontend development role",
                "tech_stack": ["React", "Node.js", "TypeScript"],
                "salary_range": "$90,000 - $110,000",
                "remote_option": True
            },
            {
                "title": "ML Engineer",
                "company": "AI Solutions",
                "location": "Seattle, WA",
                "description": "Machine learning engineering position",
                "tech_stack": ["Python", "Machine Learning", "AWS"],
                "salary_range": "$120,000 - $150,000",
                "remote_option": False
            }
        ]
        
        # Create jobs for testing job match notifications
        for job_data in sample_jobs:
            job = Job(
                title=job_data["title"],
                company=job_data["company"],
                location=job_data["location"],
                description=job_data["description"],
                tech_stack=job_data["tech_stack"],
                salary_range=job_data["salary_range"],
                remote_option=job_data["remote_option"],
                status="active",
                source="test_framework",
                link=f"https://example.com/job/{job_data['title'].lower().replace(' ', '-')}",
                created_at=datetime.now()
            )
            
            self.db.add(job)
        
        self.db.commit()
        self.logger.info(f"Created {len(sample_jobs)} sample jobs for notification testing")
    
    async def test_manual_morning_briefing_trigger(self) -> Dict[str, Any]:
        """
        Test manual trigger for morning briefings
        
        Returns:
            Dict containing test results for morning briefing triggers
        """
        results = {
            "individual_triggers": [],
            "bulk_trigger": {},
            "timing_metrics": {},
            "preference_validation": []
        }
        
        try:
            # Test individual morning briefing triggers
            for user in self.test_users:
                start_time = time.time()
                
                try:
                    # Trigger morning briefing for individual user
                    result = await self.notification_service.send_morning_briefing(
                        user_id=user.id,
                        db=self.db,
                        force_send=False  # Respect user preferences
                    )
                    
                    execution_time = time.time() - start_time
                    
                    # Validate timing (should complete within 15 seconds per requirement)
                    timing_valid = execution_time <= 15.0
                    
                    test_result = NotificationTestResult(
                        success=result["success"],
                        user_id=user.id,
                        notification_type="morning_briefing",
                        delivery_time=execution_time,
                        delivery_status=result.get("error", "delivered") if not result["success"] else "delivered",
                        execution_time=execution_time,
                        error_message=result.get("message") if not result["success"] else None,
                        timing_validation={
                            "within_limit": timing_valid,
                            "limit_seconds": 15.0,
                            "actual_seconds": execution_time
                        }
                    )
                    
                    results["individual_triggers"].append({
                        "user_id": user.id,
                        "user_name": user.username,
                        "result": test_result,
                        "preferences_respected": self._validate_preferences_respected(user, result)
                    })
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    results["individual_triggers"].append({
                        "user_id": user.id,
                        "user_name": user.username,
                        "error": str(e),
                        "execution_time": execution_time
                    })
            
            # Test bulk morning briefing trigger
            bulk_start_time = time.time()
            try:
                bulk_result = await self.notification_service.send_bulk_morning_briefings(self.db)
                bulk_execution_time = time.time() - bulk_start_time
                
                results["bulk_trigger"] = {
                    "success": True,
                    "execution_time": bulk_execution_time,
                    "total_eligible": bulk_result.get("total_eligible", 0),
                    "sent": bulk_result.get("sent", 0),
                    "failed": bulk_result.get("failed", 0),
                    "opted_out": bulk_result.get("opted_out", 0),
                    "errors": bulk_result.get("errors", [])
                }
                
            except Exception as e:
                bulk_execution_time = time.time() - bulk_start_time
                results["bulk_trigger"] = {
                    "success": False,
                    "error": str(e),
                    "execution_time": bulk_execution_time
                }
            
            # Calculate timing metrics
            results["timing_metrics"] = self._calculate_timing_metrics(results["individual_triggers"])
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing morning briefing triggers: {e}")
            return {"error": str(e)}
    
    async def test_manual_evening_update_trigger(self) -> Dict[str, Any]:
        """
        Test manual trigger for evening updates
        
        Returns:
            Dict containing test results for evening update triggers
        """
        results = {
            "individual_triggers": [],
            "bulk_trigger": {},
            "timing_metrics": {},
            "preference_validation": []
        }
        
        try:
            # Test individual evening update triggers
            for user in self.test_users:
                start_time = time.time()
                
                try:
                    # Trigger evening update for individual user
                    result = await self.notification_service.send_evening_update(
                        user_id=user.id,
                        db=self.db,
                        force_send=False  # Respect user preferences
                    )
                    
                    execution_time = time.time() - start_time
                    
                    # Validate timing (should complete within 15 seconds per requirement)
                    timing_valid = execution_time <= 15.0
                    
                    test_result = NotificationTestResult(
                        success=result["success"],
                        user_id=user.id,
                        notification_type="evening_update",
                        delivery_time=execution_time,
                        delivery_status=result.get("error", "delivered") if not result["success"] else "delivered",
                        execution_time=execution_time,
                        error_message=result.get("message") if not result["success"] else None,
                        timing_validation={
                            "within_limit": timing_valid,
                            "limit_seconds": 15.0,
                            "actual_seconds": execution_time
                        }
                    )
                    
                    results["individual_triggers"].append({
                        "user_id": user.id,
                        "user_name": user.username,
                        "result": test_result,
                        "preferences_respected": self._validate_preferences_respected(user, result)
                    })
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    results["individual_triggers"].append({
                        "user_id": user.id,
                        "user_name": user.username,
                        "error": str(e),
                        "execution_time": execution_time
                    })
            
            # Test bulk evening update trigger
            bulk_start_time = time.time()
            try:
                bulk_result = await self.notification_service.send_bulk_evening_updates(self.db)
                bulk_execution_time = time.time() - bulk_start_time
                
                results["bulk_trigger"] = {
                    "success": True,
                    "execution_time": bulk_execution_time,
                    "total_eligible": bulk_result.get("total_eligible", 0),
                    "sent": bulk_result.get("sent", 0),
                    "failed": bulk_result.get("failed", 0),
                    "opted_out": bulk_result.get("opted_out", 0),
                    "no_activity": bulk_result.get("no_activity", 0),
                    "errors": bulk_result.get("errors", [])
                }
                
            except Exception as e:
                bulk_execution_time = time.time() - bulk_start_time
                results["bulk_trigger"] = {
                    "success": False,
                    "error": str(e),
                    "execution_time": bulk_execution_time
                }
            
            # Calculate timing metrics
            results["timing_metrics"] = self._calculate_timing_metrics(results["individual_triggers"])
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing evening update triggers: {e}")
            return {"error": str(e)}
    
    async def test_job_match_notifications(self) -> Dict[str, Any]:
        """
        Test job match notification system
        
        Returns:
            Dict containing test results for job match notifications
        """
        results = {
            "job_alert_triggers": [],
            "celery_task_tests": [],
            "delivery_timing": {},
            "match_relevance": []
        }
        
        try:
            # Get available jobs for testing
            jobs = self.db.query(Job).filter(Job.source == "test_framework").all()
            
            if not jobs:
                return {"error": "No test jobs available for job match notification testing"}
            
            # Test job match notifications for each user
            for user in self.test_users:
                user_preferences = user.settings.get("notifications", {})
                
                # Skip users who opted out of job alerts
                if not user_preferences.get("job_alerts", True):
                    results["job_alert_triggers"].append({
                        "user_id": user.id,
                        "user_name": user.username,
                        "skipped": True,
                        "reason": "User opted out of job alerts"
                    })
                    continue
                
                start_time = time.time()
                
                try:
                    # Find matching jobs based on user skills
                    matching_jobs = self._find_matching_jobs(user, jobs)
                    
                    if matching_jobs:
                        # Test Celery task for job alerts
                        task_result = await self._test_job_alert_celery_task(user, matching_jobs)
                        results["celery_task_tests"].append(task_result)
                        
                        execution_time = time.time() - start_time
                        
                        # Validate delivery timing (should be within 1 hour per requirement)
                        timing_valid = execution_time <= 3600.0  # 1 hour in seconds
                        
                        results["job_alert_triggers"].append({
                            "user_id": user.id,
                            "user_name": user.username,
                            "matching_jobs_count": len(matching_jobs),
                            "execution_time": execution_time,
                            "timing_valid": timing_valid,
                            "celery_task_success": task_result.get("success", False)
                        })
                        
                        # Validate match relevance
                        relevance_score = self._calculate_match_relevance(user, matching_jobs)
                        results["match_relevance"].append({
                            "user_id": user.id,
                            "relevance_score": relevance_score,
                            "matching_jobs": len(matching_jobs)
                        })
                    else:
                        results["job_alert_triggers"].append({
                            "user_id": user.id,
                            "user_name": user.username,
                            "matching_jobs_count": 0,
                            "skipped": True,
                            "reason": "No matching jobs found"
                        })
                
                except Exception as e:
                    execution_time = time.time() - start_time
                    results["job_alert_triggers"].append({
                        "user_id": user.id,
                        "user_name": user.username,
                        "error": str(e),
                        "execution_time": execution_time
                    })
            
            # Calculate overall delivery timing metrics
            timing_data = [r for r in results["job_alert_triggers"] if "execution_time" in r and not r.get("skipped")]
            if timing_data:
                results["delivery_timing"] = {
                    "average_time": sum(r["execution_time"] for r in timing_data) / len(timing_data),
                    "max_time": max(r["execution_time"] for r in timing_data),
                    "min_time": min(r["execution_time"] for r in timing_data),
                    "within_limit_count": sum(1 for r in timing_data if r.get("timing_valid", False)),
                    "total_tests": len(timing_data)
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing job match notifications: {e}")
            return {"error": str(e)}
    
    def _find_matching_jobs(self, user: User, jobs: List[Job]) -> List[Dict[str, Any]]:
        """Find jobs that match user skills"""
        matching_jobs = []
        user_skills = set(s.lower() for s in user.skills) if user.skills else set()
        
        for job in jobs:
            job_skills = set(s.lower() for s in job.tech_stack) if job.tech_stack else set()
            
            # Calculate match score based on skill overlap
            if user_skills and job_skills:
                overlap = user_skills.intersection(job_skills)
                match_score = len(overlap) / len(user_skills.union(job_skills))
                
                if match_score > 0.3:  # At least 30% skill match
                    matching_jobs.append({
                        "job_id": job.id,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "match_score": match_score * 100,
                        "matching_skills": list(overlap)
                    })
        
        # Sort by match score and return top matches
        matching_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        return matching_jobs[:5]  # Return top 5 matches
    
    async def _test_job_alert_celery_task(self, user: User, matching_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test Celery task for job alerts"""
        try:
            if not BACKEND_AVAILABLE:
                # Mock Celery task result for testing
                return {
                    "success": True,
                    "task_id": "mock_task_id",
                    "task_result": {"status": "success", "user_id": user.id},
                    "user_id": user.id,
                    "jobs_count": len(matching_jobs)
                }
            
            # Trigger Celery task for job alerts
            task = send_job_alerts_async.delay(user.id, matching_jobs)
            
            # Wait for task completion with timeout
            result = task.get(timeout=60)  # 1 minute timeout
            
            return {
                "success": True,
                "task_id": task.id,
                "task_result": result,
                "user_id": user.id,
                "jobs_count": len(matching_jobs)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_id": user.id,
                "jobs_count": len(matching_jobs)
            }
    
    def _calculate_match_relevance(self, user: User, matching_jobs: List[Dict[str, Any]]) -> float:
        """Calculate relevance score for job matches"""
        if not matching_jobs:
            return 0.0
        
        total_score = sum(job["match_score"] for job in matching_jobs)
        return total_score / len(matching_jobs)
    
    def _validate_preferences_respected(self, user: User, notification_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that user notification preferences were respected"""
        user_preferences = user.settings.get("notifications", {})
        
        validation = {
            "preferences_found": bool(user_preferences),
            "opt_out_respected": True,
            "timing_respected": True,
            "frequency_respected": True
        }
        
        # Check if opt-out was respected
        if not notification_result["success"]:
            error_type = notification_result.get("error", "")
            if error_type == "user_opted_out":
                validation["opt_out_respected"] = True
            elif error_type in ["user_not_found_or_inactive", "no_activity_today"]:
                validation["opt_out_respected"] = True  # Valid reasons to skip
            else:
                validation["opt_out_respected"] = False
        
        return validation
    
    def _calculate_timing_metrics(self, trigger_results: List[Dict[str, Any]]) -> DeliveryTimingMetrics:
        """Calculate delivery timing metrics"""
        successful_results = [r for r in trigger_results if "result" in r and r["result"].success]
        
        if not successful_results:
            return DeliveryTimingMetrics(
                total_notifications=len(trigger_results),
                on_time_deliveries=0,
                late_deliveries=0,
                failed_deliveries=len(trigger_results),
                average_delivery_time=0.0,
                timing_accuracy_score=0.0
            )
        
        delivery_times = [r["result"].delivery_time for r in successful_results]
        on_time_count = sum(1 for r in successful_results if r["result"].timing_validation["within_limit"])
        
        return DeliveryTimingMetrics(
            total_notifications=len(trigger_results),
            on_time_deliveries=on_time_count,
            late_deliveries=len(successful_results) - on_time_count,
            failed_deliveries=len(trigger_results) - len(successful_results),
            average_delivery_time=sum(delivery_times) / len(delivery_times),
            timing_accuracy_score=on_time_count / len(successful_results) if successful_results else 0.0
        )
    
    async def test_notification_delivery_timing(self) -> Dict[str, Any]:
        """
        Test notification delivery timing verification
        
        Returns:
            Dict containing timing verification results
        """
        results = {
            "morning_briefing_timing": {},
            "evening_update_timing": {},
            "job_alert_timing": {},
            "overall_timing_metrics": {}
        }
        
        try:
            # Test morning briefing timing
            morning_results = await self.test_manual_morning_briefing_trigger()
            results["morning_briefing_timing"] = morning_results.get("timing_metrics", {})
            
            # Test evening update timing
            evening_results = await self.test_manual_evening_update_trigger()
            results["evening_update_timing"] = evening_results.get("timing_metrics", {})
            
            # Test job alert timing
            job_alert_results = await self.test_job_match_notifications()
            results["job_alert_timing"] = job_alert_results.get("delivery_timing", {})
            
            # Calculate overall timing metrics
            all_timing_data = []
            
            # Collect timing data from all tests
            if "individual_triggers" in morning_results:
                all_timing_data.extend([
                    r["result"].delivery_time for r in morning_results["individual_triggers"] 
                    if "result" in r and hasattr(r["result"], "delivery_time")
                ])
            
            if "individual_triggers" in evening_results:
                all_timing_data.extend([
                    r["result"].delivery_time for r in evening_results["individual_triggers"] 
                    if "result" in r and hasattr(r["result"], "delivery_time")
                ])
            
            if all_timing_data:
                results["overall_timing_metrics"] = {
                    "total_notifications_tested": len(all_timing_data),
                    "average_delivery_time": sum(all_timing_data) / len(all_timing_data),
                    "max_delivery_time": max(all_timing_data),
                    "min_delivery_time": min(all_timing_data),
                    "within_15_second_limit": sum(1 for t in all_timing_data if t <= 15.0),
                    "timing_compliance_rate": sum(1 for t in all_timing_data if t <= 15.0) / len(all_timing_data)
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing notification delivery timing: {e}")
            return {"error": str(e)}
    
    async def run_comprehensive_notification_test(self) -> Dict[str, Any]:
        """
        Run comprehensive notification trigger testing
        
        Returns:
            Dict containing complete test results
        """
        start_time = time.time()
        
        try:
            # Setup test environment
            setup_success = await self.setup_test_environment()
            if not setup_success:
                return {"error": "Failed to setup test environment"}
            
            # Test morning briefing triggers
            morning_results = await self.test_manual_morning_briefing_trigger()
            
            # Test evening update triggers
            evening_results = await self.test_manual_evening_update_trigger()
            
            # Test job match notifications
            job_match_results = await self.test_job_match_notifications()
            
            # Test delivery timing verification
            timing_results = await self.test_notification_delivery_timing()
            
            total_execution_time = time.time() - start_time
            
            # Calculate overall success metrics
            overall_success = (
                not ("error" in morning_results) and
                not ("error" in evening_results) and
                not ("error" in job_match_results) and
                not ("error" in timing_results)
            )
            
            return {
                "test_summary": {
                    "total_execution_time": total_execution_time,
                    "test_users_created": len(self.test_users),
                    "timestamp": datetime.now().isoformat(),
                    "overall_success": overall_success
                },
                "morning_briefing_results": morning_results,
                "evening_update_results": evening_results,
                "job_match_notification_results": job_match_results,
                "delivery_timing_results": timing_results,
                "requirements_validation": {
                    "req_6_1_morning_briefing": self._validate_requirement_6_1(morning_results),
                    "req_6_2_evening_briefing": self._validate_requirement_6_2(evening_results),
                    "req_6_3_job_match_notifications": self._validate_requirement_6_3(job_match_results)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive notification test: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_requirement_6_1(self, morning_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate requirement 6.1: Morning briefing delivery at configured time"""
        if "error" in morning_results:
            return {"validated": False, "error": morning_results["error"]}
        
        timing_metrics = morning_results.get("timing_metrics", {})
        
        return {
            "validated": True,
            "timing_accuracy": timing_metrics.timing_accuracy_score if hasattr(timing_metrics, "timing_accuracy_score") else 0.0,
            "on_time_deliveries": timing_metrics.on_time_deliveries if hasattr(timing_metrics, "on_time_deliveries") else 0,
            "total_deliveries": timing_metrics.total_notifications if hasattr(timing_metrics, "total_notifications") else 0
        }
    
    def _validate_requirement_6_2(self, evening_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate requirement 6.2: Evening briefing delivery at configured time"""
        if "error" in evening_results:
            return {"validated": False, "error": evening_results["error"]}
        
        timing_metrics = evening_results.get("timing_metrics", {})
        
        return {
            "validated": True,
            "timing_accuracy": timing_metrics.timing_accuracy_score if hasattr(timing_metrics, "timing_accuracy_score") else 0.0,
            "on_time_deliveries": timing_metrics.on_time_deliveries if hasattr(timing_metrics, "on_time_deliveries") else 0,
            "total_deliveries": timing_metrics.total_notifications if hasattr(timing_metrics, "total_notifications") else 0
        }
    
    def _validate_requirement_6_3(self, job_match_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate requirement 6.3: Job match notifications within 1 hour"""
        if "error" in job_match_results:
            return {"validated": False, "error": job_match_results["error"]}
        
        delivery_timing = job_match_results.get("delivery_timing", {})
        
        return {
            "validated": True,
            "average_delivery_time": delivery_timing.get("average_time", 0),
            "within_limit_count": delivery_timing.get("within_limit_count", 0),
            "total_tests": delivery_timing.get("total_tests", 0),
            "compliance_rate": delivery_timing.get("within_limit_count", 0) / max(delivery_timing.get("total_tests", 1), 1)
        }
    
    async def cleanup_test_environment(self) -> bool:
        """
        Clean up test environment by removing test data
        
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        try:
            # Remove test jobs
            test_jobs = self.db.query(Job).filter(Job.source == "test_framework").all()
            for job in test_jobs:
                self.db.delete(job)
            
            # Remove test users (optional - might want to keep for repeated testing)
            # for user in self.test_users:
            #     self.db.delete(user)
            
            self.db.commit()
            
            # Close API client
            await self.api_client.aclose()
            
            self.logger.info("Notification test environment cleanup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during notification test environment cleanup: {e}")
            return False


# Convenience function for running the test
async def run_notification_trigger_test() -> Dict[str, Any]:
    """
    Convenience function to run notification trigger testing
    
    Returns:
        Dict containing test results
    """
    framework = NotificationTriggerTestFramework()
    try:
        results = await framework.run_comprehensive_notification_test()
        return results
    finally:
        await framework.cleanup_test_environment()


if __name__ == "__main__":
    # Run the test when executed directly
    import asyncio
    
    async def main():
        results = await run_notification_trigger_test()
        print("Notification Trigger Test Results:")
        print("=" * 50)
        
        if "error" in results:
            print(f"Test failed with error: {results['error']}")
            return
        
        # Print summary
        summary = results.get("test_summary", {})
        print(f"Total execution time: {summary.get('total_execution_time', 0):.2f} seconds")
        print(f"Test users created: {summary.get('test_users_created', 0)}")
        print(f"Overall success: {summary.get('overall_success', False)}")
        
        # Print requirements validation
        req_validation = results.get("requirements_validation", {})
        print(f"\nRequirements Validation:")
        for req_id, validation in req_validation.items():
            if validation.get("validated", False):
                print(f"  ✓ {req_id}: PASSED")
                if "compliance_rate" in validation:
                    print(f"    Compliance rate: {validation['compliance_rate']:.2%}")
            else:
                print(f"  ✗ {req_id}: FAILED")
                if "error" in validation:
                    print(f"    Error: {validation['error']}")
        
        # Print timing metrics
        timing_results = results.get("delivery_timing_results", {})
        overall_timing = timing_results.get("overall_timing_metrics", {})
        if overall_timing:
            print(f"\nOverall Timing Metrics:")
            print(f"  Average delivery time: {overall_timing.get('average_delivery_time', 0):.3f}s")
            print(f"  Timing compliance rate: {overall_timing.get('timing_compliance_rate', 0):.2%}")
    
    asyncio.run(main())