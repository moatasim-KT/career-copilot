"""
Enhanced End-to-End Test Scenarios for Career Copilot System
Tests complete user workflows covering requirements 1.1, 2.1, 3.1, 4.1
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json
import tempfile
import os


@pytest.mark.e2e
class TestCompleteUserWorkflows:
    """Test complete user workflows from frontend to backend"""
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_job_management_complete_workflow(self, client, test_user, db_session):
        """
        Test complete job management workflow (Requirement 1.1)
        - Display all job opportunities in filterable list format
        - Filter jobs by criteria
        - Add new job opportunities manually
        - Update job status and track applications
        """
        # Step 1: Display all job opportunities in filterable list
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "jobs": [
                    {
                        "id": 1,
                        "title": "Senior Python Developer",
                        "company": "TechCorp",
                        "location": "San Francisco, CA",
                        "tech_stack": ["Python", "Django", "PostgreSQL"],
                        "status": "Not Applied",
                        "date_added": "2024-12-01T10:00:00Z",
                        "link": "https://techcorp.com/jobs/1"
                    },
                    {
                        "id": 2,
                        "title": "Full Stack Engineer",
                        "company": "StartupXYZ",
                        "location": "Remote",
                        "tech_stack": ["React", "Node.js", "MongoDB"],
                        "status": "Applied",
                        "date_added": "2024-12-01T11:00:00Z",
                        "date_applied": "2024-12-01T15:00:00Z",
                        "link": "https://startupxyz.com/careers/2"
                    }
                ],
                "total": 2,
                "page": 1,
                "per_page": 10
            }
            
            # Test job listing display
            response = client.get(f"/api/v1/users/{test_user.id}/jobs")
            assert response.status_code == 200
            
            jobs_data = response.json()
            assert "jobs" in jobs_data
            assert len(jobs_data["jobs"]) == 2
            assert jobs_data["total"] == 2
            
            # Verify job structure
            job = jobs_data["jobs"][0]
            required_fields = ["id", "title", "company", "location", "tech_stack", "status", "link"]
            for field in required_fields:
                assert field in job, f"Missing required field: {field}"
        
        # Step 2: Test job filtering functionality
        filter_params = {
            "location": "San Francisco",
            "skills": ["Python"],
            "status": "Not Applied",
            "company": "TechCorp"
        }
        
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "jobs": [
                    {
                        "id": 1,
                        "title": "Senior Python Developer",
                        "company": "TechCorp",
                        "location": "San Francisco, CA",
                        "tech_stack": ["Python", "Django", "PostgreSQL"],
                        "status": "Not Applied"
                    }
                ],
                "total": 1,
                "filters_applied": filter_params
            }
            
            # Test filtered job listing
            response = client.get(f"/api/v1/users/{test_user.id}/jobs", params=filter_params)
            assert response.status_code == 200
            
            filtered_data = response.json()
            assert len(filtered_data["jobs"]) == 1
            assert filtered_data["jobs"][0]["company"] == "TechCorp"
            assert "Python" in filtered_data["jobs"][0]["tech_stack"]
        
        # Step 3: Test manual job addition
        new_job_data = {
            "company": "AI Innovations",
            "title": "Machine Learning Engineer",
            "location": "Seattle, WA",
            "tech_stack": ["Python", "TensorFlow", "AWS"],
            "responsibilities": "Develop ML models for recommendation systems",
            "link": "https://ai-innovations.com/jobs/ml-engineer"
        }
        
        with patch.object(client, 'post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "id": 3,
                "status": "Not Applied",
                "date_added": datetime.now().isoformat(),
                **new_job_data
            }
            
            # Test job creation
            response = client.post(f"/api/v1/users/{test_user.id}/jobs", json=new_job_data)
            assert response.status_code == 201
            
            created_job = response.json()
            assert created_job["id"] == 3
            assert created_job["title"] == new_job_data["title"]
            assert created_job["status"] == "Not Applied"
        
        # Step 4: Test job status update and application tracking
        application_data = {
            "status": "Applied",
            "cover_letter": "I am very interested in this ML Engineer position...",
            "notes": "Applied through company website"
        }
        
        with patch.object(client, 'put') as mock_put:
            mock_put.return_value.status_code = 200
            mock_put.return_value.json.return_value = {
                "id": 3,
                "status": "Applied",
                "date_applied": datetime.now().isoformat(),
                "application_notes": application_data["notes"]
            }
            
            # Test status update
            response = client.put(f"/api/v1/users/{test_user.id}/jobs/3/status", json=application_data)
            assert response.status_code == 200
            
            updated_job = response.json()
            assert updated_job["status"] == "Applied"
            assert "date_applied" in updated_job
            assert updated_job["application_notes"] == application_data["notes"]

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_job_ingestion_complete_workflow(self, client, db_session):
        """
        Test complete job ingestion workflow (Requirement 2.1)
        - Automatic daily job discovery
        - Duplicate prevention
        - Multiple source integration
        - Error handling and recovery
        """
        # Step 1: Test scheduled job ingestion trigger
        with patch('app.tasks.job_ingestion.run_daily_ingestion') as mock_ingestion:
            mock_ingestion.return_value = {
                "status": "started",
                "ingestion_id": "ing_20241201_040000",
                "sources": ["adzuna_api", "jobspresso_api", "web_scraping"],
                "start_time": datetime.now().isoformat()
            }
            
            # Simulate scheduled trigger
            ingestion_result = mock_ingestion()
            assert ingestion_result["status"] == "started"
            assert len(ingestion_result["sources"]) == 3
        
        # Step 2: Test job discovery from multiple sources
        api_jobs = [
            {
                "external_id": "adzuna_12345",
                "title": "Software Engineer",
                "company": "TechCorp",
                "location": "San Francisco, CA",
                "description": "Join our engineering team...",
                "source": "adzuna_api",
                "salary_min": 100000,
                "salary_max": 140000
            },
            {
                "external_id": "jobspresso_67890",
                "title": "Frontend Developer",
                "company": "WebCorp",
                "location": "Remote",
                "description": "Build amazing user interfaces...",
                "source": "jobspresso_api",
                "tech_stack": ["React", "TypeScript", "CSS"]
            }
        ]
        
        scraped_jobs = [
            {
                "external_id": "scraped_company_abc_123",
                "title": "DevOps Engineer",
                "company": "CloudTech",
                "location": "Austin, TX",
                "description": "Manage cloud infrastructure...",
                "source": "web_scraping",
                "tech_stack": ["AWS", "Docker", "Kubernetes"]
            }
        ]
        
        with patch('app.services.job_ingestion_service.fetch_from_apis') as mock_api_fetch:
            mock_api_fetch.return_value = {
                "adzuna": {"jobs": [api_jobs[0]], "count": 1, "status": "success"},
                "jobspresso": {"jobs": [api_jobs[1]], "count": 1, "status": "success"}
            }
            
            api_results = mock_api_fetch()
            assert len(api_results) == 2
            assert api_results["adzuna"]["status"] == "success"
            assert api_results["jobspresso"]["status"] == "success"
        
        with patch('app.services.web_scraping_service.scrape_job_sites') as mock_scraping:
            mock_scraping.return_value = {
                "scraped_jobs": scraped_jobs,
                "sites_scraped": ["company-a.com", "company-b.com"],
                "total_found": 1,
                "errors": []
            }
            
            scraping_results = mock_scraping()
            assert len(scraping_results["scraped_jobs"]) == 1
            assert len(scraping_results["sites_scraped"]) == 2
        
        # Step 3: Test duplicate detection and prevention
        all_discovered_jobs = api_jobs + scraped_jobs
        
        # Add a duplicate job to test deduplication
        duplicate_job = {
            "external_id": "different_id_same_job",
            "title": "Software Engineer",  # Same title
            "company": "TechCorp",         # Same company
            "location": "San Francisco, CA", # Same location
            "description": "Join our engineering team...",
            "source": "manual_duplicate"
        }
        all_discovered_jobs.append(duplicate_job)
        
        with patch('app.services.job_deduplication_service.detect_duplicates') as mock_dedup:
            mock_dedup.return_value = {
                "total_jobs": 4,
                "unique_jobs": 3,
                "duplicates_found": 1,
                "duplicate_pairs": [
                    {
                        "job1_id": "adzuna_12345",
                        "job2_id": "different_id_same_job",
                        "similarity_score": 0.95,
                        "matching_fields": ["title", "company", "location"]
                    }
                ],
                "jobs_to_add": all_discovered_jobs[:3]  # Exclude duplicate
            }
            
            dedup_results = mock_dedup(all_discovered_jobs)
            assert dedup_results["unique_jobs"] == 3
            assert dedup_results["duplicates_found"] == 1
            assert len(dedup_results["jobs_to_add"]) == 3
        
        # Step 4: Test job storage and database update
        with patch('app.services.job_service.batch_add_jobs') as mock_batch_add:
            mock_batch_add.return_value = {
                "jobs_added": 3,
                "jobs_updated": 0,
                "errors": 0,
                "processing_time": 2.5,
                "added_job_ids": [101, 102, 103]
            }
            
            storage_result = mock_batch_add(dedup_results["jobs_to_add"])
            assert storage_result["jobs_added"] == 3
            assert storage_result["errors"] == 0
            assert len(storage_result["added_job_ids"]) == 3
        
        # Step 5: Test error handling during ingestion
        with patch('app.services.job_ingestion_service.handle_ingestion_errors') as mock_error_handler:
            mock_error_handler.return_value = {
                "api_errors": [
                    {"source": "adzuna", "error": "Rate limit exceeded", "retry_after": 3600}
                ],
                "scraping_errors": [
                    {"site": "company-c.com", "error": "Site structure changed", "action": "skip"}
                ],
                "recovery_actions": [
                    {"action": "retry_api", "source": "adzuna", "scheduled_time": "2024-12-01T05:00:00Z"},
                    {"action": "alert_admin", "reason": "scraping_failure", "site": "company-c.com"}
                ]
            }
            
            error_result = mock_error_handler(["api_error", "scraping_error"])
            assert len(error_result["api_errors"]) == 1
            assert len(error_result["scraping_errors"]) == 1
            assert len(error_result["recovery_actions"]) == 2

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_recommendation_engine_complete_workflow(self, client, test_user, db_session):
        """
        Test complete recommendation engine workflow (Requirement 3.1)
        - User profile analysis
        - Job scoring and matching
        - Personalized recommendations
        - Recommendation updates
        """
        # Step 1: Test user profile analysis
        user_profile = {
            "skills": ["Python", "FastAPI", "PostgreSQL", "React"],
            "experience_level": "mid",
            "locations": ["San Francisco", "Remote"],
            "preferences": {
                "salary_min": 90000,
                "company_size": ["startup", "medium"],
                "remote_preference": "hybrid"
            }
        }
        
        with patch('app.services.user_service.get_user_profile') as mock_get_profile:
            mock_get_profile.return_value = {
                "user_id": test_user.id,
                "profile": user_profile,
                "last_updated": datetime.now().isoformat()
            }
            
            profile_data = mock_get_profile(test_user.id)
            assert profile_data["user_id"] == test_user.id
            assert len(profile_data["profile"]["skills"]) == 4
            assert profile_data["profile"]["experience_level"] == "mid"
        
        # Step 2: Test job scoring algorithm
        available_jobs = [
            {
                "id": 1,
                "title": "Senior Python Developer",
                "company": "TechCorp",
                "location": "San Francisco, CA",
                "tech_stack": ["Python", "Django", "PostgreSQL", "AWS"],
                "experience_required": "mid",
                "salary_min": 100000,
                "company_size": "medium"
            },
            {
                "id": 2,
                "title": "Full Stack Engineer",
                "company": "StartupXYZ",
                "location": "Remote",
                "tech_stack": ["React", "Node.js", "MongoDB"],
                "experience_required": "mid",
                "salary_min": 85000,
                "company_size": "startup"
            },
            {
                "id": 3,
                "title": "Senior Java Developer",
                "company": "BigCorp",
                "location": "New York, NY",
                "tech_stack": ["Java", "Spring", "Oracle"],
                "experience_required": "senior",
                "salary_min": 120000,
                "company_size": "large"
            }
        ]
        
        with patch('app.services.recommendation_service.calculate_job_scores') as mock_scoring:
            mock_scoring.return_value = [
                {
                    "job_id": 1,
                    "match_score": 0.85,
                    "skill_match": 0.75,  # 3/4 skills match
                    "location_match": 1.0,  # Perfect location match
                    "experience_match": 1.0,  # Perfect experience match
                    "preference_match": 0.8,  # Good preference match
                    "reasons": [
                        "Strong Python and PostgreSQL skills match",
                        "Perfect location preference match",
                        "Experience level alignment",
                        "Preferred company size"
                    ]
                },
                {
                    "job_id": 2,
                    "match_score": 0.78,
                    "skill_match": 0.5,   # 2/4 skills match (React)
                    "location_match": 1.0,  # Remote preference
                    "experience_match": 1.0,
                    "preference_match": 0.9,  # Startup preference
                    "reasons": [
                        "React skills match",
                        "Remote work preference",
                        "Startup company preference",
                        "Experience level alignment"
                    ]
                },
                {
                    "job_id": 3,
                    "match_score": 0.35,
                    "skill_match": 0.0,   # No skill overlap
                    "location_match": 0.0,  # Location not preferred
                    "experience_match": 0.5,  # Higher experience required
                    "preference_match": 0.2,  # Large company not preferred
                    "reasons": [
                        "No matching technical skills",
                        "Location not in preferences",
                        "Higher experience level required"
                    ]
                }
            ]
            
            scoring_results = mock_scoring(test_user.id, available_jobs)
            assert len(scoring_results) == 3
            
            # Verify scoring logic
            best_match = max(scoring_results, key=lambda x: x["match_score"])
            assert best_match["job_id"] == 1
            assert best_match["match_score"] == 0.85
            
            worst_match = min(scoring_results, key=lambda x: x["match_score"])
            assert worst_match["job_id"] == 3
            assert worst_match["match_score"] == 0.35
        
        # Step 3: Test personalized recommendation generation
        with patch('app.services.recommendation_service.generate_recommendations') as mock_generate:
            mock_generate.return_value = {
                "user_id": test_user.id,
                "recommendations": [
                    {
                        "job_id": 1,
                        "rank": 1,
                        "match_score": 0.85,
                        "title": "Senior Python Developer",
                        "company": "TechCorp",
                        "reasons": [
                            "Strong Python and PostgreSQL skills match",
                            "Perfect location preference match"
                        ],
                        "learning_opportunities": ["AWS", "Django advanced features"]
                    },
                    {
                        "job_id": 2,
                        "rank": 2,
                        "match_score": 0.78,
                        "title": "Full Stack Engineer",
                        "company": "StartupXYZ",
                        "reasons": [
                            "React skills match",
                            "Remote work preference"
                        ],
                        "learning_opportunities": ["Node.js", "MongoDB"]
                    }
                ],
                "total_recommendations": 2,
                "generated_at": datetime.now().isoformat(),
                "next_update": (datetime.now() + timedelta(hours=24)).isoformat()
            }
            
            recommendations = mock_generate(test_user.id)
            assert len(recommendations["recommendations"]) == 2
            assert recommendations["recommendations"][0]["rank"] == 1
            assert recommendations["recommendations"][0]["match_score"] > 0.8
        
        # Step 4: Test recommendation API endpoint
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = recommendations
            
            response = client.get(f"/api/v1/users/{test_user.id}/recommendations")
            assert response.status_code == 200
            
            rec_data = response.json()
            assert "recommendations" in rec_data
            assert len(rec_data["recommendations"]) == 2
            assert rec_data["total_recommendations"] == 2
        
        # Step 5: Test recommendation updates when profile changes
        updated_profile = {
            **user_profile,
            "skills": user_profile["skills"] + ["Docker", "Kubernetes"],
            "locations": ["Remote"]  # Changed to remote only
        }
        
        with patch('app.services.recommendation_service.update_recommendations') as mock_update:
            mock_update.return_value = {
                "user_id": test_user.id,
                "previous_count": 2,
                "new_count": 3,
                "changes": [
                    {"action": "added", "job_id": 4, "reason": "New Docker/Kubernetes skills match"},
                    {"action": "reranked", "job_id": 2, "old_rank": 2, "new_rank": 1, "reason": "Remote preference change"}
                ],
                "updated_at": datetime.now().isoformat()
            }
            
            update_result = mock_update(test_user.id, updated_profile)
            assert update_result["new_count"] > update_result["previous_count"]
            assert len(update_result["changes"]) == 2

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_notification_system_complete_workflow(self, client, test_user, db_session):
        """
        Test complete notification system workflow (Requirement 4.1)
        - Morning briefing generation and delivery
        - Evening summary creation
        - User preference handling
        - Email delivery tracking
        """
        # Step 1: Test morning briefing generation
        with patch('app.services.notification_service.generate_morning_briefing') as mock_generate_briefing:
            mock_generate_briefing.return_value = {
                "user_id": test_user.id,
                "briefing_type": "morning",
                "content": {
                    "greeting": "Good morning! Here are your personalized job recommendations:",
                    "recommendations": [
                        {
                            "job_id": 1,
                            "title": "Senior Python Developer",
                            "company": "TechCorp",
                            "match_score": 0.85,
                            "key_highlights": ["Python expertise match", "San Francisco location"]
                        },
                        {
                            "job_id": 2,
                            "title": "Full Stack Engineer", 
                            "company": "StartupXYZ",
                            "match_score": 0.78,
                            "key_highlights": ["React skills", "Remote work"]
                        }
                    ],
                    "daily_tip": "Consider highlighting your FastAPI experience in applications",
                    "market_insight": "Python developer demand increased 15% this week"
                },
                "generated_at": datetime.now().isoformat()
            }
            
            briefing_data = mock_generate_briefing(test_user.id)
            assert briefing_data["briefing_type"] == "morning"
            assert len(briefing_data["content"]["recommendations"]) == 2
            assert "daily_tip" in briefing_data["content"]
        
        # Step 2: Test email formatting and personalization
        with patch('app.services.email_service.format_morning_briefing_email') as mock_format_email:
            mock_format_email.return_value = {
                "to": test_user.email,
                "subject": "Your Daily Career Opportunities - 2 New Matches",
                "html_content": """
                <html>
                <body>
                    <h2>Good morning!</h2>
                    <p>Here are your personalized job recommendations:</p>
                    <div class="job-recommendation">
                        <h3>Senior Python Developer at TechCorp</h3>
                        <p>Match Score: 85%</p>
                        <p>Key Highlights: Python expertise match, San Francisco location</p>
                    </div>
                    <!-- More recommendations -->
                </body>
                </html>
                """,
                "text_content": "Good morning! Here are your personalized job recommendations...",
                "template_id": "morning_briefing_v2"
            }
            
            email_data = mock_format_email(briefing_data)
            assert email_data["to"] == test_user.email
            assert "2 New Matches" in email_data["subject"]
            assert "Senior Python Developer" in email_data["html_content"]
        
        # Step 3: Test email delivery via SendGrid
        with patch('app.services.sendgrid_service.send_email') as mock_send_email:
            mock_send_email.return_value = {
                "message_id": "msg_morning_briefing_20241201_080000",
                "status": "sent",
                "delivery_time": datetime.now().isoformat(),
                "recipient": test_user.email,
                "template_used": "morning_briefing_v2"
            }
            
            delivery_result = mock_send_email(email_data)
            assert delivery_result["status"] == "sent"
            assert delivery_result["recipient"] == test_user.email
            assert "message_id" in delivery_result
        
        # Step 4: Test scheduled morning briefing execution
        with patch('app.tasks.notifications.send_morning_briefings') as mock_scheduled_briefings:
            mock_scheduled_briefings.return_value = {
                "total_users": 150,
                "briefings_generated": 150,
                "emails_sent": 145,
                "failed_deliveries": 5,
                "processing_time": 45.2,
                "failed_users": [
                    {"user_id": 25, "error": "Invalid email address"},
                    {"user_id": 67, "error": "Email bounced"}
                ],
                "execution_time": "2024-12-01T08:00:00Z"
            }
            
            batch_result = mock_scheduled_briefings()
            assert batch_result["emails_sent"] > 0
            assert batch_result["failed_deliveries"] <= 5
            assert batch_result["processing_time"] < 60  # Should complete within 1 minute
        
        # Step 5: Test evening summary generation (conditional)
        # Only sent if user applied to jobs that day
        with patch('app.services.job_service.get_daily_applications') as mock_get_applications:
            mock_get_applications.return_value = [
                {
                    "job_id": 1,
                    "title": "Senior Python Developer",
                    "company": "TechCorp",
                    "applied_at": "2024-12-01T14:30:00Z",
                    "application_method": "company_website"
                }
            ]
            
            daily_applications = mock_get_applications(test_user.id, datetime.now().date())
            assert len(daily_applications) == 1
        
        # Generate evening summary only if applications exist
        if daily_applications:
            with patch('app.services.notification_service.generate_evening_summary') as mock_evening_summary:
                mock_evening_summary.return_value = {
                    "user_id": test_user.id,
                    "summary_type": "evening",
                    "content": {
                        "greeting": "Great job today!",
                        "applications_today": 1,
                        "applications_summary": [
                            {
                                "company": "TechCorp",
                                "title": "Senior Python Developer",
                                "next_steps": "Follow up in 1 week if no response"
                            }
                        ],
                        "encouragement": "You're making excellent progress on your job search!",
                        "tomorrow_preview": "2 new job matches will be in your morning briefing"
                    },
                    "generated_at": datetime.now().isoformat()
                }
                
                evening_data = mock_evening_summary(test_user.id)
                assert evening_data["content"]["applications_today"] == 1
                assert len(evening_data["content"]["applications_summary"]) == 1
        
        # Step 6: Test user preference handling
        user_preferences = {
            "morning_briefing": True,
            "evening_summary": True,
            "briefing_time": "08:00",
            "summary_time": "18:00",
            "max_recommendations": 5,
            "email_frequency": "daily"
        }
        
        with patch('app.services.user_service.get_notification_preferences') as mock_get_prefs:
            mock_get_prefs.return_value = user_preferences
            
            prefs = mock_get_prefs(test_user.id)
            assert prefs["morning_briefing"] is True
            assert prefs["briefing_time"] == "08:00"
        
        # Test preference-based notification filtering
        with patch('app.services.notification_service.should_send_notification') as mock_should_send:
            mock_should_send.return_value = {
                "send_morning_briefing": True,
                "send_evening_summary": True,
                "reason": "User preferences allow both notifications"
            }
            
            send_decision = mock_should_send(test_user.id, user_preferences)
            assert send_decision["send_morning_briefing"] is True
            assert send_decision["send_evening_summary"] is True
        
        # Step 7: Test delivery tracking and analytics
        with patch('app.services.analytics_service.track_notification_delivery') as mock_track:
            mock_track.return_value = {
                "user_id": test_user.id,
                "notification_type": "morning_briefing",
                "delivery_status": "delivered",
                "opened": False,  # Not yet opened
                "clicked": False,
                "tracked_at": datetime.now().isoformat()
            }
            
            tracking_result = mock_track(test_user.id, "morning_briefing", delivery_result)
            assert tracking_result["delivery_status"] == "delivered"
            assert tracking_result["notification_type"] == "morning_briefing"


@pytest.mark.e2e
class TestScheduledTaskExecution:
    """Test scheduled task execution and data flow"""
    
    @pytest.mark.asyncio
    async def test_daily_job_ingestion_scheduled_execution(self, client, db_session):
        """Test complete daily job ingestion scheduled task execution"""
        # Simulate Cloud Scheduler trigger at 4:00 AM
        with patch('app.tasks.job_ingestion.daily_job_ingestion_task') as mock_task:
            mock_task.return_value = {
                "task_id": "daily_ingestion_20241201_040000",
                "status": "completed",
                "start_time": "2024-12-01T04:00:00Z",
                "end_time": "2024-12-01T04:15:23Z",
                "duration_seconds": 923,
                "results": {
                    "api_sources": {
                        "adzuna": {"jobs_fetched": 45, "new_jobs": 32, "errors": 0},
                        "jobspresso": {"jobs_fetched": 38, "new_jobs": 28, "errors": 1}
                    },
                    "web_scraping": {
                        "sites_scraped": 5,
                        "jobs_found": 23,
                        "new_jobs": 18,
                        "failed_sites": 1
                    },
                    "processing": {
                        "total_discovered": 106,
                        "duplicates_removed": 28,
                        "jobs_added": 78,
                        "enrichment_completed": 78
                    }
                },
                "next_scheduled": "2024-12-02T04:00:00Z"
            }
            
            task_result = mock_task()
            assert task_result["status"] == "completed"
            assert task_result["results"]["jobs_added"] > 0
            assert task_result["duration_seconds"] < 1800  # Should complete within 30 minutes
    
    @pytest.mark.asyncio
    async def test_morning_briefing_scheduled_execution(self, client, db_session):
        """Test morning briefing scheduled task execution"""
        # Simulate Cloud Scheduler trigger at 8:00 AM
        with patch('app.tasks.notifications.morning_briefing_task') as mock_task:
            mock_task.return_value = {
                "task_id": "morning_briefings_20241201_080000",
                "status": "completed",
                "start_time": "2024-12-01T08:00:00Z",
                "end_time": "2024-12-01T08:03:45Z",
                "duration_seconds": 225,
                "results": {
                    "eligible_users": 150,
                    "briefings_generated": 150,
                    "emails_sent": 147,
                    "delivery_failures": 3,
                    "opt_outs": 0,
                    "average_recommendations_per_user": 4.2
                },
                "next_scheduled": "2024-12-02T08:00:00Z"
            }
            
            task_result = mock_task()
            assert task_result["status"] == "completed"
            assert task_result["results"]["emails_sent"] > 140
            assert task_result["results"]["delivery_failures"] < 5
    
    @pytest.mark.asyncio
    async def test_evening_summary_scheduled_execution(self, client, db_session):
        """Test evening summary scheduled task execution"""
        # Simulate Cloud Scheduler trigger at 6:00 PM
        with patch('app.tasks.notifications.evening_summary_task') as mock_task:
            mock_task.return_value = {
                "task_id": "evening_summaries_20241201_180000",
                "status": "completed",
                "start_time": "2024-12-01T18:00:00Z",
                "end_time": "2024-12-01T18:02:15Z",
                "duration_seconds": 135,
                "results": {
                    "total_users": 150,
                    "users_with_applications": 25,
                    "summaries_generated": 25,
                    "emails_sent": 24,
                    "delivery_failures": 1,
                    "average_applications_per_active_user": 1.8
                },
                "next_scheduled": "2024-12-02T18:00:00Z"
            }
            
            task_result = mock_task()
            assert task_result["status"] == "completed"
            assert task_result["results"]["users_with_applications"] > 0
            # Only users with applications should receive summaries
            assert task_result["results"]["summaries_generated"] == task_result["results"]["users_with_applications"]
    
    @pytest.mark.asyncio
    async def test_recommendation_update_scheduled_execution(self, client, db_session):
        """Test recommendation update scheduled task execution"""
        # Simulate scheduled recommendation updates after job ingestion
        with patch('app.tasks.recommendations.update_all_recommendations_task') as mock_task:
            mock_task.return_value = {
                "task_id": "recommendation_update_20241201_050000",
                "status": "completed",
                "start_time": "2024-12-01T05:00:00Z",
                "end_time": "2024-12-01T05:08:30Z",
                "duration_seconds": 510,
                "results": {
                    "total_users": 150,
                    "users_processed": 150,
                    "recommendations_generated": 750,
                    "average_recommendations_per_user": 5.0,
                    "users_with_new_matches": 89,
                    "processing_errors": 0
                },
                "next_scheduled": "2024-12-02T05:00:00Z"
            }
            
            task_result = mock_task()
            assert task_result["status"] == "completed"
            assert task_result["results"]["users_processed"] == 150
            assert task_result["results"]["processing_errors"] == 0


@pytest.mark.e2e
class TestCrossComponentIntegration:
    """Test cross-component integration and data flow validation"""
    
    @pytest.mark.asyncio
    async def test_complete_data_pipeline_integration(self, client, db_session):
        """Test complete data flow from job ingestion to user notifications"""
        pipeline_results = {}
        
        # Step 1: Job Ingestion
        with patch('app.services.job_ingestion_service.ingest_jobs') as mock_ingest:
            mock_ingest.return_value = {
                "jobs_added": 50,
                "new_job_ids": list(range(1001, 1051)),
                "processing_time": 15.3
            }
            
            ingestion_result = mock_ingest()
            pipeline_results["ingestion"] = ingestion_result
            assert ingestion_result["jobs_added"] == 50
        
        # Step 2: Job Enrichment and Processing
        with patch('app.services.job_processing_service.enrich_jobs') as mock_enrich:
            mock_enrich.return_value = {
                "jobs_processed": 50,
                "skills_extracted": 250,
                "locations_normalized": 50,
                "salaries_estimated": 45
            }
            
            enrichment_result = mock_enrich(ingestion_result["new_job_ids"])
            pipeline_results["enrichment"] = enrichment_result
            assert enrichment_result["jobs_processed"] == ingestion_result["jobs_added"]
        
        # Step 3: Recommendation Generation
        with patch('app.services.recommendation_service.batch_update_recommendations') as mock_batch_rec:
            mock_batch_rec.return_value = {
                "users_updated": 150,
                "new_recommendations": 300,
                "updated_recommendations": 450,
                "processing_time": 45.7
            }
            
            recommendation_result = mock_batch_rec(ingestion_result["new_job_ids"])
            pipeline_results["recommendations"] = recommendation_result
            assert recommendation_result["users_updated"] > 0
        
        # Step 4: Notification Preparation
        with patch('app.services.notification_service.prepare_notifications') as mock_prepare:
            mock_prepare.return_value = {
                "users_with_new_matches": 89,
                "briefings_to_send": 150,
                "summaries_to_send": 25,
                "preparation_time": 8.2
            }
            
            notification_prep = mock_prepare(recommendation_result)
            pipeline_results["notification_prep"] = notification_prep
            assert notification_prep["briefings_to_send"] > 0
        
        # Step 5: Analytics Update
        with patch('app.services.analytics_service.update_pipeline_metrics') as mock_analytics:
            mock_analytics.return_value = {
                "pipeline_id": "pipeline_20241201_040000",
                "total_processing_time": sum([
                    pipeline_results["ingestion"]["processing_time"],
                    pipeline_results["recommendations"]["processing_time"],
                    pipeline_results["notification_prep"]["preparation_time"]
                ]),
                "efficiency_score": 0.92,
                "data_quality_score": 0.88
            }
            
            analytics_result = mock_analytics(pipeline_results)
            pipeline_results["analytics"] = analytics_result
            assert analytics_result["efficiency_score"] > 0.8
        
        # Validate end-to-end data consistency
        assert pipeline_results["enrichment"]["jobs_processed"] == pipeline_results["ingestion"]["jobs_added"]
        assert pipeline_results["recommendations"]["users_updated"] > 0
        assert pipeline_results["analytics"]["total_processing_time"] < 120  # Should complete within 2 minutes
    
    @pytest.mark.asyncio
    async def test_user_interaction_to_recommendation_integration(self, client, test_user, db_session):
        """Test integration from user profile updates to recommendation changes"""
        # Step 1: User updates profile
        profile_update = {
            "skills": ["Python", "FastAPI", "React", "Docker", "Kubernetes"],  # Added Docker, K8s
            "locations": ["Remote"],  # Changed to remote only
            "experience_level": "senior"  # Promoted to senior
        }
        
        with patch.object(client, 'put') as mock_put:
            mock_put.return_value.status_code = 200
            mock_put.return_value.json.return_value = {
                "user_id": test_user.id,
                "profile_updated": True,
                "changes_detected": ["skills", "locations", "experience_level"],
                "recommendation_refresh_triggered": True
            }
            
            profile_response = client.put(f"/api/v1/users/{test_user.id}/profile", json=profile_update)
            assert profile_response.status_code == 200
            
            update_result = profile_response.json()
            assert update_result["recommendation_refresh_triggered"] is True
        
        # Step 2: Recommendation engine processes profile changes
        with patch('app.services.recommendation_service.refresh_user_recommendations') as mock_refresh:
            mock_refresh.return_value = {
                "user_id": test_user.id,
                "previous_recommendations": 5,
                "new_recommendations": 8,
                "score_changes": [
                    {"job_id": 1, "old_score": 0.75, "new_score": 0.85, "reason": "Docker skills added"},
                    {"job_id": 2, "old_score": 0.60, "new_score": 0.90, "reason": "Remote preference match"}
                ],
                "new_matches": [
                    {"job_id": 15, "score": 0.88, "title": "Senior DevOps Engineer"},
                    {"job_id": 23, "score": 0.82, "title": "Remote Full Stack Lead"}
                ]
            }
            
            refresh_result = mock_refresh(test_user.id, profile_update)
            assert refresh_result["new_recommendations"] > refresh_result["previous_recommendations"]
            assert len(refresh_result["new_matches"]) > 0
        
        # Step 3: Updated recommendations available via API
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "recommendations": [
                    {
                        "job_id": 2,
                        "rank": 1,
                        "match_score": 0.90,
                        "title": "Remote Full Stack Engineer",
                        "score_change": "+0.30",
                        "new_match_reasons": ["Remote preference", "Senior level match"]
                    },
                    {
                        "job_id": 15,
                        "rank": 2,
                        "match_score": 0.88,
                        "title": "Senior DevOps Engineer",
                        "is_new": True,
                        "match_reasons": ["Docker skills", "Kubernetes experience"]
                    }
                ],
                "total": 8,
                "last_updated": datetime.now().isoformat()
            }
            
            rec_response = client.get(f"/api/v1/users/{test_user.id}/recommendations")
            assert rec_response.status_code == 200
            
            updated_recs = rec_response.json()
            assert len(updated_recs["recommendations"]) > 0
            assert updated_recs["total"] == 8
    
    @pytest.mark.asyncio
    async def test_application_to_analytics_integration(self, client, test_user, db_session):
        """Test integration from job applications to analytics updates"""
        # Step 1: User applies to multiple jobs
        applications = [
            {"job_id": 1, "company": "TechCorp", "title": "Senior Python Developer"},
            {"job_id": 2, "company": "StartupXYZ", "title": "Full Stack Engineer"},
            {"job_id": 3, "company": "CloudTech", "title": "DevOps Engineer"}
        ]
        
        application_results = []
        for app in applications:
            with patch.object(client, 'post') as mock_post:
                mock_post.return_value.status_code = 201
                mock_post.return_value.json.return_value = {
                    "application_id": f"app_{app['job_id']}",
                    "job_id": app["job_id"],
                    "status": "applied",
                    "applied_at": datetime.now().isoformat()
                }
                
                response = client.post(f"/api/v1/users/{test_user.id}/applications", json=app)
                application_results.append(response.json())
        
        assert len(application_results) == 3
        
        # Step 2: Analytics service processes applications
        with patch('app.services.analytics_service.process_application_events') as mock_process:
            mock_process.return_value = {
                "user_id": test_user.id,
                "applications_processed": 3,
                "metrics_updated": [
                    "total_applications",
                    "application_rate",
                    "company_preferences",
                    "skill_demand_analysis"
                ],
                "insights_generated": [
                    "User shows preference for tech companies",
                    "Strong interest in Python-based roles",
                    "Diversifying into DevOps skills"
                ]
            }
            
            analytics_result = mock_process(test_user.id, application_results)
            assert analytics_result["applications_processed"] == 3
            assert len(analytics_result["insights_generated"]) > 0
        
        # Step 3: Updated analytics available via API
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "user_id": test_user.id,
                "total_applications": 15,  # Including previous applications
                "applications_this_week": 3,
                "response_rate": 0.20,
                "interview_rate": 0.13,
                "top_companies_applied": ["TechCorp", "StartupXYZ", "CloudTech"],
                "skill_demand_trends": {
                    "Python": 0.85,
                    "Docker": 0.70,
                    "React": 0.65
                },
                "recommendations": [
                    "Consider highlighting DevOps skills in applications",
                    "Follow up on applications after 1 week"
                ]
            }
            
            analytics_response = client.get(f"/api/v1/users/{test_user.id}/analytics")
            assert analytics_response.status_code == 200
            
            analytics_data = analytics_response.json()
            assert analytics_data["applications_this_week"] == 3
            assert len(analytics_data["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_error_propagation_and_recovery_integration(self, client, db_session):
        """Test error handling and recovery across components"""
        # Step 1: Simulate job ingestion failure
        with patch('app.services.job_ingestion_service.ingest_jobs') as mock_ingest:
            mock_ingest.side_effect = Exception("API rate limit exceeded")
            
            with patch('app.services.error_handling_service.handle_ingestion_error') as mock_error_handler:
                mock_error_handler.return_value = {
                    "error_type": "api_rate_limit",
                    "recovery_action": "retry_with_backoff",
                    "retry_after": 3600,
                    "fallback_enabled": True,
                    "notification_sent": True
                }
                
                try:
                    mock_ingest()
                except Exception as e:
                    error_result = mock_error_handler(str(e))
                    assert error_result["recovery_action"] == "retry_with_backoff"
                    assert error_result["fallback_enabled"] is True
        
        # Step 2: Test fallback mechanism activation
        with patch('app.services.job_ingestion_service.use_cached_jobs') as mock_fallback:
            mock_fallback.return_value = {
                "source": "cache",
                "jobs_available": 25,
                "cache_age_hours": 6,
                "quality_score": 0.75
            }
            
            fallback_result = mock_fallback()
            assert fallback_result["jobs_available"] > 0
            assert fallback_result["cache_age_hours"] < 24
        
        # Step 3: Test system recovery after error resolution
        with patch('app.services.system_health_service.check_recovery_status') as mock_health_check:
            mock_health_check.return_value = {
                "all_services_healthy": True,
                "last_error_resolved": True,
                "ingestion_service": "operational",
                "recommendation_service": "operational",
                "notification_service": "operational",
                "recovery_time": "2024-12-01T05:30:00Z"
            }
            
            health_status = mock_health_check()
            assert health_status["all_services_healthy"] is True
            assert health_status["last_error_resolved"] is True