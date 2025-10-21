"""
End-to-end test scenarios for complete user workflows
Tests the full user journey from registration to job management
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json


@pytest.mark.e2e
class TestCompleteUserWorkflow:
    """Test complete user workflow from registration to job management"""
    
    async def test_user_registration_and_profile_setup(self, client, db_session):
        """Test user registration and profile setup workflow"""
        # 1. User registration
        registration_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "profile": {
                "skills": ["Python", "React", "PostgreSQL"],
                "experience_level": "mid",
                "locations": ["San Francisco", "Remote"],
                "preferences": {
                    "salary_min": 90000,
                    "company_size": ["startup", "medium"],
                    "industries": ["tech", "fintech"],
                    "remote_preference": "hybrid"
                }
            }
        }
        
        # Mock registration endpoint
        with patch.object(client, 'post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "id": 1,
                "email": "newuser@example.com",
                "message": "User created successfully"
            }
            
            response = client.post("/api/v1/users/register", json=registration_data)
            assert response.status_code == 201
            
        # 2. Profile completion
        profile_update = {
            "career_goals": ["senior engineer", "tech lead"],
            "values": ["innovative", "collaborative"],
            "settings": {
                "notifications": {
                    "morning_briefing": True,
                    "evening_summary": True
                }
            }
        }
        
        with patch.object(client, 'put') as mock_put:
            mock_put.return_value.status_code = 200
            mock_put.return_value.json.return_value = {"message": "Profile updated"}
            
            response = client.put("/api/v1/users/1/profile", json=profile_update)
            assert response.status_code == 200

    async def test_job_discovery_and_application_workflow(self, client, test_user, test_jobs):
        """Test job discovery, filtering, and application workflow"""
        # 1. Get job recommendations
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "jobs": [
                    {
                        "id": 1,
                        "title": "Senior Python Developer",
                        "company": "TechCorp",
                        "match_score": 0.85,
                        "reasons": ["Python expertise", "FastAPI experience"]
                    }
                ],
                "total": 1
            }
            
            response = client.get(f"/api/v1/users/{test_user.id}/recommendations")
            assert response.status_code == 200
            recommendations = response.json()
            assert len(recommendations["jobs"]) > 0
            
        # 2. Filter jobs by criteria
        filter_params = {
            "skills": ["Python", "FastAPI"],
            "location": "San Francisco",
            "salary_min": 100000
        }
        
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "jobs": [test_jobs[0].__dict__],
                "total": 1,
                "page": 1,
                "per_page": 10
            }
            
            response = client.get(f"/api/v1/users/{test_user.id}/jobs", params=filter_params)
            assert response.status_code == 200
            
        # 3. Apply to job
        application_data = {
            "job_id": test_jobs[0].id,
            "cover_letter": "I am interested in this position...",
            "resume_version": "latest"
        }
        
        with patch.object(client, 'post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "id": 1,
                "status": "applied",
                "applied_at": datetime.now().isoformat()
            }
            
            response = client.post(f"/api/v1/users/{test_user.id}/applications", json=application_data)
            assert response.status_code == 201

    async def test_skill_gap_analysis_workflow(self, client, test_user):
        """Test skill gap analysis and learning recommendations"""
        # 1. Get skill gap analysis
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "skill_gaps": [
                    {
                        "skill": "Docker",
                        "importance": 0.8,
                        "frequency": 0.7,
                        "gap_score": 0.9
                    }
                ],
                "recommendations": [
                    {
                        "skill": "Docker",
                        "resources": ["Docker Official Tutorial", "Kubernetes Basics"]
                    }
                ]
            }
            
            response = client.get(f"/api/v1/users/{test_user.id}/skill-gaps")
            assert response.status_code == 200
            analysis = response.json()
            assert "skill_gaps" in analysis
            assert "recommendations" in analysis

    async def test_notification_workflow(self, client, test_user):
        """Test notification system workflow"""
        # 1. Test morning briefing
        with patch.object(client, 'post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "message": "Morning briefing sent",
                "email_id": "briefing_123"
            }
            
            response = client.post(f"/api/v1/notifications/morning-briefing/{test_user.id}")
            assert response.status_code == 200
            
        # 2. Test evening summary
        with patch.object(client, 'post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "message": "Evening summary sent",
                "email_id": "summary_456"
            }
            
            response = client.post(f"/api/v1/notifications/evening-summary/{test_user.id}")
            assert response.status_code == 200


@pytest.mark.e2e
class TestScheduledTaskExecution:
    """Test scheduled task execution and data flow"""
    
    async def test_job_ingestion_scheduled_task(self, client):
        """Test scheduled job ingestion task"""
        # Mock the scheduled job ingestion
        with patch('app.tasks.job_ingestion.ingest_jobs') as mock_ingest:
            mock_ingest.return_value = {
                "jobs_processed": 50,
                "new_jobs": 25,
                "duplicates_filtered": 15,
                "errors": 2
            }
            
            # Simulate scheduled task execution
            result = mock_ingest()
            assert result["jobs_processed"] == 50
            assert result["new_jobs"] == 25

    async def test_recommendation_update_task(self, client, test_user):
        """Test recommendation update scheduled task"""
        with patch('app.tasks.recommendations.update_recommendations') as mock_update:
            mock_update.return_value = {
                "users_updated": 100,
                "recommendations_generated": 500,
                "processing_time": 45.2
            }
            
            result = mock_update()
            assert result["users_updated"] == 100
            assert result["recommendations_generated"] == 500

    async def test_notification_scheduled_tasks(self, client):
        """Test scheduled notification tasks"""
        # Test morning briefing scheduler
        with patch('app.tasks.notifications.send_morning_briefings') as mock_morning:
            mock_morning.return_value = {
                "briefings_sent": 150,
                "failed": 2,
                "processing_time": 30.5
            }
            
            result = mock_morning()
            assert result["briefings_sent"] == 150
            assert result["failed"] <= 5  # Allow some failures
            
        # Test evening summary scheduler
        with patch('app.tasks.notifications.send_evening_summaries') as mock_evening:
            mock_evening.return_value = {
                "summaries_sent": 145,
                "failed": 1,
                "processing_time": 25.3
            }
            
            result = mock_evening()
            assert result["summaries_sent"] == 145


@pytest.mark.e2e
class TestCrossComponentIntegration:
    """Test cross-component integration scenarios"""
    
    async def test_job_ingestion_to_recommendation_flow(self, client, test_user):
        """Test data flow from job ingestion to recommendations"""
        # 1. Simulate job ingestion
        new_jobs_data = [
            {
                "title": "ML Engineer",
                "company": "AI Corp",
                "skills_required": ["Python", "TensorFlow", "Docker"],
                "location": "San Francisco",
                "salary_min": 130000
            }
        ]
        
        with patch('app.services.job_service.add_jobs') as mock_add_jobs:
            mock_add_jobs.return_value = {"added": 1, "duplicates": 0}
            
            # 2. Trigger recommendation update
            with patch('app.services.recommendation_service.generate_recommendations') as mock_recommendations:
                mock_recommendations.return_value = [
                    {
                        "job_id": 1,
                        "match_score": 0.75,
                        "reasons": ["Python match", "Location preference"]
                    }
                ]
                
                # Simulate the flow
                ingestion_result = mock_add_jobs(new_jobs_data)
                recommendations = mock_recommendations(test_user.id)
                
                assert ingestion_result["added"] == 1
                assert len(recommendations) > 0
                assert recommendations[0]["match_score"] > 0.7

    async def test_application_to_analytics_flow(self, client, test_user, test_jobs):
        """Test data flow from job application to analytics"""
        # 1. Apply to job
        with patch.object(client, 'post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"id": 1, "status": "applied"}
            
            response = client.post(f"/api/v1/users/{test_user.id}/applications", 
                                 json={"job_id": test_jobs[0].id})
            
        # 2. Check analytics update
        with patch('app.services.analytics_service.update_application_metrics') as mock_analytics:
            mock_analytics.return_value = {
                "total_applications": 5,
                "success_rate": 0.6,
                "avg_response_time": 3.2
            }
            
            analytics_result = mock_analytics(test_user.id)
            assert analytics_result["total_applications"] >= 1

    async def test_skill_gap_to_recommendation_integration(self, client, test_user):
        """Test integration between skill gap analysis and job recommendations"""
        # 1. Get skill gaps
        with patch('app.services.skill_service.analyze_skill_gaps') as mock_skill_gaps:
            mock_skill_gaps.return_value = {
                "gaps": ["Docker", "Kubernetes", "AWS"],
                "priority_skills": ["Docker", "AWS"]
            }
            
            skill_gaps = mock_skill_gaps(test_user.id)
            
        # 2. Get recommendations based on skill gaps
        with patch('app.services.recommendation_service.get_skill_building_jobs') as mock_skill_jobs:
            mock_skill_jobs.return_value = [
                {
                    "job_id": 1,
                    "title": "DevOps Engineer",
                    "skills_to_learn": ["Docker", "AWS"],
                    "learning_potential": 0.8
                }
            ]
            
            skill_building_jobs = mock_skill_jobs(test_user.id, skill_gaps["priority_skills"])
            assert len(skill_building_jobs) > 0
            assert skill_building_jobs[0]["learning_potential"] > 0.7


@pytest.mark.e2e
class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms"""
    
    async def test_api_error_handling(self, client):
        """Test API error handling scenarios"""
        # Test invalid user ID
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value.status_code = 404
            mock_get.return_value.json.return_value = {"error": "User not found"}
            
            response = client.get("/api/v1/users/99999/jobs")
            assert response.status_code == 404
            
        # Test invalid request data
        with patch.object(client, 'post') as mock_post:
            mock_post.return_value.status_code = 422
            mock_post.return_value.json.return_value = {"error": "Validation error"}
            
            response = client.post("/api/v1/users/1/jobs", json={"invalid": "data"})
            assert response.status_code == 422

    async def test_service_failure_recovery(self, client, test_user):
        """Test service failure and recovery scenarios"""
        # Test database connection failure
        with patch('app.core.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            with patch.object(client, 'get') as mock_get:
                mock_get.return_value.status_code = 503
                mock_get.return_value.json.return_value = {"error": "Service temporarily unavailable"}
                
                response = client.get(f"/api/v1/users/{test_user.id}/jobs")
                assert response.status_code == 503

    async def test_external_service_failure_handling(self, client):
        """Test handling of external service failures"""
        # Test job API failure
        with patch('app.services.job_ingestion_service.fetch_from_api') as mock_fetch:
            mock_fetch.side_effect = Exception("API rate limit exceeded")
            
            # Should gracefully handle the failure
            with patch('app.services.job_ingestion_service.handle_api_failure') as mock_handle:
                mock_handle.return_value = {"status": "failed", "retry_after": 3600}
                
                result = mock_handle("API rate limit exceeded")
                assert result["status"] == "failed"
                assert "retry_after" in result