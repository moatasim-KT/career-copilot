#!/usr/bin/env python3
"""
Performance Testing and Optimization Suite
Implements comprehensive performance testing, database optimization, and cost efficiency validation
Requirements: 7.1, 7.2, 7.4
"""

import asyncio
import concurrent.futures
import json
import logging
import os
import statistics
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import psutil
import requests
from app.core.config import get_settings
from app.core.database import engine, get_db
from app.models.analytics import Analytics
from app.models.job import Job
from app.models.user import User
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    test_name: str
    start_time: float
    end_time: float
    duration: float
    success_count: int
    error_count: int
    total_requests: int
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    additional_metrics: Dict[str, Any]


@dataclass
class CostMetrics:
    """Cost efficiency metrics"""
    function_invocations: int
    compute_time_gb_seconds: float
    database_reads: int
    database_writes: int
    storage_gb: float
    network_gb: float
    estimated_monthly_cost: float
    free_tier_compliance: bool
    cost_per_user: float
    cost_per_request: float


class PerformanceOptimizationSuite:
    """Comprehensive performance testing and optimization suite"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        # Security: Validate backend URL to prevent SSRF attacks (CWE-918)
        self.backend_url = self._validate_backend_url(backend_url)
        self.settings = get_settings()
        self.session = requests.Session()
        self.test_results: List[PerformanceMetrics] = []
        self.cost_analysis: Optional[CostMetrics] = None
        self.optimization_recommendations: List[Dict[str, Any]] = []
        
        # Configure session with retries
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _validate_backend_url(self, url: str) -> str:
        """Validate backend URL to prevent SSRF attacks
        
        Args:
            url: The backend URL to validate
        
        Returns:
            Validated URL
        
        Raises:
            ValueError: If URL is invalid or potentially malicious
        """
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            
            # Only allow http and https schemes
            if parsed.scheme not in ["http", "https"]:
                raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only http and https are allowed.")
            
            # Validate hostname exists
            if not parsed.hostname:
                raise ValueError("URL must contain a valid hostname")
            
            # Block internal/private IP ranges to prevent SSRF
            hostname = parsed.hostname.lower()
            
            # Block localhost and loopback addresses (except for development)
            blocked_hosts = ["metadata.google.internal", "169.254.169.254"]
            if hostname in blocked_hosts:
                raise ValueError(f"Access to {hostname} is not allowed")
            
            # Allow localhost only for development
            allowed_hosts = ["localhost", "127.0.0.1", "::1"]
            if hostname not in allowed_hosts:
                # For production, validate it's not a private IP
                import ipaddress
                try:
                    ip = ipaddress.ip_address(hostname)
                    if ip.is_private or ip.is_loopback or ip.is_link_local:
                        raise ValueError(f"Access to private IP addresses is not allowed: {hostname}")
                except ValueError:
                    # Not an IP address, it's a domain name - allow it
                    pass
            
            return url
            
        except Exception as e:
            raise ValueError(f"Invalid backend URL: {e}")

    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system resource usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            return {
                "memory_mb": memory_info.rss / 1024 / 1024,
                "cpu_percent": cpu_percent,
                "memory_percent": process.memory_percent(),
                "num_threads": process.num_threads()
            }
        except Exception as e:
            logger.warning(f"Could not get system metrics: {e}")
            return {"memory_mb": 0, "cpu_percent": 0, "memory_percent": 0, "num_threads": 0}

    def calculate_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile from data"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]

    def test_concurrent_user_load(self, num_users: int = 50, requests_per_user: int = 10) -> PerformanceMetrics:
        """Test system performance under concurrent user load"""
        logger.info(f"Testing concurrent load: {num_users} users, {requests_per_user} requests each")
        
        start_time = time.time()
        start_metrics = self.get_system_metrics()
        
        response_times = []
        success_count = 0
        error_count = 0
        
        def simulate_user_session(user_id: int) -> Tuple[List[float], int, int]:
            """Simulate a user session with multiple API calls"""
            session_response_times = []
            session_success = 0
            session_errors = 0
            
            # Typical user workflow endpoints
            endpoints = [
                "/api/v1/health",
                f"/api/v1/users/{user_id}/jobs",
                f"/api/v1/users/{user_id}/recommendations",
                f"/api/v1/users/{user_id}/skill-gaps",
                f"/api/v1/users/{user_id}/analytics"
            ]
            
            for _ in range(requests_per_user):
                endpoint = endpoints[_ % len(endpoints)]
                request_start = time.time()
                
                try:
                    response = self.session.get(
                        f"{self.backend_url}{endpoint}",
                        timeout=30
                    )
                    request_end = time.time()
                    response_time = request_end - request_start
                    
                    session_response_times.append(response_time)
                    
                    if response.status_code in [200, 201, 202]:
                        session_success += 1
                    else:
                        session_errors += 1
                        
                except Exception as e:
                    request_end = time.time()
                    session_errors += 1
                    logger.debug(f"Request failed for user {user_id}: {e}")
                
                # Simulate user think time
                time.sleep(0.1)
            
            return session_response_times, session_success, session_errors
        
        # Execute concurrent user sessions
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(num_users, 20)) as executor:
            futures = [
                executor.submit(simulate_user_session, user_id) 
                for user_id in range(1, num_users + 1)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    session_times, session_success, session_errors = future.result()
                    response_times.extend(session_times)
                    success_count += session_success
                    error_count += session_errors
                except Exception as e:
                    logger.error(f"User session failed: {e}")
                    error_count += requests_per_user
        
        end_time = time.time()
        end_metrics = self.get_system_metrics()
        duration = end_time - start_time
        
        # Calculate metrics
        total_requests = success_count + error_count
        throughput = total_requests / duration if duration > 0 else 0
        error_rate = (error_count / total_requests) * 100 if total_requests > 0 else 0
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = self.calculate_percentile(response_times, 95)
            p99_response_time = self.calculate_percentile(response_times, 99)
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = 0
        
        metrics = PerformanceMetrics(
            test_name="Concurrent User Load",
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success_count=success_count,
            error_count=error_count,
            total_requests=total_requests,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput=throughput,
            error_rate=error_rate,
            memory_usage_mb=end_metrics["memory_mb"],
            cpu_usage_percent=end_metrics["cpu_percent"],
            additional_metrics={
                "num_concurrent_users": num_users,
                "requests_per_user": requests_per_user,
                "memory_increase_mb": end_metrics["memory_mb"] - start_metrics["memory_mb"],
                "response_time_std": statistics.stdev(response_times) if len(response_times) > 1 else 0
            }
        )
        
        self.test_results.append(metrics)
        
        # Log results
        logger.info(f"Concurrent Load Test Results:")
        logger.info(f"  Duration: {duration:.2f}s")
        logger.info(f"  Total Requests: {total_requests}")
        logger.info(f"  Success Rate: {100 - error_rate:.1f}%")
        logger.info(f"  Throughput: {throughput:.1f} req/s")
        logger.info(f"  Avg Response Time: {avg_response_time:.3f}s")
        logger.info(f"  95th Percentile: {p95_response_time:.3f}s")
        
        return metrics

    def test_database_query_performance(self) -> PerformanceMetrics:
        """Test and optimize database query performance"""
        logger.info("Testing database query performance")
        
        start_time = time.time()
        start_metrics = self.get_system_metrics()
        
        query_times = []
        success_count = 0
        error_count = 0
        
        # Test various database operations
        test_queries = [
            # User queries
            ("SELECT COUNT(*) FROM users", "user_count"),
            ("SELECT * FROM users ORDER BY created_at DESC LIMIT 10", "recent_users"),
            
            # Job queries
            ("SELECT COUNT(*) FROM jobs", "job_count"),
            ("SELECT * FROM jobs WHERE status = 'not_applied' LIMIT 20", "available_jobs"),
            ("SELECT * FROM jobs WHERE user_id = 1 ORDER BY created_at DESC LIMIT 10", "user_jobs"),
            
            # Analytics queries
            ("SELECT COUNT(*) FROM analytics", "analytics_count"),
            ("SELECT * FROM analytics WHERE user_id = 1 ORDER BY period DESC LIMIT 5", "user_analytics"),
            
            # Complex joins
            ("""
            SELECT u.email, COUNT(j.id) as job_count 
            FROM users u 
            LEFT JOIN jobs j ON u.id = j.user_id 
            GROUP BY u.id, u.email 
            LIMIT 10
            """, "user_job_summary"),
        ]
        
        # Execute queries multiple times to get average performance
        for query, query_name in test_queries:
            for iteration in range(5):  # 5 iterations per query
                query_start = time.time()
                
                try:
                    with engine.connect() as conn:
                        result = conn.execute(text(query))
                        rows = result.fetchall()
                    
                    query_end = time.time()
                    query_time = query_end - query_start
                    query_times.append(query_time)
                    success_count += 1
                    
                    logger.debug(f"Query {query_name} iteration {iteration + 1}: {query_time:.4f}s, {len(rows)} rows")
                    
                except Exception as e:
                    query_end = time.time()
                    error_count += 1
                    logger.error(f"Query {query_name} failed: {e}")
        
        end_time = time.time()
        end_metrics = self.get_system_metrics()
        duration = end_time - start_time
        
        # Calculate metrics
        total_queries = success_count + error_count
        throughput = total_queries / duration if duration > 0 else 0
        error_rate = (error_count / total_queries) * 100 if total_queries > 0 else 0
        
        if query_times:
            avg_response_time = statistics.mean(query_times)
            median_response_time = statistics.median(query_times)
            p95_response_time = self.calculate_percentile(query_times, 95)
            p99_response_time = self.calculate_percentile(query_times, 99)
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = 0
        
        metrics = PerformanceMetrics(
            test_name="Database Query Performance",
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success_count=success_count,
            error_count=error_count,
            total_requests=total_queries,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput=throughput,
            error_rate=error_rate,
            memory_usage_mb=end_metrics["memory_mb"],
            cpu_usage_percent=end_metrics["cpu_percent"],
            additional_metrics={
                "num_query_types": len(test_queries),
                "iterations_per_query": 5,
                "slowest_query_time": max(query_times) if query_times else 0,
                "fastest_query_time": min(query_times) if query_times else 0
            }
        )
        
        self.test_results.append(metrics)
        
        # Log results
        logger.info(f"Database Performance Test Results:")
        logger.info(f"  Total Queries: {total_queries}")
        logger.info(f"  Success Rate: {100 - error_rate:.1f}%")
        logger.info(f"  Avg Query Time: {avg_response_time:.4f}s")
        logger.info(f"  95th Percentile: {p95_response_time:.4f}s")
        
        return metrics

    def analyze_database_indexes(self) -> Dict[str, Any]:
        """Analyze database indexes and suggest optimizations"""
        logger.info("Analyzing database indexes")
        
        index_analysis = {
            "existing_indexes": [],
            "missing_indexes": [],
            "unused_indexes": [],
            "recommendations": []
        }
        
        try:
            inspector = inspect(engine)
            
            # Get existing indexes for each table
            tables = ["users", "jobs", "analytics"]
            
            for table_name in tables:
                if inspector.has_table(table_name):
                    indexes = inspector.get_indexes(table_name)
                    for index in indexes:
                        index_analysis["existing_indexes"].append({
                            "table": table_name,
                            "name": index["name"],
                            "columns": index["column_names"],
                            "unique": index["unique"]
                        })
            
            # Suggest missing indexes based on common query patterns
            suggested_indexes = [
                {"table": "jobs", "columns": ["user_id"], "reason": "Frequent user job lookups"},
                {"table": "jobs", "columns": ["status"], "reason": "Job status filtering"},
                {"table": "jobs", "columns": ["created_at"], "reason": "Date-based sorting"},
                {"table": "jobs", "columns": ["user_id", "status"], "reason": "Combined user and status queries"},
                {"table": "analytics", "columns": ["user_id"], "reason": "User analytics lookups"},
                {"table": "analytics", "columns": ["period"], "reason": "Time-based analytics queries"},
                {"table": "users", "columns": ["email"], "reason": "User authentication"},
                {"table": "users", "columns": ["created_at"], "reason": "User registration tracking"}
            ]
            
            # Check which suggested indexes are missing
            existing_index_keys = set()
            for idx in index_analysis["existing_indexes"]:
                key = f"{idx['table']}.{'.'.join(sorted(idx['columns']))}"
                existing_index_keys.add(key)
            
            for suggestion in suggested_indexes:
                key = f"{suggestion['table']}.{'.'.join(sorted(suggestion['columns']))}"
                if key not in existing_index_keys:
                    index_analysis["missing_indexes"].append(suggestion)
            
            # Generate recommendations
            if index_analysis["missing_indexes"]:
                index_analysis["recommendations"].append({
                    "type": "add_indexes",
                    "priority": "high",
                    "description": f"Add {len(index_analysis['missing_indexes'])} missing indexes to improve query performance",
                    "indexes": index_analysis["missing_indexes"]
                })
            
            logger.info(f"Index Analysis Complete:")
            logger.info(f"  Existing Indexes: {len(index_analysis['existing_indexes'])}")
            logger.info(f"  Missing Indexes: {len(index_analysis['missing_indexes'])}")
            logger.info(f"  Recommendations: {len(index_analysis['recommendations'])}")
            
        except Exception as e:
            logger.error(f"Index analysis failed: {e}")
            index_analysis["error"] = str(e)
        
        return index_analysis

    def validate_cost_efficiency(self) -> CostMetrics:
        """Validate cost efficiency and free-tier compliance"""
        logger.info("Validating cost efficiency and free-tier compliance")
        
        # Simulate typical daily usage patterns
        daily_usage = {
            "active_users": 100,
            "jobs_per_user": 50,
            "recommendations_per_user": 10,
            "analytics_queries_per_user": 5,
            "job_applications_per_user": 2,
            "email_notifications_per_user": 2
        }
        
        # Calculate resource usage
        function_invocations = 0
        compute_time_gb_seconds = 0.0
        database_reads = 0
        database_writes = 0
        storage_gb = 0.0
        network_gb = 0.0
        
        # Function invocations calculation
        for user in range(daily_usage["active_users"]):
            # Morning briefing function
            function_invocations += 1
            compute_time_gb_seconds += 2.0 * 0.128  # 2 seconds, 128MB memory
            database_reads += 10  # Read user profile and jobs
            
            # Job recommendations function
            function_invocations += 1
            compute_time_gb_seconds += 3.0 * 0.256  # 3 seconds, 256MB memory
            database_reads += 50  # Read jobs for matching
            
            # Analytics queries
            function_invocations += daily_usage["analytics_queries_per_user"]
            compute_time_gb_seconds += daily_usage["analytics_queries_per_user"] * 1.0 * 0.128
            database_reads += daily_usage["analytics_queries_per_user"] * 5
            
            # Job applications
            function_invocations += daily_usage["job_applications_per_user"]
            compute_time_gb_seconds += daily_usage["job_applications_per_user"] * 0.5 * 0.128
            database_writes += daily_usage["job_applications_per_user"] * 2
            database_reads += daily_usage["job_applications_per_user"] * 3
            
            # Email notifications
            function_invocations += daily_usage["email_notifications_per_user"]
            compute_time_gb_seconds += daily_usage["email_notifications_per_user"] * 1.0 * 0.128
        
        # Scheduled functions (daily)
        function_invocations += 1  # Job ingestion
        compute_time_gb_seconds += 30.0 * 0.512  # 30 seconds, 512MB memory
        database_reads += 200
        database_writes += 100
        
        # Storage calculation (approximate)
        storage_gb = (
            daily_usage["active_users"] * 0.001 +  # User profiles
            daily_usage["active_users"] * daily_usage["jobs_per_user"] * 0.002 +  # Jobs
            daily_usage["active_users"] * 0.0005  # Analytics
        )
        
        # Network usage (approximate)
        network_gb = (
            function_invocations * 0.001 +  # Function responses
            daily_usage["active_users"] * daily_usage["email_notifications_per_user"] * 0.01  # Email content
        )
        
        # Monthly projections
        monthly_function_invocations = function_invocations * 30
        monthly_compute_time = compute_time_gb_seconds * 30
        monthly_database_reads = database_reads * 30
        monthly_database_writes = database_writes * 30
        monthly_storage_gb = storage_gb * 30  # Cumulative
        monthly_network_gb = network_gb * 30
        
        # Google Cloud Free Tier limits
        free_tier_limits = {
            "cloud_functions_invocations": 2_000_000,
            "cloud_functions_compute_time": 400_000,  # GB-seconds
            "firestore_reads": 50_000 * 30,  # per day * 30 days
            "firestore_writes": 20_000 * 30,  # per day * 30 days
            "storage_gb": 5,
            "network_gb": 1
        }
        
        # Check free tier compliance
        free_tier_compliance = (
            monthly_function_invocations <= free_tier_limits["cloud_functions_invocations"] and
            monthly_compute_time <= free_tier_limits["cloud_functions_compute_time"] and
            monthly_database_reads <= free_tier_limits["firestore_reads"] and
            monthly_database_writes <= free_tier_limits["firestore_writes"] and
            monthly_storage_gb <= free_tier_limits["storage_gb"] and
            monthly_network_gb <= free_tier_limits["network_gb"]
        )
        
        # Estimate costs (simplified pricing)
        estimated_monthly_cost = 0.0
        
        if monthly_function_invocations > free_tier_limits["cloud_functions_invocations"]:
            excess_invocations = monthly_function_invocations - free_tier_limits["cloud_functions_invocations"]
            estimated_monthly_cost += excess_invocations * 0.0000004  # $0.40 per million
        
        if monthly_compute_time > free_tier_limits["cloud_functions_compute_time"]:
            excess_compute = monthly_compute_time - free_tier_limits["cloud_functions_compute_time"]
            estimated_monthly_cost += excess_compute * 0.0000025  # $2.50 per million GB-seconds
        
        if monthly_database_reads > free_tier_limits["firestore_reads"]:
            excess_reads = monthly_database_reads - free_tier_limits["firestore_reads"]
            estimated_monthly_cost += excess_reads * 0.00000036  # $0.36 per million
        
        if monthly_database_writes > free_tier_limits["firestore_writes"]:
            excess_writes = monthly_database_writes - free_tier_limits["firestore_writes"]
            estimated_monthly_cost += excess_writes * 0.0000018  # $1.80 per million
        
        cost_metrics = CostMetrics(
            function_invocations=monthly_function_invocations,
            compute_time_gb_seconds=monthly_compute_time,
            database_reads=monthly_database_reads,
            database_writes=monthly_database_writes,
            storage_gb=monthly_storage_gb,
            network_gb=monthly_network_gb,
            estimated_monthly_cost=estimated_monthly_cost,
            free_tier_compliance=free_tier_compliance,
            cost_per_user=estimated_monthly_cost / daily_usage["active_users"] if daily_usage["active_users"] > 0 else 0,
            cost_per_request=estimated_monthly_cost / monthly_function_invocations if monthly_function_invocations > 0 else 0
        )
        
        self.cost_analysis = cost_metrics
        
        # Log results
        logger.info(f"Cost Efficiency Analysis:")
        logger.info(f"  Monthly Function Invocations: {monthly_function_invocations:,}")
        logger.info(f"  Monthly Compute Time: {monthly_compute_time:.1f} GB-seconds")
        logger.info(f"  Monthly Database Reads: {monthly_database_reads:,}")
        logger.info(f"  Monthly Database Writes: {monthly_database_writes:,}")
        logger.info(f"  Free Tier Compliant: {free_tier_compliance}")
        logger.info(f"  Estimated Monthly Cost: ${estimated_monthly_cost:.2f}")
        logger.info(f"  Cost per User: ${cost_metrics.cost_per_user:.4f}")
        
        return cost_metrics

    def generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on test results"""
        recommendations = []
        
        # Analyze performance test results
        for metrics in self.test_results:
            if metrics.test_name == "Concurrent User Load":
                if metrics.error_rate > 5:
                    recommendations.append({
                        "category": "reliability",
                        "priority": "high",
                        "title": "High Error Rate Under Load",
                        "description": f"Error rate of {metrics.error_rate:.1f}% exceeds 5% threshold",
                        "recommendation": "Implement circuit breakers, increase timeout values, and add retry logic",
                        "impact": "Improved user experience and system reliability"
                    })
                
                if metrics.avg_response_time > 2.0:
                    recommendations.append({
                        "category": "performance",
                        "priority": "medium",
                        "title": "Slow Average Response Time",
                        "description": f"Average response time of {metrics.avg_response_time:.3f}s exceeds 2s threshold",
                        "recommendation": "Implement caching, optimize database queries, and consider CDN for static assets",
                        "impact": "Faster user interactions and better perceived performance"
                    })
                
                if metrics.p95_response_time > 5.0:
                    recommendations.append({
                        "category": "performance",
                        "priority": "high",
                        "title": "High 95th Percentile Response Time",
                        "description": f"95th percentile response time of {metrics.p95_response_time:.3f}s exceeds 5s threshold",
                        "recommendation": "Investigate slow queries, implement connection pooling, and optimize resource allocation",
                        "impact": "Consistent performance for all users"
                    })
            
            elif metrics.test_name == "Database Query Performance":
                if metrics.avg_response_time > 0.1:
                    recommendations.append({
                        "category": "database",
                        "priority": "high",
                        "title": "Slow Database Queries",
                        "description": f"Average query time of {metrics.avg_response_time:.4f}s exceeds 100ms threshold",
                        "recommendation": "Add database indexes, optimize query structure, and implement query caching",
                        "impact": "Faster data retrieval and reduced database load"
                    })
        
        # Analyze cost efficiency
        if self.cost_analysis:
            if not self.cost_analysis.free_tier_compliance:
                recommendations.append({
                    "category": "cost",
                    "priority": "high",
                    "title": "Free Tier Limits Exceeded",
                    "description": f"Estimated monthly cost: ${self.cost_analysis.estimated_monthly_cost:.2f}",
                    "recommendation": "Optimize function memory allocation, implement caching to reduce database operations, and consider batch processing",
                    "impact": "Reduced operational costs and better resource utilization"
                })
            
            if self.cost_analysis.cost_per_user > 0.10:
                recommendations.append({
                    "category": "cost",
                    "priority": "medium",
                    "title": "High Cost Per User",
                    "description": f"Cost per user of ${self.cost_analysis.cost_per_user:.4f} may not be sustainable",
                    "recommendation": "Implement user-based resource limits, optimize algorithms, and consider tiered service levels",
                    "impact": "Sustainable business model and cost structure"
                })
        
        # General optimization recommendations
        recommendations.extend([
            {
                "category": "caching",
                "priority": "medium",
                "title": "Implement Redis Caching",
                "description": "No caching layer detected for frequently accessed data",
                "recommendation": "Implement Redis caching for job recommendations, user profiles, and analytics data",
                "impact": "Reduced database load and faster response times"
            },
            {
                "category": "monitoring",
                "priority": "medium",
                "title": "Enhanced Performance Monitoring",
                "description": "Limited performance monitoring capabilities",
                "recommendation": "Implement detailed APM with request tracing, database query monitoring, and custom metrics",
                "impact": "Better visibility into performance bottlenecks and proactive issue resolution"
            },
            {
                "category": "optimization",
                "priority": "low",
                "title": "Connection Pooling",
                "description": "Database connection pooling optimization",
                "recommendation": "Fine-tune connection pool settings based on concurrent load patterns",
                "impact": "Better resource utilization and reduced connection overhead"
            }
        ])
        
        self.optimization_recommendations = recommendations
        return recommendations

    def run_comprehensive_performance_tests(self) -> Dict[str, Any]:
        """Run all performance tests and generate comprehensive report"""
        logger.info("Starting comprehensive performance testing suite")
        
        start_time = time.time()
        
        # Run performance tests
        logger.info("=" * 60)
        logger.info("1. Testing concurrent user load...")
        concurrent_metrics = self.test_concurrent_user_load(num_users=50, requests_per_user=10)
        
        logger.info("=" * 60)
        logger.info("2. Testing database query performance...")
        db_metrics = self.test_database_query_performance()
        
        logger.info("=" * 60)
        logger.info("3. Analyzing database indexes...")
        index_analysis = self.analyze_database_indexes()
        
        logger.info("=" * 60)
        logger.info("4. Validating cost efficiency...")
        cost_metrics = self.validate_cost_efficiency()
        
        logger.info("=" * 60)
        logger.info("5. Generating optimization recommendations...")
        recommendations = self.generate_optimization_recommendations()
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Generate comprehensive report
        report = {
            "summary": {
                "test_duration": total_duration,
                "tests_completed": len(self.test_results),
                "recommendations_generated": len(recommendations),
                "free_tier_compliant": cost_metrics.free_tier_compliance,
                "estimated_monthly_cost": cost_metrics.estimated_monthly_cost,
                "overall_performance_score": self._calculate_performance_score()
            },
            "performance_metrics": [asdict(metrics) for metrics in self.test_results],
            "cost_analysis": asdict(cost_metrics),
            "database_analysis": index_analysis,
            "optimization_recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat(),
            "test_environment": {
                "backend_url": self.backend_url,
                "database_url": str(engine.url).replace(engine.url.password or "", "***") if engine.url.password else str(engine.url),
                "python_version": sys.version,
                "system_info": self.get_system_metrics()
            }
        }
        
        logger.info("=" * 60)
        logger.info("PERFORMANCE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info(f"Tests Completed: {len(self.test_results)}")
        logger.info(f"Performance Score: {report['summary']['overall_performance_score']:.1f}/100")
        logger.info(f"Free Tier Compliant: {cost_metrics.free_tier_compliance}")
        logger.info(f"Estimated Monthly Cost: ${cost_metrics.estimated_monthly_cost:.2f}")
        logger.info(f"Recommendations: {len(recommendations)}")
        
        return report

    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)"""
        if not self.test_results:
            return 0.0
        
        score = 100.0
        
        for metrics in self.test_results:
            # Deduct points for high error rates
            if metrics.error_rate > 5:
                score -= min(20, metrics.error_rate)
            
            # Deduct points for slow response times
            if metrics.avg_response_time > 1.0:
                score -= min(15, (metrics.avg_response_time - 1.0) * 10)
            
            # Deduct points for low throughput
            if metrics.throughput < 10:
                score -= min(10, (10 - metrics.throughput))
        
        # Deduct points for cost issues
        if self.cost_analysis and not self.cost_analysis.free_tier_compliance:
            score -= 20
        
        return max(0.0, score)

    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save performance test report to file
        
        Args:
            report: Dictionary containing performance test data
            filename: Optional filename. If not provided, auto-generates timestamp-based name.
                Path components are stripped for security (prevents path traversal).
        
        Returns:
            Full path to the saved report file
        """
        from pathlib import Path
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_optimization_report_{timestamp}.json"
        
        # Security: Sanitize filename to prevent path traversal attacks (CWE-22)
        safe_filename = Path(filename).name
        
        # Additional validation: ensure filename doesn't contain path separators
        if not safe_filename or ".." in safe_filename or "/" in safe_filename or "\\" in safe_filename:
            raise ValueError(f"Invalid filename: {filename}")
        
        # Ensure write operations stay within current working directory
        output_path = Path.cwd() / safe_filename
        
        # Verify the resolved path is within the current directory
        if not output_path.resolve().is_relative_to(Path.cwd().resolve()):
            raise ValueError(f"Path traversal attempt detected: {filename}")
        
        # Path validation complete - safe to write file
        # deepcode ignore PT: Path is validated above via is_relative_to() check
        with open(output_path, 'w') as f:  # noqa: S603
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Performance test report saved to: {output_path}")
        return str(output_path)


