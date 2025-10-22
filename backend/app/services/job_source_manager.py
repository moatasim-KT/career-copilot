from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.core.logging import get_logger
from app.models.job import Job
from app.models.user import User
from app.models.user_job_preferences import UserJobPreferences
from app.models.application import Application
from datetime import datetime, timedelta
import json
import asyncio
import httpx

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
        
        # Enhanced source metadata for better management
        self.source_metadata = {
            'linkedin': {
                'display_name': 'LinkedIn Jobs',
                'description': 'Professional network with comprehensive job data and company insights',
                'requires_api_key': True,
                'data_quality': 'high',
                'update_frequency': 'real-time',
                'specialties': ['professional', 'corporate', 'tech', 'finance'],
                'enrichment_capabilities': ['salary_data', 'company_info', 'employee_count', 'industry']
            },
            'glassdoor': {
                'display_name': 'Glassdoor',
                'description': 'Company reviews and salary data with job postings',
                'requires_api_key': True,
                'data_quality': 'high',
                'update_frequency': 'daily',
                'specialties': ['salary_insights', 'company_culture', 'reviews'],
                'enrichment_capabilities': ['salary_data', 'company_reviews', 'interview_insights']
            },
            'indeed': {
                'display_name': 'Indeed',
                'description': 'Large job aggregator with broad coverage across industries',
                'requires_api_key': True,
                'data_quality': 'medium',
                'update_frequency': 'hourly',
                'specialties': ['volume', 'diverse_industries', 'entry_level'],
                'enrichment_capabilities': ['basic_company_info']
            },
            'adzuna': {
                'display_name': 'Adzuna',
                'description': 'Job search engine with salary predictions and market insights',
                'requires_api_key': True,
                'data_quality': 'medium',
                'update_frequency': 'daily',
                'specialties': ['salary_predictions', 'market_trends'],
                'enrichment_capabilities': ['salary_predictions', 'market_data']
            },
            'usajobs': {
                'display_name': 'USAJobs',
                'description': 'Official U.S. government job portal',
                'requires_api_key': False,
                'data_quality': 'high',
                'update_frequency': 'daily',
                'specialties': ['government', 'federal', 'public_sector'],
                'enrichment_capabilities': ['benefits_info', 'security_clearance']
            },
            'github_jobs': {
                'display_name': 'GitHub Jobs',
                'description': 'Developer-focused job board (deprecated)',
                'requires_api_key': False,
                'data_quality': 'low',
                'update_frequency': 'none',
                'specialties': ['tech', 'remote', 'startups'],
                'enrichment_capabilities': []
            },
            'remoteok': {
                'display_name': 'Remote OK',
                'description': 'Remote work focused job board',
                'requires_api_key': False,
                'data_quality': 'medium',
                'update_frequency': 'daily',
                'specialties': ['remote', 'tech', 'digital_nomad'],
                'enrichment_capabilities': ['remote_benefits']
            },
            'manual': {
                'display_name': 'Manual Entry',
                'description': 'Jobs added manually by users',
                'requires_api_key': False,
                'data_quality': 'variable',
                'update_frequency': 'user_driven',
                'specialties': ['custom', 'networking', 'referrals'],
                'enrichment_capabilities': []
            }
        }
        
        self.source_quality_weights = {
            'data_completeness': 0.3,    # How complete is the job data
            'accuracy': 0.25,            # How accurate is the data
            'freshness': 0.2,            # How recent are the job postings
            'user_engagement': 0.15,     # How often users interact with jobs from this source
            'success_rate': 0.1          # Application success rate from this source
        }

    def get_source_priority(self, source: str, user_id: Optional[int] = None) -> int:
        """Get priority score for a job source, considering user preferences"""
        base_priority = self.source_priorities.get(source, 0)
        
        if user_id:
            user_prefs = self.get_user_preferences(user_id)
            if user_prefs and user_prefs.source_priorities:
                custom_priority = user_prefs.source_priorities.get(source)
                if custom_priority is not None:
                    return int(custom_priority)
        
        return base_priority

    def get_source_metadata(self, source: str) -> Dict[str, Any]:
        """Get comprehensive metadata for a job source"""
        return self.source_metadata.get(source, {
            'display_name': source.title(),
            'description': f'Job source: {source}',
            'requires_api_key': False,
            'data_quality': 'unknown',
            'update_frequency': 'unknown',
            'specialties': [],
            'enrichment_capabilities': []
        })

    def get_user_preferences(self, user_id: int) -> Optional[UserJobPreferences]:
        """Get user's job source preferences"""
        return self.db.query(UserJobPreferences).filter(
            UserJobPreferences.user_id == user_id
        ).first()

    def create_or_update_user_preferences(self, user_id: int, preferences_data: Dict[str, Any]) -> UserJobPreferences:
        """Create or update user job source preferences"""
        existing_prefs = self.get_user_preferences(user_id)
        
        if existing_prefs:
            # Update existing preferences
            for key, value in preferences_data.items():
                if hasattr(existing_prefs, key):
                    setattr(existing_prefs, key, value)
            existing_prefs.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing_prefs)
            return existing_prefs
        else:
            # Create new preferences
            new_prefs = UserJobPreferences(user_id=user_id, **preferences_data)
            self.db.add(new_prefs)
            self.db.commit()
            self.db.refresh(new_prefs)
            return new_prefs

    def calculate_source_quality_score(self, source: str, timeframe_days: int = 30, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Calculate comprehensive quality score for a job source"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=timeframe_days)
        
        # Get jobs from this source in the timeframe
        query = self.db.query(Job).filter(
            Job.source == source,
            Job.created_at >= start_date,
            Job.created_at <= end_date
        )
        
        # If user_id is provided, focus on that user's jobs for personalized scoring
        if user_id:
            query = query.filter(Job.user_id == user_id)
        
        jobs = query.all()
        
        if not jobs:
            return {
                'source': source,
                'quality_score': 0,
                'metrics': {},
                'job_count': 0,
                'metadata': self.get_source_metadata(source)
            }
        
        # Calculate individual quality metrics
        data_completeness = self._calculate_data_completeness(jobs)
        freshness_score = self._calculate_freshness_score(jobs)
        user_engagement = self._calculate_user_engagement(jobs)
        success_rate = self._calculate_success_rate(jobs)
        accuracy_score = self._calculate_accuracy_score(jobs, source)
        
        # Calculate weighted quality score
        quality_score = (
            data_completeness * self.source_quality_weights['data_completeness'] +
            freshness_score * self.source_quality_weights['freshness'] +
            user_engagement * self.source_quality_weights['user_engagement'] +
            success_rate * self.source_quality_weights['success_rate'] +
            accuracy_score * self.source_quality_weights['accuracy']
        ) * 100
        
        return {
            'source': source,
            'quality_score': round(quality_score, 2),
            'metrics': {
                'data_completeness': round(data_completeness * 100, 2),
                'freshness_score': round(freshness_score * 100, 2),
                'user_engagement': round(user_engagement * 100, 2),
                'success_rate': round(success_rate * 100, 2),
                'accuracy': round(accuracy_score * 100, 2)
            },
            'job_count': len(jobs),
            'priority': self.get_source_priority(source, user_id),
            'metadata': self.get_source_metadata(source),
            'enrichment_data': self._get_source_enrichment_summary(jobs, source)
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

    def _calculate_accuracy_score(self, jobs: List[Job], source: str) -> float:
        """Calculate data accuracy score based on source reliability (0-1 scale)"""
        # Base accuracy scores by source type
        base_accuracy = {
            'linkedin': 0.9,    # High accuracy, professional data
            'glassdoor': 0.85,  # High accuracy, verified company data
            'indeed': 0.75,     # Good accuracy, large aggregator
            'adzuna': 0.7,      # Good accuracy, API-based
            'usajobs': 0.95,    # Very high accuracy, government source
            'github_jobs': 0.6, # Lower accuracy, deprecated
            'remoteok': 0.7,    # Good accuracy for remote jobs
            'manual': 0.8       # Variable, but user-verified
        }
        
        base_score = base_accuracy.get(source, 0.5)
        
        # Adjust based on data consistency
        if jobs:
            # Check for consistent data patterns
            consistency_factors = []
            
            # Check salary range consistency
            salary_jobs = [j for j in jobs if j.salary_range]
            if salary_jobs:
                valid_salaries = sum(1 for j in salary_jobs if self._is_valid_salary_format(j.salary_range))
                consistency_factors.append(valid_salaries / len(salary_jobs))
            
            # Check location consistency
            location_jobs = [j for j in jobs if j.location]
            if location_jobs:
                valid_locations = sum(1 for j in location_jobs if len(j.location.strip()) > 2)
                consistency_factors.append(valid_locations / len(location_jobs))
            
            # Check tech stack consistency
            tech_jobs = [j for j in jobs if j.tech_stack]
            if tech_jobs:
                valid_tech = sum(1 for j in tech_jobs if isinstance(j.tech_stack, list) and len(j.tech_stack) > 0)
                consistency_factors.append(valid_tech / len(tech_jobs))
            
            if consistency_factors:
                consistency_score = sum(consistency_factors) / len(consistency_factors)
                # Blend base score with consistency
                base_score = (base_score * 0.7) + (consistency_score * 0.3)
        
        return base_score

    def _is_valid_salary_format(self, salary_range: str) -> bool:
        """Check if salary range follows expected format"""
        if not salary_range:
            return False
        
        # Common valid patterns: "$50,000 - $70,000", "50k-70k", "$50K-$70K"
        import re
        patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',  # $50,000 - $70,000
            r'\d+k\s*-\s*\d+k',          # 50k-70k
            r'\$\d+K\s*-\s*\$\d+K',      # $50K-$70K
            r'\d+\s*-\s*\d+',            # 50000-70000
        ]
        
        return any(re.search(pattern, salary_range, re.IGNORECASE) for pattern in patterns)

    def _get_source_enrichment_summary(self, jobs: List[Job], source: str) -> Dict[str, Any]:
        """Get summary of enrichment data available from this source"""
        if not jobs:
            return {}
        
        metadata = self.get_source_metadata(source)
        capabilities = metadata.get('enrichment_capabilities', [])
        
        enrichment_summary = {
            'capabilities': capabilities,
            'data_coverage': {}
        }
        
        # Calculate coverage for each capability
        total_jobs = len(jobs)
        
        if 'salary_data' in capabilities:
            salary_coverage = sum(1 for job in jobs if job.salary_range) / total_jobs
            enrichment_summary['data_coverage']['salary_data'] = round(salary_coverage * 100, 1)
        
        if 'company_info' in capabilities:
            company_coverage = sum(1 for job in jobs if job.company and len(job.company.strip()) > 2) / total_jobs
            enrichment_summary['data_coverage']['company_info'] = round(company_coverage * 100, 1)
        
        if 'tech_stack' in capabilities:
            tech_coverage = sum(1 for job in jobs if job.tech_stack and len(job.tech_stack) > 0) / total_jobs
            enrichment_summary['data_coverage']['tech_stack'] = round(tech_coverage * 100, 1)
        
        return enrichment_summary

    def get_source_analytics(self, timeframe_days: int = 30, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive analytics for all job sources"""
        # Get all available sources (both used and available)
        used_sources = self.db.query(Job.source).distinct().all()
        used_source_names = [source[0] for source in used_sources if source[0]]
        all_source_names = list(set(used_source_names + list(self.source_metadata.keys())))
        
        analytics = {
            'timeframe_days': timeframe_days,
            'user_id': user_id,
            'sources': {},
            'summary': {
                'total_sources': len(all_source_names),
                'active_sources': len(used_source_names),
                'best_source': None,
                'worst_source': None,
                'average_quality': 0,
                'total_jobs': 0,
                'source_distribution': {}
            },
            'trends': self._calculate_source_trends(timeframe_days, user_id),
            'recommendations': self._get_source_recommendations(user_id)
        }
        
        quality_scores = []
        total_jobs = 0
        
        for source in all_source_names:
            source_data = self.calculate_source_quality_score(source, timeframe_days, user_id)
            analytics['sources'][source] = source_data
            
            if source_data['job_count'] > 0:
                quality_scores.append((source, source_data['quality_score']))
                total_jobs += source_data['job_count']
                analytics['summary']['source_distribution'][source] = source_data['job_count']
        
        analytics['summary']['total_jobs'] = total_jobs
        
        if quality_scores:
            # Sort by quality score
            quality_scores.sort(key=lambda x: x[1], reverse=True)
            analytics['summary']['best_source'] = quality_scores[0][0]
            analytics['summary']['worst_source'] = quality_scores[-1][0]
            analytics['summary']['average_quality'] = round(
                sum(score for _, score in quality_scores) / len(quality_scores), 2
            )
        
        return analytics

    def _calculate_source_trends(self, timeframe_days: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Calculate trends in job source performance over time"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=timeframe_days)
        
        # Split timeframe into periods for trend analysis
        periods = 4
        period_length = timeframe_days // periods
        
        trends = {}
        
        for i in range(periods):
            period_end = end_date - timedelta(days=i * period_length)
            period_start = period_end - timedelta(days=period_length)
            
            query = self.db.query(Job.source, func.count(Job.id)).filter(
                Job.created_at >= period_start,
                Job.created_at < period_end
            )
            
            if user_id:
                query = query.filter(Job.user_id == user_id)
            
            period_data = query.group_by(Job.source).all()
            
            period_name = f"period_{periods - i}"
            trends[period_name] = {
                'start_date': period_start.isoformat(),
                'end_date': period_end.isoformat(),
                'sources': {source: count for source, count in period_data}
            }
        
        return trends

    def _get_source_recommendations(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get personalized source recommendations"""
        recommendations = []
        
        if user_id:
            user_prefs = self.get_user_preferences(user_id)
            user_data = self.get_user_source_preferences(user_id)
            
            # Get sources user hasn't tried yet
            tried_sources = set(user_data.get('source_preferences', {}).keys())
            available_sources = set(self.source_metadata.keys()) - tried_sources
            
            for source in available_sources:
                metadata = self.get_source_metadata(source)
                quality_data = self.calculate_source_quality_score(source, 30)
                
                recommendations.append({
                    'source': source,
                    'reason': 'untried_source',
                    'display_name': metadata['display_name'],
                    'description': metadata['description'],
                    'quality_score': quality_data['quality_score'],
                    'specialties': metadata.get('specialties', []),
                    'priority': 'medium'
                })
            
            # Recommend high-performing sources user has low engagement with
            for source, stats in user_data.get('source_preferences', {}).items():
                if stats['job_count'] > 0 and stats['application_count'] / stats['job_count'] < 0.1:
                    if stats['quality_score'] > 70:
                        recommendations.append({
                            'source': source,
                            'reason': 'underutilized_quality_source',
                            'display_name': self.get_source_metadata(source)['display_name'],
                            'description': f"High quality source ({stats['quality_score']:.1f}%) with low engagement",
                            'quality_score': stats['quality_score'],
                            'priority': 'high'
                        })
        
        # Sort by priority and quality
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['quality_score']), reverse=True)
        
        return recommendations[:5]  # Return top 5 recommendations

    def get_user_source_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user's job source preferences and performance"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Get user's stored preferences
        user_prefs = self.get_user_preferences(user_id)
        
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
                    'quality_score': 0,
                    'avg_match_score': 0,
                    'recent_jobs': 0,
                    'salary_data_coverage': 0,
                    'tech_stack_coverage': 0
                }
            
            source_stats[source]['job_count'] += 1
            
            # Check recent jobs (last 30 days)
            if job.created_at >= datetime.utcnow() - timedelta(days=30):
                source_stats[source]['recent_jobs'] += 1
            
            # Check data coverage
            if job.salary_range:
                source_stats[source]['salary_data_coverage'] += 1
            if job.tech_stack and len(job.tech_stack) > 0:
                source_stats[source]['tech_stack_coverage'] += 1
            
            # Count applications and successes
            applications = self.db.query(Application).filter(Application.job_id == job.id).all()
            source_stats[source]['application_count'] += len(applications)
            
            for app in applications:
                if app.status in ['interview', 'offer', 'accepted']:
                    source_stats[source]['success_count'] += 1
        
        # Calculate derived metrics
        for source, stats in source_stats.items():
            # Success rate
            if stats['application_count'] > 0:
                stats['success_rate'] = stats['success_count'] / stats['application_count']
            else:
                stats['success_rate'] = 0.0
            
            # Data coverage percentages
            if stats['job_count'] > 0:
                stats['salary_data_coverage'] = stats['salary_data_coverage'] / stats['job_count']
                stats['tech_stack_coverage'] = stats['tech_stack_coverage'] / stats['job_count']
            
            # Get overall source quality score
            quality_data = self.calculate_source_quality_score(source, 30, user_id)
            stats['quality_score'] = quality_data['quality_score']
            stats['metadata'] = quality_data['metadata']
            stats['enrichment_data'] = quality_data.get('enrichment_data', {})
        
        # Get available sources not yet used
        all_sources = set(self.source_metadata.keys())
        used_sources = set(source_stats.keys())
        available_sources = all_sources - used_sources
        
        available_source_info = {}
        for source in available_sources:
            quality_data = self.calculate_source_quality_score(source, 30)
            available_source_info[source] = {
                'quality_score': quality_data['quality_score'],
                'metadata': quality_data['metadata'],
                'job_count': 0,
                'is_available': True,
                'requires_setup': quality_data['metadata'].get('requires_api_key', False)
            }
        
        return {
            'user_id': user_id,
            'preferences': {
                'preferred_sources': user_prefs.preferred_sources if user_prefs else [],
                'disabled_sources': user_prefs.disabled_sources if user_prefs else [],
                'source_priorities': user_prefs.source_priorities if user_prefs else {},
                'auto_scraping_enabled': user_prefs.auto_scraping_enabled if user_prefs else True,
                'max_jobs_per_source': user_prefs.max_jobs_per_source if user_prefs else 10,
                'min_quality_threshold': user_prefs.min_quality_threshold if user_prefs else 60.0
            },
            'source_performance': source_stats,
            'available_sources': available_source_info,
            'recommended_sources': self._get_recommended_sources_for_user(source_stats, user_prefs),
            'insights': self._generate_user_insights(source_stats, user_prefs)
        }

    def _generate_user_insights(self, source_stats: Dict[str, Any], user_prefs: Optional[UserJobPreferences]) -> List[Dict[str, str]]:
        """Generate actionable insights for the user based on their source usage"""
        insights = []
        
        if not source_stats:
            insights.append({
                'type': 'info',
                'title': 'Get Started',
                'message': 'Start by adding jobs manually or enabling automatic job scraping to see source analytics.'
            })
            return insights
        
        # Find best performing source
        best_source = max(source_stats.items(), key=lambda x: x[1]['success_rate'] * x[1]['quality_score'])
        if best_source[1]['success_rate'] > 0:
            insights.append({
                'type': 'success',
                'title': 'Top Performing Source',
                'message': f"{best_source[1]['metadata']['display_name']} has your highest success rate ({best_source[1]['success_rate']:.1%}). Consider focusing more on this source."
            })
        
        # Find underutilized high-quality sources
        for source, stats in source_stats.items():
            if stats['quality_score'] > 80 and stats['application_count'] / max(stats['job_count'], 1) < 0.1:
                insights.append({
                    'type': 'warning',
                    'title': 'Underutilized Quality Source',
                    'message': f"{stats['metadata']['display_name']} has high quality ({stats['quality_score']:.1f}%) but low application rate. Consider applying to more jobs from this source."
                })
        
        # Check for sources with poor data coverage
        for source, stats in source_stats.items():
            if stats['salary_data_coverage'] < 0.3 and stats['job_count'] > 5:
                insights.append({
                    'type': 'info',
                    'title': 'Limited Salary Data',
                    'message': f"{stats['metadata']['display_name']} has limited salary information. Consider supplementing with Glassdoor data."
                })
        
        # Recommend diversification if user relies too heavily on one source
        total_jobs = sum(stats['job_count'] for stats in source_stats.values())
        if total_jobs > 10:
            dominant_source = max(source_stats.items(), key=lambda x: x[1]['job_count'])
            if dominant_source[1]['job_count'] / total_jobs > 0.7:
                insights.append({
                    'type': 'info',
                    'title': 'Diversify Your Sources',
                    'message': f"Most of your jobs come from {dominant_source[1]['metadata']['display_name']}. Try exploring other sources for better opportunities."
                })
        
        return insights[:5]  # Limit to top 5 insights

    def _get_recommended_sources_for_user(self, source_stats: Dict[str, Any], user_prefs: Optional[UserJobPreferences] = None) -> List[Dict[str, Any]]:
        """Recommend best job sources for a user based on their history and preferences"""
        recommendations = []
        
        # Score existing sources based on user's success rate and overall quality
        for source, stats in source_stats.items():
            if stats['job_count'] > 0:
                # Combine user success rate with overall source quality
                user_score = stats['success_rate'] * 0.4 + (stats['quality_score'] / 100) * 0.3 + (stats['recent_jobs'] / max(stats['job_count'], 1)) * 0.3
                
                recommendations.append({
                    'source': source,
                    'score': user_score,
                    'reason': 'proven_performance',
                    'display_name': stats['metadata']['display_name'],
                    'description': f"Success rate: {stats['success_rate']:.1%}, Quality: {stats['quality_score']:.1f}%",
                    'metrics': {
                        'success_rate': stats['success_rate'],
                        'quality_score': stats['quality_score'],
                        'job_count': stats['job_count'],
                        'recent_activity': stats['recent_jobs']
                    }
                })
        
        # Add sources the user hasn't tried yet
        all_sources = set(self.source_metadata.keys())
        user_sources = set(source_stats.keys())
        new_sources = all_sources - user_sources
        
        # Filter out disabled sources if user has preferences
        if user_prefs and user_prefs.disabled_sources:
            new_sources = new_sources - set(user_prefs.disabled_sources)
        
        for source in new_sources:
            quality_data = self.calculate_source_quality_score(source, 30)
            metadata = self.get_source_metadata(source)
            
            # Score based on quality and user preferences
            base_score = (quality_data['quality_score'] / 100) * 0.7  # Slightly lower for untried sources
            
            # Boost score if it's in user's preferred sources
            if user_prefs and user_prefs.preferred_sources and source in user_prefs.preferred_sources:
                base_score *= 1.2
            
            recommendations.append({
                'source': source,
                'score': base_score,
                'reason': 'untried_source',
                'display_name': metadata['display_name'],
                'description': f"Quality: {quality_data['quality_score']:.1f}%, {metadata['description']}",
                'metrics': {
                    'quality_score': quality_data['quality_score'],
                    'requires_setup': metadata.get('requires_api_key', False),
                    'specialties': metadata.get('specialties', [])
                }
            })
        
        # Sort by score and return top sources
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:8]  # Return top 8 recommendations

    def enrich_job_with_source_data(self, job: Job, include_external_data: bool = False) -> Dict[str, Any]:
        """Enrich job data with source-specific information and external data"""
        source_data = self.calculate_source_quality_score(job.source, user_id=job.user_id)
        metadata = self.get_source_metadata(job.source)
        
        enriched_data = {
            'source_priority': self.get_source_priority(job.source, job.user_id),
            'source_quality_score': source_data['quality_score'],
            'source_metrics': source_data['metrics'],
            'reliability_indicator': self._get_reliability_indicator(source_data['quality_score']),
            'source_metadata': metadata,
            'enrichment_capabilities': metadata.get('enrichment_capabilities', []),
            'data_completeness': self._calculate_job_data_completeness(job)
        }
        
        # Add external enrichment data if requested
        if include_external_data:
            enriched_data['external_data'] = self._get_external_enrichment_data(job)
        
        return enriched_data

    def _calculate_job_data_completeness(self, job: Job) -> Dict[str, Any]:
        """Calculate data completeness for a specific job"""
        fields = {
            'title': bool(job.title),
            'company': bool(job.company),
            'location': bool(job.location),
            'description': bool(job.description and len(job.description) > 50),
            'salary_range': bool(job.salary_range),
            'tech_stack': bool(job.tech_stack and len(job.tech_stack) > 0),
            'job_type': bool(job.job_type),
            'remote_option': bool(job.remote_option),
            'requirements': bool(job.requirements),
            'responsibilities': bool(job.responsibilities),
            'link': bool(job.link)
        }
        
        completed_fields = sum(fields.values())
        total_fields = len(fields)
        completeness_score = (completed_fields / total_fields) * 100
        
        return {
            'score': round(completeness_score, 1),
            'completed_fields': completed_fields,
            'total_fields': total_fields,
            'missing_fields': [field for field, present in fields.items() if not present],
            'field_status': fields
        }

    def _get_external_enrichment_data(self, job: Job) -> Dict[str, Any]:
        """Get external enrichment data for a job (placeholder for future implementation)"""
        # This would integrate with external APIs for additional data
        # For now, return placeholder structure
        return {
            'company_data': {
                'size': None,
                'industry': None,
                'rating': None,
                'reviews_count': None
            },
            'salary_insights': {
                'market_average': None,
                'salary_range_accuracy': None,
                'benefits_info': None
            },
            'market_data': {
                'demand_level': None,
                'competition_level': None,
                'skill_match_market': None
            }
        }

    async def enrich_job_with_external_apis(self, job: Job) -> Dict[str, Any]:
        """Enrich job with data from external APIs (async implementation)"""
        enrichment_data = {}
        
        try:
            # Glassdoor company data enrichment
            if job.source != 'glassdoor':
                company_data = await self._fetch_glassdoor_company_data(job.company)
                if company_data:
                    enrichment_data['glassdoor_data'] = company_data
            
            # LinkedIn company insights
            if job.source != 'linkedin':
                linkedin_data = await self._fetch_linkedin_company_data(job.company)
                if linkedin_data:
                    enrichment_data['linkedin_data'] = linkedin_data
            
            # Salary data from multiple sources
            salary_data = await self._fetch_salary_data(job.title, job.location)
            if salary_data:
                enrichment_data['salary_insights'] = salary_data
                
        except Exception as e:
            logger.error(f"Error enriching job {job.id} with external data: {e}")
            enrichment_data['error'] = str(e)
        
        return enrichment_data

    async def _fetch_glassdoor_company_data(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Fetch company data from Glassdoor API"""
        # Placeholder for Glassdoor API integration
        # Would require proper API credentials and implementation
        return None

    async def _fetch_linkedin_company_data(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Fetch company data from LinkedIn API"""
        # Placeholder for LinkedIn API integration
        # Would require proper API credentials and implementation
        return None

    async def _fetch_salary_data(self, job_title: str, location: str) -> Optional[Dict[str, Any]]:
        """Fetch salary data from multiple sources"""
        # Placeholder for salary data aggregation
        # Could integrate with Glassdoor, PayScale, Salary.com APIs
        return None

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

    def update_source_performance_metrics(self, source: str, metric_type: str, value: float, user_id: Optional[int] = None):
        """Update performance metrics for a job source"""
        # Log the metrics for monitoring
        logger.info(f"Source performance update: {source} - {metric_type}: {value} (user: {user_id})")
        
        # Could be expanded to store in a dedicated metrics table
        # For now, we track through existing job and application data

    def get_source_performance_summary(self, user_id: Optional[int] = None, timeframe_days: int = 30) -> Dict[str, Any]:
        """Get a comprehensive performance summary for all sources"""
        analytics = self.get_source_analytics(timeframe_days, user_id)
        
        # Calculate performance rankings
        source_rankings = []
        for source, data in analytics['sources'].items():
            if data['job_count'] > 0:
                # Composite performance score
                performance_score = (
                    data['quality_score'] * 0.4 +
                    data['metrics']['user_engagement'] * 0.3 +
                    data['metrics']['success_rate'] * 0.2 +
                    data['metrics']['freshness_score'] * 0.1
                )
                
                source_rankings.append({
                    'source': source,
                    'display_name': data['metadata']['display_name'],
                    'performance_score': round(performance_score, 2),
                    'quality_score': data['quality_score'],
                    'job_count': data['job_count'],
                    'engagement': data['metrics']['user_engagement'],
                    'success_rate': data['metrics']['success_rate']
                })
        
        # Sort by performance score
        source_rankings.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return {
            'timeframe_days': timeframe_days,
            'user_id': user_id,
            'source_rankings': source_rankings,
            'top_performer': source_rankings[0] if source_rankings else None,
            'summary': analytics['summary'],
            'recommendations': analytics['recommendations']
        }

    def get_available_sources_info(self) -> List[Dict[str, Any]]:
        """Get information about all available job sources"""
        sources_info = []
        
        for source, metadata in self.source_metadata.items():
            quality_data = self.calculate_source_quality_score(source, 30)
            
            sources_info.append({
                'source': source,
                'display_name': metadata['display_name'],
                'description': metadata['description'],
                'requires_api_key': metadata.get('requires_api_key', False),
                'data_quality': metadata.get('data_quality', 'unknown'),
                'update_frequency': metadata.get('update_frequency', 'unknown'),
                'specialties': metadata.get('specialties', []),
                'enrichment_capabilities': metadata.get('enrichment_capabilities', []),
                'quality_score': quality_data['quality_score'],
                'job_count': quality_data['job_count'],
                'priority': self.get_source_priority(source),
                'is_active': quality_data['job_count'] > 0
            })
        
        # Sort by priority and quality
        sources_info.sort(key=lambda x: (x['priority'], x['quality_score']), reverse=True)
        
        return sources_info

    def filter_sources_by_user_preferences(self, user_id: int, available_sources: List[str]) -> List[str]:
        """Filter sources based on user preferences"""
        user_prefs = self.get_user_preferences(user_id)
        
        if not user_prefs:
            return available_sources
        
        filtered_sources = []
        
        for source in available_sources:
            # Skip disabled sources
            if user_prefs.disabled_sources and source in user_prefs.disabled_sources:
                continue
            
            # Check quality threshold
            quality_data = self.calculate_source_quality_score(source, 30, user_id)
            if quality_data['quality_score'] < user_prefs.min_quality_threshold:
                continue
            
            filtered_sources.append(source)
        
        # Sort by user's preferred sources first, then by priority
        preferred_sources = user_prefs.preferred_sources or []
        
        def sort_key(source):
            is_preferred = source in preferred_sources
            priority = self.get_source_priority(source, user_id)
            return (is_preferred, priority)
        
        filtered_sources.sort(key=sort_key, reverse=True)
        
        return filtered_sources