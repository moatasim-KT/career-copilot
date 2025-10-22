from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.models.job import Job
from app.models.user import User
from datetime import datetime, timedelta
import json

logger = get_logger(__name__)

class JobSourceManager:
    """Manages job source priority, quality scoring, and analytics"""
    
    def __init__(self, db: Session):
        self.db = db
        self.source_priorities = {
            'linkedin': 5,    # Highest priority - most comprehensive data
            'glassdoor': 4,   # High priority - good salary and company data  
            'indeed': 3,      # Medium-high priority - good coverage
            'adzuna': 2,      # Medium priority - decent data quality
            'usajobs': 2,     # Medium priority - government jobs
            'github_jobs': 1, # Low priority - deprecated API
            'remoteok': 1,    # Low priority - limited data
            'manual': 5       # User-added jobs get high priority
        }
        
        self.source_quality_weights = {
            'data_completeness': 0.3,    # How complete is the job data
            'accuracy': 0.25,            # How accurate is the data
            'freshness': 0.2,            # How recent are the job postings
            'user_engagement': 0.15,     # How often users interact with jobs from this source
            'success_rate': 0.1          # Application success rate from this source
        }

    def get_source_priority(self, source: str) -> int:
        """Get priority score for a job source"""
        return self.source_priorities.get(source, 0)

    def calculate_source_quality_score(self, source: str, timeframe_days: int = 30) -> Dict[str, Any]:
        """Calculate comprehensive quality score for a job source"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=timeframe_days)
        
        # Get jobs from this source in the timeframe
        jobs = self.db.query(Job).filter(
            Job.source == source,
            Job.created_at >= start_date,
            Job.created_at <= end_date
        ).all()
        
        if not jobs:
            return {
                'source': source,
                'quality_score': 0,
                'metrics': {},
                'job_count': 0
            }
        
        # Calculate individual quality metrics
        data_completeness = self._calculate_data_completeness(jobs)
        freshness_score = self._calculate_freshness_score(jobs)
        user_engagement = self._calculate_user_engagement(jobs)
        success_rate = self._calculate_success_rate(jobs)
        
        # Calculate weighted quality score
        quality_score = (
            data_completeness * self.source_quality_weights['data_completeness'] +
            freshness_score * self.source_quality_weights['freshness'] +
            user_engagement * self.source_quality_weights['user_engagement'] +
            success_rate * self.source_quality_weights['success_rate'] +
            0.8 * self.source_quality_weights['accuracy']  # Default accuracy score
        ) * 100
        
        return {
            'source': source,
            'quality_score': round(quality_score, 2),
            'metrics': {
                'data_completeness': round(data_completeness * 100, 2),
                'freshness_score': round(freshness_score * 100, 2),
                'user_engagement': round(user_engagement * 100, 2),
                'success_rate': round(success_rate * 100, 2),
                'accuracy': 80.0  # Default accuracy
            },
            'job_count': len(jobs),
            'priority': self.get_source_priority(source)
        }

    def _calculate_data_completeness(self, jobs: List[Job]) -> float:
        """Calculate how complete the job data is (0-1 scale)"""
        if not jobs:
            return 0.0
        
        total_score = 0
        for job in jobs:
            score = 0
            max_score = 8  # Total number of fields to check
            
            # Check for presence of key fields
            if job.title: score += 1
            if job.company: score += 1
            if job.location: score += 1
            if job.description: score += 1
            if job.salary_range: score += 1
            if job.tech_stack: score += 1
            if job.job_type: score += 1
            if job.link: score += 1
            
            total_score += score / max_score
        
        return total_score / len(jobs)

    def _calculate_freshness_score(self, jobs: List[Job]) -> float:
        """Calculate how fresh/recent the job postings are (0-1 scale)"""
        if not jobs:
            return 0.0
        
        now = datetime.utcnow()
        total_score = 0
        
        for job in jobs:
            days_old = (now - job.created_at).days
            # Jobs are considered fresh if posted within 7 days
            # Score decreases linearly after that
            if days_old <= 7:
                score = 1.0
            elif days_old <= 30:
                score = 1.0 - ((days_old - 7) / 23)  # Linear decrease from 1.0 to 0.0
            else:
                score = 0.0
            
            total_score += score
        
        return total_score / len(jobs)

    def _calculate_user_engagement(self, jobs: List[Job]) -> float:
        """Calculate user engagement with jobs from this source (0-1 scale)"""
        if not jobs:
            return 0.0
        
        from app.models.application import Application
        
        total_jobs = len(jobs)
        engaged_jobs = 0
        
        for job in jobs:
            # Check if users have created applications for this job
            applications = self.db.query(Application).filter(Application.job_id == job.id).count()
            if applications > 0:
                engaged_jobs += 1
        
        return engaged_jobs / total_jobs if total_jobs > 0 else 0.0

    def _calculate_success_rate(self, jobs: List[Job]) -> float:
        """Calculate application success rate for jobs from this source (0-1 scale)"""
        if not jobs:
            return 0.0
        
        from app.models.application import Application
        
        total_applications = 0
        successful_applications = 0
        
        for job in jobs:
            applications = self.db.query(Application).filter(Application.job_id == job.id).all()
            total_applications += len(applications)
            
            # Count successful applications (interview, offer, accepted)
            for app in applications:
                if app.status in ['interview', 'offer', 'accepted']:
                    successful_applications += 1
        
        return successful_applications / total_applications if total_applications > 0 else 0.0

    def get_source_analytics(self, timeframe_days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics for all job sources"""
        sources = self.db.query(Job.source).distinct().all()
        source_names = [source[0] for source in sources if source[0]]
        
        analytics = {
            'timeframe_days': timeframe_days,
            'sources': {},
            'summary': {
                'total_sources': len(source_names),
                'best_source': None,
                'worst_source': None,
                'average_quality': 0
            }
        }
        
        quality_scores = []
        
        for source in source_names:
            source_data = self.calculate_source_quality_score(source, timeframe_days)
            analytics['sources'][source] = source_data
            quality_scores.append((source, source_data['quality_score']))
        
        if quality_scores:
            # Sort by quality score
            quality_scores.sort(key=lambda x: x[1], reverse=True)
            analytics['summary']['best_source'] = quality_scores[0][0]
            analytics['summary']['worst_source'] = quality_scores[-1][0]
            analytics['summary']['average_quality'] = sum(score for _, score in quality_scores) / len(quality_scores)
        
        return analytics

    def get_user_source_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user's job source preferences and performance"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Get user's job sources and their performance
        user_jobs = self.db.query(Job).filter(Job.user_id == user_id).all()
        source_stats = {}
        
        for job in user_jobs:
            source = job.source
            if source not in source_stats:
                source_stats[source] = {
                    'job_count': 0,
                    'application_count': 0,
                    'success_count': 0,
                    'quality_score': 0
                }
            
            source_stats[source]['job_count'] += 1
            
            # Count applications and successes
            from app.models.application import Application
            applications = self.db.query(Application).filter(Application.job_id == job.id).all()
            source_stats[source]['application_count'] += len(applications)
            
            for app in applications:
                if app.status in ['interview', 'offer', 'accepted']:
                    source_stats[source]['success_count'] += 1
        
        # Calculate success rates and add quality scores
        for source, stats in source_stats.items():
            if stats['application_count'] > 0:
                stats['success_rate'] = stats['success_count'] / stats['application_count']
            else:
                stats['success_rate'] = 0.0
            
            # Get overall source quality score
            quality_data = self.calculate_source_quality_score(source)
            stats['quality_score'] = quality_data['quality_score']
        
        return {
            'user_id': user_id,
            'source_preferences': source_stats,
            'recommended_sources': self._get_recommended_sources_for_user(source_stats)
        }

    def _get_recommended_sources_for_user(self, source_stats: Dict[str, Any]) -> List[str]:
        """Recommend best job sources for a user based on their history"""
        # Score sources based on user's success rate and overall quality
        source_scores = []
        
        for source, stats in source_stats.items():
            # Combine user success rate with overall source quality
            user_score = stats['success_rate'] * 0.6 + (stats['quality_score'] / 100) * 0.4
            source_scores.append((source, user_score))
        
        # Add sources the user hasn't tried yet (with default scores)
        all_sources = set(self.source_priorities.keys())
        user_sources = set(source_stats.keys())
        new_sources = all_sources - user_sources
        
        for source in new_sources:
            quality_data = self.calculate_source_quality_score(source)
            default_score = (quality_data['quality_score'] / 100) * 0.8  # Slightly lower for untried sources
            source_scores.append((source, default_score))
        
        # Sort by score and return top sources
        source_scores.sort(key=lambda x: x[1], reverse=True)
        return [source for source, _ in source_scores[:5]]

    def enrich_job_with_source_data(self, job: Job) -> Dict[str, Any]:
        """Enrich job data with source-specific information"""
        source_data = self.calculate_source_quality_score(job.source)
        
        enriched_data = {
            'source_priority': self.get_source_priority(job.source),
            'source_quality_score': source_data['quality_score'],
            'source_metrics': source_data['metrics'],
            'reliability_indicator': self._get_reliability_indicator(source_data['quality_score'])
        }
        
        return enriched_data

    def _get_reliability_indicator(self, quality_score: float) -> str:
        """Get human-readable reliability indicator"""
        if quality_score >= 80:
            return "High"
        elif quality_score >= 60:
            return "Medium"
        elif quality_score >= 40:
            return "Low"
        else:
            return "Very Low"

    def update_source_performance_metrics(self, source: str, metric_type: str, value: float):
        """Update performance metrics for a job source"""
        # This could be expanded to store metrics in a dedicated table
        # For now, we'll log the metrics for monitoring
        logger.info(f"Source performance update: {source} - {metric_type}: {value}")