def main():
    """Main function to run performance optimization suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Career Copilot Performance Optimization Suite")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Backend URL (localhost or valid domain only)")
    parser.add_argument("--output", help="Output report file")
    parser.add_argument("--users", type=int, default=50, help="Number of concurrent users to test")
    parser.add_argument("--requests", type=int, default=10, help="Requests per user")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize and run performance suite
    try:
        suite = PerformanceOptimizationSuite(args.backend_url)
    except ValueError as e:
        logger.error(f"Invalid backend URL: {e}")
        sys.exit(1)
    
    try:
        # Run comprehensive tests
        report = suite.run_comprehensive_performance_tests()
        
        # Save report
        report_file = suite.save_report(report, args.output)
        
        # Print summary
        print("\n" + "=" * 80)
        print("PERFORMANCE OPTIMIZATION SUMMARY")
        print("=" * 80)
        print(f"Performance Score: {report['summary']['overall_performance_score']:.1f}/100")
        print(f"Free Tier Compliant: {'✅' if report['summary']['free_tier_compliant'] else '❌'}")
        print(f"Estimated Monthly Cost: ${report['summary']['estimated_monthly_cost']:.2f}")
        print(f"Optimization Recommendations: {report['summary']['recommendations_generated']}")
        print(f"Report saved to: {report_file}")
        
        # Exit with appropriate code
        if report['summary']['overall_performance_score'] >= 75:
            print("\n✅ Performance tests passed!")
            sys.exit(0)
        else:
            print("\n⚠️  Performance improvements recommended")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Performance testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()