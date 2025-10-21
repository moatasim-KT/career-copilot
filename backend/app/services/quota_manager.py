"""
Quota management service for handling API limits and fallback mechanisms
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session
from app.core.database import get_db


logger = logging.getLogger(__name__)


class QuotaStatus(Enum):
    """Quota status enumeration"""
    AVAILABLE = "available"
    LIMITED = "limited"
    EXHAUSTED = "exhausted"
    BLOCKED = "blocked"


@dataclass
class QuotaLimit:
    """Quota limit configuration"""
    daily_limit: int
    hourly_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    rate_limit_seconds: float = 1.0
    burst_limit: Optional[int] = None
    reset_time: Optional[str] = None  # "00:00" for daily reset


@dataclass
class QuotaUsage:
    """Current quota usage tracking"""
    api_name: str
    date: datetime = field(default_factory=lambda: datetime.utcnow().date())
    daily_requests: int = 0
    hourly_requests: int = 0
    monthly_requests: int = 0
    last_request_time: Optional[datetime] = None
    blocked_until: Optional[datetime] = None
    consecutive_failures: int = 0
    last_reset: Optional[datetime] = None


class QuotaManager:
    """Manages API quotas and implements fallback mechanisms"""
    
    def __init__(self):
        self.quota_limits = self._initialize_quota_limits()
        self.quota_usage = {}
        self.fallback_chains = self._initialize_fallback_chains()
        
    def _initialize_quota_limits(self) -> Dict[str, QuotaLimit]:
        """Initialize quota limits for different APIs"""
        return {
            # Free tier APIs
            'adzuna': QuotaLimit(
                daily_limit=33,  # 1000/month ≈ 33/day
                monthly_limit=1000,
                rate_limit_seconds=1.0,
                burst_limit=5
            ),
            'usajobs': QuotaLimit(
                daily_limit=1000,
                hourly_limit=100,
                rate_limit_seconds=0.5,
                burst_limit=10
            ),
            'github_jobs': QuotaLimit(
                daily_limit=500,
                hourly_limit=50,
                rate_limit_seconds=1.0,
                burst_limit=5
            ),
            'remoteok': QuotaLimit(
                daily_limit=100,
                hourly_limit=20,
                rate_limit_seconds=3.0,
                burst_limit=2
            ),
            'jobspresso': QuotaLimit(
                daily_limit=100,
                rate_limit_seconds=2.0,
                burst_limit=3
            ),
            
            # RSS feeds (more lenient)
            'rss_feeds': QuotaLimit(
                daily_limit=1000,
                hourly_limit=100,
                rate_limit_seconds=0.5,
                burst_limit=20
            ),
            
            # Web scraping (most restrictive)
            'indeed_scraper': QuotaLimit(
                daily_limit=200,
                hourly_limit=25,
                rate_limit_seconds=5.0,
                burst_limit=2
            ),
            'linkedin_scraper': QuotaLimit(
                daily_limit=100,
                hourly_limit=15,
                rate_limit_seconds=8.0,
                burst_limit=1
            )
        }
    
    def _initialize_fallback_chains(self) -> Dict[str, List[str]]:
        """Initialize fallback chains for different job sources"""
        return {
            'government_jobs': ['usajobs'],
            'tech_jobs': ['github_jobs', 'remoteok', 'rss_feeds', 'indeed_scraper'],
            'remote_jobs': ['remoteok', 'github_jobs', 'rss_feeds'],
            'general_jobs': ['adzuna', 'usajobs', 'rss_feeds', 'indeed_scraper'],
            'startup_jobs': ['github_jobs', 'remoteok', 'rss_feeds'],
            'enterprise_jobs': ['adzuna', 'usajobs', 'linkedin_scraper', 'indeed_scraper']
        }
    
    def get_quota_usage(self, api_name: str) -> QuotaUsage:
        """Get current quota usage for an API"""
        if api_name not in self.quota_usage:
            self.quota_usage[api_name] = QuotaUsage(api_name=api_name)
        
        usage = self.quota_usage[api_name]
        
        # Reset counters if needed
        self._reset_counters_if_needed(usage)
        
        return usage
    
    def _reset_counters_if_needed(self, usage: QuotaUsage):
        """Reset usage counters based on time periods"""
        now = datetime.utcnow()
        
        # Daily reset
        if usage.date != now.date():
            usage.date = now.date()
            usage.daily_requests = 0
            usage.last_reset = now
        
        # Hourly reset
        if usage.last_request_time:
            hours_elapsed = (now - usage.last_request_time).total_seconds() / 3600
            if hours_elapsed >= 1.0:
                usage.hourly_requests = max(0, usage.hourly_requests - int(hours_elapsed))
        
        # Monthly reset (simplified - reset on 1st of month)
        if now.day == 1 and (not usage.last_reset or usage.last_reset.day != 1):
            usage.monthly_requests = 0
    
    def check_quota_status(self, api_name: str) -> QuotaStatus:
        """Check current quota status for an API"""
        if api_name not in self.quota_limits:
            logger.warning(f"No quota limits defined for {api_name}")
            return QuotaStatus.AVAILABLE
        
        usage = self.get_quota_usage(api_name)
        limits = self.quota_limits[api_name]
        
        # Check if blocked
        if usage.blocked_until and datetime.utcnow() < usage.blocked_until:
            return QuotaStatus.BLOCKED
        elif usage.blocked_until and datetime.utcnow() >= usage.blocked_until:
            # Unblock
            usage.blocked_until = None
            usage.consecutive_failures = 0
        
        # Check limits
        if usage.daily_requests >= limits.daily_limit:
            return QuotaStatus.EXHAUSTED
        
        if limits.hourly_limit and usage.hourly_requests >= limits.hourly_limit:
            return QuotaStatus.EXHAUSTED
        
        if limits.monthly_limit and usage.monthly_requests >= limits.monthly_limit:
            return QuotaStatus.EXHAUSTED
        
        # Check if approaching limits (80% threshold)
        daily_usage_pct = usage.daily_requests / limits.daily_limit
        if daily_usage_pct >= 0.8:
            return QuotaStatus.LIMITED
        
        return QuotaStatus.AVAILABLE
    
    def can_make_request(self, api_name: str) -> bool:
        """Check if a request can be made to the API"""
        status = self.check_quota_status(api_name)
        return status in [QuotaStatus.AVAILABLE, QuotaStatus.LIMITED]
    
    def record_request(self, api_name: str, success: bool = True):
        """Record a request and update usage counters"""
        usage = self.get_quota_usage(api_name)
        
        # Update counters
        usage.daily_requests += 1
        usage.hourly_requests += 1
        usage.monthly_requests += 1
        usage.last_request_time = datetime.utcnow()
        
        # Handle failures
        if not success:
            usage.consecutive_failures += 1
            
            # Block API after consecutive failures
            if usage.consecutive_failures >= 3:
                block_duration = min(usage.consecutive_failures * 30, 3600)  # Max 1 hour
                usage.blocked_until = datetime.utcnow() + timedelta(seconds=block_duration)
                logger.warning(f"Blocking {api_name} for {block_duration} seconds due to consecutive failures")
        else:
            usage.consecutive_failures = 0
    
    def get_rate_limit_delay(self, api_name: str) -> float:
        """Get the required delay before next request"""
        if api_name not in self.quota_limits:
            return 1.0
        
        usage = self.get_quota_usage(api_name)
        limits = self.quota_limits[api_name]
        
        if not usage.last_request_time:
            return 0.0
        
        elapsed = (datetime.utcnow() - usage.last_request_time).total_seconds()
        required_delay = limits.rate_limit_seconds
        
        # Increase delay if approaching limits
        status = self.check_quota_status(api_name)
        if status == QuotaStatus.LIMITED:
            required_delay *= 2
        
        return max(0.0, required_delay - elapsed)
    
    def get_fallback_sources(self, job_category: str = 'general_jobs') -> List[str]:
        """Get fallback sources for a job category, filtered by availability"""
        fallback_chain = self.fallback_chains.get(job_category, self.fallback_chains['general_jobs'])
        
        # Filter by availability
        available_sources = []
        for source in fallback_chain:
            if self.can_make_request(source):
                available_sources.append(source)
        
        return available_sources
    
    def get_best_source(self, job_category: str = 'general_jobs') -> Optional[str]:
        """Get the best available source for a job category"""
        available_sources = self.get_fallback_sources(job_category)
        
        if not available_sources:
            return None
        
        # Prioritize by quota status
        for source in available_sources:
            status = self.check_quota_status(source)
            if status == QuotaStatus.AVAILABLE:
                return source
        
        # Return first limited source if no fully available sources
        for source in available_sources:
            status = self.check_quota_status(source)
            if status == QuotaStatus.LIMITED:
                return source
        
        return None
    
    def get_quota_summary(self) -> Dict[str, Any]:
        """Get summary of all quota statuses"""
        summary = {}
        
        for api_name in self.quota_limits.keys():
            usage = self.get_quota_usage(api_name)
            limits = self.quota_limits[api_name]
            status = self.check_quota_status(api_name)
            
            summary[api_name] = {
                'status': status.value,
                'daily_usage': f"{usage.daily_requests}/{limits.daily_limit}",
                'daily_percentage': round((usage.daily_requests / limits.daily_limit) * 100, 1),
                'hourly_usage': f"{usage.hourly_requests}/{limits.hourly_limit}" if limits.hourly_limit else "N/A",
                'blocked_until': usage.blocked_until.isoformat() if usage.blocked_until else None,
                'consecutive_failures': usage.consecutive_failures,
                'last_request': usage.last_request_time.isoformat() if usage.last_request_time else None
            }
        
        return summary
    
    def reset_api_quota(self, api_name: str):
        """Reset quota for a specific API (admin function)"""
        if api_name in self.quota_usage:
            usage = self.quota_usage[api_name]
            usage.daily_requests = 0
            usage.hourly_requests = 0
            usage.monthly_requests = 0
            usage.blocked_until = None
            usage.consecutive_failures = 0
            usage.last_reset = datetime.utcnow()
            logger.info(f"Reset quota for {api_name}")
    
    def block_api(self, api_name: str, duration_minutes: int = 60):
        """Manually block an API for a specified duration"""
        usage = self.get_quota_usage(api_name)
        usage.blocked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        logger.info(f"Manually blocked {api_name} for {duration_minutes} minutes")
    
    def unblock_api(self, api_name: str):
        """Manually unblock an API"""
        usage = self.get_quota_usage(api_name)
        usage.blocked_until = None
        usage.consecutive_failures = 0
        logger.info(f"Manually unblocked {api_name}")
    
    def optimize_source_selection(
        self, 
        job_category: str, 
        keywords: str, 
        location: str = ""
    ) -> List[str]:
        """Optimize source selection based on job requirements and quota status"""
        # Get base fallback chain
        sources = self.get_fallback_sources(job_category)
        
        # Optimize based on job characteristics
        optimized_sources = []
        
        # Prioritize based on keywords and location
        keyword_lower = keywords.lower()
        location_lower = location.lower()
        
        # Government jobs
        if any(term in keyword_lower for term in ['government', 'federal', 'public', 'civil']):
            if 'usajobs' in sources:
                optimized_sources.append('usajobs')
        
        # Remote jobs
        if 'remote' in location_lower or any(term in keyword_lower for term in ['remote', 'work from home']):
            for source in ['remoteok', 'github_jobs']:
                if source in sources and source not in optimized_sources:
                    optimized_sources.append(source)
        
        # Tech jobs
        if any(term in keyword_lower for term in ['developer', 'engineer', 'programmer', 'software', 'tech']):
            for source in ['github_jobs', 'remoteok']:
                if source in sources and source not in optimized_sources:
                    optimized_sources.append(source)
        
        # Add remaining sources
        for source in sources:
            if source not in optimized_sources:
                optimized_sources.append(source)
        
        return optimized_sources
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of all job sources"""
        total_sources = len(self.quota_limits)
        available_sources = 0
        limited_sources = 0
        exhausted_sources = 0
        blocked_sources = 0
        
        for api_name in self.quota_limits.keys():
            status = self.check_quota_status(api_name)
            
            if status == QuotaStatus.AVAILABLE:
                available_sources += 1
            elif status == QuotaStatus.LIMITED:
                limited_sources += 1
            elif status == QuotaStatus.EXHAUSTED:
                exhausted_sources += 1
            elif status == QuotaStatus.BLOCKED:
                blocked_sources += 1
        
        health_percentage = ((available_sources + limited_sources * 0.5) / total_sources) * 100
        
        return {
            'health_percentage': round(health_percentage, 1),
            'total_sources': total_sources,
            'available': available_sources,
            'limited': limited_sources,
            'exhausted': exhausted_sources,
            'blocked': blocked_sources,
            'status': 'healthy' if health_percentage >= 70 else 'degraded' if health_percentage >= 40 else 'critical'
        }