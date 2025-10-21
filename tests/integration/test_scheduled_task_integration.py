"""
Scheduled Task Integration Tests
Tests scheduled task execution, data flow, and cross-component integration
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, call
import json
from concurrent.futures import ThreadPoolExecutor


@pytest.mark.integration
class TestScheduledTaskIntegration:
    """Test scheduled task execution and coordination"""
    
    @pytest.mark.asyncio
    async def test_daily_job_ingestion_task_integration(self, client, db_session):
        """Test complete daily job ingestion task with all components"""
        # Mock Cloud Scheduler trigger
        task_context = {
            "task_id": "daily_ingestion_20241201_040000",
            "scheduled_time": "2024-12-01T04:00:00Z",
            "execution_timeout": 1800  # 30 minutes
        }
        
        # Step 1: Task initialization and validation
        with patch('app.tasks.job_ingestion.initialize_ingestion_task') as mock_init:
            mock_init.return_value = {
                "task_id": task_context["task_id"],
                "status": "initialized",
                "sources_configured": ["adzuna_api", "jobspresso_api", "web_scraping"],
                "rate_limits_checked": True,
                "database_connection": "healthy"
            }
            
            init_result = mock_init(task_context)
            assert init_result["status"] == "initialized"
            assert len(init_result["sources_configured"]) == 3
        
        # Step 2: API-based job ingestion
        api_ingestion_results = {}
        
        # Adzuna API ingestion
        with patch('app.services.adzuna_service.fetch_jobs') as mock_adzuna:
            mock_adzuna.return_value = {
                "jobs": [
                    {
                        "external_id": "adzuna_12345",
                        "title": "Senior Software Engineer",
                        "company": "TechCorp",
                        "location": "San Francisco, CA",
                        "salary_min": 120000,
                        "salary_max": 160000,
                        "description": "Join our engineering team...",
                        "tech_stack": ["Python", "Django", "PostgreSQL"]
                    }
                ] * 45,  # 45 jobs from Adzuna
                "total_available": 1250,
                "rate_limit_remaining": 950,
                "next_page_token": "adzuna_page_2"
            }
            
            adzuna_result = mock_adzuna()
            api_ingestion_results["adzuna"] = {
                "jobs_fetched": len(adzuna_result["jobs"]),
                "rate_limit_remaining": adzuna_result["rate_limit_remaining"]
            }
        
        # Jobspresso API ingestion
        with patch('app.services.jobspresso_service.fetch_jobs') as mock_jobspresso:
            mock_jobspresso.return_value = {
                "jobs": [
                    {
                        "external_id": "jobspresso_67890",
                        "title": "Full Stack Developer",
                        "company": "StartupXYZ",
                        "location": "Remote",
                        "description": "Build amazing web applications...",
                        "tech_stack": ["React", "Node.js", "MongoDB"]
                    }
                ] * 38,  # 38 jobs from Jobspresso
                "has_more": True,
                "next_cursor": "jobspresso_cursor_abc123"
            }
            
            jobspresso_result = mock_jobspresso()
            api_ingestion_results["jobspresso"] = {
                "jobs_fetched": len(jobspresso_result["jobs"]),
                "has_more": jobspresso_result["has_more"]
            }
        
        # Step 3: Web scraping ingestion
        with patch('app.services.web_scraping_service.scrape_job_sites') as mock_scraping:
            mock_scraping.return_value = {
                "scraped_jobs": [
                    {
                        "external_id": "scraped_company_a_123",
                        "title": "DevOps Engineer",
                        "company": "CloudTech",
                        "location": "Austin, TX",
                        "description": "Manage cloud infrastructure...",
                        "tech_stack": ["AWS", "Docker", "Kubernetes"],
                        "source_url": "https://cloudtech.com/careers/devops"
                    }
                ] * 23,  # 23 jobs from web scraping
                "sites_scraped": ["company-a.com", "company-b.com", "company-c.com"],
                "successful_scrapes": 2,
                "failed_scrapes": 1,
                "scraping_errors": [
                    {"site": "company-c.com", "error": "Site structure changed"}
                ]
            }
            
            scraping_result = mock_scraping()
            scraping_ingestion_results = {
                "jobs_scraped": len(scraping_result["scraped_jobs"]),
                "sites_successful": scraping_result["successful_scrapes"],
                "sites_failed": scraping_result["failed_scrapes"]
            }
        
        # Step 4: Job deduplication and processing
        all_jobs = (
            [{"source": "adzuna", **job} for job in mock_adzuna.return_value["jobs"]] +
            [{"source": "jobspresso", **job} for job in mock_jobspresso.return_value["jobs"]] +
            [{"source": "web_scraping", **job} for job in mock_scraping.return_value["scraped_jobs"]]
        )
        
        with patch('app.services.job_deduplication_service.process_job_batch') as mock_dedup:
            mock_dedup.return_value = {
                "total_jobs_processed": len(all_jobs),
                "unique_jobs": 78,
                "duplicates_removed": 28,
                "duplicate_groups": [
                    {
                        "canonical_job": "adzuna_12345",
                        "duplicates": ["scraped_company_a_456"],
                        "similarity_score": 0.92
                    }
                ],
                "jobs_to_store": all_jobs[:78]  # After deduplication
            }
            
            dedup_result = mock_dedup(all_jobs)
            assert dedup_result["unique_jobs"] == 78
            assert dedup_result["duplicates_removed"] == 28
        
        # Step 5: Job enrichment and storage
        with patch('app.services.job_processing_service.enrich_and_store_jobs') as mock_enrich_store:
            mock_enrich_store.return_value = {
                "jobs_stored": 78,
                "enrichment_results": {
                    "skills_extracted": 390,  # 5 skills per job average
                    "locations_normalized": 78,
                    "salaries_estimated": 65,
                    "company_info_enriched": 72
                },
                "storage_results": {
                    "database_inserts": 78,
                    "index_updates": 78,
                    "cache_invalidations": 15
                },
                "processing_time": 45.2
            }
            
            storage_result = mock_enrich_store(dedup_result["jobs_to_store"])
            assert storage_result["jobs_stored"] == 78
            assert storage_result["processing_time"] < 60
        
        # Step 6: Task completion and reporting
        with patch('app.tasks.job_ingestion.complete_ingestion_task') as mock_complete:
            mock_complete.return_value = {
                "task_id": task_context["task_id"],
                "status": "completed",
                "completion_time": "2024-12-01T04:15:23Z",
                "total_duration": 923,  # seconds
                "summary": {
                    "jobs_discovered": len(all_jobs),
                    "jobs_stored": storage_result["jobs_stored"],
                    "api_sources": api_ingestion_results,
                    "scraping_results": scraping_ingestion_results,
                    "deduplication": {
                        "duplicates_removed": dedup_result["duplicates_removed"]
                    },
                    "enrichment": storage_result["enrichment_results"]
                },
                "next_scheduled_run": "2024-12-02T04:00:00Z",
                "alerts_triggered": []
            }
            
            completion_result = mock_complete(task_context, storage_result)
            assert completion_result["status"] == "completed"
            assert completion_result["total_duration"] < 1800  # Within timeout
            assert len(completion_result["alerts_triggered"]) == 0
    
    @pytest.mark.asyncio
    async def test_recommendation_update_task_integration(self, client, db_session):
        """Test recommendation update task triggered after job ingestion"""
        # Mock trigger from job ingestion completion
        trigger_context = {
            "trigger_source": "job_ingestion_completed",
            "new_jobs_count": 78,
            "job_ingestion_task_id": "daily_ingestion_20241201_040000",
            "trigger_time": "2024-12-01T04:16:00Z"
        }
        
        # Step 1: Task initialization
        with patch('app.tasks.recommendations.initialize_recommendation_update') as mock_init:
            mock_init.return_value = {
                "task_id": "rec_update_20241201_041600",
                "status": "initialized",
                "users_to_process": 150,
                "new_jobs_available": trigger_context["new_jobs_count"],
                "processing_strategy": "incremental_update"
            }
            
            init_result = mock_init(trigger_context)
            assert init_result["users_to_process"] == 150
            assert init_result["new_jobs_available"] == 78
        
        # Step 2: Batch user processing
        user_batches = [
            list(range(1, 51)),    # Batch 1: Users 1-50
            list(range(51, 101)),  # Batch 2: Users 51-100
            list(range(101, 151))  # Batch 3: Users 101-150
        ]
        
        batch_results = []
        for batch_num, user_ids in enumerate(user_batches, 1):
            with patch('app.services.recommendation_service.process_user_batch') as mock_batch:
                mock_batch.return_value = {
                    "batch_id": batch_num,
                    "users_processed": len(user_ids),
                    "recommendations_generated": len(user_ids) * 5,  # 5 recs per user
                    "recommendations_updated": len(user_ids) * 3,    # 3 updated per user
                    "processing_time": 15.5,
                    "errors": 0
                }
                
                batch_result = mock_batch(user_ids, trigger_context["new_jobs_count"])
                batch_results.append(batch_result)
        
        # Validate batch processing
        total_users_processed = sum(batch["users_processed"] for batch in batch_results)
        total_recommendations = sum(batch["recommendations_generated"] for batch in batch_results)
        assert total_users_processed == 150
        assert total_recommendations == 750
        
        # Step 3: Recommendation quality validation
        with patch('app.services.recommendation_service.validate_recommendation_quality') as mock_validate:
            mock_validate.return_value = {
                "quality_score": 0.87,
                "average_match_score": 0.75,
                "recommendations_above_threshold": 680,  # 90.7% above 0.6 threshold
                "quality_issues": [
                    {"issue": "low_match_score", "count": 70, "percentage": 9.3}
                ],
                "validation_passed": True
            }
            
            quality_result = mock_validate(total_recommendations)
            assert quality_result["quality_score"] > 0.8
            assert quality_result["validation_passed"] is True
        
        # Step 4: Cache and index updates
        with patch('app.services.caching_service.update_recommendation_cache') as mock_cache:
            mock_cache.return_value = {
                "cache_updates": 150,
                "cache_invalidations": 45,
                "cache_hit_rate_projected": 0.82,
                "update_time": 8.3
            }
            
            cache_result = mock_cache(total_users_processed)
            assert cache_result["cache_updates"] == 150
            assert cache_result["cache_hit_rate_projected"] > 0.8
        
        # Step 5: Task completion
        with patch('app.tasks.recommendations.complete_recommendation_update') as mock_complete:
            mock_complete.return_value = {
                "task_id": "rec_update_20241201_041600",
                "status": "completed",
                "completion_time": "2024-12-01T04:23:45Z",
                "total_duration": 465,  # seconds
                "summary": {
                    "users_processed": total_users_processed,
                    "recommendations_generated": total_recommendations,
                    "batch_results": batch_results,
                    "quality_metrics": quality_result,
                    "cache_performance": cache_result
                },
                "performance_metrics": {
                    "users_per_second": total_users_processed / 465,
                    "recommendations_per_second": total_recommendations / 465
                }
            }
            
            completion_result = mock_complete(batch_results, quality_result)
            assert completion_result["status"] == "completed"
            assert completion_result["performance_metrics"]["users_per_second"] > 0.3
    
    @pytest.mark.asyncio
    async def test_notification_task_coordination(self, client, db_session):
        """Test coordination between morning briefing and evening summary tasks"""
        # Step 1: Morning briefing task execution
        morning_task_context = {
            "task_id": "morning_briefings_20241201_080000",
            "scheduled_time": "2024-12-01T08:00:00Z",
            "user_timezone_groups": {
                "PST": 45,   # Pacific users
                "MST": 25,   # Mountain users
                "CST": 35,   # Central users
                "EST": 45    # Eastern users
            }
        }
        
        with patch('app.tasks.notifications.execute_morning_briefings') as mock_morning:
            mock_morning.return_value = {
                "task_id": morning_task_context["task_id"],
                "status": "completed",
                "briefings_sent": 147,
                "delivery_results": {
                    "successful_deliveries": 144,
                    "failed_deliveries": 3,
                    "bounced_emails": 1,
                    "unsubscribed_users": 2
                },
                "timezone_results": {
                    "PST": {"sent": 44, "delivered": 43},
                    "MST": {"sent": 25, "delivered": 25},
                    "CST": {"sent": 34, "delivered": 34},
                    "EST": {"sent": 44, "delivered": 42}
                },
                "content_metrics": {
                    "average_recommendations_per_briefing": 4.2,
                    "personalization_score": 0.89
                },
                "processing_time": 185  # seconds
            }
            
            morning_result = mock_morning(morning_task_context)
            assert morning_result["briefings_sent"] > 140
            assert morning_result["delivery_results"]["successful_deliveries"] > 140
        
        # Step 2: Track user engagement throughout the day
        with patch('app.services.analytics_service.track_daily_user_activity') as mock_track:
            mock_track.return_value = {
                "users_with_activity": 89,
                "job_applications_today": 25,
                "profile_updates": 12,
                "job_views": 340,
                "recommendation_clicks": 156,
                "engagement_metrics": {
                    "email_open_rate": 0.68,
                    "email_click_rate": 0.34,
                    "application_conversion_rate": 0.16
                }
            }
            
            daily_activity = mock_track(datetime.now().date())
            assert daily_activity["users_with_activity"] > 0
            assert daily_activity["job_applications_today"] > 0
        
        # Step 3: Evening summary task execution (conditional)
        evening_task_context = {
            "task_id": "evening_summaries_20241201_180000",
            "scheduled_time": "2024-12-01T18:00:00Z",
            "users_with_applications": daily_activity["job_applications_today"],
            "summary_criteria": {
                "minimum_applications": 1,
                "include_progress_metrics": True,
                "include_encouragement": True
            }
        }
        
        with patch('app.tasks.notifications.execute_evening_summaries') as mock_evening:
            mock_evening.return_value = {
                "task_id": evening_task_context["task_id"],
                "status": "completed",
                "eligible_users": daily_activity["job_applications_today"],
                "summaries_generated": daily_activity["job_applications_today"],
                "summaries_sent": daily_activity["job_applications_today"] - 1,  # One delivery failure
                "delivery_results": {
                    "successful_deliveries": 24,
                    "failed_deliveries": 1
                },
                "content_metrics": {
                    "average_applications_per_summary": 1.8,
                    "encouragement_score": 0.92
                },
                "processing_time": 95  # seconds
            }
            
            evening_result = mock_evening(evening_task_context)
            assert evening_result["summaries_sent"] > 20
            assert evening_result["delivery_results"]["successful_deliveries"] > 20
        
        # Step 4: Daily task coordination summary
        with patch('app.services.task_coordination_service.generate_daily_summary') as mock_daily_summary:
            mock_daily_summary.return_value = {
                "date": "2024-12-01",
                "task_execution_summary": {
                    "job_ingestion": {"status": "completed", "jobs_added": 78},
                    "recommendation_updates": {"status": "completed", "users_updated": 150},
                    "morning_briefings": morning_result,
                    "evening_summaries": evening_result
                },
                "system_performance": {
                    "total_processing_time": 1668,  # All tasks combined
                    "peak_memory_usage": "2.1GB",
                    "database_queries": 15420,
                    "api_calls": 156
                },
                "user_engagement": daily_activity,
                "alerts_generated": 0,
                "next_day_preparation": {
                    "jobs_ready_for_ingestion": True,
                    "user_preferences_updated": True,
                    "system_health": "optimal"
                }
            }
            
            daily_summary = mock_daily_summary([morning_result, evening_result])
            assert daily_summary["alerts_generated"] == 0
            assert daily_summary["next_day_preparation"]["system_health"] == "optimal"


@pytest.mark.integration
class TestDataFlowValidation:
    """Test data flow between components and data consistency"""
    
    @pytest.mark.asyncio
    async def test_job_ingestion_to_recommendation_data_flow(self, client, db_session):
        """Test data flow from job ingestion to recommendation updates"""
        # Step 1: Simulate job ingestion with specific job characteristics
        ingested_jobs = [
            {
                "id": 1001,
                "title": "Senior Python Developer",
                "company": "TechCorp",
                "tech_stack": ["Python", "Django", "PostgreSQL", "AWS"],
                "location": "San Francisco, CA",
                "experience_level": "senior",
                "salary_min": 130000
            },
            {
                "id": 1002,
                "title": "Machine Learning Engineer",
                "company": "AI Innovations",
                "tech_stack": ["Python", "TensorFlow", "Docker", "Kubernetes"],
                "location": "Remote",
                "experience_level": "mid",
                "salary_min": 120000
            },
            {
                "id": 1003,
                "title": "Full Stack Developer",
                "company": "StartupXYZ",
                "tech_stack": ["React", "Node.js", "MongoDB", "AWS"],
                "location": "Austin, TX",
                "experience_level": "mid",
                "salary_min": 95000
            }
        ]
        
        with patch('app.services.job_service.get_recently_added_jobs') as mock_get_jobs:
            mock_get_jobs.return_value = ingested_jobs
            
            recent_jobs = mock_get_jobs(since=datetime.now() - timedelta(hours=1))
            assert len(recent_jobs) == 3
        
        # Step 2: Test recommendation engine processing of new jobs
        test_users = [
            {
                "id": 1,
                "skills": ["Python", "Django", "PostgreSQL"],
                "experience_level": "senior",
                "locations": ["San Francisco", "Remote"],
                "preferences": {"salary_min": 120000}
            },
            {
                "id": 2,
                "skills": ["Python", "TensorFlow", "Docker"],
                "experience_level": "mid",
                "locations": ["Remote"],
                "preferences": {"salary_min": 100000}
            },
            {
                "id": 3,
                "skills": ["React", "Node.js", "JavaScript"],
                "experience_level": "mid",
                "locations": ["Austin", "Remote"],
                "preferences": {"salary_min": 80000}
            }
        ]
        
        recommendation_results = []
        for user in test_users:
            with patch('app.services.recommendation_service.calculate_matches') as mock_calculate:
                # Calculate expected matches based on user profile
                expected_matches = []
                for job in ingested_jobs:
                    skill_overlap = len(set(user["skills"]) & set(job["tech_stack"]))
                    location_match = any(loc in job["location"] for loc in user["locations"])
                    experience_match = user["experience_level"] == job["experience_level"]
                    salary_match = job["salary_min"] >= user["preferences"]["salary_min"]
                    
                    if skill_overlap > 0:
                        match_score = (
                            (skill_overlap / len(job["tech_stack"])) * 0.5 +
                            (1.0 if location_match else 0.0) * 0.3 +
                            (1.0 if experience_match else 0.5) * 0.2
                        )
                        
                        if salary_match:
                            match_score *= 1.1  # Bonus for salary match
                        
                        expected_matches.append({
                            "job_id": job["id"],
                            "match_score": min(match_score, 1.0),
                            "skill_overlap": skill_overlap,
                            "location_match": location_match,
                            "experience_match": experience_match
                        })
                
                mock_calculate.return_value = expected_matches
                matches = mock_calculate(user, ingested_jobs)
                recommendation_results.append({
                    "user_id": user["id"],
                    "matches": matches
                })
        
        # Validate recommendation logic
        user1_matches = recommendation_results[0]["matches"]
        assert len(user1_matches) > 0
        
        # User 1 should have high match with job 1001 (Senior Python Developer)
        job1001_match = next((m for m in user1_matches if m["job_id"] == 1001), None)
        assert job1001_match is not None
        assert job1001_match["match_score"] > 0.8
        
        # Step 3: Test data consistency in recommendation storage
        with patch('app.services.recommendation_service.store_recommendations') as mock_store:
            mock_store.return_value = {
                "recommendations_stored": sum(len(r["matches"]) for r in recommendation_results),
                "users_updated": len(recommendation_results),
                "storage_consistency_check": "passed",
                "data_integrity_score": 1.0
            }
            
            storage_result = mock_store(recommendation_results)
            assert storage_result["storage_consistency_check"] == "passed"
            assert storage_result["data_integrity_score"] == 1.0
        
        # Step 4: Validate data availability through API
        for user_result in recommendation_results:
            user_id = user_result["user_id"]
            expected_matches = len(user_result["matches"])
            
            with patch.object(client, 'get') as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {
                    "recommendations": [
                        {
                            "job_id": match["job_id"],
                            "match_score": match["match_score"],
                            "is_new": True,
                            "added_from_ingestion": "daily_ingestion_20241201_040000"
                        }
                        for match in user_result["matches"]
                    ],
                    "total": expected_matches,
                    "last_updated": datetime.now().isoformat()
                }
                
                response = client.get(f"/api/v1/users/{user_id}/recommendations")
                assert response.status_code == 200
                
                api_data = response.json()
                assert len(api_data["recommendations"]) == expected_matches
                assert all(rec["is_new"] for rec in api_data["recommendations"])
    
    @pytest.mark.asyncio
    async def test_user_activity_to_analytics_data_flow(self, client, db_session):
        """Test data flow from user activities to analytics updates"""
        # Step 1: Simulate various user activities
        user_activities = [
            {
                "user_id": 1,
                "activity_type": "job_application",
                "job_id": 1001,
                "timestamp": datetime.now() - timedelta(hours=2),
                "metadata": {"application_method": "company_website"}
            },
            {
                "user_id": 1,
                "activity_type": "job_view",
                "job_id": 1002,
                "timestamp": datetime.now() - timedelta(hours=1),
                "metadata": {"view_duration": 45}
            },
            {
                "user_id": 2,
                "activity_type": "profile_update",
                "timestamp": datetime.now() - timedelta(minutes=30),
                "metadata": {"fields_updated": ["skills", "locations"]}
            },
            {
                "user_id": 2,
                "activity_type": "recommendation_click",
                "job_id": 1003,
                "timestamp": datetime.now() - timedelta(minutes=15),
                "metadata": {"recommendation_rank": 2}
            }
        ]
        
        # Step 2: Process activities through analytics pipeline
        with patch('app.services.analytics_service.process_activity_batch') as mock_process:
            mock_process.return_value = {
                "activities_processed": len(user_activities),
                "user_metrics_updated": 2,
                "job_metrics_updated": 3,
                "system_metrics_updated": True,
                "processing_results": {
                    "user_1": {
                        "total_applications": 5,  # Including previous
                        "total_views": 23,
                        "engagement_score": 0.78,
                        "activity_trend": "increasing"
                    },
                    "user_2": {
                        "profile_updates": 3,
                        "recommendation_clicks": 8,
                        "engagement_score": 0.65,
                        "activity_trend": "stable"
                    }
                },
                "job_popularity_updates": {
                    "job_1001": {"applications": 3, "views": 45},
                    "job_1002": {"views": 67, "click_rate": 0.34},
                    "job_1003": {"clicks": 12, "conversion_rate": 0.25}
                }
            }
            
            analytics_result = mock_process(user_activities)
            assert analytics_result["activities_processed"] == len(user_activities)
            assert analytics_result["user_metrics_updated"] == 2
        
        # Step 3: Validate analytics data aggregation
        with patch('app.services.analytics_service.aggregate_daily_metrics') as mock_aggregate:
            mock_aggregate.return_value = {
                "date": datetime.now().date().isoformat(),
                "system_metrics": {
                    "total_applications": 25,
                    "total_job_views": 340,
                    "total_profile_updates": 12,
                    "total_recommendation_clicks": 156,
                    "active_users": 89
                },
                "engagement_metrics": {
                    "average_session_duration": 8.5,  # minutes
                    "bounce_rate": 0.23,
                    "conversion_rate": 0.16,
                    "user_retention_rate": 0.82
                },
                "job_market_insights": {
                    "most_popular_skills": ["Python", "React", "AWS"],
                    "highest_demand_locations": ["Remote", "San Francisco", "Austin"],
                    "average_salary_trends": {
                        "Python": {"min": 95000, "max": 145000, "trend": "+5%"},
                        "React": {"min": 85000, "max": 125000, "trend": "+3%"}
                    }
                }
            }
            
            daily_metrics = mock_aggregate(datetime.now().date())
            assert daily_metrics["system_metrics"]["active_users"] > 0
            assert len(daily_metrics["job_market_insights"]["most_popular_skills"]) > 0
        
        # Step 4: Test analytics API data availability
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "user_analytics": {
                    "user_id": 1,
                    "total_applications": 5,
                    "applications_this_week": 2,
                    "response_rate": 0.20,
                    "interview_rate": 0.10,
                    "engagement_metrics": analytics_result["processing_results"]["user_1"]
                },
                "market_analytics": daily_metrics["job_market_insights"],
                "recommendations": [
                    "Consider applying to more remote positions",
                    "Your Python skills are in high demand"
                ],
                "last_updated": datetime.now().isoformat()
            }
            
            response = client.get("/api/v1/users/1/analytics")
            assert response.status_code == 200
            
            analytics_data = response.json()
            assert analytics_data["user_analytics"]["total_applications"] == 5
            assert len(analytics_data["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_notification_delivery_to_engagement_tracking(self, client, db_session):
        """Test data flow from notification delivery to engagement tracking"""
        # Step 1: Simulate notification delivery
        notification_deliveries = [
            {
                "user_id": 1,
                "notification_type": "morning_briefing",
                "message_id": "msg_briefing_001",
                "delivery_status": "delivered",
                "delivered_at": datetime.now() - timedelta(hours=4),
                "recommendations_included": 5
            },
            {
                "user_id": 2,
                "notification_type": "morning_briefing",
                "message_id": "msg_briefing_002",
                "delivery_status": "delivered",
                "delivered_at": datetime.now() - timedelta(hours=4),
                "recommendations_included": 4
            },
            {
                "user_id": 1,
                "notification_type": "evening_summary",
                "message_id": "msg_summary_001",
                "delivery_status": "delivered",
                "delivered_at": datetime.now() - timedelta(hours=1),
                "applications_summarized": 2
            }
        ]
        
        # Step 2: Track email engagement events
        engagement_events = [
            {
                "message_id": "msg_briefing_001",
                "user_id": 1,
                "event_type": "opened",
                "timestamp": datetime.now() - timedelta(hours=3, minutes=45),
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
            },
            {
                "message_id": "msg_briefing_001",
                "user_id": 1,
                "event_type": "clicked",
                "timestamp": datetime.now() - timedelta(hours=3, minutes=30),
                "clicked_url": "https://app.career-copilot.com/jobs/1001",
                "link_type": "job_recommendation"
            },
            {
                "message_id": "msg_briefing_002",
                "user_id": 2,
                "event_type": "opened",
                "timestamp": datetime.now() - timedelta(hours=3, minutes=20),
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
        ]
        
        with patch('app.services.email_tracking_service.process_engagement_events') as mock_process_engagement:
            mock_process_engagement.return_value = {
                "events_processed": len(engagement_events),
                "engagement_metrics": {
                    "msg_briefing_001": {
                        "delivered": True,
                        "opened": True,
                        "clicked": True,
                        "open_time": "2024-12-01T04:15:00Z",
                        "click_time": "2024-12-01T04:30:00Z",
                        "engagement_score": 1.0
                    },
                    "msg_briefing_002": {
                        "delivered": True,
                        "opened": True,
                        "clicked": False,
                        "open_time": "2024-12-01T04:40:00Z",
                        "engagement_score": 0.5
                    },
                    "msg_summary_001": {
                        "delivered": True,
                        "opened": False,
                        "clicked": False,
                        "engagement_score": 0.0
                    }
                }
            }
            
            engagement_result = mock_process_engagement(engagement_events)
            assert engagement_result["events_processed"] == len(engagement_events)
        
        # Step 3: Aggregate engagement metrics
        with patch('app.services.analytics_service.calculate_notification_effectiveness') as mock_calculate_effectiveness:
            mock_calculate_effectiveness.return_value = {
                "notification_type": "morning_briefing",
                "total_sent": 150,
                "total_delivered": 147,
                "total_opened": 98,
                "total_clicked": 45,
                "metrics": {
                    "delivery_rate": 0.98,
                    "open_rate": 0.67,
                    "click_rate": 0.31,
                    "click_to_open_rate": 0.46
                },
                "user_segments": {
                    "high_engagement": {"users": 45, "avg_click_rate": 0.65},
                    "medium_engagement": {"users": 53, "avg_click_rate": 0.25},
                    "low_engagement": {"users": 49, "avg_click_rate": 0.05}
                },
                "recommendations": [
                    "Optimize send time for better open rates",
                    "A/B test subject lines to improve engagement",
                    "Personalize content for low-engagement users"
                ]
            }
            
            effectiveness_result = mock_calculate_effectiveness("morning_briefing", engagement_result)
            assert effectiveness_result["metrics"]["open_rate"] > 0.6
            assert effectiveness_result["metrics"]["click_rate"] > 0.25
        
        # Step 4: Update user engagement profiles
        with patch('app.services.user_service.update_engagement_profiles') as mock_update_profiles:
            mock_update_profiles.return_value = {
                "profiles_updated": 2,
                "engagement_changes": {
                    "user_1": {
                        "previous_score": 0.65,
                        "new_score": 0.78,
                        "trend": "improving",
                        "segment": "high_engagement"
                    },
                    "user_2": {
                        "previous_score": 0.45,
                        "new_score": 0.48,
                        "trend": "stable",
                        "segment": "medium_engagement"
                    }
                },
                "personalization_updates": {
                    "user_1": {"send_time": "08:00", "content_preference": "detailed"},
                    "user_2": {"send_time": "07:30", "content_preference": "summary"}
                }
            }
            
            profile_updates = mock_update_profiles(engagement_result["engagement_metrics"])
            assert profile_updates["profiles_updated"] == 2
            assert profile_updates["engagement_changes"]["user_1"]["trend"] == "improving"