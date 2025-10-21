"""
Enhanced recommendation engine with advanced scoring algorithms and personalization
"""

import math
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import numpy as np

from app.models.user import User
from app.models.job import Job
from app.models.application import JobApplication
from app.services.skill_matching_service import skill_matching_service
from app.core.cache import job_recommendation_cache

logger = logging.getLogger(__name__)


class EnhancedRecommendationService:
    """Enhanced recommendation service with weighted scoring and advanced algorithms"""
    
    def __init__(self):
        # Enhanced scoring weights with more granular control
        self.weights = {
            'skill_match': 0.35,           # Core technical compatibility
            'experience_alignment': 0.20,  # Experience level fit
            'location_preference': 0.15,   # Location and remote work
            'company_culture': 0.10,       # Company fit and culture
            'career_growth': 0.10,         # Growth potential
            'market_timing': 0.05,         # Job posting recency
            'salary_alignment': 0.05       # Compensation fit
        }
        
        # Experience level mapping for precise scoring
        self.experience_hierarchy = {
            'intern': 0, 'entry': 1, 'junior': 2, 'mid': 3, 
            'senior': 4, 'lead': 5, 'principal': 6, 'director': 7, 'vp': 8, 'executive': 9
        }
        
        # Skill importance weights for different categories
        self.skill_categories = {
            'core_programming': ['python', 'javascript', 'java', 'typescript', 'go', 'rust'],
            'web_frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'express'],
            'databases': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch'],
            'cloud_platforms': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
            'data_science': ['pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn'],
            'devops': ['jenkins', 'gitlab-ci', 'terraform', 'ansible', 'prometheus']
        }
        
        # Location scoring parameters
        self.location_scoring = {
            'exact_match': 1.0,
            'same_city': 0.9,
            'same_metro': 0.8,
            'same_state': 0.6,
            'same_country': 0.4,
            'remote_perfect': 1.0,
            'remote_good': 0.85,
            'hybrid_perfect': 1.0,
            'hybrid_good': 0.8
        }

    def calculate_enhanced_skill_score(
        self, 
        user_skills: List[str], 
        job: Job,
        user_profile: Dict
    ) -> Tuple[float, Dict[str, Any]]:
        """Enhanced skill matching with category weighting and semantic analysis"""
        
        requirements = job.requirements or {}
        required_skills = requirements.get('skills_required', [])
        preferred_skills = requirements.get('skills_preferred', [])
        
        if not required_skills and not preferred_skills:
            return 0.5, {
                'score': 0.5,
                'reason': 'No specific skills listed',
                'category_scores': {},
                'missing_critical': [],
                'skill_gaps': []
            }
        
        # Get detailed skill matching from existing service
        required_score, required_details = skill_matching_service.calculate_skill_match_score(
            user_skills, required_skills, use_semantic=True
        )
        
        preferred_score = 0.0
        preferred_details = {}
        if preferred_skills:
            preferred_score, preferred_details = skill_matching_service.calculate_skill_match_score(
                user_skills, preferred_skills, use_semantic=True
            )
        
        # Calculate category-based scoring
        category_scores = self._calculate_skill_category_scores(user_skills, required_skills + preferred_skills)
        
        # Weight required vs preferred skills
        combined_score = (required_score * 0.8) + (preferred_score * 0.2)
        
        # Apply category bonuses
        category_bonus = self._calculate_category_bonus(category_scores)
        
        # Experience-skill alignment bonus
        experience_bonus = self._calculate_experience_skill_bonus(
            user_profile.get('experience_level', 'mid'),
            user_skills,
            required_skills
        )
        
        final_score = min(combined_score + category_bonus + experience_bonus, 1.0)
        
        return final_score, {
            'score': round(final_score, 3),
            'required_match': required_score,
            'preferred_match': preferred_score,
            'category_scores': category_scores,
            'category_bonus': category_bonus,
            'experience_bonus': experience_bonus,
            'matching_skills': required_details.get('matching_skills', []),
            'missing_skills': required_details.get('missing_skills', []),
            'semantic_matches': required_details.get('semantic_matches', []),
            'reason': self._generate_skill_reason(required_score, preferred_score, category_scores)
        }

    def _calculate_skill_category_scores(self, user_skills: List[str], job_skills: List[str]) -> Dict[str, float]:
        """Calculate scores for different skill categories"""
        user_skills_lower = [s.lower() for s in user_skills]
        job_skills_lower = [s.lower() for s in job_skills]
        
        category_scores = {}
        
        for category, skills in self.skill_categories.items():
            user_category_skills = [s for s in user_skills_lower if s in skills]
            job_category_skills = [s for s in job_skills_lower if s in skills]
            
            if job_category_skills:
                matches = len(set(user_category_skills) & set(job_category_skills))
                category_scores[category] = matches / len(job_category_skills)
            else:
                category_scores[category] = 0.0
        
        return category_scores

    def _calculate_category_bonus(self, category_scores: Dict[str, float]) -> float:
        """Calculate bonus based on category coverage"""
        # Bonus for having skills across multiple categories
        covered_categories = sum(1 for score in category_scores.values() if score > 0)
        diversity_bonus = min(covered_categories * 0.02, 0.1)
        
        # Bonus for high scores in important categories
        important_categories = ['core_programming', 'web_frameworks', 'cloud_platforms']
        importance_bonus = sum(
            category_scores.get(cat, 0) * 0.03 
            for cat in important_categories
        )
        
        return min(diversity_bonus + importance_bonus, 0.15)

    def _calculate_experience_skill_bonus(self, experience_level: str, user_skills: List[str], required_skills: List[str]) -> float:
        """Calculate bonus based on experience-skill alignment"""
        exp_level = self.experience_hierarchy.get(experience_level.lower(), 3)
        
        # Senior+ developers get bonus for advanced skills
        if exp_level >= 4:
            advanced_skills = ['kubernetes', 'terraform', 'microservices', 'system design']
            advanced_matches = len(set(s.lower() for s in user_skills) & set(advanced_skills))
            return min(advanced_matches * 0.02, 0.08)
        
        # Junior developers get bonus for foundational skills
        elif exp_level <= 2:
            foundational_skills = ['git', 'testing', 'debugging', 'documentation']
            foundational_matches = len(set(s.lower() for s in user_skills) & set(foundational_skills))
            return min(foundational_matches * 0.015, 0.06)
        
        return 0.0

    def _generate_skill_reason(self, required_score: float, preferred_score: float, category_scores: Dict[str, float]) -> str:
        """Generate human-readable explanation for skill scoring"""
        if required_score >= 0.8:
            base = "Strong skill match"
        elif required_score >= 0.6:
            base = "Good skill alignment"
        elif required_score >= 0.4:
            base = "Moderate skill fit"
        else:
            base = "Limited skill match"
        
        # Add category insights
        top_category = max(category_scores.items(), key=lambda x: x[1]) if category_scores else None
        if top_category and top_category[1] > 0.7:
            base += f", excellent {top_category[0].replace('_', ' ')} skills"
        
        return base

    def calculate_enhanced_location_score(
        self, 
        user_locations: List[str], 
        job: Job,
        user_profile: Dict
    ) -> Tuple[float, Dict[str, Any]]:
        """Enhanced location scoring with commute analysis and remote work preferences"""
        
        if not job.location:
            return 0.6, {'score': 0.6, 'reason': 'Location not specified', 'match_type': 'unknown'}
        
        job_location = job.location.lower()
        requirements = job.requirements or {}
        remote_options = requirements.get('remote_options', '').lower()
        
        # Enhanced remote work detection
        remote_keywords = ['remote', 'work from home', 'wfh', 'distributed', 'anywhere', 'virtual']
        hybrid_keywords = ['hybrid', 'flexible', 'part remote', 'mixed', 'optional office']
        
        is_remote = any(keyword in job_location or keyword in remote_options for keyword in remote_keywords)
        is_hybrid = any(keyword in remote_options for keyword in hybrid_keywords)
        
        user_remote_pref = user_profile.get('preferences', {}).get('remote_preference', 'hybrid')
        
        # Remote work scoring with enhanced logic
        if is_remote:
            return self._score_remote_work(user_remote_pref, 'remote')
        elif is_hybrid:
            return self._score_remote_work(user_remote_pref, 'hybrid')
        
        # Physical location scoring with enhanced matching
        if not user_locations:
            return 0.5, {'score': 0.5, 'reason': 'No location preferences set', 'match_type': 'no_preference'}
        
        best_score = 0.0
        best_match = None
        match_type = 'no_match'
        
        for user_loc in user_locations:
            score, match_info = self._calculate_location_similarity(user_loc, job.location)
            if score > best_score:
                best_score = score
                best_match = user_loc
                match_type = match_info['type']
        
        return best_score, {
            'score': best_score,
            'reason': f"{match_type.replace('_', ' ').title()} match: {best_match}",
            'match_type': match_type,
            'matched_location': best_match
        }

    def _score_remote_work(self, user_preference: str, job_type: str) -> Tuple[float, Dict[str, Any]]:
        """Score remote work compatibility"""
        scoring_matrix = {
            ('remote', 'remote'): (self.location_scoring['remote_perfect'], 'Perfect remote match'),
            ('hybrid', 'remote'): (self.location_scoring['remote_good'], 'Remote work with hybrid preference'),
            ('office', 'remote'): (0.7, 'Remote work but prefers office'),
            ('remote', 'hybrid'): (self.location_scoring['hybrid_good'], 'Hybrid with remote preference'),
            ('hybrid', 'hybrid'): (self.location_scoring['hybrid_perfect'], 'Perfect hybrid match'),
            ('office', 'hybrid'): (self.location_scoring['hybrid_good'], 'Hybrid offers office option')
        }
        
        score, reason = scoring_matrix.get((user_preference, job_type), (0.6, 'Moderate remote compatibility'))
        
        return score, {
            'score': score,
            'reason': reason,
            'match_type': f'{job_type}_work',
            'remote_compatibility': True
        }

    def _calculate_location_similarity(self, user_location: str, job_location: str) -> Tuple[float, Dict[str, str]]:
        """Calculate similarity between two physical locations"""
        user_loc = user_location.lower().strip()
        job_loc = job_location.lower().strip()
        
        # Exact match
        if user_loc == job_loc or user_loc in job_loc or job_loc in user_loc:
            return self.location_scoring['exact_match'], {'type': 'exact_match'}
        
        # City-level matching
        user_parts = user_loc.replace(',', ' ').split()
        job_parts = job_loc.replace(',', ' ').split()
        
        # Check for city name matches
        for user_part in user_parts:
            for job_part in job_parts:
                if len(user_part) > 2 and len(job_part) > 2:
                    if user_part == job_part:
                        return self.location_scoring['same_city'], {'type': 'same_city'}
        
        # State/region matching (simplified)
        state_mappings = {
            'ca': ['california', 'san francisco', 'los angeles', 'san diego'],
            'ny': ['new york', 'nyc', 'manhattan', 'brooklyn'],
            'tx': ['texas', 'dallas', 'houston', 'austin'],
            'wa': ['washington', 'seattle', 'bellevue', 'redmond']
        }
        
        user_state = None
        job_state = None
        
        for state, cities in state_mappings.items():
            if any(city in user_loc for city in cities) or state in user_loc:
                user_state = state
            if any(city in job_loc for city in cities) or state in job_loc:
                job_state = state
        
        if user_state and job_state and user_state == job_state:
            return self.location_scoring['same_state'], {'type': 'same_state'}
        
        # Country matching (default to same country for now)
        return self.location_scoring['same_country'], {'type': 'same_country'}

    def calculate_enhanced_experience_score(
        self, 
        user_experience: str, 
        job: Job,
        user_profile: Dict
    ) -> Tuple[float, Dict[str, Any]]:
        """Enhanced experience scoring with career trajectory analysis"""
        
        requirements = job.requirements or {}
        required_level = requirements.get('experience_level', 'mid')
        min_years = requirements.get('min_years_experience', 0)
        max_years = requirements.get('max_years_experience', 20)
        
        user_level_num = self.experience_hierarchy.get(user_experience.lower(), 3)
        required_level_num = self.experience_hierarchy.get(required_level.lower(), 3)
        user_years = user_profile.get('years_experience', user_level_num * 2)
        
        # Base score from level alignment
        level_diff = required_level_num - user_level_num
        base_score = self._calculate_level_alignment_score(level_diff)
        
        # Years of experience alignment
        years_score = self._calculate_years_alignment_score(user_years, min_years, max_years)
        
        # Career trajectory bonus
        trajectory_bonus = self._calculate_trajectory_bonus(
            user_profile.get('career_goals', []),
            job.title,
            level_diff
        )
        
        # Industry experience bonus
        industry_bonus = self._calculate_industry_experience_bonus(
            user_profile.get('industry_experience', []),
            requirements.get('industry', '')
        )
        
        final_score = min(
            (base_score * 0.5) + (years_score * 0.3) + trajectory_bonus + industry_bonus,
            1.0
        )
        
        return final_score, {
            'score': round(final_score, 3),
            'level_alignment': base_score,
            'years_alignment': years_score,
            'trajectory_bonus': trajectory_bonus,
            'industry_bonus': industry_bonus,
            'level_difference': level_diff,
            'reason': self._generate_experience_reason(level_diff, years_score, trajectory_bonus)
        }

    def _calculate_level_alignment_score(self, level_diff: int) -> float:
        """Calculate score based on experience level difference"""
        if level_diff == 0:
            return 1.0  # Perfect match
        elif level_diff == 1:
            return 0.85  # Growth opportunity
        elif level_diff == -1:
            return 0.8   # Slightly overqualified
        elif level_diff == 2:
            return 0.6   # Stretch role
        elif level_diff == -2:
            return 0.65  # Moderately overqualified
        elif level_diff >= 3:
            return 0.3   # Too advanced
        else:  # level_diff <= -3
            return 0.4   # Significantly overqualified

    def _calculate_years_alignment_score(self, user_years: int, min_years: int, max_years: int) -> float:
        """Calculate score based on years of experience alignment"""
        if min_years <= user_years <= max_years:
            return 1.0
        elif user_years < min_years:
            gap = min_years - user_years
            return max(0.3, 1.0 - (gap * 0.1))
        else:  # user_years > max_years
            excess = user_years - max_years
            return max(0.5, 1.0 - (excess * 0.05))

    def _calculate_trajectory_bonus(self, career_goals: List[str], job_title: str, level_diff: int) -> float:
        """Calculate bonus for career trajectory alignment"""
        if not career_goals:
            return 0.0
        
        job_title_lower = job_title.lower()
        goal_alignment = any(goal.lower() in job_title_lower for goal in career_goals)
        
        if goal_alignment and level_diff > 0:
            return 0.1  # Growth opportunity aligned with goals
        elif goal_alignment:
            return 0.05  # Goal alignment without growth
        
        return 0.0

    def _calculate_industry_experience_bonus(self, user_industries: List[str], job_industry: str) -> float:
        """Calculate bonus for industry experience"""
        if not user_industries or not job_industry:
            return 0.0
        
        job_industry_lower = job_industry.lower()
        industry_match = any(industry.lower() in job_industry_lower for industry in user_industries)
        
        return 0.05 if industry_match else 0.0

    def _generate_experience_reason(self, level_diff: int, years_score: float, trajectory_bonus: float) -> str:
        """Generate human-readable experience explanation"""
        if level_diff == 0:
            base = "Perfect experience level match"
        elif level_diff == 1:
            base = "Good growth opportunity"
        elif level_diff == -1:
            base = "Slightly overqualified but good fit"
        elif level_diff >= 2:
            base = "Significant stretch role"
        else:
            base = "Overqualified for this level"
        
        if years_score >= 0.8:
            base += ", excellent years of experience fit"
        elif years_score >= 0.6:
            base += ", good experience duration match"
        
        if trajectory_bonus > 0:
            base += ", aligns with career goals"
        
        return base

    def calculate_market_timing_score(self, job: Job) -> Tuple[float, Dict[str, Any]]:
        """Calculate score based on job posting recency and market factors"""
        
        if not job.date_posted:
            return 0.6, {'score': 0.6, 'reason': 'No posting date available', 'days_old': None}
        
        days_old = (datetime.now() - job.date_posted).days
        
        # Recency scoring with decay
        if days_old <= 3:
            recency_score = 1.0
            freshness = "Very fresh posting"
        elif days_old <= 7:
            recency_score = 0.9
            freshness = "Recent posting"
        elif days_old <= 14:
            recency_score = 0.8
            freshness = "Moderately recent"
        elif days_old <= 30:
            recency_score = 0.6
            freshness = "Older posting"
        else:
            recency_score = 0.4
            freshness = "Stale posting"
        
        # Application urgency factor
        urgency_keywords = ['urgent', 'immediate', 'asap', 'start immediately']
        job_text = f"{job.title} {job.description or ''}".lower()
        has_urgency = any(keyword in job_text for keyword in urgency_keywords)
        urgency_bonus = 0.1 if has_urgency else 0.0
        
        final_score = min(recency_score + urgency_bonus, 1.0)
        
        return final_score, {
            'score': round(final_score, 3),
            'days_old': days_old,
            'recency_score': recency_score,
            'urgency_bonus': urgency_bonus,
            'reason': f"{freshness} ({days_old} days old)"
        }

    def calculate_salary_alignment_score(
        self, 
        job: Job, 
        user_profile: Dict
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate score based on salary expectations alignment"""
        
        user_salary_min = user_profile.get('salary_expectations', {}).get('min', 0)
        user_salary_max = user_profile.get('salary_expectations', {}).get('max', 999999)
        
        if not job.salary_min and not job.salary_max:
            return 0.6, {'score': 0.6, 'reason': 'Salary not specified', 'alignment': 'unknown'}
        
        job_salary_min = job.salary_min or 0
        job_salary_max = job.salary_max or job_salary_min or 999999
        
        # Calculate overlap between ranges
        overlap_start = max(user_salary_min, job_salary_min)
        overlap_end = min(user_salary_max, job_salary_max)
        
        if overlap_start <= overlap_end:
            # There's overlap
            user_range = user_salary_max - user_salary_min
            job_range = job_salary_max - job_salary_min
            overlap_size = overlap_end - overlap_start
            
            if user_range > 0:
                overlap_ratio = overlap_size / user_range
            else:
                overlap_ratio = 1.0 if job_salary_min >= user_salary_min else 0.0
            
            score = min(0.6 + (overlap_ratio * 0.4), 1.0)
            alignment = "Good salary alignment"
        else:
            # No overlap
            if job_salary_max < user_salary_min:
                gap = user_salary_min - job_salary_max
                score = max(0.2, 0.6 - (gap / user_salary_min * 0.4))
                alignment = "Below salary expectations"
            else:
                score = 0.8  # Above expectations is generally good
                alignment = "Above salary expectations"
        
        return score, {
            'score': round(score, 3),
            'reason': alignment,
            'job_range': f"${job_salary_min:,}-${job_salary_max:,}" if job_salary_min else "Not specified",
            'user_range': f"${user_salary_min:,}-${user_salary_max:,}" if user_salary_min else "Not specified"
        }

    def generate_enhanced_recommendation(
        self, 
        db: Session, 
        user_id: int, 
        job: Job
    ) -> Dict[str, Any]:
        """Generate comprehensive recommendation with enhanced scoring"""
        
        # Check cache first
        cache_key = f"enhanced_rec_{user_id}_{job.id}"
        cached_result = job_recommendation_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        profile = user.profile or {}
        user_skills = profile.get('skills', [])
        user_experience = profile.get('experience_level', 'mid')
        user_locations = profile.get('locations', [])
        
        # Calculate all scoring components
        skill_score, skill_details = self.calculate_enhanced_skill_score(user_skills, job, profile)
        experience_score, experience_details = self.calculate_enhanced_experience_score(user_experience, job, profile)
        location_score, location_details = self.calculate_enhanced_location_score(user_locations, job, profile)
        timing_score, timing_details = self.calculate_market_timing_score(job)
        salary_score, salary_details = self.calculate_salary_alignment_score(job, profile)
        
        # Company culture score (using existing logic)
        from app.services.recommendation_service import recommendation_service
        company_score, company_details = recommendation_service.calculate_company_preference_score(
            profile.get('preferences', {}), job, profile
        )
        growth_score, growth_details = recommendation_service.calculate_career_growth_potential_score(
            profile.get('career_goals', []), job, profile
        )
        
        # Calculate weighted overall score
        overall_score = (
            skill_score * self.weights['skill_match'] +
            experience_score * self.weights['experience_alignment'] +
            location_score * self.weights['location_preference'] +
            company_score * self.weights['company_culture'] +
            growth_score * self.weights['career_growth'] +
            timing_score * self.weights['market_timing'] +
            salary_score * self.weights['salary_alignment']
        )
        
        # Calculate confidence score
        confidence = self._calculate_enhanced_confidence(
            skill_details, experience_details, location_details, timing_details
        )
        
        # Generate comprehensive explanation
        explanation = self._generate_enhanced_explanation(
            overall_score, skill_details, experience_details, location_details,
            company_details, growth_details, timing_details, salary_details
        )
        
        # Generate personalized action items
        action_items = self._generate_enhanced_action_items(
            skill_details, experience_details, growth_details, overall_score
        )
        
        result = {
            'job_id': job.id,
            'job_title': job.title,
            'company': job.company,
            'location': job.location,
            'overall_score': round(overall_score, 3),
            'confidence': round(confidence, 3),
            'score_breakdown': {
                'skill_match': {
                    'score': skill_details['score'],
                    'weight': self.weights['skill_match'],
                    'contribution': round(skill_score * self.weights['skill_match'], 3),
                    'details': skill_details
                },
                'experience_alignment': {
                    'score': experience_details['score'],
                    'weight': self.weights['experience_alignment'],
                    'contribution': round(experience_score * self.weights['experience_alignment'], 3),
                    'details': experience_details
                },
                'location_preference': {
                    'score': location_details['score'],
                    'weight': self.weights['location_preference'],
                    'contribution': round(location_score * self.weights['location_preference'], 3),
                    'details': location_details
                },
                'company_culture': {
                    'score': company_details['score'],
                    'weight': self.weights['company_culture'],
                    'contribution': round(company_score * self.weights['company_culture'], 3),
                    'details': company_details
                },
                'career_growth': {
                    'score': growth_details['score'],
                    'weight': self.weights['career_growth'],
                    'contribution': round(growth_score * self.weights['career_growth'], 3),
                    'details': growth_details
                },
                'market_timing': {
                    'score': timing_details['score'],
                    'weight': self.weights['market_timing'],
                    'contribution': round(timing_score * self.weights['market_timing'], 3),
                    'details': timing_details
                },
                'salary_alignment': {
                    'score': salary_details['score'],
                    'weight': self.weights['salary_alignment'],
                    'contribution': round(salary_score * self.weights['salary_alignment'], 3),
                    'details': salary_details
                }
            },
            'explanation': explanation,
            'action_items': action_items,
            'metadata': {
                'algorithm_version': '3.0_enhanced',
                'generated_at': datetime.now().isoformat(),
                'scoring_factors': 7,
                'personalization_level': 'high'
            }
        }
        
        # Cache the result
        job_recommendation_cache.set(cache_key, result, timeout=3600)  # 1 hour cache
        
        return result

    def _calculate_enhanced_confidence(
        self, 
        skill_details: Dict, 
        experience_details: Dict, 
        location_details: Dict,
        timing_details: Dict
    ) -> float:
        """Calculate confidence in recommendation based on data quality"""
        
        confidence_factors = []
        
        # Skill matching confidence
        if skill_details.get('matching_skills'):
            confidence_factors.append(0.9)
        elif skill_details.get('semantic_matches'):
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.4)
        
        # Experience confidence
        level_diff = abs(experience_details.get('level_difference', 0))
        if level_diff <= 1:
            confidence_factors.append(0.9)
        elif level_diff <= 2:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Location confidence
        match_type = location_details.get('match_type', '')
        if 'exact' in match_type or 'perfect' in match_type:
            confidence_factors.append(0.9)
        elif 'good' in match_type or 'same' in match_type:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
        
        # Timing confidence
        days_old = timing_details.get('days_old')
        if days_old is not None and days_old <= 7:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
        
        return sum(confidence_factors) / len(confidence_factors)

    def _generate_enhanced_explanation(
        self, 
        overall_score: float, 
        skill_details: Dict,
        experience_details: Dict, 
        location_details: Dict,
        company_details: Dict,
        growth_details: Dict,
        timing_details: Dict,
        salary_details: Dict
    ) -> Dict[str, Any]:
        """Generate comprehensive explanation for the recommendation"""
        
        score_percentage = int(overall_score * 100)
        
        # Overall assessment
        if score_percentage >= 85:
            summary = f"Excellent match ({score_percentage}%) - Highly recommended"
            recommendation = "Apply immediately"
        elif score_percentage >= 70:
            summary = f"Strong match ({score_percentage}%) - Recommended"
            recommendation = "Strong candidate for application"
        elif score_percentage >= 55:
            summary = f"Good match ({score_percentage}%) - Worth considering"
            recommendation = "Consider applying with tailored materials"
        else:
            summary = f"Moderate match ({score_percentage}%) - Proceed with caution"
            recommendation = "May require significant preparation"
        
        # Identify top strengths and concerns
        all_scores = [
            ('Skills', skill_details['score'], skill_details['reason']),
            ('Experience', experience_details['score'], experience_details['reason']),
            ('Location', location_details['score'], location_details['reason']),
            ('Company Fit', company_details['score'], company_details['reason']),
            ('Growth Potential', growth_details['score'], growth_details['reason']),
            ('Market Timing', timing_details['score'], timing_details['reason']),
            ('Salary Alignment', salary_details['score'], salary_details['reason'])
        ]
        
        all_scores.sort(key=lambda x: x[1], reverse=True)
        
        strengths = [f"{name}: {reason}" for name, score, reason in all_scores[:3] if score > 0.7]
        concerns = [f"{name}: {reason}" for name, score, reason in all_scores if score < 0.5]
        
        # Key insights
        insights = []
        
        if skill_details.get('category_bonus', 0) > 0.05:
            insights.append("Strong skill diversity across multiple technology areas")
        
        if experience_details.get('trajectory_bonus', 0) > 0:
            insights.append("Aligns well with your career trajectory")
        
        if timing_details.get('days_old', 30) <= 7:
            insights.append("Recent job posting - good timing for application")
        
        if salary_details['score'] > 0.8:
            insights.append("Excellent salary alignment with your expectations")
        
        return {
            'summary': summary,
            'recommendation': recommendation,
            'score_percentage': score_percentage,
            'top_strengths': strengths[:3],
            'main_concerns': concerns[:2],
            'key_insights': insights,
            'detailed_breakdown': {
                factor: {'score': score, 'reason': reason}
                for factor, score, reason in all_scores
            }
        }

    def _generate_enhanced_action_items(
        self, 
        skill_details: Dict, 
        experience_details: Dict,
        growth_details: Dict, 
        overall_score: float
    ) -> List[Dict[str, str]]:
        """Generate personalized action items based on scoring analysis"""
        
        action_items = []
        
        # Skill-based actions
        missing_skills = skill_details.get('missing_skills', [])
        if missing_skills:
            priority_skills = missing_skills[:3]
            action_items.append({
                'category': 'skill_development',
                'priority': 'high' if len(missing_skills) > 3 else 'medium',
                'action': f"Develop key skills: {', '.join(priority_skills)}",
                'description': 'Focus on these skills to significantly improve your match score',
                'impact': 'High - could increase match score by 15-25%'
            })
        
        # Experience positioning
        level_diff = experience_details.get('level_difference', 0)
        if level_diff > 1:
            action_items.append({
                'category': 'experience',
                'priority': 'high',
                'action': 'Highlight relevant experience and achievements',
                'description': 'Emphasize projects and accomplishments that demonstrate readiness for this level',
                'impact': 'Medium - helps bridge experience gap'
            })
        elif level_diff < -1:
            action_items.append({
                'category': 'positioning',
                'priority': 'medium',
                'action': 'Address overqualification concerns',
                'description': 'Explain motivation for this role and long-term career strategy',
                'impact': 'Medium - addresses potential employer concerns'
            })
        
        # Application strategy based on overall score
        if overall_score >= 0.8:
            action_items.append({
                'category': 'application',
                'priority': 'high',
                'action': 'Apply with confidence - you\'re a strong match',
                'description': 'Prioritize this application and apply quickly',
                'impact': 'High - excellent fit for this role'
            })
        elif overall_score >= 0.6:
            action_items.append({
                'category': 'application',
                'priority': 'medium',
                'action': 'Customize application materials',
                'description': 'Tailor resume and cover letter to highlight matching qualifications',
                'impact': 'Medium - improves application competitiveness'
            })
        else:
            action_items.append({
                'category': 'preparation',
                'priority': 'medium',
                'action': 'Significant preparation recommended',
                'description': 'Consider skill development or gaining relevant experience first',
                'impact': 'High - may significantly improve future match potential'
            })
        
        # Growth opportunity actions
        if growth_details.get('aligned_goals'):
            action_items.append({
                'category': 'application',
                'priority': 'high',
                'action': 'Emphasize career goal alignment',
                'description': 'Highlight how this role fits your career objectives in your application',
                'impact': 'Medium - demonstrates strategic career thinking'
            })
        
        return action_items[:4]  # Limit to most important actions

    def get_personalized_recommendations(
        self, 
        db: Session, 
        user_id: int,
        limit: int = 10,
        min_score: float = 0.5,
        include_applied: bool = False
    ) -> List[Dict[str, Any]]:
        """Get personalized recommendations using enhanced scoring"""
        
        # Get jobs to recommend
        query = db.query(Job).filter(Job.status == 'active')
        
        if not include_applied:
            applied_job_ids = db.query(JobApplication.job_id).filter(
                JobApplication.user_id == user_id
            ).subquery()
            query = query.filter(~Job.id.in_(applied_job_ids))
        
        jobs = query.order_by(desc(Job.date_posted)).limit(limit * 3).all()  # Get more to filter
        
        if not jobs:
            return []
        
        # Generate recommendations
        recommendations = []
        for job in jobs:
            rec = self.generate_enhanced_recommendation(db, user_id, job)
            if rec and rec.get('overall_score', 0) >= min_score:
                recommendations.append(rec)
        
        # Sort by combined score (overall + confidence + recency)
        for rec in recommendations:
            timing_score = rec['score_breakdown']['market_timing']['score']
            combined_score = (
                rec['overall_score'] * 0.7 + 
                rec['confidence'] * 0.2 + 
                timing_score * 0.1
            )
            rec['combined_score'] = combined_score
        
        recommendations.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Add ranking metadata
        for i, rec in enumerate(recommendations[:limit]):
            rec['rank'] = i + 1
            rec['percentile'] = round((1 - i / len(recommendations)) * 100, 1) if recommendations else 0
        
        return recommendations[:limit]


# Global service instance
enhanced_recommendation_service = EnhancedRecommendationService()