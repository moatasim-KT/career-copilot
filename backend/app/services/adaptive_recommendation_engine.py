"""
Adaptive recommendation engine that adjusts based on user feedback
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import hashlib

from app.models.user import User
from app.models.job import Job
from app.services.recommendation_engine import RecommendationEngine
from app.services.feedback_analysis_service import FeedbackAnalysisService
from app.core.logging import get_logger

logger = get_logger(__name__)


class AdaptiveRecommendationEngine(RecommendationEngine):
    """
    Enhanced recommendation engine that adapts based on user feedback
    Supports A/B testing and dynamic weight adjustment
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.feedback_service = FeedbackAnalysisService(db)
        
        # Default weights (can be overridden)
        self.default_weights = {
            "skill_matching": 50,
            "location_matching": 30,
            "experience_matching": 20
        }
        
        # A/B test configurations
        self.ab_test_configs = {
            "skill_weight_test": {
                "variant_a": {"skill_matching": 50, "location_matching": 30, "experience_matching": 20},
                "variant_b": {"skill_matching": 60, "location_matching": 25, "experience_matching": 15},
                "active": True,
                "traffic_split": 0.5  # 50% of users get variant B
            },
            "location_weight_test": {
                "variant_a": {"skill_matching": 50, "location_matching": 30, "experience_matching": 20},
                "variant_b": {"skill_matching": 45, "location_matching": 40, "experience_matching": 15},
                "active": False,
                "traffic_split": 0.3  # 30% of users get variant B
            }
        }
    
    def get_user_algorithm_variant(self, user_id: int, test_name: str) -> str:
        """
        Determine which algorithm variant a user should get for A/B testing
        Uses consistent hashing to ensure same user always gets same variant
        """
        if test_name not in self.ab_test_configs:
            return "variant_a"
        
        test_config = self.ab_test_configs[test_name]
        if not test_config.get("active", False):
            return "variant_a"
        
        # Use consistent hashing based on user_id and test_name
        hash_input = f"{user_id}_{test_name}".encode('utf-8')
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        hash_ratio = (hash_value % 1000) / 1000.0  # Convert to 0-1 range
        
        if hash_ratio < test_config["traffic_split"]:
            return "variant_b"
        else:
            return "variant_a"
    
    def get_algorithm_weights(self, user_id: int) -> Dict[str, float]:
        """
        Get algorithm weights for a specific user, considering A/B tests
        """
        weights = self.default_weights.copy()
        
        # Check active A/B tests
        for test_name, test_config in self.ab_test_configs.items():
            if test_config.get("active", False):
                variant = self.get_user_algorithm_variant(user_id, test_name)
                if variant in test_config:
                    weights = test_config[variant].copy()
                    logger.info(f"User {user_id} assigned to {test_name} {variant}")
                    break  # Use first active test
        
        return weights
    
    def calculate_match_score_adaptive(self, user: User, job: Job, weights: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate match score using adaptive weights
        """
        if weights is None:
            weights = self.get_algorithm_weights(user.id)
        
        score = 0.0
        
        # 1. Tech Stack Match
        user_skills = set(s.lower() for s in user.skills) if user.skills else set()
        job_tech_stack = set(t.lower() for t in job.tech_stack) if job.tech_stack else set()
        
        if user_skills and job_tech_stack:
            common_skills = user_skills.intersection(job_tech_stack)
            skill_match_percentage = len(common_skills) / len(job_tech_stack)
            score += skill_match_percentage * weights["skill_matching"]
        
        # 2. Location Match
        user_locations = set(l.lower() for l in user.preferred_locations) if user.preferred_locations else set()
        job_location = job.location.lower() if job.location else ""
        
        location_score = 0
        if user_locations and job_location:
            if "remote" in user_locations and "remote" in job_location:
                location_score = 1.0  # Perfect remote match
            elif any(loc in job_location for loc in user_locations):
                location_score = 0.8  # Good location match
            elif "remote" in user_locations and "remote" not in job_location:
                location_score = 0.3  # User prefers remote, job is not
            elif "remote" not in user_locations and "remote" in job_location:
                location_score = 0.3  # Job is remote, user doesn't prefer
            elif "remote" in user_locations and not job_location:
                location_score = 0.5  # User prefers remote, job location unknown
            elif not user_locations and job_location:
                location_score = 0.2  # User has no preference, job has location
        
        score += location_score * weights["location_matching"]
        
        # 3. Experience Level Match
        user_exp = self.experience_levels.get(user.experience_level.lower(), 0) if user.experience_level else 0
        
        job_title_lower = job.title.lower()
        job_exp = 0
        if "junior" in job_title_lower: job_exp = 1
        elif "mid" in job_title_lower: job_exp = 2
        elif "senior" in job_title_lower: job_exp = 3
        elif "lead" in job_title_lower: job_exp = 4
        elif "staff" in job_title_lower: job_exp = 5
        elif "principal" in job_title_lower: job_exp = 6
        
        experience_score = 0
        if user_exp > 0 and job_exp > 0:
            if user_exp == job_exp:
                experience_score = 1.0  # Perfect match
            elif abs(user_exp - job_exp) == 1:
                experience_score = 0.5  # Close match
            else:
                experience_score = 0.25  # Some match
        
        score += experience_score * weights["experience_matching"]
        
        return min(score, 100.0)
    
    def get_recommendations_adaptive(self, user: User, skip: int = 0, limit: int = 5) -> List[Dict]:
        """
        Get recommendations using adaptive algorithm
        """
        # Get user's algorithm weights (considering A/B tests)
        weights = self.get_algorithm_weights(user.id)
        
        # Query jobs that haven't been applied to
        jobs = self.db.query(Job).filter(
            Job.user_id == user.id,
            Job.status == "not_applied"
        ).all()
        
        # Calculate adaptive match scores
        scored_jobs = []
        for job in jobs:
            score = self.calculate_match_score_adaptive(user, job, weights)
            scored_jobs.append({
                "job": job,
                "score": score,
                "algorithm_variant": self._get_active_test_variant(user.id),
                "weights_used": weights
            })
        
        # Sort by score descending
        scored_jobs.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_jobs[skip:skip + limit]
    
    def _get_active_test_variant(self, user_id: int) -> Optional[str]:
        """Get the active test variant for a user"""
        for test_name, test_config in self.ab_test_configs.items():
            if test_config.get("active", False):
                variant = self.get_user_algorithm_variant(user_id, test_name)
                return f"{test_name}_{variant}"
        return None
    
    def update_algorithm_weights(self, new_weights: Dict[str, float], test_name: Optional[str] = None):
        """
        Update algorithm weights based on feedback analysis
        """
        # Validate weights sum to 100
        total_weight = sum(new_weights.values())
        if abs(total_weight - 100) > 0.1:
            raise ValueError(f"Weights must sum to 100, got {total_weight}")
        
        if test_name:
            # Update specific A/B test variant
            if test_name in self.ab_test_configs:
                self.ab_test_configs[test_name]["variant_b"] = new_weights.copy()
                logger.info(f"Updated A/B test {test_name} variant B weights: {new_weights}")
        else:
            # Update default weights
            self.default_weights = new_weights.copy()
            logger.info(f"Updated default algorithm weights: {new_weights}")
    
    def start_ab_test(self, test_name: str, variant_a_weights: Dict[str, float], 
                      variant_b_weights: Dict[str, float], traffic_split: float = 0.5):
        """
        Start a new A/B test
        """
        if traffic_split < 0 or traffic_split > 1:
            raise ValueError("Traffic split must be between 0 and 1")
        
        self.ab_test_configs[test_name] = {
            "variant_a": variant_a_weights.copy(),
            "variant_b": variant_b_weights.copy(),
            "active": True,
            "traffic_split": traffic_split,
            "started_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Started A/B test {test_name} with {traffic_split:.1%} traffic to variant B")
    
    def stop_ab_test(self, test_name: str):
        """
        Stop an A/B test
        """
        if test_name in self.ab_test_configs:
            self.ab_test_configs[test_name]["active"] = False
            self.ab_test_configs[test_name]["stopped_at"] = datetime.utcnow().isoformat()
            logger.info(f"Stopped A/B test {test_name}")
    
    def get_ab_test_results(self, test_name: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Get A/B test results comparing feedback between variants
        """
        if test_name not in self.ab_test_configs:
            raise ValueError(f"A/B test {test_name} not found")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get feedback data for the test period
        from app.models.feedback import JobRecommendationFeedback
        
        feedback_data = self.db.query(JobRecommendationFeedback).filter(
            JobRecommendationFeedback.created_at >= cutoff_date
        ).all()
        
        # Separate feedback by variant
        variant_a_feedback = []
        variant_b_feedback = []
        
        for feedback in feedback_data:
            user_variant = self.get_user_algorithm_variant(feedback.user_id, test_name)
            if user_variant == "variant_a":
                variant_a_feedback.append(feedback)
            else:
                variant_b_feedback.append(feedback)
        
        # Calculate metrics for each variant
        def calculate_metrics(feedback_list):
            if not feedback_list:
                return {"total": 0, "helpful": 0, "satisfaction_rate": 0}
            
            helpful_count = sum(1 for f in feedback_list if f.is_helpful)
            total_count = len(feedback_list)
            satisfaction_rate = helpful_count / total_count if total_count > 0 else 0
            
            return {
                "total": total_count,
                "helpful": helpful_count,
                "unhelpful": total_count - helpful_count,
                "satisfaction_rate": satisfaction_rate
            }
        
        variant_a_metrics = calculate_metrics(variant_a_feedback)
        variant_b_metrics = calculate_metrics(variant_b_feedback)
        
        # Calculate statistical significance (basic chi-square test)
        significance = self._calculate_statistical_significance(
            variant_a_metrics, variant_b_metrics
        )
        
        return {
            "test_name": test_name,
            "test_config": self.ab_test_configs[test_name],
            "analysis_period_days": days_back,
            "variant_a": {
                "weights": self.ab_test_configs[test_name]["variant_a"],
                "metrics": variant_a_metrics
            },
            "variant_b": {
                "weights": self.ab_test_configs[test_name]["variant_b"],
                "metrics": variant_b_metrics
            },
            "statistical_significance": significance,
            "recommendation": self._generate_test_recommendation(variant_a_metrics, variant_b_metrics, significance)
        }
    
    def _calculate_statistical_significance(self, variant_a: Dict, variant_b: Dict) -> Dict[str, Any]:
        """
        Calculate basic statistical significance between variants
        """
        # Simple chi-square test for proportions
        a_total = variant_a["total"]
        a_helpful = variant_a["helpful"]
        b_total = variant_b["total"]
        b_helpful = variant_b["helpful"]
        
        if a_total < 10 or b_total < 10:
            return {
                "significant": False,
                "confidence": 0,
                "reason": "Insufficient sample size"
            }
        
        # Calculate pooled proportion
        total_helpful = a_helpful + b_helpful
        total_samples = a_total + b_total
        
        if total_samples == 0:
            return {"significant": False, "confidence": 0, "reason": "No data"}
        
        pooled_p = total_helpful / total_samples
        
        # Calculate standard error
        se = (pooled_p * (1 - pooled_p) * (1/a_total + 1/b_total)) ** 0.5
        
        if se == 0:
            return {"significant": False, "confidence": 0, "reason": "No variance"}
        
        # Calculate z-score
        p_a = a_helpful / a_total if a_total > 0 else 0
        p_b = b_helpful / b_total if b_total > 0 else 0
        z_score = abs(p_a - p_b) / se
        
        # Determine significance (simplified)
        if z_score > 2.58:  # 99% confidence
            confidence = 99
            significant = True
        elif z_score > 1.96:  # 95% confidence
            confidence = 95
            significant = True
        elif z_score > 1.64:  # 90% confidence
            confidence = 90
            significant = True
        else:
            confidence = max(0, int((z_score / 1.96) * 95))
            significant = False
        
        return {
            "significant": significant,
            "confidence": confidence,
            "z_score": z_score,
            "effect_size": abs(p_a - p_b)
        }
    
    def _generate_test_recommendation(self, variant_a: Dict, variant_b: Dict, significance: Dict) -> str:
        """
        Generate recommendation based on A/B test results
        """
        a_rate = variant_a["satisfaction_rate"]
        b_rate = variant_b["satisfaction_rate"]
        
        if not significance["significant"]:
            return "Continue test - no statistically significant difference detected"
        
        if b_rate > a_rate:
            improvement = ((b_rate - a_rate) / a_rate) * 100 if a_rate > 0 else 0
            return f"Implement variant B - shows {improvement:.1f}% improvement with {significance['confidence']}% confidence"
        else:
            decline = ((a_rate - b_rate) / a_rate) * 100 if a_rate > 0 else 0
            return f"Keep variant A - variant B shows {decline:.1f}% decline with {significance['confidence']}% confidence"
    
    def apply_feedback_insights(self):
        """
        Apply insights from feedback analysis to improve the algorithm
        """
        suggestions = self.feedback_service.get_algorithm_adjustment_suggestions()
        
        if suggestions["confidence_score"] > 0.7 and suggestions["sample_size"] > 50:
            # High confidence - apply suggested weights
            new_weights = suggestions["suggested_weights"]
            self.update_algorithm_weights(new_weights)
            
            logger.info(f"Applied feedback insights with {suggestions['confidence_score']:.1%} confidence")
            logger.info(f"Weight changes: {suggestions['adjustments']}")
            
            return {
                "applied": True,
                "confidence": suggestions["confidence_score"],
                "changes": suggestions["adjustments"]
            }
        else:
            # Low confidence - start A/B test instead
            test_name = f"feedback_adjustment_{datetime.utcnow().strftime('%Y%m%d')}"
            
            self.start_ab_test(
                test_name,
                self.default_weights,
                suggestions["suggested_weights"],
                traffic_split=0.3  # Conservative 30% test
            )
            
            logger.info(f"Started A/B test {test_name} due to low confidence ({suggestions['confidence_score']:.1%})")
            
            return {
                "applied": False,
                "ab_test_started": test_name,
                "confidence": suggestions["confidence_score"],
                "reason": "Low confidence - testing via A/B test"
            }