"""
Skill gap analysis service with NLP-based extraction and market trend analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.job import Job
from app.models.user import User
from app.services.skill_matching_service import skill_matching_service

logger = logging.getLogger(__name__)


class SkillGapAnalysisService:
    """Service for analyzing skill gaps and market trends"""
    
    def __init__(self):
        # Learning resource mappings
        self.learning_resources = {
            'python': {
                'courses': ['Python.org Tutorial', 'Real Python', 'Automate the Boring Stuff'],
                'certifications': ['PCAP', 'PCPP'],
                'difficulty': 'beginner',
                'time_estimate': '2-3 months'
            },
            'javascript': {
                'courses': ['MDN Web Docs', 'JavaScript.info', 'FreeCodeCamp'],
                'certifications': ['JavaScript Institute'],
                'difficulty': 'beginner',
                'time_estimate': '2-4 months'
            },
            'react': {
                'courses': ['React Official Docs', 'Scrimba React Course', 'Epic React'],
                'certifications': ['Meta React Certificate'],
                'difficulty': 'intermediate',
                'time_estimate': '1-2 months'
            },
            'aws': {
                'courses': ['AWS Training', 'A Cloud Guru', 'Linux Academy'],
                'certifications': ['AWS Cloud Practitioner', 'AWS Solutions Architect'],
                'difficulty': 'intermediate',
                'time_estimate': '3-6 months'
            },
            'docker': {
                'courses': ['Docker Official Tutorial', 'Docker Mastery', 'Kubernetes Course'],
                'certifications': ['Docker Certified Associate'],
                'difficulty': 'intermediate',
                'time_estimate': '1-3 months'
            }
        }
        
        # Skill importance weights based on market demand
        self.skill_importance = {
            'python': 0.95, 'javascript': 0.90, 'java': 0.85, 'sql': 0.80,
            'aws': 0.85, 'react': 0.80, 'docker': 0.75, 'kubernetes': 0.70,
            'node.js': 0.75, 'postgresql': 0.70, 'mongodb': 0.65, 'redis': 0.60
        }

    def extract_skills_from_jobs(self, jobs: List[Job]) -> Dict[str, Any]:
        """Extract and analyze skills from job listings"""
        all_skills = []
        job_skill_map = {}
        
        for job in jobs:
            # Extract skills from job description and requirements
            job_text = f"{job.title} {job.description or ''}"
            requirements = job.requirements or {}
            
            # Get required and preferred skills
            required_skills = requirements.get('skills_required', [])
            preferred_skills = requirements.get('skills_preferred', [])
            
            # Extract skills from text
            extracted_skills = skill_matching_service.extract_skills_from_text(job_text)
            
            # Combine all skills for this job
            job_skills = list(set(
                [s.lower().strip() for s in required_skills + preferred_skills + extracted_skills]
            ))
            
            job_skill_map[job.id] = {
                'skills': job_skills,
                'required': [s.lower().strip() for s in required_skills],
                'preferred': [s.lower().strip() for s in preferred_skills],
                'extracted': [s.lower().strip() for s in extracted_skills],
                'company': job.company,
                'title': job.title,
                'salary_min': job.salary_min,
                'date_posted': job.date_posted
            }
            
            all_skills.extend(job_skills)
        
        return {
            'all_skills': all_skills,
            'job_skill_map': job_skill_map,
            'total_jobs': len(jobs)
        }

    def analyze_skill_frequency(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze skill frequency and trends across job opportunities"""
        all_skills = skill_data['all_skills']
        job_skill_map = skill_data['job_skill_map']
        
        # Calculate skill frequency
        skill_counter = Counter(all_skills)
        total_skills = len(all_skills)
        
        # Calculate skill statistics
        skill_stats = {}
        for skill, count in skill_counter.items():
            jobs_with_skill = [
                job_id for job_id, job_data in job_skill_map.items()
                if skill in job_data['skills']
            ]
            
            # Calculate average salary for jobs requiring this skill
            salaries = [
                job_skill_map[job_id]['salary_min']
                for job_id in jobs_with_skill
                if job_skill_map[job_id]['salary_min']
            ]
            avg_salary = sum(salaries) / len(salaries) if salaries else None
            
            # Calculate skill importance score
            importance = self.skill_importance.get(skill, 0.5)
            
            skill_stats[skill] = {
                'frequency': count,
                'percentage': (count / total_skills) * 100,
                'job_count': len(jobs_with_skill),
                'job_percentage': (len(jobs_with_skill) / skill_data['total_jobs']) * 100,
                'avg_salary': avg_salary,
                'importance_score': importance,
                'market_score': (count / skill_data['total_jobs']) * importance
            }
        
        # Rank skills by market demand
        top_skills = sorted(
            skill_stats.items(),
            key=lambda x: x[1]['market_score'],
            reverse=True
        )
        
        return {
            'skill_stats': skill_stats,
            'top_skills': top_skills[:20],
            'total_unique_skills': len(skill_stats),
            'analysis_date': datetime.now().isoformat()
        }

    def identify_skill_gaps(
        self, 
        user_skills: List[str], 
        market_analysis: Dict[str, Any],
        target_roles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Identify skill gaps for a user based on market analysis"""
        user_skills_lower = set(s.lower().strip() for s in user_skills)
        skill_stats = market_analysis['skill_stats']
        
        # Identify missing high-demand skills
        missing_skills = []
        for skill, stats in skill_stats.items():
            if skill not in user_skills_lower:
                missing_skills.append({
                    'skill': skill,
                    'market_demand': stats['job_percentage'],
                    'avg_salary': stats['avg_salary'],
                    'importance': stats['importance_score'],
                    'priority_score': stats['market_score']
                })
        
        # Sort by priority score
        missing_skills.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Categorize gaps by priority
        high_priority = [s for s in missing_skills if s['priority_score'] > 0.7]
        medium_priority = [s for s in missing_skills if 0.4 <= s['priority_score'] <= 0.7]
        low_priority = [s for s in missing_skills if s['priority_score'] < 0.4]
        
        # Calculate skill coverage
        total_market_skills = len(skill_stats)
        user_market_skills = len(user_skills_lower.intersection(set(skill_stats.keys())))
        coverage_percentage = (user_market_skills / total_market_skills) * 100
        
        return {
            'user_skills': list(user_skills_lower),
            'missing_skills': missing_skills[:15],  # Top 15 gaps
            'skill_gaps_by_priority': {
                'high': high_priority[:5],
                'medium': medium_priority[:5],
                'low': low_priority[:5]
            },
            'skill_coverage': {
                'percentage': coverage_percentage,
                'covered_skills': user_market_skills,
                'total_market_skills': total_market_skills
            },
            'analysis_date': datetime.now().isoformat()
        }

    def generate_learning_recommendations(
        self, 
        skill_gaps: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate personalized learning recommendations"""
        recommendations = []
        
        # Get high and medium priority gaps
        priority_gaps = (
            skill_gaps['skill_gaps_by_priority']['high'] +
            skill_gaps['skill_gaps_by_priority']['medium']
        )
        
        for gap in priority_gaps[:8]:  # Top 8 recommendations
            skill = gap['skill']
            
            # Get learning resources
            resources = self.learning_resources.get(skill, {
                'courses': [f'{skill.title()} fundamentals', f'Learn {skill.title()}'],
                'certifications': [f'{skill.title()} certification'],
                'difficulty': 'intermediate',
                'time_estimate': '2-4 months'
            })
            
            # Calculate ROI estimate
            salary_impact = gap.get('avg_salary', 0) - 100000  # Baseline salary
            roi_estimate = max(salary_impact, 5000)  # Minimum $5k impact
            
            recommendation = {
                'skill': skill,
                'priority': 'high' if gap['priority_score'] > 0.7 else 'medium',
                'market_demand': f"{gap['market_demand']:.1f}%",
                'salary_impact': f"${roi_estimate:,}" if roi_estimate > 0 else "Market rate",
                'learning_path': {
                    'courses': resources['courses'][:3],
                    'certifications': resources['certifications'][:2],
                    'difficulty': resources['difficulty'],
                    'estimated_time': resources['time_estimate']
                },
                'next_steps': self._generate_next_steps(skill, resources['difficulty'])
            }
            
            recommendations.append(recommendation)
        
        return recommendations

    def _generate_next_steps(self, skill: str, difficulty: str) -> List[str]:
        """Generate specific next steps for learning a skill"""
        if difficulty == 'beginner':
            return [
                f"Start with {skill} fundamentals tutorial",
                f"Practice with simple {skill} projects",
                f"Join {skill} community forums"
            ]
        elif difficulty == 'intermediate':
            return [
                f"Review {skill} prerequisites",
                f"Enroll in structured {skill} course",
                f"Build portfolio project using {skill}"
            ]
        else:  # advanced
            return [
                f"Assess current {skill} knowledge gaps",
                f"Take advanced {skill} certification",
                f"Contribute to {skill} open source projects"
            ]

    def analyze_market_trends(
        self, 
        db: Session,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """Analyze skill trends in the job market"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get recent jobs
        recent_jobs = db.query(Job).filter(
            Job.date_posted >= cutoff_date,
            Job.status == 'active'
        ).all()
        
        if not recent_jobs:
            return {'error': 'No recent jobs found for trend analysis'}
        
        # Extract skills from recent jobs
        skill_data = self.extract_skills_from_jobs(recent_jobs)
        market_analysis = self.analyze_skill_frequency(skill_data)
        
        # Calculate trend metrics
        skill_stats = market_analysis['skill_stats']
        
        # Identify trending skills (high frequency + high salary)
        trending_skills = []
        for skill, stats in skill_stats.items():
            if stats['job_percentage'] > 10 and stats['avg_salary']:  # >10% of jobs
                trend_score = (
                    stats['job_percentage'] * 0.6 +
                    (stats['avg_salary'] / 200000) * 100 * 0.4  # Normalize salary
                )
                
                trending_skills.append({
                    'skill': skill,
                    'trend_score': trend_score,
                    'job_percentage': stats['job_percentage'],
                    'avg_salary': stats['avg_salary'],
                    'growth_indicator': 'rising' if trend_score > 50 else 'stable'
                })
        
        trending_skills.sort(key=lambda x: x['trend_score'], reverse=True)
        
        return {
            'analysis_period': f"{days_back} days",
            'jobs_analyzed': len(recent_jobs),
            'trending_skills': trending_skills[:10],
            'market_summary': {
                'most_demanded': market_analysis['top_skills'][0][0] if market_analysis['top_skills'] else None,
                'total_skills_tracked': market_analysis['total_unique_skills'],
                'avg_skills_per_job': len(skill_data['all_skills']) / len(recent_jobs)
            },
            'generated_at': datetime.now().isoformat()
        }

    def get_comprehensive_skill_analysis(
        self, 
        db: Session,
        user_id: int,
        include_trends: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive skill analysis for a user"""
        # Get user profile
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {'error': 'User not found'}
        
        user_profile = user.profile or {}
        user_skills = user_profile.get('skills', [])
        
        # Get recent jobs for analysis
        recent_jobs = db.query(Job).filter(
            Job.status == 'active',
            Job.date_posted >= datetime.now() - timedelta(days=60)
        ).limit(500).all()
        
        if not recent_jobs:
            return {'error': 'No recent jobs available for analysis'}
        
        # Perform skill analysis
        skill_data = self.extract_skills_from_jobs(recent_jobs)
        market_analysis = self.analyze_skill_frequency(skill_data)
        skill_gaps = self.identify_skill_gaps(user_skills, market_analysis)
        learning_recommendations = self.generate_learning_recommendations(skill_gaps, user_profile)
        
        result = {
            'user_id': user_id,
            'skill_analysis': {
                'current_skills': user_skills,
                'skill_coverage': skill_gaps['skill_coverage'],
                'top_skill_gaps': skill_gaps['missing_skills'][:10],
                'priority_gaps': skill_gaps['skill_gaps_by_priority']
            },
            'learning_recommendations': learning_recommendations,
            'market_insights': {
                'jobs_analyzed': len(recent_jobs),
                'top_market_skills': [skill for skill, _ in market_analysis['top_skills'][:10]],
                'skill_diversity': market_analysis['total_unique_skills']
            }
        }
        
        # Add trend analysis if requested
        if include_trends:
            trends = self.analyze_market_trends(db, days_back=30)
            if 'error' not in trends:
                result['market_trends'] = trends
        
        result['generated_at'] = datetime.now().isoformat()
        return result


# Global service instance
skill_gap_analysis_service = SkillGapAnalysisService()