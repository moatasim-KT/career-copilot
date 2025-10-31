#!/usr/bin/env python3
"""
Cost Efficiency and Free-Tier Compliance Validator
Validates system cost efficiency and ensures compliance with cloud provider free tiers
Requirements: 7.1, 7.2, 7.4
"""

import json
import logging
import math
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ResourceUsage:
    """Resource usage metrics"""
    resource_type: str
    current_usage: float
    projected_monthly_usage: float
    free_tier_limit: float
    unit: str
    cost_per_unit: float
    free_tier_compliant: bool
    excess_usage: float
    excess_cost: float


@dataclass
class CostProjection:
    """Cost projection for different user volumes"""
    user_count: int
    monthly_function_invocations: int
    monthly_compute_gb_seconds: float
    monthly_database_reads: int
    monthly_database_writes: int
    monthly_storage_gb: float
    monthly_network_gb: float
    total_monthly_cost: float
    cost_per_user: float
    free_tier_compliant: bool


class CostEfficiencyValidator:
    """Validates cost efficiency and free-tier compliance"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Google Cloud Free Tier limits (as of 2024)
        self.free_tier_limits = {
            "cloud_functions_invocations": 2_000_000,  # per month
            "cloud_functions_compute_time": 400_000,   # GB-seconds per month
            "firestore_reads": 50_000 * 30,            # 50K per day * 30 days
            "firestore_writes": 20_000 * 30,           # 20K per day * 30 days
            "firestore_deletes": 20_000 * 30,          # 20K per day * 30 days
            "firestore_storage": 1,                    # GB
            "cloud_storage": 5,                        # GB
            "network_egress": 1,                       # GB per month (to internet)
            "cloud_scheduler_jobs": 3,                 # jobs
            "cloud_logging": 50,                       # GB per month
        }
        
        # Pricing (simplified, in USD)
        self.pricing = {
            "cloud_functions_invocations": 0.0000004,  # per invocation after free tier
            "cloud_functions_compute_time": 0.0000025, # per GB-second after free tier
            "firestore_reads": 0.00000036,             # per read after free tier
            "firestore_writes": 0.0000018,             # per write after free tier
            "firestore_deletes": 0.0000002,            # per delete after free tier
            "firestore_storage": 0.18,                 # per GB per month after free tier
            "cloud_storage": 0.020,                    # per GB per month after free tier
            "network_egress": 0.12,                    # per GB after free tier
            "sendgrid_emails": 0.0,                    # 100 emails/day free, then $14.95/month
        }
        
        self.resource_usage: List[ResourceUsage] = []
        self.cost_projections: List[CostProjection] = []
    
    def calculate_user_activity_patterns(self) -> Dict[str, Any]:
        """Calculate typical user activity patterns"""
        logger.info("Calculating user activity patterns")
        
        # Define user behavior patterns based on typical job search activity
        patterns = {
            "daily_active_users_percentage": 0.3,  # 30% of users active daily
            "weekly_active_users_percentage": 0.7,  # 70% of users active weekly
            "monthly_active_users_percentage": 0.9,  # 90% of users active monthly
            
            # Per active user per day
            "job_searches_per_day": 5,
            "job_applications_per_day": 0.5,  # Average (some days 0, some days 2-3)
            "profile_updates_per_day": 0.1,
            "analytics_views_per_day": 2,
            "recommendation_requests_per_day": 3,
            
            # System-generated activities
            "morning_briefings_per_user": 1,  # Daily
            "evening_updates_per_user": 0.3,  # Only when applications made
            "skill_gap_analyses_per_user": 0.1,  # Weekly
            
            # Scheduled system activities (independent of user count)
            "job_ingestion_runs_per_day": 1,
            "analytics_generation_runs_per_day": 1,
            "system_maintenance_runs_per_day": 0.1,
        }
        
        return patterns
    
    def calculate_resource_usage_for_user_count(self, user_count: int) -> Dict[str, float]:
        """Calculate resource usage for a given number of users"""
        patterns = self.calculate_user_activity_patterns()
        
        # Calculate daily active users
        daily_active_users = int(user_count * patterns["daily_active_users_percentage"])
        
        # Function invocations per day
        daily_invocations = 0
        
        # User-triggered functions
        daily_invocations += daily_active_users * patterns["job_searches_per_day"]
        daily_invocations += daily_active_users * patterns["job_applications_per_day"]
        daily_invocations += daily_active_users * patterns["profile_updates_per_day"]
        daily_invocations += daily_active_users * patterns["analytics_views_per_day"]
        daily_invocations += daily_active_users * patterns["recommendation_requests_per_day"]
        
        # System-generated functions per user
        daily_invocations += user_count * patterns["morning_briefings_per_user"]
        daily_invocations += user_count * patterns["evening_updates_per_user"]
        daily_invocations += user_count * patterns["skill_gap_analyses_per_user"]
        
        # Scheduled system functions (independent of user count)
        daily_invocations += patterns["job_ingestion_runs_per_day"]
        daily_invocations += patterns["analytics_generation_runs_per_day"]
        daily_invocations += patterns["system_maintenance_runs_per_day"]
        
        # Compute time calculation (GB-seconds per day)
        daily_compute_time = 0
        
        # Different function types have different memory and execution time requirements
        function_specs = {
            "job_search": {"memory_gb": 0.128, "avg_duration_s": 1.5},
            "job_application": {"memory_gb": 0.128, "avg_duration_s": 0.8},
            "profile_update": {"memory_gb": 0.128, "avg_duration_s": 0.5},
            "analytics_view": {"memory_gb": 0.256, "avg_duration_s": 2.0},
            "recommendation": {"memory_gb": 0.256, "avg_duration_s": 3.0},
            "morning_briefing": {"memory_gb": 0.128, "avg_duration_s": 2.0},
            "evening_update": {"memory_gb": 0.128, "avg_duration_s": 1.5},
            "skill_gap_analysis": {"memory_gb": 0.256, "avg_duration_s": 5.0},
            "job_ingestion": {"memory_gb": 0.512, "avg_duration_s": 30.0},
            "analytics_generation": {"memory_gb": 0.256, "avg_duration_s": 10.0},
            "system_maintenance": {"memory_gb": 0.128, "avg_duration_s": 5.0},
        }
        
        # Calculate compute time for each function type
        daily_compute_time += (daily_active_users * patterns["job_searches_per_day"] * 
                              function_specs["job_search"]["memory_gb"] * function_specs["job_search"]["avg_duration_s"])
        daily_compute_time += (daily_active_users * patterns["job_applications_per_day"] * 
                              function_specs["job_application"]["memory_gb"] * function_specs["job_application"]["avg_duration_s"])
        daily_compute_time += (daily_active_users * patterns["profile_updates_per_day"] * 
                              function_specs["profile_update"]["memory_gb"] * function_specs["profile_update"]["avg_duration_s"])
        daily_compute_time += (daily_active_users * patterns["analytics_views_per_day"] * 
                              function_specs["analytics_view"]["memory_gb"] * function_specs["analytics_view"]["avg_duration_s"])
        daily_compute_time += (daily_active_users * patterns["recommendation_requests_per_day"] * 
                              function_specs["recommendation"]["memory_gb"] * function_specs["recommendation"]["avg_duration_s"])
        daily_compute_time += (user_count * patterns["morning_briefings_per_user"] * 
                              function_specs["morning_briefing"]["memory_gb"] * function_specs["morning_briefing"]["avg_duration_s"])
        daily_compute_time += (user_count * patterns["evening_updates_per_user"] * 
                              function_specs["evening_update"]["memory_gb"] * function_specs["evening_update"]["avg_duration_s"])
        daily_compute_time += (user_count * patterns["skill_gap_analyses_per_user"] * 
                              function_specs["skill_gap_analysis"]["memory_gb"] * function_specs["skill_gap_analysis"]["avg_duration_s"])
        daily_compute_time += (patterns["job_ingestion_runs_per_day"] * 
                              function_specs["job_ingestion"]["memory_gb"] * function_specs["job_ingestion"]["avg_duration_s"])
        daily_compute_time += (patterns["analytics_generation_runs_per_day"] * 
                              function_specs["analytics_generation"]["memory_gb"] * function_specs["analytics_generation"]["avg_duration_s"])
        daily_compute_time += (patterns["system_maintenance_runs_per_day"] * 
                              function_specs["system_maintenance"]["memory_gb"] * function_specs["system_maintenance"]["avg_duration_s"])
        
        # Database operations per day
        daily_reads = 0
        daily_writes = 0
        
        # Estimate database operations per function call
        daily_reads += daily_active_users * patterns["job_searches_per_day"] * 20  # Read jobs for search
        daily_reads += daily_active_users * patterns["job_applications_per_day"] * 5  # Read job details
        daily_writes += daily_active_users * patterns["job_applications_per_day"] * 2  # Update job status
        daily_reads += daily_active_users * patterns["profile_updates_per_day"] * 3  # Read current profile
        daily_writes += daily_active_users * patterns["profile_updates_per_day"] * 1  # Update profile
        daily_reads += daily_active_users * patterns["analytics_views_per_day"] * 10  # Read analytics data
        daily_reads += daily_active_users * patterns["recommendation_requests_per_day"] * 50  # Read jobs for matching
        daily_reads += user_count * patterns["morning_briefings_per_user"] * 15  # Read user data and jobs
        daily_reads += user_count * patterns["evening_updates_per_user"] * 10  # Read user activity
        daily_reads += user_count * patterns["skill_gap_analyses_per_user"] * 30  # Read jobs and user skills
        daily_writes += user_count * patterns["skill_gap_analyses_per_user"] * 1  # Write analysis results
        daily_reads += patterns["job_ingestion_runs_per_day"] * 100  # Check for duplicates
        daily_writes += patterns["job_ingestion_runs_per_day"] * 50  # Write new jobs
        daily_reads += patterns["analytics_generation_runs_per_day"] * 200  # Read all user data
        daily_writes += patterns["analytics_generation_runs_per_day"] * user_count * 0.1  # Write analytics
        
        # Storage calculation (GB)
        storage_per_user = 0.002  # 2MB per user (profile, preferences, etc.)
        jobs_per_user = 100  # Average jobs tracked per user
        storage_per_job = 0.003  # 3KB per job
        analytics_per_user = 12  # Monthly analytics records
        storage_per_analytics = 0.001  # 1KB per analytics record
        
        total_storage = (user_count * storage_per_user + 
                        user_count * jobs_per_user * storage_per_job +
                        user_count * analytics_per_user * storage_per_analytics)
        
        # Network usage (GB per day)
        # Estimate based on API responses and email notifications
        daily_network = (daily_invocations * 0.002 +  # 2KB average response size
                        user_count * (patterns["morning_briefings_per_user"] + patterns["evening_updates_per_user"]) * 0.05)  # 50KB email
        
        return {
            "daily_function_invocations": daily_invocations,
            "daily_compute_gb_seconds": daily_compute_time,
            "daily_database_reads": daily_reads,
            "daily_database_writes": daily_writes,
            "total_storage_gb": total_storage,
            "daily_network_gb": daily_network,
            "daily_active_users": daily_active_users
        }
    
    def validate_free_tier_compliance(self, user_count: int) -> List[ResourceUsage]:
        """Validate free tier compliance for given user count"""
        logger.info(f"Validating free tier compliance for {user_count} users")
        
        usage = self.calculate_resource_usage_for_user_count(user_count)
        
        # Project to monthly usage
        monthly_usage = {
            "function_invocations": usage["daily_function_invocations"] * 30,
            "compute_gb_seconds": usage["daily_compute_gb_seconds"] * 30,
            "database_reads": usage["daily_database_reads"] * 30,
            "database_writes": usage["daily_database_writes"] * 30,
            "storage_gb": usage["total_storage_gb"],  # Cumulative
            "network_gb": usage["daily_network_gb"] * 30,
        }
        
        resource_analyses = []
        
        # Analyze each resource type
        resources = [
            ("cloud_functions_invocations", monthly_usage["function_invocations"], "invocations"),
            ("cloud_functions_compute_time", monthly_usage["compute_gb_seconds"], "GB-seconds"),
            ("firestore_reads", monthly_usage["database_reads"], "reads"),
            ("firestore_writes", monthly_usage["database_writes"], "writes"),
            ("firestore_storage", monthly_usage["storage_gb"], "GB"),
            ("network_egress", monthly_usage["network_gb"], "GB"),
        ]
        
        for resource_type, current_usage, unit in resources:
            free_tier_limit = self.free_tier_limits.get(resource_type, 0)
            cost_per_unit = self.pricing.get(resource_type, 0)
            
            free_tier_compliant = current_usage <= free_tier_limit
            excess_usage = max(0, current_usage - free_tier_limit)
            excess_cost = excess_usage * cost_per_unit
            
            resource_analysis = ResourceUsage(
                resource_type=resource_type,
                current_usage=current_usage,
                projected_monthly_usage=current_usage,
                free_tier_limit=free_tier_limit,
                unit=unit,
                cost_per_unit=cost_per_unit,
                free_tier_compliant=free_tier_compliant,
                excess_usage=excess_usage,
                excess_cost=excess_cost
            )
            
            resource_analyses.append(resource_analysis)
            
            logger.info(f"{resource_type}: {current_usage:,.0f} {unit} "
                       f"(limit: {free_tier_limit:,.0f}, compliant: {free_tier_compliant})")
        
        return resource_analyses
    
    def generate_cost_projections(self, user_counts: List[int]) -> List[CostProjection]:
        """Generate cost projections for different user volumes"""
        logger.info(f"Generating cost projections for user counts: {user_counts}")
        
        projections = []
        
        for user_count in user_counts:
            usage = self.calculate_resource_usage_for_user_count(user_count)
            resource_analyses = self.validate_free_tier_compliance(user_count)
            
            # Calculate total monthly cost
            total_monthly_cost = sum(analysis.excess_cost for analysis in resource_analyses)
            
            # Add SendGrid cost if email volume exceeds free tier
            daily_emails = user_count * 1.3  # Morning briefing + evening updates
            monthly_emails = daily_emails * 30
            if monthly_emails > 3000:  # SendGrid free tier: 100 emails/day
                total_monthly_cost += 14.95  # Basic plan
            
            cost_per_user = total_monthly_cost / user_count if user_count > 0 else 0
            free_tier_compliant = all(analysis.free_tier_compliant for analysis in resource_analyses)
            
            projection = CostProjection(
                user_count=user_count,
                monthly_function_invocations=int(usage["daily_function_invocations"] * 30),
                monthly_compute_gb_seconds=usage["daily_compute_gb_seconds"] * 30,
                monthly_database_reads=int(usage["daily_database_reads"] * 30),
                monthly_database_writes=int(usage["daily_database_writes"] * 30),
                monthly_storage_gb=usage["total_storage_gb"],
                monthly_network_gb=usage["daily_network_gb"] * 30,
                total_monthly_cost=total_monthly_cost,
                cost_per_user=cost_per_user,
                free_tier_compliant=free_tier_compliant
            )
            
            projections.append(projection)
            
            logger.info(f"Users: {user_count}, Cost: ${total_monthly_cost:.2f}/month, "
                       f"Per User: ${cost_per_user:.4f}, Free Tier: {free_tier_compliant}")
        
        return projections
    
    def find_free_tier_user_limit(self) -> int:
        """Find maximum number of users that can be supported within free tier"""
        logger.info("Finding free tier user limit")
        
        # Binary search for maximum users within free tier
        low, high = 1, 10000
        max_free_tier_users = 0
        
        while low <= high:
            mid = (low + high) // 2
            resource_analyses = self.validate_free_tier_compliance(mid)
            
            if all(analysis.free_tier_compliant for analysis in resource_analyses):
                max_free_tier_users = mid
                low = mid + 1
            else:
                high = mid - 1
        
        logger.info(f"Maximum users within free tier: {max_free_tier_users}")
        return max_free_tier_users
    
    def analyze_cost_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Analyze opportunities for cost optimization"""
        logger.info("Analyzing cost optimization opportunities")
        
        optimizations = []
        
        # Function memory optimization
        optimizations.append({
            "category": "compute_optimization",
            "title": "Function Memory Optimization",
            "description": "Right-size Cloud Function memory allocation based on actual usage",
            "potential_savings": "10-30% reduction in compute costs",
            "implementation": "Monitor function memory usage and adjust allocation accordingly",
            "priority": "medium"
        })
        
        # Caching implementation
        optimizations.append({
            "category": "caching",
            "title": "Implement Redis Caching",
            "description": "Cache frequently accessed data to reduce database operations",
            "potential_savings": "40-60% reduction in database read costs",
            "implementation": "Implement Redis caching for job recommendations and user profiles",
            "priority": "high"
        })
        
        # Batch processing
        optimizations.append({
            "category": "batch_processing",
            "title": "Batch Processing Optimization",
            "description": "Process multiple operations in single function invocations",
            "potential_savings": "20-40% reduction in function invocation costs",
            "implementation": "Batch email notifications and analytics generation",
            "priority": "medium"
        })
        
        # Database query optimization
        optimizations.append({
            "category": "database_optimization",
            "title": "Database Query Optimization",
            "description": "Optimize database queries to reduce read/write operations",
            "potential_savings": "15-25% reduction in database costs",
            "implementation": "Add indexes, optimize query structure, implement pagination",
            "priority": "high"
        })
        
        # Cold start optimization
        optimizations.append({
            "category": "cold_start_optimization",
            "title": "Cold Start Optimization",
            "description": "Reduce function cold start times and frequency",
            "potential_savings": "5-15% reduction in compute costs",
            "implementation": "Keep functions warm, optimize initialization code",
            "priority": "low"
        })
        
        # Resource scheduling
        optimizations.append({
            "category": "scheduling_optimization",
            "title": "Smart Resource Scheduling",
            "description": "Schedule resource-intensive operations during off-peak hours",
            "potential_savings": "10-20% reduction in overall costs",
            "implementation": "Schedule job ingestion and analytics during low-traffic periods",
            "priority": "low"
        })
        
        return optimizations
    
    def run_comprehensive_cost_analysis(self) -> Dict[str, Any]:
        """Run comprehensive cost efficiency analysis"""
        logger.info("Starting comprehensive cost efficiency analysis")
        
        start_time = time.time()
        
        # 1. Find free tier user limit
        logger.info("1. Finding free tier user limit...")
        max_free_tier_users = self.find_free_tier_user_limit()
        
        # 2. Generate cost projections for different user volumes
        logger.info("2. Generating cost projections...")
        user_counts = [10, 50, 100, 250, 500, 1000, 2500, 5000]
        cost_projections = self.generate_cost_projections(user_counts)
        
        # 3. Validate current expected usage
        logger.info("3. Validating current expected usage...")
        expected_users = 100  # Expected initial user base
        current_resource_usage = self.validate_free_tier_compliance(expected_users)
        
        # 4. Analyze optimization opportunities
        logger.info("4. Analyzing cost optimization opportunities...")
        optimization_opportunities = self.analyze_cost_optimization_opportunities()
        
        # 5. Generate recommendations
        recommendations = self._generate_cost_recommendations(
            max_free_tier_users, cost_projections, current_resource_usage
        )
        
        end_time = time.time()
        analysis_duration = end_time - start_time
        
        # Generate comprehensive report
        report = {
            "summary": {
                "analysis_duration": analysis_duration,
                "max_free_tier_users": max_free_tier_users,
                "expected_users": expected_users,
                "expected_monthly_cost": next(
                    (p.total_monthly_cost for p in cost_projections if p.user_count == expected_users), 0
                ),
                "free_tier_compliant_at_expected_volume": next(
                    (p.free_tier_compliant for p in cost_projections if p.user_count == expected_users), False
                ),
                "optimization_opportunities": len(optimization_opportunities),
                "total_recommendations": len(recommendations)
            },
            "free_tier_analysis": {
                "max_users_supported": max_free_tier_users,
                "resource_limits": self.free_tier_limits,
                "pricing_model": self.pricing
            },
            "cost_projections": [asdict(projection) for projection in cost_projections],
            "current_resource_usage": [asdict(usage) for usage in current_resource_usage],
            "optimization_opportunities": optimization_opportunities,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log summary
        logger.info("=" * 60)
        logger.info("COST EFFICIENCY ANALYSIS COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Analysis Duration: {analysis_duration:.2f}s")
        logger.info(f"Max Free Tier Users: {max_free_tier_users}")
        logger.info(f"Expected Monthly Cost (100 users): ${report['summary']['expected_monthly_cost']:.2f}")
        logger.info(f"Free Tier Compliant: {report['summary']['free_tier_compliant_at_expected_volume']}")
        logger.info(f"Optimization Opportunities: {len(optimization_opportunities)}")
        
        return report
    
    def _generate_cost_recommendations(self, max_free_tier_users: int, 
                                     cost_projections: List[CostProjection],
                                     current_usage: List[ResourceUsage]) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # Free tier compliance recommendation
        if max_free_tier_users < 100:
            recommendations.append({
                "category": "free_tier_compliance",
                "priority": "high",
                "title": "Limited Free Tier Capacity",
                "description": f"System can only support {max_free_tier_users} users within free tier limits",
                "recommendation": "Implement cost optimizations to increase free tier capacity",
                "impact": "Extended free tier usage and reduced operational costs"
            })
        
        # Resource-specific recommendations
        for usage in current_usage:
            if not usage.free_tier_compliant:
                recommendations.append({
                    "category": "resource_optimization",
                    "priority": "high",
                    "title": f"Excessive {usage.resource_type.replace('_', ' ').title()}",
                    "description": f"Usage of {usage.current_usage:,.0f} {usage.unit} exceeds free tier limit of {usage.free_tier_limit:,.0f}",
                    "recommendation": f"Optimize {usage.resource_type} usage to stay within free tier",
                    "impact": f"Save ${usage.excess_cost:.2f}/month"
                })
        
        # Scaling recommendations
        expensive_projections = [p for p in cost_projections if p.cost_per_user > 0.10]
        if expensive_projections:
            min_expensive_users = min(p.user_count for p in expensive_projections)
            recommendations.append({
                "category": "scaling_strategy",
                "priority": "medium",
                "title": "High Cost Per User at Scale",
                "description": f"Cost per user exceeds $0.10 starting at {min_expensive_users} users",
                "recommendation": "Implement tiered pricing or premium features to offset costs",
                "impact": "Sustainable business model at scale"
            })
        
        # General optimization recommendations
        recommendations.extend([
            {
                "category": "monitoring",
                "priority": "medium",
                "title": "Cost Monitoring and Alerting",
                "description": "Implement real-time cost monitoring and budget alerts",
                "recommendation": "Set up Google Cloud billing alerts and cost monitoring dashboards",
                "impact": "Proactive cost management and budget control"
            },
            {
                "category": "resource_management",
                "priority": "low",
                "title": "Resource Lifecycle Management",
                "description": "Implement automated resource cleanup and lifecycle management",
                "recommendation": "Automatically clean up old data and unused resources",
                "impact": "Reduced storage costs and improved system efficiency"
            }
        ])
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save cost analysis report to file with path traversal protection"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cost_efficiency_report_{timestamp}.json"
        
        # Security: Sanitize filename to prevent path traversal attacks (CWE-22)
        from pathlib import Path
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
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Cost efficiency report saved to: {output_path}")
        return str(output_path)


def main():
    """Main function to run cost efficiency validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cost Efficiency and Free-Tier Compliance Validator")
    parser.add_argument("--output", help="Output report file")
    parser.add_argument("--expected-users", type=int, default=100, help="Expected number of users")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize validator
    validator = CostEfficiencyValidator()
    
    try:
        # Run comprehensive analysis
        report = validator.run_comprehensive_cost_analysis()
        
        # Save report
        report_file = validator.save_report(report, args.output)
        
        # Print summary
        print("\n" + "=" * 80)
        print("COST EFFICIENCY ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"Max Free Tier Users: {report['summary']['max_free_tier_users']}")
        print(f"Expected Monthly Cost ({args.expected_users} users): ${report['summary']['expected_monthly_cost']:.2f}")
        print(f"Free Tier Compliant: {'✅' if report['summary']['free_tier_compliant_at_expected_volume'] else '❌'}")
        print(f"Optimization Opportunities: {report['summary']['optimization_opportunities']}")
        print(f"Recommendations: {report['summary']['total_recommendations']}")
        print(f"Report saved to: {report_file}")
        
        # Exit with appropriate code
        if report['summary']['free_tier_compliant_at_expected_volume']:
            print("\n✅ Cost efficiency validated - free tier compliant!")
            sys.exit(0)
        else:
            print("\n⚠️  Cost optimization required")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Cost efficiency validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()