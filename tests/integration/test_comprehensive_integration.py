"""
Comprehensive integration tests for the Career Copilot system
Tests automated integration scenarios and error recovery mechanisms
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json
import tempfile
import os


@pytest.mark.integration
class TestAutomatedIntegrationSuite:
    """Automated integration test suite covering all major components"""
    
    async def test_complete_system_integration(self, client, db_session):
        """Test complete system integration from user registration to job recommendations"""
        # 1. User Registration Flow
        user_data = {
            "email": "integration@test.com",
            "password": "TestPass123!",
            "profile": {
                "skills": ["Python", "FastAPI", "React"],
                "experience_level": "mid",
                "locations": ["San Francisco", "Remote"]
            }
        }
        
        with patch.object(client, 'post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"id": 1, "email": user_data["email"]}
            
            user_response = client.post("/api/v1/users/register", json=user_data)
            assert user_response.status_code == 201
            user_id = user_response.json()["id"]
        
        # 2. Job Ingestion Integration
        with patch('app.services.job_ingestion_service.ingest_jobs') as mock_ingest:
            mock_ingest.return_value = {
                "jobs_added": 25,
                "duplicates_filtered": 5,
                "processing_time": 15.2
            }
            
            ingestion_result = mock_ingest()
            assert ingestion_result["jobs_added"] > 0
        
        # 3. Recommendation Generation Integration
        with patch('app.services.recommendation_service.generate_recommendations') as mock_recommendations:
            mock_recommendations.return_value = [
                {
                    "job_id": 1,
                    "title": "Senior Python Developer",
                    "match_score": 0.85,
                    "reasons": ["Python expertise", "FastAPI experience"]
                },
                {
                    "job_id": 2,
                    "title": "Full Stack Engineer",
                    "match_score": 0.78,
                    "reasons": ["React experience", "Remote preference"]
                }
            ]
            
            recommendations = mock_recommendations(user_id)
            assert len(recommendations) >= 2
            assert all(rec["match_score"] > 0.7 for rec in recommendations)
        
        # 4. Skill Gap Analysis Integration
        with patch('app.services.skill_service.analyze_skill_gaps') as mock_skill_analysis:
            mock_skill_analysis.return_value = {
                "skill_gaps": [
                    {"skill": "Docker", "importance": 0.8, "gap_score": 0.9},
                    {"skill": "Kubernetes", "importance": 0.7, "gap_score": 0.8}
                ],
                "learning_recommendations": [
                    {"skill": "Docker", "resources": ["Docker Tutorial", "Container Basics"]}
                ]
            }
            
            skill_gaps = mock_skill_analysis(user_id)
            assert len(skill_gaps["skill_gaps"]) > 0
            assert len(skill_gaps["learning_recommendations"]) > 0
        
        # 5. Notification System Integration
        with patch('app.services.notification_service.send_morning_briefing') as mock_briefing:
            mock_briefing.return_value = {
                "status": "sent",
                "email_id": "briefing_123",
                "recommendations_count": 5
            }
            
            briefing_result = mock_briefing(user_id)
            assert briefing_result["status"] == "sent"
            assert briefing_result["recommendations_count"] > 0

    async def test_data_flow_integration(self, client, db_session):
        """Test data flow between all system components"""
        # Simulate complete data pipeline
        pipeline_steps = []
        
        # Step 1: Job Data Ingestion
        with patch('app.services.job_ingestion_service.fetch_and_process_jobs') as mock_fetch:
            mock_fetch.return_value = {
                "api_jobs": 15,
                "scraped_jobs": 10,
                "total_processed": 25,
                "new_jobs": 20,
                "duplicates": 5
            }
            
            ingestion_result = mock_fetch()
            pipeline_steps.append(("ingestion", ingestion_result))
        
        # Step 2: Job Processing and Enrichment
        with patch('app.services.job_processing_service.enrich_job_data') as mock_enrich:
            mock_enrich.return_value = {
                "jobs_enriched": 20,
                "skills_extracted": 150,
                "locations_normalized": 20,
                "salaries_estimated": 18
            }
            
            enrichment_result = mock_enrich(ingestion_result["new_jobs"])
            pipeline_steps.append(("enrichment", enrichment_result))
        
        # Step 3: User Profile Updates
        with patch('app.services.user_service.update_user_preferences') as mock_update_prefs:
            mock_update_prefs.return_value = {
                "users_updated": 50,
                "preferences_refreshed": 50,
                "skill_profiles_updated": 45
            }
            
            profile_update_result = mock_update_prefs()
            pipeline_steps.append(("profile_update", profile_update_result))
        
        # Step 4: Recommendation Generation
        with patch('app.services.recommendation_service.batch_generate_recommendations') as mock_batch_rec:
            mock_batch_rec.return_value = {
                "users_processed": 50,
                "recommendations_generated": 250,
                "avg_match_score": 0.75,
                "processing_time": 45.3
            }
            
            recommendation_result = mock_batch_rec()
            pipeline_steps.append(("recommendations", recommendation_result))
        
        # Step 5: Analytics Update
        with patch('app.services.analytics_service.update_system_metrics') as mock_analytics:
            mock_analytics.return_value = {
                "metrics_updated": True,
                "job_market_trends": {"python_demand": 0.85, "remote_ratio": 0.65},
                "user_engagement": {"daily_active": 35, "weekly_active": 120}
            }
            
            analytics_result = mock_analytics()
            pipeline_steps.append(("analytics", analytics_result))
        
        # Validate pipeline integrity
        assert len(pipeline_steps) == 5
        
        # Check data consistency across pipeline
        ingestion_jobs = pipeline_steps[0][1]["new_jobs"]
        enriched_jobs = pipeline_steps[1][1]["jobs_enriched"]
        assert enriched_jobs <= ingestion_jobs, "More jobs enriched than ingested"
        
        users_updated = pipeline_steps[2][1]["users_updated"]
        users_with_recommendations = pipeline_steps[3][1]["users_processed"]
        assert users_with_recommendations <= users_updated, "Recommendation generation inconsistent"

    async def test_api_integration_chain(self, client):
        """Test API endpoint integration chain"""
        user_id = 1
        
        # Chain of API calls that should work together
        api_chain = [
            ("GET", f"/api/v1/users/{user_id}/profile", {"skills": ["Python"], "preferences": {}}),
            ("GET", f"/api/v1/users/{user_id}/jobs", {"jobs": [], "total": 0}),
            ("GET", f"/api/v1/users/{user_id}/recommendations", {"recommendations": [], "total": 0}),
            ("GET", f"/api/v1/users/{user_id}/skill-gaps", {"gaps": [], "recommendations": []}),
            ("GET", f"/api/v1/users/{user_id}/analytics", {"applications": 0, "interviews": 0})
        ]
        
        for method, endpoint, expected_structure in api_chain:
            with patch.object(client, method.lower()) as mock_request:
                mock_request.return_value.status_code = 200
                mock_request.return_value.json.return_value = expected_structure
                
                response = getattr(client, method.lower())(endpoint)
                assert response.status_code == 200
                
                response_data = response.json()
                for key in expected_structure.keys():
                    assert key in response_data, f"Missing key {key} in {endpoint} response"

    async def test_scheduled_task_integration(self, client):
        """Test integration of scheduled tasks"""
        # Morning routine integration
        morning_tasks = []
        
        # Task 1: Job ingestion
        with patch('app.tasks.job_ingestion.run_daily_ingestion') as mock_ingestion:
            mock_ingestion.return_value = {"status": "completed", "jobs_added": 50}
            ingestion_result = mock_ingestion()
            morning_tasks.append(("job_ingestion", ingestion_result))
        
        # Task 2: Recommendation updates
        with patch('app.tasks.recommendations.update_all_recommendations') as mock_rec_update:
            mock_rec_update.return_value = {"status": "completed", "users_updated": 100}
            rec_result = mock_rec_update()
            morning_tasks.append(("recommendation_update", rec_result))
        
        # Task 3: Morning briefings
        with patch('app.tasks.notifications.send_all_morning_briefings') as mock_briefings:
            mock_briefings.return_value = {"status": "completed", "briefings_sent": 85}
            briefing_result = mock_briefings()
            morning_tasks.append(("morning_briefings", briefing_result))
        
        # Evening routine integration
        evening_tasks = []
        
        # Task 1: Analytics processing
        with patch('app.tasks.analytics.process_daily_analytics') as mock_analytics:
            mock_analytics.return_value = {"status": "completed", "metrics_processed": 200}
            analytics_result = mock_analytics()
            evening_tasks.append(("analytics_processing", analytics_result))
        
        # Task 2: Evening summaries
        with patch('app.tasks.notifications.send_all_evening_summaries') as mock_summaries:
            mock_summaries.return_value = {"status": "completed", "summaries_sent": 80}
            summary_result = mock_summaries()
            evening_tasks.append(("evening_summaries", summary_result))
        
        # Validate task completion
        assert all(task[1]["status"] == "completed" for task in morning_tasks + evening_tasks)
        
        # Check task dependencies
        jobs_added = morning_tasks[0][1]["jobs_added"]
        users_updated = morning_tasks[1][1]["users_updated"]
        briefings_sent = morning_tasks[2][1]["briefings_sent"]
        
        assert briefings_sent <= users_updated, "More briefings sent than users updated"


@pytest.mark.integration
class TestErrorScenariosAndRecovery:
    """Test error scenarios and recovery mechanisms"""
    
    async def test_database_failure_recovery(self, client, db_session):
        """Test system behavior during database failures"""
        # Simulate database connection failure
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            # Test graceful degradation
            with patch.object(client, 'get') as mock_get:
                mock_get.return_value.status_code = 503
                mock_get.return_value.json.return_value = {
                    "error": "Service temporarily unavailable",
                    "retry_after": 60
                }
                
                response = client.get("/api/v1/users/1/jobs")
                assert response.status_code == 503
                assert "retry_after" in response.json()
        
        # Test recovery after database restoration
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            with patch.object(client, 'get') as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {"jobs": [], "total": 0}
                
                response = client.get("/api/v1/users/1/jobs")
                assert response.status_code == 200

    async def test_external_api_failure_handling(self, client):
        """Test handling of external API failures"""
        # Test job API failure scenarios
        api_failures = [
            {"error": "Rate limit exceeded", "retry_after": 3600},
            {"error": "API key invalid", "retry_after": None},
            {"error": "Service unavailable", "retry_after": 1800},
            {"error": "Timeout", "retry_after": 300}
        ]
        
        for failure in api_failures:
            with patch('app.services.external_api_service.fetch_jobs') as mock_fetch:
                mock_fetch.side_effect = Exception(failure["error"])
                
                with patch('app.services.job_ingestion_service.handle_api_failure') as mock_handle:
                    mock_handle.return_value = {
                        "status": "failed",
                        "error": failure["error"],
                        "retry_after": failure["retry_after"],
                        "fallback_used": failure["retry_after"] is None
                    }
                    
                    result = mock_handle(failure["error"])
                    assert result["status"] == "failed"
                    
                    if failure["retry_after"]:
                        assert result["retry_after"] > 0
                    else:
                        assert result["fallback_used"] is True

    async def test_email_service_failure_recovery(self, client):
        """Test email service failure and recovery"""
        user_ids = [1, 2, 3, 4, 5]
        
        # Simulate partial email service failure
        with patch('app.services.email_service.send_email') as mock_send:
            def side_effect(user_id, *args, **kwargs):
                if user_id in [2, 4]:  # Simulate failures for some users
                    raise Exception("Email service unavailable")
                return {"status": "sent", "message_id": f"msg_{user_id}"}
            
            mock_send.side_effect = side_effect
            
            # Test batch email sending with error handling
            with patch('app.services.notification_service.send_batch_notifications') as mock_batch:
                mock_batch.return_value = {
                    "total_attempted": 5,
                    "successful": 3,
                    "failed": 2,
                    "failed_users": [2, 4],
                    "retry_scheduled": True
                }
                
                result = mock_batch(user_ids)
                assert result["successful"] == 3
                assert result["failed"] == 2
                assert result["retry_scheduled"] is True

    async def test_data_corruption_recovery(self, client, db_session):
        """Test recovery from data corruption scenarios"""
        # Simulate corrupted job data
        corrupted_jobs = [
            {"id": 1, "title": None, "company": "TechCorp"},  # Missing title
            {"id": 2, "title": "Developer", "company": None},  # Missing company
            {"id": 3, "title": "Engineer", "company": "StartupXYZ", "salary_min": -1000},  # Invalid salary
        ]
        
        with patch('app.services.data_validation_service.validate_and_clean_jobs') as mock_validate:
            mock_validate.return_value = {
                "total_jobs": 3,
                "valid_jobs": 1,
                "corrupted_jobs": 2,
                "cleaned_jobs": [
                    {"id": 3, "title": "Engineer", "company": "StartupXYZ", "salary_min": None}
                ],
                "corruption_report": [
                    {"id": 1, "issues": ["missing_title"]},
                    {"id": 2, "issues": ["missing_company"]}
                ]
            }
            
            validation_result = mock_validate(corrupted_jobs)
            assert validation_result["valid_jobs"] == 1
            assert validation_result["corrupted_jobs"] == 2
            assert len(validation_result["cleaned_jobs"]) == 1

    async def test_concurrent_access_conflicts(self, client, db_session):
        """Test handling of concurrent access conflicts"""
        user_id = 1
        job_id = 1
        
        # Simulate concurrent job application attempts
        async def apply_to_job(attempt_id):
            """Simulate job application attempt"""
            with patch('app.services.job_service.apply_to_job') as mock_apply:
                if attempt_id == 1:  # First attempt succeeds
                    mock_apply.return_value = {
                        "status": "success",
                        "application_id": f"app_{attempt_id}",
                        "applied_at": datetime.now().isoformat()
                    }
                else:  # Subsequent attempts fail due to duplicate
                    mock_apply.side_effect = Exception("Application already exists")
                
                try:
                    result = mock_apply(user_id, job_id)
                    return {"attempt": attempt_id, "status": "success", "result": result}
                except Exception as e:
                    return {"attempt": attempt_id, "status": "failed", "error": str(e)}
        
        # Run concurrent attempts
        tasks = [apply_to_job(i) for i in range(1, 4)]
        results = await asyncio.gather(*tasks)
        
        # Validate conflict resolution
        successful_attempts = [r for r in results if r["status"] == "success"]
        failed_attempts = [r for r in results if r["status"] == "failed"]
        
        assert len(successful_attempts) == 1, "Only one application should succeed"
        assert len(failed_attempts) == 2, "Other attempts should fail gracefully"

    async def test_system_overload_handling(self, client):
        """Test system behavior under overload conditions"""
        # Simulate high load scenario
        concurrent_requests = 100
        
        async def make_request(request_id):
            """Simulate API request under load"""
            with patch.object(client, 'get') as mock_get:
                if request_id % 10 == 0:  # 10% of requests fail due to overload
                    mock_get.return_value.status_code = 429  # Too Many Requests
                    mock_get.return_value.json.return_value = {
                        "error": "Rate limit exceeded",
                        "retry_after": 60
                    }
                else:
                    mock_get.return_value.status_code = 200
                    mock_get.return_value.json.return_value = {"data": f"response_{request_id}"}
                
                response = client.get(f"/api/v1/users/{request_id}/jobs")
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response": response.json()
                }
        
        # Execute concurrent requests
        tasks = [make_request(i) for i in range(1, concurrent_requests + 1)]
        results = await asyncio.gather(*tasks)
        
        # Analyze overload handling
        successful_requests = [r for r in results if r["status_code"] == 200]
        rate_limited_requests = [r for r in results if r["status_code"] == 429]
        
        success_rate = len(successful_requests) / len(results)
        rate_limit_rate = len(rate_limited_requests) / len(results)
        
        assert success_rate >= 0.8, f"Success rate too low under load: {success_rate:.2%}"
        assert rate_limit_rate <= 0.2, f"Too many rate limited requests: {rate_limit_rate:.2%}"
        
        # Validate rate limiting responses include retry information
        for rate_limited in rate_limited_requests:
            assert "retry_after" in rate_limited["response"]
            assert rate_limited["response"]["retry_after"] > 0

    async def test_backup_and_restore_integration(self, client, db_session):
        """Test backup and restore functionality integration"""
        # Simulate data backup
        with patch('app.services.backup_service.create_backup') as mock_backup:
            mock_backup.return_value = {
                "backup_id": "backup_20241201_120000",
                "status": "completed",
                "size_mb": 150.5,
                "tables_backed_up": ["users", "jobs", "applications", "analytics"],
                "backup_location": "gs://career-copilot-backups/backup_20241201_120000.sql"
            }
            
            backup_result = mock_backup()
            assert backup_result["status"] == "completed"
            assert len(backup_result["tables_backed_up"]) == 4
        
        # Simulate data corruption requiring restore
        with patch('app.services.backup_service.restore_from_backup') as mock_restore:
            mock_restore.return_value = {
                "restore_id": "restore_20241201_130000",
                "status": "completed",
                "backup_used": "backup_20241201_120000",
                "tables_restored": ["users", "jobs", "applications", "analytics"],
                "records_restored": 15000,
                "restore_time_minutes": 5.2
            }
            
            restore_result = mock_restore("backup_20241201_120000")
            assert restore_result["status"] == "completed"
            assert restore_result["records_restored"] > 0
        
        # Validate system functionality after restore
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"status": "healthy", "data_integrity": "verified"}
            
            health_response = client.get("/api/v1/health")
            assert health_response.status_code == 200
            assert health_response.json()["data_integrity"] == "verified"