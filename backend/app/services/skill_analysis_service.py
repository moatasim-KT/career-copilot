"""
Enhanced skill gap analysis engine with Redis caching
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.user import User
from app.models.job import Job
from app.models.analytics import Analytics
from app.core.cache import analytics_cache, cached, cache_invalidate

logger = logging.getLogger(__name__)


class SkillAnalysisService:
    """Enhanced service for analyzing skill gaps and market demand"""
    
    def __init__(self):
        # Comprehensive skill database organized by categories
        self.skill_categories = {
            'programming_languages': {
                'python', 'javascript', 'java', 'typescript', 'c++', 'c#', 'go', 'rust',
                'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl'
            },
            'web_technologies': {
                'react', 'angular', 'vue.js', 'node.js', 'express', 'django', 'flask',
                'spring', 'laravel', 'rails', 'html', 'css', 'sass', 'less', 'webpack',
                'babel', 'jquery', 'bootstrap', 'tailwind'
            },
            'databases': {
                'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                'cassandra', 'dynamodb', 'sqlite', 'oracle', 'mariadb', 'neo4j'
            },
            'cloud_platforms': {
                'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean',
                'linode', 'cloudflare', 's3', 'ec2', 'lambda', 'kubernetes', 'docker'
            },
            'devops_tools': {
                'docker', 'kubernetes', 'jenkins', 'gitlab ci', 'github actions',
                'terraform', 'ansible', 'chef', 'puppet', 'vagrant', 'nginx', 'apache'
            },
            'data_science': {
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
                'jupyter', 'matplotlib', 'seaborn', 'plotly', 'spark', 'hadoop'
            },
            'mobile_development': {
                'react native', 'flutter', 'ios', 'android', 'swift', 'kotlin',
                'xamarin', 'cordova', 'ionic'
            },
            'methodologies': {
                'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'devops', 'ci/cd',
                'tdd', 'bdd', 'pair programming', 'code review'
            },
            'soft_skills': {
                'leadership', 'communication', 'teamwork', 'problem solving',
                'project management', 'mentoring', 'presentation', 'negotiation'
            }
        }
        
        # Flatten all skills for easy lookup
        self.all_skills = set()
        for category_skills in self.skill_categories.values():
            self.all_skills.update(category_skills)
        
        # Skill synonyms and variations
        self.skill_synonyms = {
            'js': 'javascript',
            'ts': 'typescript',
            'k8s': 'kubernetes',
            'postgres': 'postgresql',
            'mongo': 'mongodb',
            'tf': 'tensorflow',
            'react.js': 'react',
            'vue': 'vue.js',
            'node': 'node.js'
        }
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Enhanced skill extraction from job description or requirements"""
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = set()
        
        # Extract skills using multiple methods
        
        # Method 1: Direct skill matching with word boundaries
        for skill in self.all_skills:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        
        # Method 2: Handle synonyms and variations
        for synonym, canonical in self.skill_synonyms.items():
            pattern = r'\b' + re.escape(synonym) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(canonical)
        
        # Method 3: Extract common patterns like "X years of Y experience"
        experience_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience\s*)?(?:with\s*)?([a-zA-Z\.\+\-]+)',
            r'experience\s*(?:with\s*)?([a-zA-Z\.\+\-]+)',
            r'proficient\s*(?:in\s*)?([a-zA-Z\.\+\-]+)',
            r'skilled\s*(?:in\s*)?([a-zA-Z\.\+\-]+)',
            r'knowledge\s*(?:of\s*)?([a-zA-Z\.\+\-]+)'
        ]
        
        for pattern in experience_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                # Get the skill part (last group if multiple groups exist)
                groups = match.groups()
                if groups:
                    skill_candidate = groups[-1].strip()
                    if skill_candidate in self.all_skills:
                        found_skills.add(skill_candidate)
                    elif skill_candidate in self.skill_synonyms:
                        found_skills.add(self.skill_synonyms[skill_candidate])
        
        return list(found_skills)
    
    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills by type for better analysis"""
        categorized = {category: [] for category in self.skill_categories.keys()}
        
        for skill in skills:
            for category, category_skills in self.skill_categories.items():
                if skill in category_skills:
                    categorized[category].append(skill)
                    break
        
        return categorized
    
    @cached(ttl=7200, key_prefix="market_demand")  # Cache for 2 hours
    def analyze_market_demand(self, db: Session, user_id: int, days: int = 30) -> Dict:
        """Enhanced market demand analysis for skills in recent job postings (cached)"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get user profile for targeted analysis
        user = db.query(User).filter(User.id == user_id).first()
        user_profile = user.profile if user else {}
        
        # Get recent jobs for the user and similar roles
        jobs_query = db.query(Job).filter(
            Job.user_id == user_id,
            Job.created_at >= cutoff_date
        )
        
        # If user has target roles, include jobs from those categories
        target_roles = user_profile.get('career_goals', [])
        if target_roles:
            # Also include jobs that match user's target roles from other users (anonymized)
            similar_jobs = db.query(Job).filter(
                Job.created_at >= cutoff_date,
                Job.title.ilike(f'%{target_roles[0]}%') if target_roles else True
            ).limit(100).all()  # Limit to prevent overwhelming analysis
            
            user_jobs = jobs_query.all()
            jobs = user_jobs + [job for job in similar_jobs if job.user_id != user_id]
        else:
            jobs = jobs_query.all()
        
        if not jobs:
            return {'error': 'No recent jobs found for analysis'}
        
        # Extract skills from all job descriptions with enhanced processing
        all_skills = []
        job_skill_matrix = {}  # Track which jobs require which skills
        
        for job in jobs:
            job_skills = set()
            
            # Extract from description
            if job.description:
                desc_skills = self.extract_skills_from_text(job.description)
                job_skills.update(desc_skills)
                all_skills.extend(desc_skills)
            
            # Extract from requirements
            if job.requirements and isinstance(job.requirements, dict):
                skills_req = job.requirements.get('skills_required', [])
                if isinstance(skills_req, list):
                    normalized_skills = [skill.lower() for skill in skills_req]
                    job_skills.update(normalized_skills)
                    all_skills.extend(normalized_skills)
            
            job_skill_matrix[job.id] = list(job_skills)
        
        # Count skill frequency and calculate advanced metrics
        skill_counts = Counter(all_skills)
        total_jobs = len(jobs)
        
        # Calculate demand percentages and trends
        market_demand = []
        for skill, count in skill_counts.most_common(50):  # Analyze top 50 skills
            percentage = round((count / total_jobs) * 100, 1)
            
            # Calculate skill importance score (frequency + co-occurrence with high-demand skills)
            importance_score = self._calculate_skill_importance(skill, job_skill_matrix, skill_counts)
            
            market_demand.append({
                'skill': skill,
                'frequency': count,
                'percentage': percentage,
                'importance_score': importance_score,
                'demand_level': self._categorize_demand_level(percentage),
                'category': self._get_skill_category(skill)
            })
        
        # Sort by importance score for better prioritization
        market_demand.sort(key=lambda x: x['importance_score'], reverse=True)
        
        # Categorize skills by type
        categorized_demand = self._categorize_market_demand(market_demand)
        
        return {
            'total_jobs_analyzed': total_jobs,
            'analysis_period_days': days,
            'user_jobs_count': len([j for j in jobs if j.user_id == user_id]),
            'market_jobs_count': len([j for j in jobs if j.user_id != user_id]),
            'top_skills': market_demand[:10],
            'all_skills': market_demand,
            'skills_by_category': categorized_demand,
            'market_insights': self._generate_market_insights(market_demand, total_jobs)
        }
    
    def _calculate_skill_importance(self, skill: str, job_skill_matrix: Dict, skill_counts: Counter) -> float:
        """Calculate importance score based on frequency and co-occurrence patterns"""
        base_score = skill_counts[skill]
        
        # Bonus for skills that frequently appear together with other high-demand skills
        co_occurrence_bonus = 0
        jobs_with_skill = [job_id for job_id, skills in job_skill_matrix.items() if skill in skills]
        
        for job_id in jobs_with_skill:
            job_skills = job_skill_matrix[job_id]
            for other_skill in job_skills:
                if other_skill != skill and skill_counts[other_skill] > 5:
                    co_occurrence_bonus += 0.1
        
        return round(base_score + co_occurrence_bonus, 2)
    
    def _categorize_demand_level(self, percentage: float) -> str:
        """Categorize demand level based on percentage"""
        if percentage >= 70:
            return 'critical'
        elif percentage >= 50:
            return 'high'
        elif percentage >= 25:
            return 'medium'
        elif percentage >= 10:
            return 'low'
        else:
            return 'minimal'
    
    def _get_skill_category(self, skill: str) -> str:
        """Get the category of a skill"""
        for category, skills in self.skill_categories.items():
            if skill in skills:
                return category
        return 'other'
    
    def _categorize_market_demand(self, market_demand: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize market demand by skill type"""
        categorized = {}
        
        for skill_data in market_demand:
            category = skill_data['category']
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(skill_data)
        
        return categorized
    
    def _generate_market_insights(self, market_demand: List[Dict], total_jobs: int) -> List[str]:
        """Generate insights about the job market"""
        insights = []
        
        if not market_demand:
            return insights
        
        # Top skill insight
        top_skill = market_demand[0]
        insights.append(f"Most in-demand skill: {top_skill['skill']} (required in {top_skill['percentage']}% of jobs)")
        
        # Critical skills count
        critical_skills = [s for s in market_demand if s['demand_level'] == 'critical']
        if critical_skills:
            insights.append(f"{len(critical_skills)} skills are critical (required in 70%+ of jobs)")
        
        # Category analysis
        category_counts = {}
        for skill_data in market_demand[:20]:  # Top 20 skills
            category = skill_data['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        if category_counts:
            top_category = max(category_counts, key=category_counts.get)
            insights.append(f"Most demanded skill category: {top_category.replace('_', ' ').title()}")
        
        # Market competitiveness
        high_demand_skills = [s for s in market_demand if s['demand_level'] in ['critical', 'high']]
        if len(high_demand_skills) > 10:
            insights.append("Highly competitive market - many skills in high demand")
        elif len(high_demand_skills) < 5:
            insights.append("Specialized market - focus on key skills for better results")
        
        return insights
    
    def analyze_skill_gap(self, db: Session, user_id: int) -> Dict:
        """Enhanced skill gap analysis comparing user skills against market demand (cached)"""
        # Check cache first
        cached_analysis = analytics_cache.get_skill_analysis(user_id)
        if cached_analysis:
            logger.debug(f"Skill analysis cache hit for user {user_id}")
            return cached_analysis
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {'error': 'User not found'}
        
        # Get user skills from profile with normalization
        user_skills = set()
        if user.profile and 'skills' in user.profile:
            raw_skills = user.profile['skills']
            for skill in raw_skills:
                normalized_skill = skill.lower().strip()
                # Handle synonyms
                if normalized_skill in self.skill_synonyms:
                    normalized_skill = self.skill_synonyms[normalized_skill]
                user_skills.add(normalized_skill)
        
        # Get enhanced market demand analysis
        market_data = self.analyze_market_demand(db, user_id, days=60)  # Extended period for better analysis
        if 'error' in market_data:
            return market_data
        
        # Analyze skill gaps with enhanced categorization
        missing_skills = []
        matching_skills = []
        partial_matches = []
        
        # Get user's experience level and preferences for better recommendations
        user_profile = user.profile or {}
        experience_level = user_profile.get('experience_level', 'mid')
        career_goals = user_profile.get('career_goals', [])
        
        for skill_data in market_data['all_skills']:
            skill = skill_data['skill']
            
            if skill in user_skills:
                matching_skills.append({
                    **skill_data,
                    'proficiency_level': self._estimate_proficiency_level(skill, user_profile),
                    'market_advantage': self._calculate_market_advantage(skill_data)
                })
            else:
                # Check for partial matches (related skills)
                related_skills = self._find_related_skills(skill, user_skills)
                
                if related_skills:
                    partial_matches.append({
                        **skill_data,
                        'related_user_skills': related_skills,
                        'learning_difficulty': self._estimate_learning_difficulty(skill, related_skills, experience_level),
                        'priority': self._calculate_skill_priority(skill_data, career_goals, experience_level),
                        'learning_resources': self.get_enhanced_learning_resources(skill, experience_level, related_skills)
                    })
                else:
                    missing_skills.append({
                        **skill_data,
                        'learning_difficulty': self._estimate_learning_difficulty(skill, [], experience_level),
                        'priority': self._calculate_skill_priority(skill_data, career_goals, experience_level),
                        'learning_resources': self.get_enhanced_learning_resources(skill, experience_level, [])
                    })
        
        # Calculate comprehensive match metrics
        total_market_demand = sum(skill['importance_score'] for skill in market_data['all_skills'][:20])
        matched_demand = sum(skill['importance_score'] for skill in matching_skills)
        partial_demand = sum(skill['importance_score'] for skill in partial_matches) * 0.5  # Partial credit
        
        match_percentage = round(((matched_demand + partial_demand) / total_market_demand) * 100, 1) if total_market_demand > 0 else 0
        
        # Generate skill development roadmap
        skill_roadmap = self._generate_skill_roadmap(missing_skills, partial_matches, experience_level, career_goals)
        
        # Calculate competitive analysis
        competitive_analysis = self._analyze_competitive_position(matching_skills, missing_skills, market_data)
        
        analysis_result = {
            'analysis_date': datetime.now().isoformat(),
            'user_skills_count': len(user_skills),
            'market_skills_analyzed': len(market_data['all_skills']),
            'match_percentage': match_percentage,
            'skill_strength_score': self._calculate_skill_strength_score(matching_skills, market_data),
            'matching_skills': matching_skills,
            'partial_matches': partial_matches[:5],
            'missing_skills': missing_skills[:10],
            'top_priority_skills': sorted(missing_skills + partial_matches, key=lambda x: x.get('priority_score', 0), reverse=True)[:5],
            'skill_roadmap': skill_roadmap,
            'competitive_analysis': competitive_analysis,
            'recommendations': self.generate_enhanced_skill_recommendations(missing_skills, partial_matches, matching_skills, experience_level),
            'market_insights': market_data.get('market_insights', [])
        }
        
        # Cache the analysis result
        analytics_cache.set_skill_analysis(user_id, analysis_result)
        logger.debug(f"Skill analysis cached for user {user_id}")
        
        return analysis_result
    
    def _estimate_proficiency_level(self, skill: str, user_profile: Dict) -> str:
        """Estimate user's proficiency level in a skill"""
        # This could be enhanced with actual proficiency data from user profile
        experience_level = user_profile.get('experience_level', 'mid')
        
        # Simple heuristic based on experience level
        if experience_level == 'senior':
            return 'advanced'
        elif experience_level == 'mid':
            return 'intermediate'
        else:
            return 'beginner'
    
    def _calculate_market_advantage(self, skill_data: Dict) -> str:
        """Calculate the market advantage of having this skill"""
        percentage = skill_data.get('percentage', 0)
        demand_level = skill_data.get('demand_level', 'low')
        
        if demand_level == 'critical':
            return 'essential'
        elif demand_level == 'high':
            return 'strong_advantage'
        elif demand_level == 'medium':
            return 'moderate_advantage'
        else:
            return 'niche_advantage'
    
    def _find_related_skills(self, target_skill: str, user_skills: Set[str]) -> List[str]:
        """Find user skills that are related to the target skill"""
        related = []
        
        # Get the category of the target skill
        target_category = self._get_skill_category(target_skill)
        
        # Find user skills in the same category
        for user_skill in user_skills:
            if self._get_skill_category(user_skill) == target_category:
                related.append(user_skill)
        
        # Add specific relationships
        skill_relationships = {
            'react': ['javascript', 'html', 'css'],
            'angular': ['javascript', 'typescript', 'html', 'css'],
            'vue.js': ['javascript', 'html', 'css'],
            'django': ['python'],
            'flask': ['python'],
            'spring': ['java'],
            'express': ['node.js', 'javascript'],
            'postgresql': ['sql'],
            'mysql': ['sql'],
            'mongodb': ['javascript'],
            'kubernetes': ['docker'],
            'terraform': ['aws', 'azure', 'gcp']
        }
        
        if target_skill in skill_relationships:
            for prereq in skill_relationships[target_skill]:
                if prereq in user_skills and prereq not in related:
                    related.append(prereq)
        
        return related
    
    def _estimate_learning_difficulty(self, skill: str, related_skills: List[str], experience_level: str) -> str:
        """Estimate the difficulty of learning a new skill"""
        base_difficulty = {
            'programming_languages': 'medium',
            'web_technologies': 'easy',
            'databases': 'medium',
            'cloud_platforms': 'hard',
            'devops_tools': 'hard',
            'data_science': 'hard',
            'mobile_development': 'medium',
            'methodologies': 'easy',
            'soft_skills': 'medium'
        }
        
        category = self._get_skill_category(skill)
        difficulty = base_difficulty.get(category, 'medium')
        
        # Adjust based on related skills
        if len(related_skills) >= 2:
            if difficulty == 'hard':
                difficulty = 'medium'
            elif difficulty == 'medium':
                difficulty = 'easy'
        
        # Adjust based on experience level
        if experience_level == 'senior':
            if difficulty == 'hard':
                difficulty = 'medium'
            elif difficulty == 'medium':
                difficulty = 'easy'
        elif experience_level == 'junior':
            if difficulty == 'easy':
                difficulty = 'medium'
            elif difficulty == 'medium':
                difficulty = 'hard'
        
        return difficulty
    
    def _calculate_skill_priority(self, skill_data: Dict, career_goals: List[str], experience_level: str) -> str:
        """Calculate priority for learning a skill"""
        # Base priority on market demand
        demand_level = skill_data.get('demand_level', 'low')
        percentage = skill_data.get('percentage', 0)
        importance_score = skill_data.get('importance_score', 0)
        
        # Calculate priority score
        priority_score = 0
        
        # Market demand weight (40%)
        if demand_level == 'critical':
            priority_score += 40
        elif demand_level == 'high':
            priority_score += 30
        elif demand_level == 'medium':
            priority_score += 20
        else:
            priority_score += 10
        
        # Career goal alignment weight (30%)
        skill = skill_data.get('skill', '')
        for goal in career_goals:
            if goal.lower() in skill or skill in goal.lower():
                priority_score += 30
                break
        
        # Importance score weight (20%)
        priority_score += min(importance_score * 2, 20)
        
        # Experience level adjustment (10%)
        if experience_level == 'senior' and demand_level in ['critical', 'high']:
            priority_score += 10
        elif experience_level == 'junior' and demand_level in ['medium', 'low']:
            priority_score += 10
        
        # Store the numeric score for sorting
        skill_data['priority_score'] = priority_score
        
        # Convert to categorical priority
        if priority_score >= 80:
            return 'critical'
        elif priority_score >= 60:
            return 'high'
        elif priority_score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def _generate_skill_roadmap(self, missing_skills: List[Dict], partial_matches: List[Dict], 
                               experience_level: str, career_goals: List[str]) -> Dict:
        """Generate a structured skill development roadmap"""
        roadmap = {
            'immediate_focus': [],  # Next 1-3 months
            'short_term': [],       # 3-6 months
            'medium_term': [],      # 6-12 months
            'long_term': []         # 12+ months
        }
        
        all_skills = missing_skills + partial_matches
        
        # Sort by priority and learning difficulty
        prioritized_skills = sorted(all_skills, key=lambda x: (
            x.get('priority_score', 0),
            -{'easy': 3, 'medium': 2, 'hard': 1}.get(x.get('learning_difficulty', 'medium'), 2)
        ), reverse=True)
        
        # Distribute skills across timeline
        for i, skill in enumerate(prioritized_skills[:12]):  # Limit to top 12 skills
            difficulty = skill.get('learning_difficulty', 'medium')
            priority = skill.get('priority', 'low')
            
            if i < 2 and priority in ['critical', 'high'] and difficulty == 'easy':
                roadmap['immediate_focus'].append(skill)
            elif i < 4 and priority in ['critical', 'high']:
                roadmap['short_term'].append(skill)
            elif i < 8 and priority in ['high', 'medium']:
                roadmap['medium_term'].append(skill)
            else:
                roadmap['long_term'].append(skill)
        
        return roadmap
    
    def _analyze_competitive_position(self, matching_skills: List[Dict], missing_skills: List[Dict], 
                                    market_data: Dict) -> Dict:
        """Analyze user's competitive position in the market"""
        total_skills_analyzed = len(market_data.get('all_skills', []))
        critical_skills = [s for s in market_data.get('all_skills', []) if s.get('demand_level') == 'critical']
        
        user_critical_skills = [s for s in matching_skills if s.get('demand_level') == 'critical']
        missing_critical_skills = [s for s in missing_skills if s.get('demand_level') == 'critical']
        
        competitive_score = 0
        if critical_skills:
            competitive_score = (len(user_critical_skills) / len(critical_skills)) * 100
        
        return {
            'competitive_score': round(competitive_score, 1),
            'critical_skills_coverage': f"{len(user_critical_skills)}/{len(critical_skills)}",
            'missing_critical_skills': len(missing_critical_skills),
            'market_position': self._determine_market_position(competitive_score),
            'improvement_potential': round(100 - competitive_score, 1) if competitive_score < 100 else 0
        }
    
    def _determine_market_position(self, competitive_score: float) -> str:
        """Determine market position based on competitive score"""
        if competitive_score >= 90:
            return 'market_leader'
        elif competitive_score >= 75:
            return 'strong_candidate'
        elif competitive_score >= 50:
            return 'competitive'
        elif competitive_score >= 25:
            return 'developing'
        else:
            return 'entry_level'
    
    def _calculate_skill_strength_score(self, matching_skills: List[Dict], market_data: Dict) -> float:
        """Calculate overall skill strength score"""
        if not matching_skills:
            return 0.0
        
        total_importance = sum(skill.get('importance_score', 0) for skill in matching_skills)
        max_possible_importance = sum(skill.get('importance_score', 0) for skill in market_data.get('all_skills', [])[:len(matching_skills)])
        
        if max_possible_importance == 0:
            return 0.0
        
        return round((total_importance / max_possible_importance) * 100, 1)
    
    def get_enhanced_learning_resources(self, skill: str, experience_level: str, related_skills: List[str]) -> List[Dict]:
        """Get comprehensive learning resources tailored to user's experience and background"""
        
        # Comprehensive resource database
        resources_map = {
            # Programming Languages
            'python': {
                'beginner': [
                    {'type': 'course', 'name': 'Python.org Tutorial', 'url': 'https://docs.python.org/3/tutorial/', 'duration': '2-3 weeks'},
                    {'type': 'course', 'name': 'Codecademy Python', 'url': 'https://www.codecademy.com/learn/learn-python-3', 'duration': '4-6 weeks'},
                    {'type': 'book', 'name': 'Automate the Boring Stuff with Python', 'url': 'https://automatetheboringstuff.com/', 'duration': '6-8 weeks'}
                ],
                'intermediate': [
                    {'type': 'course', 'name': 'Real Python Tutorials', 'url': 'https://realpython.com/', 'duration': '4-6 weeks'},
                    {'type': 'practice', 'name': 'LeetCode Python', 'url': 'https://leetcode.com/', 'duration': 'ongoing'},
                    {'type': 'project', 'name': 'Build a Web Scraper', 'url': 'https://realpython.com/web-scraping-python/', 'duration': '1-2 weeks'}
                ],
                'advanced': [
                    {'type': 'course', 'name': 'Advanced Python Features', 'url': 'https://realpython.com/python-advanced-features/', 'duration': '3-4 weeks'},
                    {'type': 'book', 'name': 'Effective Python', 'url': 'https://effectivepython.com/', 'duration': '4-6 weeks'},
                    {'type': 'practice', 'name': 'Python Design Patterns', 'url': 'https://python-patterns.guide/', 'duration': '2-3 weeks'}
                ]
            },
            'javascript': {
                'beginner': [
                    {'type': 'course', 'name': 'MDN JavaScript Guide', 'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide', 'duration': '3-4 weeks'},
                    {'type': 'course', 'name': 'freeCodeCamp JavaScript', 'url': 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/', 'duration': '6-8 weeks'},
                    {'type': 'practice', 'name': 'JavaScript30', 'url': 'https://javascript30.com/', 'duration': '4-5 weeks'}
                ],
                'intermediate': [
                    {'type': 'course', 'name': 'You Don\'t Know JS', 'url': 'https://github.com/getify/You-Dont-Know-JS', 'duration': '4-6 weeks'},
                    {'type': 'practice', 'name': 'Codewars JavaScript', 'url': 'https://www.codewars.com/', 'duration': 'ongoing'},
                    {'type': 'project', 'name': 'Build a REST API', 'url': 'https://nodejs.org/en/docs/guides/', 'duration': '2-3 weeks'}
                ],
                'advanced': [
                    {'type': 'course', 'name': 'Advanced JavaScript Concepts', 'url': 'https://javascript.info/', 'duration': '3-4 weeks'},
                    {'type': 'book', 'name': 'JavaScript: The Good Parts', 'url': 'https://www.oreilly.com/library/view/javascript-the-good/9780596517748/', 'duration': '3-4 weeks'},
                    {'type': 'practice', 'name': 'Advanced Algorithm Challenges', 'url': 'https://leetcode.com/', 'duration': 'ongoing'}
                ]
            },
            'react': {
                'beginner': [
                    {'type': 'course', 'name': 'React Official Tutorial', 'url': 'https://react.dev/learn', 'duration': '2-3 weeks'},
                    {'type': 'course', 'name': 'React for Beginners', 'url': 'https://reactforbeginners.com/', 'duration': '4-5 weeks'},
                    {'type': 'project', 'name': 'Build a Todo App', 'url': 'https://react.dev/learn/tutorial-tic-tac-toe', 'duration': '1 week'}
                ],
                'intermediate': [
                    {'type': 'course', 'name': 'React Hooks Deep Dive', 'url': 'https://react.dev/reference/react', 'duration': '2-3 weeks'},
                    {'type': 'practice', 'name': 'React Challenges', 'url': 'https://github.com/alexgurr/react-coding-challenges', 'duration': '3-4 weeks'},
                    {'type': 'project', 'name': 'Build an E-commerce App', 'url': 'https://react.dev/learn', 'duration': '4-6 weeks'}
                ],
                'advanced': [
                    {'type': 'course', 'name': 'React Performance Optimization', 'url': 'https://react.dev/learn/render-and-commit', 'duration': '2-3 weeks'},
                    {'type': 'course', 'name': 'React Testing Library', 'url': 'https://testing-library.com/docs/react-testing-library/intro/', 'duration': '2-3 weeks'},
                    {'type': 'project', 'name': 'Build a Complex SPA', 'url': 'https://react.dev/learn', 'duration': '6-8 weeks'}
                ]
            },
            'docker': {
                'beginner': [
                    {'type': 'course', 'name': 'Docker Official Tutorial', 'url': 'https://docs.docker.com/get-started/', 'duration': '1-2 weeks'},
                    {'type': 'course', 'name': 'Docker for Beginners', 'url': 'https://docker-curriculum.com/', 'duration': '2-3 weeks'},
                    {'type': 'practice', 'name': 'Play with Docker', 'url': 'https://labs.play-with-docker.com/', 'duration': '1 week'}
                ],
                'intermediate': [
                    {'type': 'course', 'name': 'Docker Compose Deep Dive', 'url': 'https://docs.docker.com/compose/', 'duration': '2-3 weeks'},
                    {'type': 'project', 'name': 'Containerize a Web App', 'url': 'https://docs.docker.com/get-started/02_our_app/', 'duration': '1-2 weeks'},
                    {'type': 'practice', 'name': 'Docker Best Practices', 'url': 'https://docs.docker.com/develop/dev-best-practices/', 'duration': '1-2 weeks'}
                ],
                'advanced': [
                    {'type': 'course', 'name': 'Docker Security', 'url': 'https://docs.docker.com/engine/security/', 'duration': '2-3 weeks'},
                    {'type': 'course', 'name': 'Docker in Production', 'url': 'https://docs.docker.com/config/containers/logging/', 'duration': '3-4 weeks'},
                    {'type': 'certification', 'name': 'Docker Certified Associate', 'url': 'https://training.mirantis.com/dca-certification-exam/', 'duration': '6-8 weeks'}
                ]
            },
            'kubernetes': {
                'beginner': [
                    {'type': 'course', 'name': 'Kubernetes Basics', 'url': 'https://kubernetes.io/docs/tutorials/kubernetes-basics/', 'duration': '2-3 weeks'},
                    {'type': 'course', 'name': 'Introduction to Kubernetes', 'url': 'https://www.edx.org/course/introduction-to-kubernetes', 'duration': '4-6 weeks'},
                    {'type': 'practice', 'name': 'Katacoda Kubernetes', 'url': 'https://kubernetes.io/docs/tutorials/', 'duration': '2-3 weeks'}
                ],
                'intermediate': [
                    {'type': 'course', 'name': 'Kubernetes the Hard Way', 'url': 'https://github.com/kelseyhightower/kubernetes-the-hard-way', 'duration': '4-6 weeks'},
                    {'type': 'project', 'name': 'Deploy a Microservices App', 'url': 'https://kubernetes.io/docs/tutorials/stateless-application/', 'duration': '3-4 weeks'},
                    {'type': 'practice', 'name': 'Kubernetes Challenges', 'url': 'https://kodekloud.com/courses/kubernetes-challenges/', 'duration': '4-5 weeks'}
                ],
                'advanced': [
                    {'type': 'certification', 'name': 'CKA Certification', 'url': 'https://www.cncf.io/certification/cka/', 'duration': '8-12 weeks'},
                    {'type': 'course', 'name': 'Kubernetes Security', 'url': 'https://kubernetes.io/docs/concepts/security/', 'duration': '3-4 weeks'},
                    {'type': 'course', 'name': 'Kubernetes Operators', 'url': 'https://kubernetes.io/docs/concepts/extend-kubernetes/operator/', 'duration': '4-6 weeks'}
                ]
            },
            'aws': {
                'beginner': [
                    {'type': 'course', 'name': 'AWS Cloud Practitioner', 'url': 'https://aws.amazon.com/training/digital/aws-cloud-practitioner-essentials/', 'duration': '3-4 weeks'},
                    {'type': 'practice', 'name': 'AWS Free Tier', 'url': 'https://aws.amazon.com/free/', 'duration': '2-3 weeks'},
                    {'type': 'course', 'name': 'AWS Getting Started', 'url': 'https://aws.amazon.com/getting-started/', 'duration': '2-3 weeks'}
                ],
                'intermediate': [
                    {'type': 'certification', 'name': 'AWS Solutions Architect Associate', 'url': 'https://aws.amazon.com/certification/certified-solutions-architect-associate/', 'duration': '6-8 weeks'},
                    {'type': 'project', 'name': 'Build a Serverless App', 'url': 'https://aws.amazon.com/getting-started/hands-on/build-serverless-web-app-lambda-apigateway-s3-dynamodb-cognito/', 'duration': '2-3 weeks'},
                    {'type': 'course', 'name': 'AWS Well-Architected Framework', 'url': 'https://aws.amazon.com/architecture/well-architected/', 'duration': '2-3 weeks'}
                ],
                'advanced': [
                    {'type': 'certification', 'name': 'AWS Solutions Architect Professional', 'url': 'https://aws.amazon.com/certification/certified-solutions-architect-professional/', 'duration': '10-12 weeks'},
                    {'type': 'course', 'name': 'AWS Security Best Practices', 'url': 'https://aws.amazon.com/architecture/security-identity-compliance/', 'duration': '4-6 weeks'},
                    {'type': 'specialization', 'name': 'AWS DevOps Engineer', 'url': 'https://aws.amazon.com/certification/certified-devops-engineer-professional/', 'duration': '8-10 weeks'}
                ]
            }
        }
        
        # Determine appropriate experience level for resources
        resource_level = experience_level
        if related_skills:
            # If user has related skills, they can handle intermediate level
            if experience_level == 'beginner':
                resource_level = 'intermediate'
        
        # Get resources for the skill
        skill_resources = resources_map.get(skill, {})
        level_resources = skill_resources.get(resource_level, [])
        
        # If no resources for the specific level, fall back to beginner
        if not level_resources and resource_level != 'beginner':
            level_resources = skill_resources.get('beginner', [])
        
        # If still no specific resources, provide generic ones
        if not level_resources:
            level_resources = [
                {'type': 'course', 'name': f'{skill.title()} Official Documentation', 'url': f'https://www.google.com/search?q={skill}+official+documentation', 'duration': '2-4 weeks'},
                {'type': 'course', 'name': f'Learn {skill.title()}', 'url': f'https://www.google.com/search?q=learn+{skill}+tutorial', 'duration': '3-6 weeks'},
                {'type': 'practice', 'name': f'{skill.title()} Practice Problems', 'url': f'https://www.google.com/search?q={skill}+practice+problems', 'duration': 'ongoing'},
                {'type': 'community', 'name': f'{skill.title()} Community', 'url': f'https://www.reddit.com/search/?q={skill}', 'duration': 'ongoing'}
            ]
        
        # Add learning path recommendations based on related skills
        if related_skills:
            level_resources.append({
                'type': 'tip',
                'name': f'Leverage your {", ".join(related_skills)} experience',
                'url': '',
                'duration': '',
                'description': f'Since you know {", ".join(related_skills)}, focus on the differences and advanced features of {skill}'
            })
        
        return level_resources[:4]  # Limit to top 4 resources
    
    def generate_enhanced_skill_recommendations(self, missing_skills: List[Dict], partial_matches: List[Dict], 
                                              matching_skills: List[Dict], experience_level: str) -> List[str]:
        """Generate comprehensive and actionable skill development recommendations"""
        recommendations = []
        
        if not missing_skills and not partial_matches:
            recommendations.append("Excellent! You have strong skill alignment with current market demand.")
            if matching_skills:
                top_skill = max(matching_skills, key=lambda x: x.get('importance_score', 0))
                recommendations.append(f"Your strongest market skill is {top_skill['skill']} - consider becoming an expert in this area.")
            return recommendations
        
        # Priority recommendations
        all_gaps = missing_skills + partial_matches
        critical_gaps = [s for s in all_gaps if s.get('priority') == 'critical']
        high_priority_gaps = [s for s in all_gaps if s.get('priority') == 'high']
        
        if critical_gaps:
            top_critical = critical_gaps[0]
            recommendations.append(f"🎯 CRITICAL: Learn {top_critical['skill']} immediately - required in {top_critical.get('percentage', 0)}% of target jobs")
            
            # Add specific learning path
            difficulty = top_critical.get('learning_difficulty', 'medium')
            if difficulty == 'easy':
                recommendations.append(f"Good news: {top_critical['skill']} is relatively easy to learn and will give you quick wins")
            elif difficulty == 'hard':
                recommendations.append(f"Note: {top_critical['skill']} requires significant time investment - consider starting with fundamentals")
        
        # Quick wins recommendations
        easy_skills = [s for s in all_gaps if s.get('learning_difficulty') == 'easy' and s.get('priority') in ['high', 'medium']]
        if easy_skills:
            quick_wins = easy_skills[:2]
            skill_names = [s['skill'] for s in quick_wins]
            recommendations.append(f"🚀 Quick wins: Start with {', '.join(skill_names)} - easy to learn with high market impact")
        
        # Experience-based recommendations
        if experience_level == 'junior':
            foundational_skills = [s for s in all_gaps if s.get('category') in ['programming_languages', 'web_technologies']]
            if foundational_skills:
                recommendations.append("💡 Focus on foundational skills first - they'll make learning advanced tools easier")
        elif experience_level == 'senior':
            leadership_skills = [s for s in all_gaps if s.get('category') in ['methodologies', 'soft_skills']]
            if leadership_skills:
                recommendations.append("👑 Consider leadership and methodology skills to advance to senior roles")
        
        # Skill combination recommendations
        related_clusters = self._find_skill_clusters(all_gaps)
        if related_clusters:
            cluster = related_clusters[0]
            recommendations.append(f"📚 Learn skill cluster: {', '.join(cluster)} - they work well together and compound your value")
        
        # Timeline recommendations
        if len(all_gaps) > 5:
            recommendations.append("⏰ Recommended timeline: Focus on 1-2 skills at a time over 3-6 months for best retention")
        
        # Leverage existing skills
        if partial_matches:
            leverage_skill = partial_matches[0]
            related = leverage_skill.get('related_user_skills', [])
            if related:
                recommendations.append(f"🔗 Leverage your {', '.join(related)} knowledge to learn {leverage_skill['skill']} faster")
        
        # Market positioning
        if len(missing_skills) <= 3:
            recommendations.append("🎉 You're close to market leadership - focus on these final skills for maximum impact")
        elif len(missing_skills) > 10:
            recommendations.append("📈 Focus on the top 5 most critical skills first - trying to learn everything at once reduces effectiveness")
        
        return recommendations[:8]  # Limit to most important recommendations
    
    def _find_skill_clusters(self, skills: List[Dict]) -> List[List[str]]:
        """Find clusters of related skills that should be learned together"""
        clusters = []
        
        # Define skill clusters that work well together
        predefined_clusters = [
            ['react', 'javascript', 'html', 'css'],
            ['python', 'django', 'postgresql'],
            ['docker', 'kubernetes', 'aws'],
            ['node.js', 'express', 'mongodb'],
            ['java', 'spring', 'mysql'],
            ['terraform', 'aws', 'ansible'],
            ['pandas', 'numpy', 'python'],
            ['angular', 'typescript', 'html', 'css']
        ]
        
        skill_names = [s['skill'] for s in skills]
        
        for cluster in predefined_clusters:
            # Check if at least 2 skills from this cluster are in the missing skills
            cluster_matches = [skill for skill in cluster if skill in skill_names]
            if len(cluster_matches) >= 2:
                clusters.append(cluster_matches)
        
        return clusters
    
    def save_analysis(self, db: Session, user_id: int, analysis_data: Dict) -> bool:
        """Save skill gap analysis to database"""
        try:
            analytics = Analytics(
                user_id=user_id,
                type="skill_gap_analysis",
                data=analysis_data
            )
            db.add(analytics)
            db.commit()
            return True
        except Exception as e:
            print(f"Failed to save skill analysis: {e}")
            return False
    
    def get_latest_analysis(self, db: Session, user_id: int) -> Optional[Dict]:
        """Get the most recent skill gap analysis"""
        analytics = db.query(Analytics).filter(
            Analytics.user_id == user_id,
            Analytics.type == "skill_gap_analysis"
        ).order_by(Analytics.generated_at.desc()).first()
        
        return analytics.data if analytics else None


skill_analysis_service = SkillAnalysisService()