"""
Graceful degradation service for handling external API failures
Provides fallback functionality when external services are unavailable
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import re
from collections import Counter

from app.services.cache_service import cache_service
from app.models.job import Job
from app.models.user import User

logger = logging.getLogger(__name__)


class GracefulDegradationService:
    """Service for handling external API failures with local fallbacks"""
    
    def __init__(self):
        self.fallback_cache_duration = 3600  # 1 hour
        self.api_timeout_threshold = 30  # seconds
        
    def handle_skill_extraction_failure(self, job_description: str) -> List[str]:
        """Fallback skill extraction using local regex patterns"""
        try:
            # Common technical skills patterns
            skill_patterns = [
                r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Ruby|Go|Rust|PHP|Swift|Kotlin)\b',
                r'\b(?:React|Vue|Angular|Node\.js|Express|Django|Flask|Spring|Laravel)\b',
                r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|CI/CD)\b',
                r'\b(?:SQL|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch)\b',
                r'\b(?:HTML|CSS|SASS|LESS|Bootstrap|Tailwind)\b',
                r'\b(?:REST|GraphQL|API|Microservices|Serverless)\b',
                r'\b(?:Agile|Scrum|DevOps|TDD|BDD)\b'
            ]
            
            extracted_skills = set()
            description_lower = job_description.lower()
            
            for pattern in skill_patterns:
                matches = re.findall(pattern, job_description, re.IGNORECASE)
                extracted_skills.update(matches)
            
            # Add common soft skills if mentioned
            soft_skills = ['communication', 'leadership', 'teamwork', 'problem-solving', 
                          'analytical', 'creative', 'detail-oriented', 'self-motivated']
            
            for skill in soft_skills:
                if skill in description_lower:
                    extracted_skills.add(skill.title())
            
            logger.info(f"Fallback skill extraction found {len(extracted_skills)} skills")
            return list(extracted_skills)
            
        except Exception as e:
            logger.error(f"Fallback skill extraction failed: {e}")
            return []
    
    def handle_job_recommendation_failure(self, db: Session, user_id: int) -> List[Dict]:
        """Fallback job recommendations using local algorithms"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            
            user_skills = user.profile.get('skills', []) if user.profile else []
            user_location = user.profile.get('locations', []) if user.profile else []
            
            # Get all jobs for the user
            jobs = db.query(Job).filter(
                Job.user_id == user_id,
                Job.status == 'not_applied'
            ).all()
            
            recommendations = []
            
            for job in jobs:
                score = self._calculate_local_job_score(job, user_skills, user_location)
                
                if score > 0.3:  # Minimum threshold
                    recommendations.append({
                        'job_id': job.id,
                        'title': job.title,
                        'company': job.company,
                        'location': job.location,
                        'score': score,
                        'reasoning': self._generate_local_reasoning(job, user_skills, score),
                        'fallback': True
                    })
            
            # Sort by score and return top 10
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"Fallback recommendations generated: {len(recommendations[:10])}")
            return recommendations[:10]
            
        except Exception as e:
            logger.error(f"Fallback job recommendations failed: {e}")
            return []
    
    def _calculate_local_job_score(self, job: Job, user_skills: List[str], user_locations: List[str]) -> float:
        """Calculate job match score using local algorithms"""
        score = 0.0
        
        # Skill matching (40% weight)
        if user_skills and job.requirements:
            job_skills = self.handle_skill_extraction_failure(
                job.description or str(job.requirements)
            )
            
            if job_skills:
                skill_matches = len(set(user_skills) & set(job_skills))
                skill_score = skill_matches / max(len(job_skills), 1)
                score += skill_score * 0.4
        
        # Location matching (30% weight)
        if user_locations and job.location:
            location_match = any(
                loc.lower() in job.location.lower() or 'remote' in job.location.lower()
                for loc in user_locations
            )
            if location_match:
                score += 0.3
        
        # Recency bonus (20% weight)
        if job.date_posted:
            days_old = (datetime.now() - job.date_posted).days
            recency_score = max(0, 1 - (days_old / 30))  # Decay over 30 days
            score += recency_score * 0.2
        
        # Source bonus (10% weight)
        if job.source in ['linkedin', 'indeed', 'company_website']:
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_local_reasoning(self, job: Job, user_skills: List[str], score: float) -> str:
        """Generate explanation for job recommendation"""
        reasons = []
        
        if score > 0.7:
            reasons.append("Strong match based on your skills and preferences")
        elif score > 0.5:
            reasons.append("Good match with some relevant skills")
        else:
            reasons.append("Potential match worth considering")
        
        if job.location and 'remote' in job.location.lower():
            reasons.append("Offers remote work flexibility")
        
        if job.date_posted and (datetime.now() - job.date_posted).days < 7:
            reasons.append("Recently posted position")
        
        return ". ".join(reasons)
    
    def handle_market_analysis_failure(self, db: Session, user_id: int) -> Dict:
        """Fallback market analysis using local data"""
        try:
            # Get user's jobs for analysis
            jobs = db.query(Job).filter(Job.user_id == user_id).all()
            
            if not jobs:
                return {
                    'fallback': True,
                    'message': 'Insufficient data for market analysis',
                    'trends': {}
                }
            
            # Analyze local job data
            companies = [job.company for job in jobs if job.company]
            locations = [job.location for job in jobs if job.location]
            titles = [job.title for job in jobs if job.title]
            
            # Calculate basic statistics
            company_counts = Counter(companies)
            location_counts = Counter(locations)
            title_counts = Counter(titles)
            
            # Salary analysis
            salaries = [
                (job.salary_min + job.salary_max) / 2 
                for job in jobs 
                if job.salary_min and job.salary_max
            ]
            
            avg_salary = sum(salaries) / len(salaries) if salaries else 0
            
            analysis = {
                'fallback': True,
                'message': 'Analysis based on your tracked jobs (external APIs unavailable)',
                'trends': {
                    'top_companies': dict(company_counts.most_common(5)),
                    'popular_locations': dict(location_counts.most_common(5)),
                    'common_titles': dict(title_counts.most_common(5)),
                    'average_salary': round(avg_salary, 2) if avg_salary else None,
                    'total_opportunities': len(jobs),
                    'analysis_date': datetime.now().isoformat()
                },
                'recommendations': [
                    "Focus on companies you've already identified",
                    "Consider similar roles to those you've tracked",
                    "Expand search to similar locations" if locations else "Consider remote opportunities"
                ]
            }
            
            logger.info("Fallback market analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Fallback market analysis failed: {e}")
            return {
                'fallback': True,
                'error': 'Market analysis temporarily unavailable',
                'trends': {}
            }
    
    def handle_email_service_failure(self, user_email: str, content: Dict) -> Dict:
        """Fallback for email service failures"""
        try:
            # Store email content for later delivery
            cache_key = f"pending_email:{user_email}:{datetime.now().timestamp()}"
            
            email_data = {
                'recipient': user_email,
                'content': content,
                'created_at': datetime.now().isoformat(),
                'retry_count': 0,
                'type': content.get('type', 'notification')
            }
            
            # Cache for later retry
            cache_service.set(cache_key, email_data, ttl=86400)  # 24 hours
            
            logger.warning(f"Email service unavailable, cached for later delivery: {user_email}")
            
            return {
                'success': False,
                'fallback': True,
                'message': 'Email temporarily unavailable, will retry when service is restored',
                'cached_for_retry': True
            }
            
        except Exception as e:
            logger.error(f"Email fallback failed: {e}")
            return {
                'success': False,
                'error': 'Email service temporarily unavailable'
            }
    
    def handle_job_ingestion_failure(self, db: Session, user_id: int) -> Dict:
        """Fallback when job ingestion APIs fail"""
        try:
            # Get user preferences
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'error': 'User not found'}
            
            preferences = user.profile.get('preferences', {}) if user.profile else {}
            
            # Suggest manual job search strategies
            suggestions = {
                'fallback': True,
                'message': 'Automatic job discovery temporarily unavailable',
                'manual_strategies': [
                    'Check company career pages directly',
                    'Use LinkedIn job search with your preferred keywords',
                    'Visit Indeed.com and other job boards manually',
                    'Network with contacts in your target companies',
                    'Set up Google Alerts for job postings'
                ],
                'recommended_searches': self._generate_search_suggestions(preferences),
                'next_retry': (datetime.now() + timedelta(hours=4)).isoformat()
            }
            
            logger.info("Job ingestion fallback suggestions generated")
            return suggestions
            
        except Exception as e:
            logger.error(f"Job ingestion fallback failed: {e}")
            return {
                'fallback': True,
                'error': 'Job discovery temporarily unavailable'
            }
    
    def _generate_search_suggestions(self, preferences: Dict) -> List[str]:
        """Generate manual search suggestions based on user preferences"""
        suggestions = []
        
        if preferences.get('industries'):
            for industry in preferences['industries'][:3]:
                suggestions.append(f"'{industry} jobs' on major job boards")
        
        if preferences.get('job_titles'):
            for title in preferences['job_titles'][:3]:
                suggestions.append(f"'{title}' positions")
        
        if preferences.get('locations'):
            for location in preferences['locations'][:2]:
                suggestions.append(f"Jobs in {location}")
        
        # Add generic suggestions if no specific preferences
        if not suggestions:
            suggestions = [
                "Search for roles matching your skills",
                "Look for remote opportunities",
                "Check startup job boards like AngelList"
            ]
        
        return suggestions
    
    def check_api_health(self, api_name: str) -> Dict:
        """Check if external API is available"""
        try:
            # This would normally ping the actual API
            # For now, return cached status or assume degraded
            cache_key = f"api_health:{api_name}"
            cached_status = cache_service.get(cache_key)
            
            if cached_status:
                return cached_status
            
            # Default to degraded mode
            status = {
                'api': api_name,
                'status': 'degraded',
                'last_check': datetime.now().isoformat(),
                'fallback_available': True
            }
            
            cache_service.set(cache_key, status, ttl=300)  # 5 minutes
            return status
            
        except Exception as e:
            logger.error(f"API health check failed for {api_name}: {e}")
            return {
                'api': api_name,
                'status': 'unavailable',
                'error': str(e),
                'fallback_available': True
            }
    
    def get_degradation_status(self) -> Dict:
        """Get overall system degradation status"""
        apis = ['openai', 'job_boards', 'email_service', 'embedding_service']
        
        status = {
            'overall_status': 'operational',
            'degraded_services': [],
            'available_fallbacks': [],
            'offline_capabilities': {
                'data_export': True,
                'cached_recommendations': True,
                'local_job_search': True,
                'profile_management': True,
                'application_tracking': True
            },
            'last_updated': datetime.now().isoformat()
        }
        
        degraded_count = 0
        
        for api in apis:
            api_status = self.check_api_health(api)
            if api_status['status'] != 'operational':
                degraded_count += 1
                status['degraded_services'].append({
                    'service': api,
                    'status': api_status['status'],
                    'fallback': api_status.get('fallback_available', False),
                    'fallback_strategy': self._get_fallback_strategy(api)
                })
                
                if api_status.get('fallback_available'):
                    status['available_fallbacks'].append(api)
        
        # Determine overall status
        if degraded_count == 0:
            status['overall_status'] = 'operational'
        elif degraded_count < len(apis) / 2:
            status['overall_status'] = 'degraded'
        else:
            status['overall_status'] = 'limited'
        
        return status
    
    def _get_fallback_strategy(self, api_name: str) -> str:
        """Get fallback strategy description for an API"""
        strategies = {
            'openai': 'Local regex-based skill extraction and keyword matching',
            'job_boards': 'Manual job entry and cached job recommendations',
            'email_service': 'Local notification storage for later delivery',
            'embedding_service': 'Keyword-based similarity matching'
        }
        return strategies.get(api_name, 'Basic functionality maintained')
    
    def handle_complete_offline_mode(self, db: Session, user_id: int) -> Dict:
        """Handle complete offline mode with all external services unavailable"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'error': 'User not found'}
            
            # Prepare comprehensive offline package
            offline_data = {
                'mode': 'complete_offline',
                'user_profile': user.profile,
                'cached_jobs': self._get_cached_jobs(db, user_id),
                'local_recommendations': self._generate_offline_recommendations(db, user_id),
                'available_features': [
                    'Job browsing (cached data)',
                    'Application status tracking',
                    'Profile editing',
                    'Local job search and filtering',
                    'Data export and backup',
                    'Basic analytics (historical data)',
                    'Manual job entry'
                ],
                'unavailable_features': [
                    'New job discovery',
                    'AI-powered recommendations',
                    'Email notifications',
                    'Real-time market analysis',
                    'External API integrations'
                ],
                'offline_instructions': [
                    'All changes will sync when connection is restored',
                    'Use manual job entry for new opportunities',
                    'Export data regularly for backup',
                    'Check cached recommendations for relevant jobs'
                ],
                'last_sync': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'offline_data': offline_data,
                'message': 'System operating in complete offline mode'
            }
            
        except Exception as e:
            logger.error(f"Complete offline mode setup failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_cached_jobs(self, db: Session, user_id: int) -> List[Dict]:
        """Get cached jobs for offline use"""
        try:
            jobs = db.query(Job).filter(
                Job.user_id == user_id
            ).order_by(Job.created_at.desc()).limit(100).all()
            
            return [
                {
                    'id': job.id,
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'status': job.status,
                    'description': job.description,
                    'requirements': job.requirements,
                    'cached': True,
                    'last_updated': job.updated_at.isoformat()
                }
                for job in jobs
            ]
        except Exception as e:
            logger.error(f"Failed to get cached jobs: {e}")
            return []
    
    def _generate_offline_recommendations(self, db: Session, user_id: int) -> List[Dict]:
        """Generate basic recommendations using only local data"""
        try:
            # Use the existing fallback recommendation logic
            return self.handle_job_recommendation_failure(db, user_id)
        except Exception as e:
            logger.error(f"Failed to generate offline recommendations: {e}")
            return []


graceful_degradation_service = GracefulDegradationService()