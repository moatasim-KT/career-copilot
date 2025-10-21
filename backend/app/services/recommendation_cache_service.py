"""
Enhanced recommendation caching and performance tracking service
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.user import User
from app.models.analytics import Analytics
from app.services.recommendation_service import recommendation_service


class RecommendationCacheService:
    """Service for caching and tracking recommendation performance"""
    
    def __init__(self):
        self.memory_cache = {}
    
    def get_cache_key(self, user_id: int) -> str:
        """Generate cache key for user recommendations"""
        return f"recommendations_user_{user_id}"
    
    def get_cached_recommendations(
        self, 
        db: Session, 
        user_id: int,
        max_age_hours: int = 24
    ) -> Optional[List[Dict]]:
        """Get cached recommendations if available and fresh"""
        # Check memory cache first
        cache_key = self.get_cache_key(user_id)
        if cache_key in self.memory_cache:
            cached_data = self.memory_cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            
            if datetime.now() - cache_time < timedelta(hours=max_age_hours):
                return cached_data['recommendations']
        
        # Check database cache
        analytics = db.query(Analytics).filter(
            Analytics.user_id == user_id,
            Analytics.type == "recommendation_cache"
        ).order_by(Analytics.generated_at.desc()).first()
        
        if analytics:
            cache_time = analytics.generated_at
            if datetime.now() - cache_time < timedelta(hours=max_age_hours):
                recommendations = analytics.data.get('recommendations', [])
                
                # Update memory cache
                self.memory_cache[cache_key] = {
                    'recommendations': recommendations,
                    'timestamp': cache_time.isoformat()
                }
                
                return recommendations
        
        return None
    
    def save_recommendations_to_cache(
        self, 
        db: Session, 
        user_id: int, 
        recommendations: List[Dict]
    ) -> bool:
        """Save recommendations to cache"""
        try:
            # Save to database
            cache_data = {
                'recommendations': recommendations,
                'generated_at': datetime.now().isoformat(),
                'total_count': len(recommendations)
            }
            
            analytics = Analytics(
                user_id=user_id,
                type="recommendation_cache",
                data=cache_data
            )
            
            db.add(analytics)
            db.commit()
            
            # Save to memory cache
            cache_key = self.get_cache_key(user_id)
            self.memory_cache[cache_key] = {
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
            return True
        except Exception as e:
            print(f"Failed to cache recommendations: {e}")
            return False
    
    def invalidate_cache(self, db: Session, user_id: int) -> bool:
        """Invalidate cached recommendations for a user"""
        # Clear memory cache
        cache_key = self.get_cache_key(user_id)
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
        
        # Mark database cache as stale (optional - we use timestamp instead)
        return True
    
    def generate_and_cache_recommendations(
        self, 
        db: Session, 
        user_id: int,
        force_refresh: bool = False,
        include_performance_data: bool = False
    ) -> List[Dict]:
        """Enhanced recommendation generation with performance tracking"""
        start_time = datetime.now()
        
        # Check cache first unless force refresh
        if not force_refresh:
            cached = self.get_cached_recommendations(db, user_id)
            if cached:
                # Track cache hit
                if include_performance_data:
                    self._track_cache_performance(db, user_id, 'hit', start_time)
                return cached
        
        # Generate fresh recommendations with enhanced parameters
        recommendations = recommendation_service.generate_recommendations_for_user(
            db, user_id, limit=20, min_score=0.4, diversify=True
        )
        
        # Enhance recommendations with additional metadata
        for i, rec in enumerate(recommendations):
            rec['cache_generated_at'] = datetime.now().isoformat()
            rec['cache_version'] = '2.0'
            rec['personalization_score'] = self._calculate_personalization_score(db, user_id, rec)
        
        # Cache them with enhanced data
        self.save_recommendations_to_cache(db, user_id, recommendations)
        
        # Track cache miss and generation performance
        if include_performance_data:
            generation_time = (datetime.now() - start_time).total_seconds()
            self._track_cache_performance(db, user_id, 'miss', start_time, generation_time)
        
        return recommendations
    
    def _calculate_personalization_score(self, db: Session, user_id: int, recommendation: Dict) -> float:
        """Calculate how well a recommendation is personalized for the user"""
        # Get user's interaction history
        performance = self.calculate_recommendation_performance(db, user_id, days=30)
        
        base_score = recommendation.get('overall_score', 0.5)
        personalization_bonus = 0.0
        
        # Bonus for job types user typically engages with
        engagement_rate = performance.get('metrics', {}).get('engagement_rate', 0)
        if engagement_rate > 0.3:
            personalization_bonus += 0.1
        
        # Bonus for companies in user's preferred size/industry
        company_score = recommendation.get('score_breakdown', {}).get('company_preference', {}).get('score', 0.5)
        if company_score > 0.8:
            personalization_bonus += 0.05
        
        return min(base_score + personalization_bonus, 1.0)
    
    def _track_cache_performance(
        self, 
        db: Session, 
        user_id: int, 
        result_type: str, 
        start_time: datetime,
        generation_time: float = None
    ):
        """Track cache performance metrics"""
        try:
            performance_data = {
                'user_id': user_id,
                'result_type': result_type,  # 'hit' or 'miss'
                'timestamp': datetime.now().isoformat(),
                'response_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }
            
            if generation_time:
                performance_data['generation_time_seconds'] = generation_time
            
            analytics = Analytics(
                user_id=user_id,
                type="recommendation_cache_performance",
                data=performance_data
            )
            db.add(analytics)
            db.commit()
        except Exception as e:
            print(f"Failed to track cache performance: {e}")
    
    def cleanup_memory_cache(self, max_age_hours: int = 24):
        """Clean up stale entries from memory cache"""
        current_time = datetime.now()
        stale_keys = []
        
        for key, cached_data in self.memory_cache.items():
            try:
                cache_time = datetime.fromisoformat(cached_data['timestamp'])
                if current_time - cache_time > timedelta(hours=max_age_hours):
                    stale_keys.append(key)
            except (KeyError, ValueError):
                stale_keys.append(key)  # Remove invalid entries
        
        for key in stale_keys:
            del self.memory_cache[key]
        
        return len(stale_keys)
    
    def track_recommendation_interaction(
        self, 
        db: Session, 
        user_id: int, 
        job_id: int,
        interaction_type: str
    ) -> bool:
        """Track user interaction with recommendations"""
        try:
            # Get or create interaction tracking
            analytics = db.query(Analytics).filter(
                Analytics.user_id == user_id,
                Analytics.type == "recommendation_interactions"
            ).order_by(Analytics.generated_at.desc()).first()
            
            if not analytics:
                analytics = Analytics(
                    user_id=user_id,
                    type="recommendation_interactions",
                    data={'interactions': []}
                )
                db.add(analytics)
            
            # Add interaction
            interaction = {
                'job_id': job_id,
                'type': interaction_type,  # 'viewed', 'clicked', 'applied', 'dismissed'
                'timestamp': datetime.now().isoformat()
            }
            
            interactions = analytics.data.get('interactions', [])
            interactions.append(interaction)
            analytics.data = {'interactions': interactions}
            
            db.commit()
            return True
        except Exception as e:
            print(f"Failed to track interaction: {e}")
            return False
    
    def calculate_recommendation_performance(
        self, 
        db: Session, 
        user_id: int,
        days: int = 30
    ) -> Dict:
        """Calculate recommendation performance metrics"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get interaction data
        analytics = db.query(Analytics).filter(
            Analytics.user_id == user_id,
            Analytics.type == "recommendation_interactions",
            Analytics.generated_at >= cutoff_date
        ).all()
        
        if not analytics:
            return {
                'period_days': days,
                'total_recommendations': 0,
                'total_interactions': 0,
                'metrics': {}
            }
        
        # Aggregate interactions
        all_interactions = []
        for record in analytics:
            all_interactions.extend(record.data.get('interactions', []))
        
        # Count by type
        interaction_counts = {
            'viewed': 0,
            'clicked': 0,
            'applied': 0,
            'dismissed': 0
        }
        
        for interaction in all_interactions:
            interaction_type = interaction.get('type')
            if interaction_type in interaction_counts:
                interaction_counts[interaction_type] += 1
        
        # Calculate rates
        total_shown = interaction_counts['viewed'] + interaction_counts['clicked'] + interaction_counts['applied']
        
        click_through_rate = (
            interaction_counts['clicked'] / total_shown 
            if total_shown > 0 else 0
        )
        
        application_rate = (
            interaction_counts['applied'] / total_shown 
            if total_shown > 0 else 0
        )
        
        return {
            'period_days': days,
            'total_recommendations': total_shown,
            'total_interactions': len(all_interactions),
            'interaction_counts': interaction_counts,
            'metrics': {
                'click_through_rate': round(click_through_rate, 3),
                'application_rate': round(application_rate, 3),
                'engagement_rate': round(
                    (interaction_counts['clicked'] + interaction_counts['applied']) / total_shown
                    if total_shown > 0 else 0, 3
                )
            }
        }
    
    def get_personalized_recommendations(
        self, 
        db: Session, 
        user_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """Enhanced personalized recommendations based on user behavior and preferences"""
        # Get cached recommendations
        recommendations = self.generate_and_cache_recommendations(db, user_id, include_performance_data=True)
        
        if not recommendations:
            return []
        
        # Get comprehensive user interaction history
        performance = self.calculate_recommendation_performance(db, user_id, days=90)
        recent_performance = self.calculate_recommendation_performance(db, user_id, days=7)
        
        # Apply personalization algorithms
        personalized_recs = self._apply_personalization_algorithms(
            recommendations, performance, recent_performance, user_id
        )
        
        # Sort by personalization score
        personalized_recs.sort(key=lambda x: x.get('personalization_score', 0), reverse=True)
        
        return personalized_recs[:limit]
    
    def _apply_personalization_algorithms(
        self, 
        recommendations: List[Dict], 
        performance: Dict, 
        recent_performance: Dict,
        user_id: int
    ) -> List[Dict]:
        """Apply advanced personalization algorithms to recommendations"""
        engagement_rate = performance.get('metrics', {}).get('engagement_rate', 0)
        recent_engagement = recent_performance.get('metrics', {}).get('engagement_rate', 0)
        application_rate = performance.get('metrics', {}).get('application_rate', 0)
        
        personalized = []
        
        # Strategy 1: Low engagement - diversify with different job types
        if engagement_rate < 0.2:
            # Include more diverse recommendations
            high_score = recommendations[:len(recommendations)//3]
            medium_score = recommendations[len(recommendations)//3:2*len(recommendations)//3]
            diverse_picks = recommendations[2*len(recommendations)//3:]
            
            # Mix them for diversity
            mixed_recs = []
            for i in range(max(len(high_score), len(medium_score), len(diverse_picks))):
                if i < len(high_score):
                    mixed_recs.append(high_score[i])
                if i < len(diverse_picks):
                    mixed_recs.append(diverse_picks[i])
                if i < len(medium_score):
                    mixed_recs.append(medium_score[i])
            
            personalized = mixed_recs
        
        # Strategy 2: Good engagement but low applications - focus on higher quality matches
        elif engagement_rate > 0.3 and application_rate < 0.15:
            # Prioritize high-confidence, high-score recommendations
            high_confidence = [r for r in recommendations if r.get('confidence', 0) > 0.7]
            other_recs = [r for r in recommendations if r.get('confidence', 0) <= 0.7]
            
            personalized = high_confidence + other_recs
        
        # Strategy 3: Good performance - maintain current approach with slight optimization
        else:
            personalized = recommendations
        
        # Apply recent behavior adjustments
        if recent_engagement > engagement_rate * 1.5:  # Recent improvement
            # User is more engaged recently, show more challenging opportunities
            for rec in personalized:
                if rec.get('score_breakdown', {}).get('experience_level', {}).get('score', 0) < 0.8:
                    rec['personalization_score'] = rec.get('personalization_score', 0.5) + 0.1
        
        elif recent_engagement < engagement_rate * 0.5:  # Recent decline
            # User engagement declining, show more accessible opportunities
            for rec in personalized:
                if rec.get('score_breakdown', {}).get('skill_match', {}).get('score', 0) > 0.8:
                    rec['personalization_score'] = rec.get('personalization_score', 0.5) + 0.1
        
        return personalized
    
    def optimize_recommendations(
        self, 
        db: Session, 
        user_id: int
    ) -> Dict:
        """Analyze and optimize recommendation algorithm for user"""
        performance = self.calculate_recommendation_performance(db, user_id, days=90)
        
        recommendations = []
        
        # Low engagement
        if performance['metrics'].get('engagement_rate', 0) < 0.2:
            recommendations.append({
                'issue': 'Low engagement with recommendations',
                'suggestion': 'Update your profile with more specific preferences',
                'action': 'Review and update skills, location, and salary preferences'
            })
        
        # Low application rate
        if performance['metrics'].get('application_rate', 0) < 0.1:
            recommendations.append({
                'issue': 'Low application rate',
                'suggestion': 'Recommendations may be too ambitious or not aligned',
                'action': 'Adjust experience level or salary expectations'
            })
        
        # High click but low apply
        ctr = performance['metrics'].get('click_through_rate', 0)
        app_rate = performance['metrics'].get('application_rate', 0)
        
        if ctr > 0.5 and app_rate < 0.2:
            recommendations.append({
                'issue': 'High interest but low applications',
                'suggestion': 'You may need better application materials',
                'action': 'Update your resume and cover letter templates'
            })
        
        return {
            'performance': performance,
            'optimization_recommendations': recommendations,
            'overall_health': 'good' if performance['metrics'].get('engagement_rate', 0) > 0.3 else 'needs_improvement'
        }


recommendation_cache_service = RecommendationCacheService()