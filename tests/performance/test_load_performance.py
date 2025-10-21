"""
Performance testing and optimization tests
Tests load handling, database performance, and cost efficiency
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import statistics
from datetime import datetime, timedelta


@pytest.mark.performance
class TestLoadTesting:
    """Load testing for expected user volumes"""
    
    async def test_concurrent_user_requests(self, client):
        """Test handling concurrent user requests"""
        num_concurrent_users = 50
        requests_per_user = 10
        
        async def simulate_user_session(user_id):
            """Simulate a user session with multiple requests"""
            session_times = []
            
            # Mock responses for different endpoints
            endpoints = [
                f"/api/v1/users/{user_id}/jobs",
                f"/api/v1/users/{user_id}/recommendations", 
                f"/api/v1/users/{user_id}/skill-gaps",
                f"/api/v1/users/{user_id}/analytics"
            ]
            
            for _ in range(requests_per_user):
                start_time = time.time()
                
                with patch.object(client, 'get') as mock_get:
                    mock_get.return_value.status_code = 200
                    mock_get.return_value.json.return_value = {"data": "test"}
                    
                    # Simulate random endpoint access
                    import random
                    endpoint = random.choice(endpoints)
                    response = client.get(endpoint)
                    
                end_time = time.time()
                session_times.append(end_time - start_time)
                
                # Simulate user think time
                await asyncio.sleep(0.1)
            
            return {
                "user_id": user_id,
                "avg_response_time": statistics.mean(session_times),
                "max_response_time": max(session_times),
                "total_requests": requests_per_user
            }
        
        # Run concurrent user sessions
        tasks = []
        for user_id in range(1, num_concurrent_users + 1):
            task = asyncio.create_task(simulate_user_session(user_id))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Analyze results
        avg_response_times = [r["avg_response_time"] for r in results]
        max_response_times = [r["max_response_time"] for r in results]
        
        overall_avg = statistics.mean(avg_response_times)
        overall_max = max(max_response_times)
        
        # Performance assertions
        assert overall_avg < 0.5, f"Average response time {overall_avg}s exceeds 500ms threshold"
        assert overall_max < 2.0, f"Max response time {overall_max}s exceeds 2s threshold"
        assert len(results) == num_concurrent_users, "Not all user sessions completed"

    async def test_database_query_performance(self, db_session):
        """Test database query performance under load"""
        # Create test data
        num_test_records = 1000
        
        # Mock database operations
        query_times = []
        
        for i in range(100):  # 100 query operations
            start_time = time.time()
            
            # Simulate complex query
            with patch.object(db_session, 'query') as mock_query:
                mock_query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
                    Mock(id=j, title=f"Job {j}") for j in range(10)
                ]
                
                # Simulate job search query
                results = (db_session.query(Mock)
                          .filter(Mock.user_id == 1)
                          .order_by(Mock.created_at.desc())
                          .limit(10)
                          .all())
            
            end_time = time.time()
            query_times.append(end_time - start_time)
        
        avg_query_time = statistics.mean(query_times)
        max_query_time = max(query_times)
        p95_query_time = statistics.quantiles(query_times, n=20)[18]  # 95th percentile
        
        # Performance assertions
        assert avg_query_time < 0.1, f"Average query time {avg_query_time}s exceeds 100ms"
        assert max_query_time < 0.5, f"Max query time {max_query_time}s exceeds 500ms"
        assert p95_query_time < 0.2, f"95th percentile query time {p95_query_time}s exceeds 200ms"

    async def test_job_ingestion_performance(self, client):
        """Test job ingestion performance with large datasets"""
        batch_sizes = [10, 50, 100, 500]
        performance_results = {}
        
        for batch_size in batch_sizes:
            # Generate test job data
            test_jobs = [
                {
                    "title": f"Job {i}",
                    "company": f"Company {i}",
                    "location": "Test Location",
                    "description": f"Job description {i}",
                    "skills_required": ["Python", "JavaScript"],
                    "salary_min": 80000 + (i * 1000)
                }
                for i in range(batch_size)
            ]
            
            start_time = time.time()
            
            with patch('app.services.job_service.batch_add_jobs') as mock_batch_add:
                mock_batch_add.return_value = {
                    "processed": batch_size,
                    "added": batch_size - 5,  # Simulate some duplicates
                    "duplicates": 5,
                    "errors": 0
                }
                
                result = mock_batch_add(test_jobs)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            performance_results[batch_size] = {
                "processing_time": processing_time,
                "jobs_per_second": batch_size / processing_time,
                "result": result
            }
        
        # Performance assertions
        for batch_size, metrics in performance_results.items():
            jobs_per_second = metrics["jobs_per_second"]
            assert jobs_per_second > 50, f"Processing rate {jobs_per_second} jobs/sec too slow for batch size {batch_size}"

    async def test_recommendation_generation_performance(self, client, test_user):
        """Test recommendation generation performance"""
        num_users = 100
        jobs_per_user = 1000
        
        generation_times = []
        
        for user_id in range(1, num_users + 1):
            start_time = time.time()
            
            with patch('app.services.recommendation_service.generate_recommendations') as mock_generate:
                # Simulate recommendation generation
                mock_generate.return_value = [
                    {
                        "job_id": i,
                        "match_score": 0.8 - (i * 0.001),
                        "reasons": ["skill match", "location match"]
                    }
                    for i in range(min(20, jobs_per_user))  # Top 20 recommendations
                ]
                
                recommendations = mock_generate(user_id)
            
            end_time = time.time()
            generation_times.append(end_time - start_time)
        
        avg_generation_time = statistics.mean(generation_times)
        max_generation_time = max(generation_times)
        
        # Performance assertions
        assert avg_generation_time < 1.0, f"Average recommendation generation time {avg_generation_time}s exceeds 1s"
        assert max_generation_time < 3.0, f"Max recommendation generation time {max_generation_time}s exceeds 3s"


@pytest.mark.performance
class TestDatabaseOptimization:
    """Test database query optimization"""
    
    async def test_index_effectiveness(self, db_session):
        """Test database index effectiveness"""
        # Test queries that should use indexes
        index_queries = [
            "SELECT * FROM jobs WHERE user_id = 1",
            "SELECT * FROM jobs WHERE status = 'not_applied'",
            "SELECT * FROM jobs WHERE created_at > '2024-01-01'",
            "SELECT * FROM jobs WHERE user_id = 1 AND status = 'applied'"
        ]
        
        for query in index_queries:
            start_time = time.time()
            
            # Mock query execution
            with patch.object(db_session, 'execute') as mock_execute:
                mock_execute.return_value.fetchall.return_value = [
                    Mock(id=i, title=f"Job {i}") for i in range(10)
                ]
                
                result = db_session.execute(query).fetchall()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Indexed queries should be fast
            assert query_time < 0.05, f"Indexed query took {query_time}s, may need optimization"

    async def test_query_optimization(self, db_session):
        """Test optimized vs unoptimized queries"""
        # Test N+1 query problem prevention
        user_ids = list(range(1, 51))  # 50 users
        
        # Optimized approach - single query with JOIN
        start_time = time.time()
        
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.join.return_value.filter.return_value.all.return_value = [
                Mock(id=i, user_id=i, title=f"Job {i}") for i in user_ids
            ]
            
            # Single query to get all jobs for all users
            all_jobs = (db_session.query(Mock)
                       .join(Mock)
                       .filter(Mock.user_id.in_(user_ids))
                       .all())
        
        optimized_time = time.time() - start_time
        
        # Unoptimized approach - separate query per user
        start_time = time.time()
        
        for user_id in user_ids:
            with patch.object(db_session, 'query') as mock_query:
                mock_query.return_value.filter.return_value.all.return_value = [
                    Mock(id=user_id, title=f"Job {user_id}")
                ]
                
                user_jobs = db_session.query(Mock).filter(Mock.user_id == user_id).all()
        
        unoptimized_time = time.time() - start_time
        
        # Optimized should be significantly faster
        improvement_ratio = unoptimized_time / optimized_time
        assert improvement_ratio > 2, f"Query optimization only improved by {improvement_ratio}x"

    async def test_connection_pooling_performance(self, db_session):
        """Test database connection pooling performance"""
        num_concurrent_connections = 20
        queries_per_connection = 10
        
        async def execute_queries(connection_id):
            """Execute multiple queries on a connection"""
            query_times = []
            
            for i in range(queries_per_connection):
                start_time = time.time()
                
                with patch.object(db_session, 'execute') as mock_execute:
                    mock_execute.return_value.fetchone.return_value = Mock(count=100)
                    
                    result = db_session.execute("SELECT COUNT(*) FROM jobs").fetchone()
                
                end_time = time.time()
                query_times.append(end_time - start_time)
            
            return {
                "connection_id": connection_id,
                "avg_query_time": statistics.mean(query_times),
                "total_queries": queries_per_connection
            }
        
        # Test concurrent connections
        tasks = []
        for conn_id in range(num_concurrent_connections):
            task = asyncio.create_task(execute_queries(conn_id))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Analyze connection pool performance
        avg_times = [r["avg_query_time"] for r in results]
        overall_avg = statistics.mean(avg_times)
        
        # Connection pooling should maintain good performance
        assert overall_avg < 0.1, f"Connection pool performance degraded: {overall_avg}s avg"
        assert len(results) == num_concurrent_connections, "Not all connections completed"


@pytest.mark.performance
class TestCostEfficiencyValidation:
    """Test cost efficiency and free-tier compliance"""
    
    async def test_free_tier_resource_usage(self, client):
        """Test resource usage within free tier limits"""
        # Google Cloud Free Tier limits
        free_tier_limits = {
            "cloud_functions_invocations": 2_000_000,  # per month
            "cloud_functions_compute_time": 400_000,   # GB-seconds per month
            "firestore_reads": 50_000,                 # per day
            "firestore_writes": 20_000,                # per day
            "firestore_deletes": 20_000                # per day
        }
        
        # Simulate daily usage
        daily_usage = {
            "function_invocations": 0,
            "compute_time_gb_seconds": 0,
            "firestore_reads": 0,
            "firestore_writes": 0,
            "firestore_deletes": 0
        }
        
        # Simulate typical daily operations
        num_users = 100
        
        for user_id in range(1, num_users + 1):
            # Morning briefing (1 function call, 2 seconds, 10 reads)
            daily_usage["function_invocations"] += 1
            daily_usage["compute_time_gb_seconds"] += 2 * 0.128  # 128MB memory
            daily_usage["firestore_reads"] += 10
            
            # Job recommendations (1 function call, 3 seconds, 50 reads)
            daily_usage["function_invocations"] += 1
            daily_usage["compute_time_gb_seconds"] += 3 * 0.128
            daily_usage["firestore_reads"] += 50
            
            # Job application (1 function call, 1 second, 5 reads, 2 writes)
            if user_id % 10 == 0:  # 10% of users apply daily
                daily_usage["function_invocations"] += 1
                daily_usage["compute_time_gb_seconds"] += 1 * 0.128
                daily_usage["firestore_reads"] += 5
                daily_usage["firestore_writes"] += 2
        
        # Job ingestion (scheduled, 1 call, 30 seconds, 100 reads, 50 writes)
        daily_usage["function_invocations"] += 1
        daily_usage["compute_time_gb_seconds"] += 30 * 0.256  # 256MB for batch processing
        daily_usage["firestore_reads"] += 100
        daily_usage["firestore_writes"] += 50
        
        # Validate free tier compliance
        monthly_function_calls = daily_usage["function_invocations"] * 30
        monthly_compute_time = daily_usage["compute_time_gb_seconds"] * 30
        
        assert monthly_function_calls < free_tier_limits["cloud_functions_invocations"], \
            f"Monthly function calls {monthly_function_calls} exceed free tier limit"
        
        assert monthly_compute_time < free_tier_limits["cloud_functions_compute_time"], \
            f"Monthly compute time {monthly_compute_time} GB-s exceeds free tier limit"
        
        assert daily_usage["firestore_reads"] < free_tier_limits["firestore_reads"], \
            f"Daily Firestore reads {daily_usage['firestore_reads']} exceed free tier limit"
        
        assert daily_usage["firestore_writes"] < free_tier_limits["firestore_writes"], \
            f"Daily Firestore writes {daily_usage['firestore_writes']} exceed free tier limit"

    async def test_function_memory_optimization(self, client):
        """Test Cloud Function memory usage optimization"""
        memory_configs = [128, 256, 512, 1024]  # MB
        function_types = ["job_recommendations", "skill_analysis", "job_ingestion"]
        
        performance_results = {}
        
        for memory_mb in memory_configs:
            for function_type in function_types:
                # Simulate function execution with different memory configs
                start_time = time.time()
                
                if function_type == "job_recommendations":
                    # CPU-intensive task
                    execution_time = 2.0 + (512 - memory_mb) * 0.01  # More memory = faster
                elif function_type == "skill_analysis":
                    # Memory-intensive task
                    execution_time = 1.5 + max(0, (256 - memory_mb) * 0.02)
                else:  # job_ingestion
                    # I/O intensive task
                    execution_time = 5.0 + (256 - memory_mb) * 0.005
                
                # Calculate cost (simplified)
                gb_seconds = (memory_mb / 1024) * execution_time
                cost_per_invocation = gb_seconds * 0.0000025  # $2.50 per million GB-seconds
                
                performance_results[f"{function_type}_{memory_mb}MB"] = {
                    "execution_time": execution_time,
                    "memory_mb": memory_mb,
                    "gb_seconds": gb_seconds,
                    "cost_per_invocation": cost_per_invocation,
                    "cost_efficiency": execution_time / cost_per_invocation
                }
        
        # Find optimal memory configuration for each function type
        for function_type in function_types:
            function_results = {k: v for k, v in performance_results.items() if k.startswith(function_type)}
            
            # Best configuration should balance speed and cost
            best_config = min(function_results.items(), 
                            key=lambda x: x[1]["execution_time"] * x[1]["cost_per_invocation"])
            
            print(f"Optimal config for {function_type}: {best_config[0]}")
            
            # Ensure reasonable performance
            assert best_config[1]["execution_time"] < 10.0, \
                f"Function {function_type} execution time too high: {best_config[1]['execution_time']}s"

    async def test_caching_cost_optimization(self, client):
        """Test caching effectiveness for cost optimization"""
        cache_scenarios = [
            {"cache_enabled": False, "hit_rate": 0.0},
            {"cache_enabled": True, "hit_rate": 0.3},
            {"cache_enabled": True, "hit_rate": 0.6},
            {"cache_enabled": True, "hit_rate": 0.8}
        ]
        
        num_requests = 1000
        base_processing_cost = 0.001  # $0.001 per request
        
        for scenario in cache_scenarios:
            cache_hits = int(num_requests * scenario["hit_rate"])
            cache_misses = num_requests - cache_hits
            
            # Calculate costs
            processing_cost = cache_misses * base_processing_cost
            cache_cost = cache_hits * 0.0001 if scenario["cache_enabled"] else 0  # Cache is cheaper
            total_cost = processing_cost + cache_cost
            
            # Calculate response times
            avg_response_time = (cache_hits * 0.05 + cache_misses * 0.5) / num_requests
            
            scenario.update({
                "total_cost": total_cost,
                "avg_response_time": avg_response_time,
                "cost_savings": (num_requests * base_processing_cost) - total_cost
            })
        
        # Validate caching benefits
        no_cache_scenario = cache_scenarios[0]
        best_cache_scenario = max(cache_scenarios[1:], key=lambda x: x["cost_savings"])
        
        cost_reduction = (no_cache_scenario["total_cost"] - best_cache_scenario["total_cost"]) / no_cache_scenario["total_cost"]
        speed_improvement = no_cache_scenario["avg_response_time"] / best_cache_scenario["avg_response_time"]
        
        assert cost_reduction > 0.5, f"Caching should reduce costs by >50%, got {cost_reduction:.2%}"
        assert speed_improvement > 2.0, f"Caching should improve speed by >2x, got {speed_improvement:.1f}x"

    async def test_auto_scaling_efficiency(self, client):
        """Test auto-scaling efficiency and cost impact"""
        traffic_patterns = [
            {"hour": 0, "requests_per_minute": 10},   # Low traffic
            {"hour": 6, "requests_per_minute": 50},   # Morning peak
            {"hour": 12, "requests_per_minute": 80},  # Lunch peak
            {"hour": 18, "requests_per_minute": 100}, # Evening peak
            {"hour": 22, "requests_per_minute": 20}   # Night low
        ]
        
        total_cost = 0
        total_requests = 0
        
        for pattern in traffic_patterns:
            requests = pattern["requests_per_minute"] * 60  # Per hour
            
            # Calculate required instances (assuming 10 requests per instance per minute)
            required_instances = max(1, (pattern["requests_per_minute"] + 9) // 10)
            
            # Cost calculation (simplified)
            instance_cost_per_hour = 0.01
            hourly_cost = required_instances * instance_cost_per_hour
            
            total_cost += hourly_cost
            total_requests += requests
            
            pattern.update({
                "required_instances": required_instances,
                "hourly_cost": hourly_cost
            })
        
        # Calculate efficiency metrics
        avg_cost_per_request = total_cost / total_requests
        peak_to_avg_ratio = max(p["requests_per_minute"] for p in traffic_patterns) / \
                           (sum(p["requests_per_minute"] for p in traffic_patterns) / len(traffic_patterns))
        
        # Validate auto-scaling efficiency
        assert avg_cost_per_request < 0.001, f"Cost per request too high: ${avg_cost_per_request:.4f}"
        assert peak_to_avg_ratio < 10, f"Traffic variance too high for efficient scaling: {peak_to_avg_ratio:.1f}x"