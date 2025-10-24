"""
Multi-layered recommendation algorithm with explainable reasoning and Redis caching
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

from app.models.user import User
from app.models.job import Job
from app.services.skill_matching_service import skill_matching_service
from app.core.cache import job_recommendation_cache, cached, cache_invalidate

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for generating intelligent job recommendations with multi-layered algorithm"""
    
    def __init__(self):
        # Scoring weights for different factors
        self.weights = {
            'skill_match': 0.40,        # Primary factor - skill compatibility
            'location_preference': 0.25, # Location and remote work preferences
            'experience_level': 0.20,   # Experience level alignment
            'company_preference': 0.10, # Company size, industry, culture fit
            'career_growth': 0.05       # Career advancement potential
        }
        
        # Experience level hierarchy for scoring
        self.experience_levels = {
            'entry': 1, 'junior': 2, 'mid': 3, 'senior': 4, 'lead': 5, 'principal': 6, 'executive': 7
        }
        
        # Company size preferences
        self.company_sizes = {
            'startup': {'employees': (1, 50), 'culture': ['innovative', 'fast-paced', 'flexible']},
            'small': {'employees': (51, 200), 'culture': ['collaborative', 'personal', 'agile']},
            'medium': {'employees': (201, 1000), 'culture': ['structured', 'growth', 'balanced']},
            'large': {'employees': (1001, 10000), 'culture': ['stable', 'established', 'corporate']},
            'enterprise': {'employees': (10001, 100000), 'culture': ['enterprise', 'global', 'formal']}
        }
    
    def calculate_skill_match_score(
        self, 
        user_skills: List[str], 
        job: Job,
        user_profile: Dict
    ) -> Tuple[float, Dict[str, Any]]:
        """Enhanced skill matching with semantic analysis and context."""
        requirements = job.requirements or {}
        required_skills = requirements.get('skills_required', [])
        
        if not required_skills:
            return self._create_default_skill_score()
        
        # Get base skill match score
        base_score, base_details = self._calculate_base_skill_score(user_skills, required_skills)
        
        # Calculate contextual bonuses
        context_bonuses = self._calculate_skill_context_bonus(
            job, user_skills, user_profile, required_skills
        )
        
        # Calculate final score and combine details
        final_score = min(base_score + context_bonuses['total_bonus'], 1.0)
        
        # Generate explanation and return results
        explanation = self._generate_skill_match_explanation(
            base_details, len(required_skills), context_bonuses
        )
        
        return final_score, {
            'score': round(final_score, 3),
            'reason': explanation['reason'],
            'matching_skills': base_details.get('matching_skills', []),
            'missing_skills': base_details.get('missing_skills', []),
            'semantic_matches': base_details.get('semantic_matches', []),
            'additional_matches': list(context_bonuses['additional_matches']),
            'context_bonus': round(context_bonuses['total_bonus'], 3),
            'skill_gap_analysis': self._analyze_skill_gaps(base_details.get('missing_skills', []))
        }
    
    def _create_default_skill_score(self) -> Tuple[float, Dict[str, Any]]:
        """Create default skill score when no required skills are specified."""
        return 0.5, {
            'score': 0.5,
            'reason': "No specific skills listed - neutral score",
            'matching_skills': [],
            'missing_skills': [],
            'semantic_matches': [],
            'skill_gap_analysis': {}
        }
    
    def _calculate_base_skill_score(
        self,
        user_skills: List[str],
        required_skills: List[str]
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate the base skill match score without contextual factors."""
        return skill_matching_service.calculate_skill_match_score(
            user_skills, required_skills, use_semantic=True
        )
    
    def _calculate_skill_context_bonus(
        self,
        job: Job,
        user_skills: List[str],
        user_profile: Dict,
        required_skills: List[str]
    ) -> Dict[str, Any]:
        """Calculate contextual bonus scores for skill matching."""
        # Extract job description skills
        job_text = f"{job.title} {job.description or ''}"
        extracted_skills = skill_matching_service.extract_skills_from_text(job_text)
        
        # Initialize bonuses
        context_bonus = 0.0
        additional_matches = set(user_skills).intersection(set(extracted_skills)) - set(required_skills)
        
        # Additional matches bonus
        description_bonus = min(len(additional_matches) * 0.02, 0.1)
        context_bonus += description_bonus
        
        # Experience level bonus
        requirements = job.requirements or {}
        job_level = requirements.get('experience_level', 'mid')
        user_experience = user_profile.get('experience_level', 'mid')
        
        experience_bonus = 0.05 if self._is_experience_aligned(user_experience, job_level) else 0.0
        context_bonus += experience_bonus
        
        return {
            'total_bonus': context_bonus,
            'description_bonus': description_bonus,
            'experience_bonus': experience_bonus,
            'additional_matches': additional_matches
        }
    
    def _generate_skill_match_explanation(
        self,
        base_details: Dict[str, Any],
        total_required: int,
        context_bonuses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed explanation for skill match score."""
        matching_count = len(base_details.get('matching_skills', []))
        semantic_count = len(base_details.get('semantic_matches', []))
        
        reason_parts = []
        if matching_count > 0:
            reason_parts.append(f"{matching_count}/{total_required} exact skill matches")
        if semantic_count > 0:
            reason_parts.append(f"{semantic_count} semantic matches")
        if context_bonuses['total_bonus'] > 0:
            reason_parts.append(f"context bonus: +{int(context_bonuses['total_bonus']*100)}%")
        
        return {
            'reason': "; ".join(reason_parts) if reason_parts else "Limited skill alignment"
        }
    
    def calculate_location_preference_score(
        self, 
        user_locations: List[str], 
        job: Job,
        user_profile: Dict
    ) -> Tuple[float, Dict[str, Any]]:
        """Enhanced location scoring with remote work preferences."""
        if not job.location:
            return self._create_default_location_score()
        
        # Check remote work options first
        remote_score = self._calculate_remote_work_score(job, user_profile)
        if remote_score is not None:
            return remote_score
        
        # If not remote/hybrid, check physical location match
        if not user_locations:
            return self._create_no_preference_location_score()
        
        # Calculate location match score
        return self._calculate_location_match_score(user_locations, job.location.lower())
    
    def _create_default_location_score(self) -> Tuple[float, Dict[str, Any]]:
        """Create default score when no location is specified."""
        return 0.6, {
            'score': 0.6,
            'reason': "Location not specified",
            'match_type': 'unknown',
            'remote_compatibility': False
        }
    
    def _create_no_preference_location_score(self) -> Tuple[float, Dict[str, Any]]:
        """Create score when user has no location preferences."""
        return 0.5, {
            'score': 0.5,
            'reason': "No location preference set",
            'match_type': 'no_preference',
            'remote_compatibility': False
        }
    
    def _calculate_remote_work_score(
        self,
        job: Job,
        user_profile: Dict
    ) -> Optional[Tuple[float, Dict[str, Any]]]:
        """Calculate score based on remote work preferences."""
        job_location_lower = job.location.lower()
        requirements = job.requirements or {}
        remote_options = requirements.get('remote_options', '').lower()
        user_remote_pref = user_profile.get('preferences', {}).get('remote_preference', 'hybrid')
        
        # Detect remote work options
        is_remote = self._is_remote_position(job_location_lower, remote_options)
        is_hybrid = self._is_hybrid_position(remote_options)
        
        if is_remote:
            return self._score_remote_position(user_remote_pref)
        elif is_hybrid:
            return self._score_hybrid_position(user_remote_pref)
            
        return None
    
    def _is_remote_position(self, job_location: str, remote_options: str) -> bool:
        """Check if the position is remote."""
        remote_keywords = ['remote', 'work from home', 'wfh', 'distributed']
        return any(keyword in job_location or keyword in remote_options 
                  for keyword in remote_keywords)
    
    def _is_hybrid_position(self, remote_options: str) -> bool:
        """Check if the position is hybrid."""
        hybrid_keywords = ['hybrid', 'flexible', 'part remote']
        return any(keyword in remote_options for keyword in hybrid_keywords)
    
    def _score_remote_position(
        self,
        user_remote_pref: str
    ) -> Tuple[float, Dict[str, Any]]:
        """Score a remote position based on user preference."""
        if user_remote_pref in ['remote', 'fully_remote']:
            return 1.0, {
                'score': 1.0,
                'reason': "Perfect match: Remote position for remote preference",
                'match_type': 'remote_perfect',
                'remote_compatibility': True
            }
        elif user_remote_pref == 'hybrid':
            return 0.9, {
                'score': 0.9,
                'reason': "Good match: Remote position with hybrid preference",
                'match_type': 'remote_good',
                'remote_compatibility': True
            }
        else:  # office preference
            return 0.7, {
                'score': 0.7,
                'reason': "Moderate match: Remote position but prefers office",
                'match_type': 'remote_moderate',
                'remote_compatibility': True
            }
    
    def _score_hybrid_position(
        self,
        user_remote_pref: str
    ) -> Tuple[float, Dict[str, Any]]:
        """Score a hybrid position based on user preference."""
        if user_remote_pref == 'hybrid':
            return 1.0, {
                'score': 1.0,
                'reason': "Perfect match: Hybrid position for hybrid preference",
                'match_type': 'hybrid_perfect',
                'remote_compatibility': True
            }
        elif user_remote_pref in ['remote', 'office']:
            return 0.8, {
                'score': 0.8,
                'reason': "Good match: Hybrid position offers flexibility",
                'match_type': 'hybrid_good',
                'remote_compatibility': True
            }
        return None
    
    def _calculate_location_match_score(
        self,
        user_locations: List[str],
        job_location: str
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate score based on physical location match."""
        best_match_score = 0.0
        best_match_location = None
        
        for user_loc in user_locations:
            user_loc_lower = user_loc.lower()
            match_score = self._get_location_match_score(user_loc_lower, job_location)
            
            if match_score > best_match_score:
                best_match_score = match_score
                best_match_location = user_loc
                if best_match_score == 1.0:  # Perfect match found
                    break
        
        if best_match_score > 0:
            match_types = {1.0: 'exact', 0.7: 'regional', 0.4: 'country'}
            return best_match_score, {
                'score': best_match_score,
                'reason': f"{match_types[best_match_score].title()} location match: {best_match_location}",
                'match_type': f'location_{match_types[best_match_score]}',
                'matched_location': best_match_location,
                'remote_compatibility': False
            }
        
        return 0.2, {
            'score': 0.2,
            'reason': "Location doesn't match preferences",
            'match_type': 'location_mismatch',
            'remote_compatibility': False
        }
    
    def _get_location_match_score(self, user_loc: str, job_location: str) -> float:
        """Get the score for a specific location match."""
        if user_loc in job_location or job_location in user_loc:
            return 1.0  # Exact city match
        elif self._is_same_region(user_loc, job_location):
            return 0.7  # State/region match
        elif self._is_same_country(user_loc, job_location):
            return 0.4  # Country match
        return 0.0  # No match
    
    def calculate_experience_level_score(
        self, 
        user_experience: str, 
        job: Job,
        user_profile: Dict
    ) -> Tuple[float, Dict[str, Any]]:
        """Enhanced experience level scoring with career growth analysis."""
        # Get required experience level
        requirements = job.requirements or {}
        required_level = requirements.get('experience_level', 'mid')
        
        # Calculate numeric levels and difference
        level_info = self._calculate_level_difference(user_experience, required_level)
        
        # Check career growth opportunity
        career_goals = user_profile.get('career_goals', [])
        is_growth_opportunity = self._is_growth_opportunity(job.title, career_goals)
        
        # Calculate base score and details
        base_score_info = self._calculate_base_experience_score(
            level_info['difference'],
            required_level,
            is_growth_opportunity
        )
        
        # Apply growth bonus if applicable
        final_score_info = self._apply_growth_bonus(
            base_score_info,
            is_growth_opportunity,
            level_info['difference']
        )
        
        return final_score_info['score'], {
            'score': round(final_score_info['score'], 3),
            'reason': final_score_info['reason'],
            'match_type': base_score_info['match_type'],
            'level_difference': level_info['difference'],
            'is_growth_opportunity': is_growth_opportunity,
            'growth_bonus': round(final_score_info['growth_bonus'], 3)
        }
    
    def _calculate_level_difference(
        self,
        user_experience: str,
        required_level: str
    ) -> Dict[str, Any]:
        """Calculate the numeric difference between experience levels."""
        user_level_num = self.experience_levels.get(user_experience.lower(), 3)
        required_level_num = self.experience_levels.get(required_level.lower(), 3)
        
        return {
            'user_level': user_level_num,
            'required_level': required_level_num,
            'difference': required_level_num - user_level_num
        }
    
    def _calculate_base_experience_score(
        self,
        level_diff: int,
        required_level: str,
        is_growth_opportunity: bool
    ) -> Dict[str, Any]:
        """Calculate base experience score based on level difference."""
        score_mappings = {
            0: {
                'score': 1.0,
                'match_type': 'perfect',
                'reason': f"Perfect experience match: {required_level}"
            },
            1: {
                'score': 0.9 if is_growth_opportunity else 0.8,
                'match_type': 'growth',
                'reason': f"Growth opportunity: {required_level} level"
            },
            -1: {
                'score': 0.8,
                'match_type': 'overqualified_slight',
                'reason': f"Slightly overqualified for {required_level} level"
            },
            2: {
                'score': 0.6 if is_growth_opportunity else 0.4,
                'match_type': 'stretch',
                'reason': f"Significant stretch to {required_level} level"
            },
            -2: {
                'score': 0.6,
                'match_type': 'overqualified_moderate',
                'reason': f"Moderately overqualified for {required_level} level"
            }
        }
        
        if level_diff >= 3:
            return {
                'score': 0.3,
                'match_type': 'too_advanced',
                'reason': f"Position may be too advanced ({required_level})"
            }
        elif level_diff <= -3:
            return {
                'score': 0.4,
                'match_type': 'overqualified_significant',
                'reason': f"Significantly overqualified for {required_level} level"
            }
        else:
            return score_mappings.get(level_diff, {
                'score': 0.5,
                'match_type': 'neutral',
                'reason': f"Neutral experience match for {required_level} level"
            })
    
    def _apply_growth_bonus(
        self,
        base_score_info: Dict[str, Any],
        is_growth_opportunity: bool,
        level_diff: int
    ) -> Dict[str, Any]:
        """Apply career growth bonus if applicable."""
        growth_bonus = 0.0
        reason = base_score_info['reason']
        
        if is_growth_opportunity and level_diff > 0:
            growth_bonus = 0.1
            reason += " (aligns with career goals)"
        
        return {
            'score': min(base_score_info['score'] + growth_bonus, 1.0),
            'reason': reason,
            'growth_bonus': growth_bonus
        }
    
    def calculate_company_preference_score(
        self, 
        user_preferences: Dict, 
        job: Job,
        user_profile: Dict
    ) -> Tuple[float, Dict[str, Any]]:
        """Enhanced company preference scoring with culture fit analysis"""
        requirements = job.requirements or {}
        
        score_components = []
        total_weight = 0
        
        # Company size preference (40% of company score)
        preferred_sizes = user_preferences.get('company_size', [])
        company_size = requirements.get('company_size', 'medium')
        
        size_score = 0.6  # Default neutral score
        size_reason = "Company size not specified in preferences"
        
        if preferred_sizes:
            if company_size in preferred_sizes:
                size_score = 1.0
                size_reason = f"Preferred company size: {company_size}"
            else:
                # Check for adjacent sizes
                size_hierarchy = ['startup', 'small', 'medium', 'large', 'enterprise']
                try:
                    current_idx = size_hierarchy.index(company_size)
                    for pref_size in preferred_sizes:
                        pref_idx = size_hierarchy.index(pref_size)
                        if abs(current_idx - pref_idx) == 1:
                            size_score = 0.7
                            size_reason = f"Adjacent to preferred size ({pref_size})"
                            break
                    else:
                        size_score = 0.4
                        size_reason = f"Different from preferred sizes"
                except ValueError:
                    pass
        
        score_components.append(('company_size', size_score, 0.4, size_reason))
        total_weight += 0.4
        
        # Industry preference (35% of company score)
        preferred_industries = user_preferences.get('industries', [])
        industry = requirements.get('industry', '')
        
        industry_score = 0.6  # Default neutral score
        industry_reason = "Industry not specified in preferences"
        
        if preferred_industries and industry:
            if industry.lower() in [ind.lower() for ind in preferred_industries]:
                industry_score = 1.0
                industry_reason = f"Preferred industry: {industry}"
            else:
                # Check for related industries
                related_score = self._calculate_industry_similarity(industry, preferred_industries)
                if related_score > 0.5:
                    industry_score = related_score
                    industry_reason = f"Related to preferred industry"
                else:
                    industry_score = 0.4
                    industry_reason = f"Different from preferred industries"
        
        score_components.append(('industry', industry_score, 0.35, industry_reason))
        total_weight += 0.35
        
        # Company culture fit (25% of company score)
        culture_keywords = requirements.get('company_culture', [])
        user_values = user_profile.get('values', [])
        
        culture_score = 0.6  # Default neutral score
        culture_reason = "Company culture not specified"
        
        if culture_keywords and user_values:
            culture_matches = set(kw.lower() for kw in culture_keywords).intersection(
                set(val.lower() for val in user_values)
            )
            if culture_matches:
                culture_score = min(0.7 + len(culture_matches) * 0.1, 1.0)
                culture_reason = f"Culture alignment: {', '.join(list(culture_matches)[:2])}"
            else:
                # Check for semantic culture alignment
                culture_score = self._calculate_culture_alignment(culture_keywords, user_values)
                if culture_score > 0.6:
                    culture_reason = "Good culture alignment"
                else:
                    culture_reason = "Limited culture alignment"
        
        score_components.append(('culture', culture_score, 0.25, culture_reason))
        total_weight += 0.25
        
        # Calculate weighted average
        weighted_score = sum(score * weight for _, score, weight, _ in score_components) / total_weight
        
        # Generate comprehensive reason
        top_component = max(score_components, key=lambda x: x[1])
        primary_reason = top_component[3]
        
        return weighted_score, {
            'score': round(weighted_score, 3),
            'reason': primary_reason,
            'components': {
                name: {'score': round(score, 3), 'reason': reason}
                for name, score, _, reason in score_components
            }
        }
    
    def calculate_career_growth_potential_score(
        self, 
        user_goals: List[str], 
        job: Job,
        user_profile: Dict
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate career growth potential and alignment with goals"""
        requirements = job.requirements or {}
        job_title_lower = job.title.lower()
        
        growth_indicators = {
            'leadership': ['lead', 'manager', 'director', 'head', 'chief', 'vp', 'vice president'],
            'technical': ['senior', 'principal', 'staff', 'architect', 'expert', 'specialist'],
            'strategic': ['strategy', 'product', 'business', 'consulting', 'advisory'],
            'entrepreneurial': ['startup', 'founder', 'entrepreneur', 'innovation', 'venture']
        }
        
        # Check direct goal alignment
        goal_alignment_score = 0.0
        aligned_goals = []
        
        for goal in user_goals:
            goal_lower = goal.lower()
            if goal_lower in job_title_lower or any(word in job_title_lower for word in goal_lower.split()):
                goal_alignment_score = 1.0
                aligned_goals.append(goal)
        
        # Check growth trajectory
        growth_score = 0.0
        growth_type = None
        
        for growth_category, keywords in growth_indicators.items():
            if any(keyword in job_title_lower for keyword in keywords):
                growth_score = 0.8
                growth_type = growth_category
                break
        
        # Check for skill development opportunities
        skill_development_score = 0.0
        required_skills = requirements.get('skills_required', [])
        user_skills = user_profile.get('skills', [])
        
        if required_skills:
            new_skills = set(required_skills) - set(user_skills)
            if new_skills:
                skill_development_score = min(len(new_skills) * 0.1, 0.3)
        
        # Calculate final score
        final_score = max(goal_alignment_score, growth_score) + skill_development_score
        final_score = min(final_score, 1.0)
        
        # Generate reason
        reasons = []
        if aligned_goals:
            reasons.append(f"Aligns with career goals: {', '.join(aligned_goals[:2])}")
        if growth_type:
            reasons.append(f"{growth_type.title()} growth opportunity")
        if skill_development_score > 0:
            reasons.append("Offers skill development")
        
        if not reasons:
            reasons.append("Standard growth potential")
        
        return final_score, {
            'score': round(final_score, 3),
            'reason': '; '.join(reasons),
            'goal_alignment': goal_alignment_score,
            'growth_potential': growth_score,
            'skill_development': skill_development_score,
            'aligned_goals': aligned_goals,
            'growth_type': growth_type
        }
    
    # Helper methods for enhanced scoring
    
    def _is_experience_aligned(self, user_experience: str, job_level: str) -> bool:
        """Check if user experience aligns with job level"""
        user_level_num = self.experience_levels.get(user_experience.lower(), 3)
        job_level_num = self.experience_levels.get(job_level.lower(), 3)
        return abs(user_level_num - job_level_num) <= 1
    
    def _analyze_skill_gaps(self, missing_skills: List[str]) -> Dict[str, Any]:
        """Analyze skill gaps and provide learning recommendations"""
        if not missing_skills:
            return {'priority_skills': [], 'learning_recommendations': []}
        
        # Categorize skills by importance (simplified)
        high_priority = []
        medium_priority = []
        low_priority = []
        
        important_skills = {
            'python', 'javascript', 'java', 'sql', 'aws', 'docker', 'kubernetes',
            'react', 'node.js', 'postgresql', 'mongodb', 'git', 'linux'
        }
        
        for skill in missing_skills:
            if skill.lower() in important_skills:
                high_priority.append(skill)
            elif any(tech in skill.lower() for tech in ['api', 'database', 'web', 'cloud']):
                medium_priority.append(skill)
            else:
                low_priority.append(skill)
        
        return {
            'priority_skills': {
                'high': high_priority[:3],
                'medium': medium_priority[:3],
                'low': low_priority[:2]
            },
            'learning_recommendations': [
                f"Focus on high-priority skills: {', '.join(high_priority[:3])}" if high_priority else None,
                f"Consider learning: {', '.join(medium_priority[:2])}" if medium_priority else None
            ]
        }
    
    def _is_same_region(self, loc1: str, loc2: str) -> bool:
        """Check if two locations are in the same region/state"""
        # Simplified region matching - in production, use a proper geocoding service
        us_states = {
            'california': ['ca', 'calif', 'san francisco', 'los angeles', 'san diego'],
            'new york': ['ny', 'nyc', 'new york city', 'manhattan', 'brooklyn'],
            'texas': ['tx', 'dallas', 'houston', 'austin', 'san antonio'],
            'florida': ['fl', 'miami', 'orlando', 'tampa', 'jacksonville']
        }
        
        for state, cities in us_states.items():
            if (any(city in loc1 for city in cities) and any(city in loc2 for city in cities)):
                return True
        
        return False
    
    def _is_same_country(self, loc1: str, loc2: str) -> bool:
        """Check if two locations are in the same country"""
        # Simplified country matching
        countries = ['usa', 'united states', 'us', 'canada', 'uk', 'united kingdom', 'germany', 'france']
        
        for country in countries:
            if country in loc1 and country in loc2:
                return True
        
        # Default to same country if no specific country mentioned
        return True
    
    def _is_growth_opportunity(self, job_title: str, career_goals: List[str]) -> bool:
        """Check if job represents a growth opportunity based on career goals"""
        job_title_lower = job_title.lower()
        
        growth_keywords = ['senior', 'lead', 'principal', 'manager', 'director', 'head', 'chief']
        has_growth_keywords = any(keyword in job_title_lower for keyword in growth_keywords)
        
        goal_alignment = any(goal.lower() in job_title_lower for goal in career_goals)
        
        return has_growth_keywords or goal_alignment
    
    def _calculate_industry_similarity(self, job_industry: str, preferred_industries: List[str]) -> float:
        """Calculate similarity between job industry and preferred industries"""
        job_industry_lower = job_industry.lower()
        
        # Industry similarity mapping (simplified)
        industry_groups = {
            'tech': ['technology', 'software', 'saas', 'fintech', 'edtech', 'healthtech'],
            'finance': ['fintech', 'banking', 'investment', 'insurance', 'financial'],
            'healthcare': ['healthtech', 'medical', 'pharmaceutical', 'biotech'],
            'education': ['edtech', 'education', 'learning', 'training']
        }
        
        for preferred in preferred_industries:
            preferred_lower = preferred.lower()
            
            # Direct match
            if preferred_lower in job_industry_lower or job_industry_lower in preferred_lower:
                return 1.0
            
            # Group similarity
            for group, industries in industry_groups.items():
                if (preferred_lower in industries and job_industry_lower in industries):
                    return 0.7
        
        return 0.3
    
    def _calculate_culture_alignment(self, culture_keywords: List[str], user_values: List[str]) -> float:
        """Calculate culture alignment score"""
        if not culture_keywords or not user_values:
            return 0.6
        
        # Culture similarity mapping
        culture_groups = {
            'innovative': ['creative', 'cutting-edge', 'disruptive', 'forward-thinking'],
            'collaborative': ['team-oriented', 'cooperative', 'inclusive', 'supportive'],
            'fast-paced': ['dynamic', 'agile', 'rapid', 'energetic'],
            'stable': ['established', 'reliable', 'consistent', 'mature'],
            'flexible': ['adaptable', 'remote-friendly', 'work-life-balance', 'autonomous']
        }
        
        alignment_score = 0.0
        matches = 0
        
        for culture_kw in culture_keywords:
            culture_kw_lower = culture_kw.lower()
            
            for user_value in user_values:
                user_value_lower = user_value.lower()
                
                # Direct match
                if culture_kw_lower == user_value_lower:
                    alignment_score += 1.0
                    matches += 1
                    continue
                
                # Group similarity
                for group, similar_values in culture_groups.items():
                    if (culture_kw_lower in similar_values and user_value_lower in similar_values):
                        alignment_score += 0.7
                        matches += 1
                        break
        
        if matches == 0:
            return 0.6
        
        return min(alignment_score / len(culture_keywords), 1.0)
    
    def generate_recommendation(
        self, 
        db: Session, 
        user_id: int, 
        job: Job
    ) -> Dict:
        """Generate comprehensive multi-layered recommendation for a job (cached)"""
        # Check cache first
        cached_scores = job_recommendation_cache.get_recommendation_scores(user_id, job.id)
        if cached_scores:
            logger.debug(f"Recommendation cache hit for user {user_id}, job {job.id}")
            return cached_scores
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        profile = user.profile or {}
        preferences = profile.get('preferences', {})
        
        # Calculate enhanced scores using multi-layered algorithm
        user_skills = profile.get('skills', [])
        skill_score, skill_details = self.calculate_skill_match_score(user_skills, job, profile)
        
        user_locations = profile.get('locations', [])
        location_score, location_details = self.calculate_location_preference_score(user_locations, job, profile)
        
        user_experience = profile.get('experience_level', 'mid')
        experience_score, experience_details = self.calculate_experience_level_score(user_experience, job, profile)
        
        company_score, company_details = self.calculate_company_preference_score(preferences, job, profile)
        
        user_goals = profile.get('career_goals', [])
        growth_score, growth_details = self.calculate_career_growth_potential_score(user_goals, job, profile)
        
        # Calculate weighted overall score using enhanced weights
        overall_score = (
            skill_score * self.weights['skill_match'] +
            location_score * self.weights['location_preference'] +
            experience_score * self.weights['experience_level'] +
            company_score * self.weights['company_preference'] +
            growth_score * self.weights['career_growth']
        )
        
        # Generate explainable recommendations
        explanation = self._generate_explanation(
            skill_details, location_details, experience_details, 
            company_details, growth_details, overall_score
        )
        
        # Generate action items
        action_items = self._generate_action_items(
            skill_details, experience_details, growth_details, profile
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence_score(
            skill_details, location_details, experience_details
        )
        
        recommendation_result = {
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
                    'contribution': round(skill_score * self.weights['skill_match'], 3)
                },
                'location_preference': {
                    'score': location_details['score'],
                    'weight': self.weights['location_preference'],
                    'contribution': round(location_score * self.weights['location_preference'], 3)
                },
                'experience_level': {
                    'score': experience_details['score'],
                    'weight': self.weights['experience_level'],
                    'contribution': round(experience_score * self.weights['experience_level'], 3)
                },
                'company_preference': {
                    'score': company_details['score'],
                    'weight': self.weights['company_preference'],
                    'contribution': round(company_score * self.weights['company_preference'], 3)
                },
                'career_growth': {
                    'score': growth_details['score'],
                    'weight': self.weights['career_growth'],
                    'contribution': round(growth_score * self.weights['career_growth'], 3)
                }
            },
            'detailed_analysis': {
                'skills': skill_details,
                'location': location_details,
                'experience': experience_details,
                'company': company_details,
                'growth': growth_details
            },
            'explanation': explanation,
            'action_items': action_items,
            'recommendation_metadata': {
                'algorithm_version': '2.0',
                'generated_at': datetime.now().isoformat(),
                'factors_considered': len([d for d in [skill_details, location_details, experience_details, company_details, growth_details] if d['score'] > 0])
            }
        }
        
        # Cache the recommendation result
        job_recommendation_cache.set_recommendation_scores(user_id, job.id, recommendation_result)
        logger.debug(f"Recommendation cached for user {user_id}, job {job.id}")
        
        return recommendation_result
    
    def _generate_explanation(
        self, 
        skill_details: Dict, 
        location_details: Dict, 
        experience_details: Dict,
        company_details: Dict, 
        growth_details: Dict, 
        overall_score: float
    ) -> Dict[str, Any]:
        """Generate explainable recommendation reasoning"""
        
        # Collect all scoring factors
        factors = [
            ('Skills', skill_details['score'], skill_details['reason']),
            ('Location', location_details['score'], location_details['reason']),
            ('Experience', experience_details['score'], experience_details['reason']),
            ('Company', company_details['score'], company_details['reason']),
            ('Growth', growth_details['score'], growth_details['reason'])
        ]
        
        # Sort by score to identify strengths and weaknesses
        factors.sort(key=lambda x: x[1], reverse=True)
        
        # Generate summary
        score_percentage = int(overall_score * 100)
        if score_percentage >= 80:
            summary = f"Excellent match ({score_percentage}%) - Highly recommended"
        elif score_percentage >= 65:
            summary = f"Good match ({score_percentage}%) - Worth considering"
        elif score_percentage >= 50:
            summary = f"Moderate match ({score_percentage}%) - Some alignment"
        else:
            summary = f"Limited match ({score_percentage}%) - Consider with caution"
        
        # Top strengths (scores > 0.7)
        strengths = [f"{name}: {reason}" for name, score, reason in factors if score > 0.7]
        
        # Areas of concern (scores < 0.5)
        concerns = [f"{name}: {reason}" for name, score, reason in factors if score < 0.5]
        
        # Key insights
        insights = []
        
        # Skill-specific insights
        if skill_details.get('missing_skills'):
            missing_count = len(skill_details['missing_skills'])
            insights.append(f"Missing {missing_count} key skills - consider upskilling")
        
        if skill_details.get('semantic_matches'):
            semantic_count = len(skill_details['semantic_matches'])
            insights.append(f"Found {semantic_count} related skill matches")
        
        # Experience insights
        if experience_details.get('is_growth_opportunity'):
            insights.append("Represents a career growth opportunity")
        
        # Location insights
        if location_details.get('remote_compatibility'):
            insights.append("Offers remote work flexibility")
        
        return {
            'summary': summary,
            'overall_score_percentage': score_percentage,
            'strengths': strengths[:3],  # Top 3 strengths
            'concerns': concerns[:2],    # Top 2 concerns
            'key_insights': insights,
            'detailed_factors': {
                factor_name.lower(): {'score': score, 'reason': reason}
                for factor_name, score, reason in factors
            }
        }
    
    def _generate_action_items(
        self, 
        skill_details: Dict, 
        experience_details: Dict, 
        growth_details: Dict,
        user_profile: Dict
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations for the user"""
        action_items = []
        
        # Skill-based actions
        missing_skills = skill_details.get('missing_skills', [])
        if missing_skills:
            priority_skills = missing_skills[:3]  # Top 3 missing skills
            action_items.append({
                'category': 'skill_development',
                'priority': 'high',
                'action': f"Develop skills: {', '.join(priority_skills)}",
                'description': 'Focus on these skills to improve your match for similar roles'
            })
        
        # Experience-based actions
        if experience_details.get('match_type') == 'stretch':
            action_items.append({
                'category': 'experience',
                'priority': 'medium',
                'action': 'Highlight transferable experience',
                'description': 'Emphasize relevant projects and achievements that demonstrate readiness'
            })
        
        # Growth-based actions
        if growth_details.get('aligned_goals'):
            action_items.append({
                'category': 'application',
                'priority': 'high',
                'action': 'Emphasize career alignment',
                'description': 'Highlight how this role aligns with your career goals in your application'
            })
        
        # Application strategy
        overall_skill_score = skill_details.get('score', 0)
        if overall_skill_score > 0.8:
            action_items.append({
                'category': 'application',
                'priority': 'high',
                'action': 'Apply with confidence',
                'description': 'Strong skill match - prioritize this application'
            })
        elif overall_skill_score > 0.6:
            action_items.append({
                'category': 'application',
                'priority': 'medium',
                'action': 'Tailor your application',
                'description': 'Customize resume and cover letter to highlight matching skills'
            })
        
        return action_items[:4]  # Limit to 4 most important actions
    
    def _calculate_confidence_score(
        self, 
        skill_details: Dict, 
        location_details: Dict, 
        experience_details: Dict
    ) -> float:
        """Calculate confidence in the recommendation"""
        
        # Base confidence on data completeness and score reliability
        confidence_factors = []
        
        # Skill matching confidence
        if skill_details.get('matching_skills'):
            confidence_factors.append(0.9)  # High confidence with exact matches
        elif skill_details.get('semantic_matches'):
            confidence_factors.append(0.7)  # Medium confidence with semantic matches
        else:
            confidence_factors.append(0.4)  # Low confidence without clear matches
        
        # Location confidence
        if location_details.get('match_type') in ['exact', 'remote_perfect']:
            confidence_factors.append(0.9)
        elif location_details.get('match_type') in ['regional', 'hybrid_good']:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Experience confidence
        if experience_details.get('match_type') == 'perfect':
            confidence_factors.append(0.9)
        elif experience_details.get('match_type') in ['growth', 'overqualified_slight']:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
        
        # Calculate weighted average
        return sum(confidence_factors) / len(confidence_factors)
    
    def generate_recommendations_for_user(
        self, 
        db: Session, 
        user_id: int,
        limit: int = 20,
        min_score: float = 0.5,
        diversify: bool = True
    ) -> List[Dict]:
        """Generate enhanced recommendations for all available jobs with diversification (cached)"""
        # Check cache first
        cached_recommendations = job_recommendation_cache.get_recommendations(user_id)
        if cached_recommendations:
            logger.debug(f"Recommendations cache hit for user {user_id}")
            recommendations = cached_recommendations.get('recommendations', [])
            # Filter and limit based on current parameters
            filtered_recs = [r for r in recommendations if r.get('overall_score', 0) >= min_score]
            return filtered_recs[:limit]
        
        # Get jobs that haven't been applied to
        from app.models.application import JobApplication
        
        applied_job_ids = db.query(JobApplication.job_id).filter(
            JobApplication.user_id == user_id
        ).all()
        applied_ids = [job_id for (job_id,) in applied_job_ids]
        
        # Get active jobs
        jobs = db.query(Job).filter(
            Job.user_id == user_id,
            Job.status == 'not_applied',
            ~Job.id.in_(applied_ids) if applied_ids else True
        ).all()
        
        if not jobs:
            return []
        
        # Generate recommendations with enhanced algorithm
        recommendations = []
        for job in jobs:
            rec = self.generate_recommendation(db, user_id, job)
            if rec and rec.get('overall_score', 0) >= min_score:
                recommendations.append(rec)
        
        if not recommendations:
            return []
        
        # Sort by combined score (overall_score + confidence)
        for rec in recommendations:
            rec['combined_score'] = (rec['overall_score'] * 0.8) + (rec.get('confidence', 0.5) * 0.2)
        
        recommendations.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Apply diversification if requested
        if diversify and len(recommendations) > limit:
            recommendations = self._diversify_recommendations(recommendations, limit)
        
        # Add ranking information
        for i, rec in enumerate(recommendations[:limit]):
            rec['rank'] = i + 1
            rec['percentile'] = round((1 - i / len(recommendations)) * 100, 1)
        
        # Cache the full recommendations list
        job_recommendation_cache.set_recommendations(user_id, recommendations)
        logger.debug(f"Recommendations cached for user {user_id}")
        
        return recommendations[:limit]
    
    def _diversify_recommendations(self, recommendations: List[Dict], limit: int) -> List[Dict]:
        """Diversify recommendations to avoid too many similar jobs"""
        if len(recommendations) <= limit:
            return recommendations
        
        diversified = []
        used_companies = set()
        used_titles = set()
        
        # First pass: take top recommendations with diversity constraints
        for rec in recommendations:
            if len(diversified) >= limit:
                break
            
            company = rec.get('company', '').lower()
            title_words = set(rec.get('job_title', '').lower().split())
            
            # Check for diversity
            company_diversity = company not in used_companies
            title_diversity = not any(
                len(title_words.intersection(set(used_title.split()))) > 1 
                for used_title in used_titles
            )
            
            # Add if diverse or if we need to fill remaining slots
            if (company_diversity and title_diversity) or len(diversified) < limit // 2:
                diversified.append(rec)
                used_companies.add(company)
                used_titles.add(rec.get('job_title', '').lower())
        
        # Second pass: fill remaining slots with best remaining recommendations
        remaining_slots = limit - len(diversified)
        if remaining_slots > 0:
            remaining_recs = [r for r in recommendations if r not in diversified]
            diversified.extend(remaining_recs[:remaining_slots])
        
        return diversified
    
    def get_recommendation_insights(
        self, 
        db: Session, 
        user_id: int
    ) -> Dict[str, Any]:
        """Get insights about user's recommendation patterns and suggestions for improvement"""
        recommendations = self.generate_recommendations_for_user(db, user_id, limit=50, min_score=0.0)
        
        if not recommendations:
            return {
                'total_jobs_analyzed': 0,
                'insights': ['No jobs available for analysis'],
                'suggestions': ['Add more jobs to your tracker for better recommendations']
            }
        
        # Analyze recommendation patterns
        scores = [r['overall_score'] for r in recommendations]
        skill_scores = [r['score_breakdown']['skill_match']['score'] for r in recommendations]
        location_scores = [r['score_breakdown']['location_preference']['score'] for r in recommendations]
        
        insights = []
        suggestions = []
        
        # Overall match quality
        avg_score = sum(scores) / len(scores)
        high_quality_count = len([s for s in scores if s >= 0.7])
        
        if avg_score < 0.5:
            insights.append(f"Average match quality is low ({int(avg_score*100)}%)")
            suggestions.append("Consider updating your profile with more specific skills and preferences")
        elif high_quality_count < len(scores) * 0.2:
            insights.append(f"Only {high_quality_count} high-quality matches found")
            suggestions.append("Expand your job search criteria or develop in-demand skills")
        
        # Skill analysis
        avg_skill_score = sum(skill_scores) / len(skill_scores)
        if avg_skill_score < 0.6:
            insights.append("Skill matching is the primary limiting factor")
            suggestions.append("Focus on developing skills that appear frequently in job requirements")
        
        # Location analysis
        avg_location_score = sum(location_scores) / len(location_scores)
        if avg_location_score < 0.5:
            insights.append("Location preferences may be limiting opportunities")
            suggestions.append("Consider remote work options or expanding location preferences")
        
        # Top missing skills across all jobs
        all_missing_skills = []
        for rec in recommendations:
            missing = rec.get('detailed_analysis', {}).get('skills', {}).get('missing_skills', [])
            all_missing_skills.extend(missing)
        
        if all_missing_skills:
            from collections import Counter
            skill_frequency = Counter(all_missing_skills)
            top_missing = skill_frequency.most_common(5)
            
            insights.append(f"Most frequently missing skills: {', '.join([skill for skill, _ in top_missing[:3]])}")
            suggestions.append(f"Consider learning: {', '.join([skill for skill, _ in top_missing[:2]])}")
        
        return {
            'total_jobs_analyzed': len(recommendations),
            'average_match_score': round(avg_score, 3),
            'high_quality_matches': high_quality_count,
            'insights': insights,
            'suggestions': suggestions,
            'score_distribution': {
                'excellent': len([s for s in scores if s >= 0.8]),
                'good': len([s for s in scores if 0.65 <= s < 0.8]),
                'moderate': len([s for s in scores if 0.5 <= s < 0.65]),
                'poor': len([s for s in scores if s < 0.5])
            }
        }


recommendation_service = RecommendationService()