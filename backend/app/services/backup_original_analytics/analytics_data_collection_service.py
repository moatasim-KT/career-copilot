"""
Analytics Data Collection Service for Career Co-Pilot System
Implements comprehensive user activity tracking, application success monitoring, and market trend analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case, text

from app.models.user import User
from app.models.job import Job
from app.models.application import JobApplication, APPLICATION_STATUSES
from app.models.analytics import Analytics, ANALYTICS_TYPES
from app.core.database import get_db

logger = logging.getLogger(__name__)


class AnalyticsDataCollectionService:
    """Service for collecting and analyzing user activity, application success, and market trends"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # User Activity Tracking Methods
    
    def track_user_activity(self, db: Session, user_id: int, activity_type: str, metadata: Dict = None) -> bool:
        """Track user activity for analytics purposes"""
        try:
            activity_data = {
                'activity_type': activity_type,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            # Get or create user activity analytics record for today
            today = datetime.utcnow().date()
            existing_analytics = db.query(Analytics).filter(
                Analytics.user_id == user_id,
                Analytics.type == 'user_activity',
                func.date(Analytics.generated_at) == today
            ).first()
            
            if existing_analytics:
                # Append to existing activities
                activities = existing_analytics.data.get('activities', [])
                activities.append(activity_data)
                existing_analytics.data['activities'] = activities
                existing_analytics.data['activity_count'] = len(activities)
                existing_analytics.generated_at = datetime.utcnow()
            else:
                # Create new analytics record
                analytics = Analytics(
                    user_id=user_id,
                    type='user_activity',
                    data={
                        'date': today.isoformat(),
                        'activities': [activity_data],
                        'activity_count': 1
                    }
                )
                db.add(analytics)
            
            db.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to track user activity: {e}")
            db.rollback()
            return False
    
    def collect_user_engagement_metrics(self, db: Session, user_id: int, days: int = 30) -> Dict:
        """Collect comprehensive user engagement metrics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get user activity data
            activity_records = db.query(Analytics).filter(
                Analytics.user_id == user_id,
                Analytics.type == 'user_activity',
                Analytics.generated_at >= cutoff_date
            ).all()
            
            # Aggregate activity data
            total_activities = 0
            activity_types = {}
            daily_activities = {}
            
            for record in activity_records:
                activities = record.data.get('activities', [])
                total_activities += len(activities)
                
                for activity in activities:
                    activity_type = activity.get('activity_type', 'unknown')
                    activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
                    
                    # Track daily activity
                    activity_date = activity.get('timestamp', '')[:10]  # Get date part
                    daily_activities[activity_date] = daily_activities.get(activity_date, 0) + 1
            
            # Calculate engagement metrics
            active_days = len(daily_activities)
            avg_daily_activities = total_activities / max(active_days, 1)
            
            # Get job-related metrics
            jobs_viewed = db.query(Job).filter(
                Job.user_id == user_id,
                Job.created_at >= cutoff_date
            ).count()
            
            applications_submitted = db.query(JobApplication).filter(
                JobApplication.user_id == user_id,
                JobApplication.applied_at >= cutoff_date
            ).count()
            
            return {
                'analysis_date': datetime.utcnow().isoformat(),
                'period_days': days,
                'total_activities': total_activities,
                'active_days': active_days,
                'avg_daily_activities': round(avg_daily_activities, 2),
                'activity_breakdown': activity_types,
                'daily_activity_pattern': daily_activities,
                'jobs_viewed': jobs_viewed,
                'applications_submitted': applications_submitted,
                'engagement_score': self._calculate_engagement_score(
                    total_activities, active_days, applications_submitted, days
                )
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect user engagement metrics: {e}")
            return {'error': f'Failed to collect engagement metrics: {str(e)}'}
    
    def _calculate_engagement_score(self, total_activities: int, active_days: int, 
                                  applications: int, period_days: int) -> float:
        """Calculate user engagement score (0-100)"""
        # Normalize metrics
        activity_score = min(total_activities / (period_days * 5), 1.0) * 40  # Max 40 points
        consistency_score = (active_days / period_days) * 30  # Max 30 points
        application_score = min(applications / (period_days / 7), 1.0) * 30  # Max 30 points
        
        return round(activity_score + consistency_score + application_score, 2)
    
    # Application Success Rate Monitoring
    
    def monitor_application_success_rates(self, db: Session, user_id: int, days: int = 90) -> Dict:
        """Monitor and analyze application success rates with detailed metrics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all applications in the period
            applications = db.query(JobApplication, Job).join(Job).filter(
                JobApplication.user_id == user_id,
                JobApplication.applied_at >= cutoff_date
            ).all()
            
            if not applications:
                return {'error': 'No applications found in the specified period'}
            
            # Define success stages
            response_statuses = [
                'under_review', 'phone_screen_scheduled', 'phone_screen_completed',
                'interview_scheduled', 'interview_completed', 'final_round',
                'offer_received', 'offer_accepted'
            ]
            
            interview_statuses = [
                'phone_screen_scheduled', 'phone_screen_completed',
                'interview_scheduled', 'interview_completed', 'final_round',
                'offer_received', 'offer_accepted'
            ]
            
            offer_statuses = ['offer_received', 'offer_accepted']
            
            # Calculate success metrics
            total_applications = len(applications)
            responses = sum(1 for app, job in applications if app.status in response_statuses)
            interviews = sum(1 for app, job in applications if app.status in interview_statuses)
            offers = sum(1 for app, job in applications if app.status in offer_statuses)
            
            # Calculate rates
            response_rate = responses / total_applications if total_applications > 0 else 0
            interview_rate = interviews / total_applications if total_applications > 0 else 0
            offer_rate = offers / total_applications if total_applications > 0 else 0
            
            # Analyze by time periods (weekly breakdown)
            weekly_breakdown = self._analyze_weekly_success_patterns(applications, response_statuses)
            
            # Analyze by job characteristics
            company_analysis = self._analyze_success_by_company(applications, response_statuses)
            source_analysis = self._analyze_success_by_source(applications, response_statuses)
            
            success_data = {
                'analysis_date': datetime.utcnow().isoformat(),
                'period_days': days,
                'total_applications': total_applications,
                'success_metrics': {
                    'responses_received': responses,
                    'interviews_scheduled': interviews,
                    'offers_received': offers,
                    'response_rate': round(response_rate, 3),
                    'interview_rate': round(interview_rate, 3),
                    'offer_rate': round(offer_rate, 3),
                    'response_percentage': f"{response_rate:.1%}",
                    'interview_percentage': f"{interview_rate:.1%}",
                    'offer_percentage': f"{offer_rate:.1%}"
                },
                'weekly_trends': weekly_breakdown,
                'company_performance': company_analysis,
                'source_effectiveness': source_analysis,
                'benchmarks': self._get_industry_benchmarks(),
                'improvement_areas': self._identify_improvement_areas(response_rate, interview_rate, offer_rate)
            }
            
            # Save the analysis
            self._save_analytics_data(db, user_id, 'application_success_rate', success_data)
            
            return success_data
            
        except Exception as e:
            self.logger.error(f"Failed to monitor application success rates: {e}")
            return {'error': f'Failed to monitor success rates: {str(e)}'}
    
    def _analyze_weekly_success_patterns(self, applications: List[Tuple], response_statuses: List[str]) -> List[Dict]:
        """Analyze success patterns by week"""
        weekly_data = {}
        
        for app, job in applications:
            if app.applied_at:
                # Get week start date (Monday)
                week_start = app.applied_at.date() - timedelta(days=app.applied_at.weekday())
                week_key = week_start.isoformat()
                
                if week_key not in weekly_data:
                    weekly_data[week_key] = {'applications': 0, 'responses': 0}
                
                weekly_data[week_key]['applications'] += 1
                if app.status in response_statuses:
                    weekly_data[week_key]['responses'] += 1
        
        # Convert to list and calculate rates
        weekly_breakdown = []
        for week, data in sorted(weekly_data.items()):
            success_rate = data['responses'] / data['applications'] if data['applications'] > 0 else 0
            weekly_breakdown.append({
                'week_start': week,
                'applications': data['applications'],
                'responses': data['responses'],
                'success_rate': round(success_rate, 3),
                'success_percentage': f"{success_rate:.1%}"
            })
        
        return weekly_breakdown
    
    def _analyze_success_by_company(self, applications: List[Tuple], response_statuses: List[str]) -> Dict:
        """Analyze success rates by company"""
        company_data = {}
        
        for app, job in applications:
            company = job.company
            if company not in company_data:
                company_data[company] = {'applications': 0, 'responses': 0}
            
            company_data[company]['applications'] += 1
            if app.status in response_statuses:
                company_data[company]['responses'] += 1
        
        # Calculate success rates and sort
        company_analysis = {}
        for company, data in company_data.items():
            if data['applications'] >= 2:  # Only include companies with multiple applications
                success_rate = data['responses'] / data['applications']
                company_analysis[company] = {
                    'applications': data['applications'],
                    'responses': data['responses'],
                    'success_rate': round(success_rate, 3),
                    'success_percentage': f"{success_rate:.1%}"
                }
        
        return dict(sorted(company_analysis.items(), key=lambda x: x[1]['success_rate'], reverse=True))
    
    def _analyze_success_by_source(self, applications: List[Tuple], response_statuses: List[str]) -> Dict:
        """Analyze success rates by job source"""
        source_data = {}
        
        for app, job in applications:
            source = job.source
            if source not in source_data:
                source_data[source] = {'applications': 0, 'responses': 0}
            
            source_data[source]['applications'] += 1
            if app.status in response_statuses:
                source_data[source]['responses'] += 1
        
        # Calculate success rates
        source_analysis = {}
        for source, data in source_data.items():
            success_rate = data['responses'] / data['applications'] if data['applications'] > 0 else 0
            source_analysis[source] = {
                'applications': data['applications'],
                'responses': data['responses'],
                'success_rate': round(success_rate, 3),
                'success_percentage': f"{success_rate:.1%}"
            }
        
        return dict(sorted(source_analysis.items(), key=lambda x: x[1]['success_rate'], reverse=True))
    
    def _get_industry_benchmarks(self) -> Dict:
        """Get industry benchmark success rates"""
        return {
            'response_rate': {'low': 0.15, 'average': 0.25, 'high': 0.40},
            'interview_rate': {'low': 0.05, 'average': 0.10, 'high': 0.20},
            'offer_rate': {'low': 0.01, 'average': 0.03, 'high': 0.08}
        }
    
    def _identify_improvement_areas(self, response_rate: float, interview_rate: float, offer_rate: float) -> List[str]:
        """Identify areas for improvement based on success rates"""
        improvements = []
        benchmarks = self._get_industry_benchmarks()
        
        if response_rate < benchmarks['response_rate']['low']:
            improvements.append("Low response rate - improve resume and application targeting")
        
        if interview_rate < benchmarks['interview_rate']['low']:
            improvements.append("Low interview rate - enhance application quality and job matching")
        
        if offer_rate < benchmarks['offer_rate']['low']:
            improvements.append("Low offer rate - focus on interview preparation and skills development")
        
        # Check conversion between stages
        if response_rate > 0.2 and interview_rate / response_rate < 0.3:
            improvements.append("Good response rate but low interview conversion - improve initial screening performance")
        
        if interview_rate > 0.1 and offer_rate / interview_rate < 0.2:
            improvements.append("Good interview rate but low offer conversion - enhance interview skills")
        
        return improvements
    
    # Market Trend Analysis Methods
    
    def analyze_market_trends(self, db: Session, user_id: int, days: int = 90) -> Dict:
        """Analyze job market trends from collected job data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all jobs in the system (not just user's jobs for market analysis)
            all_jobs = db.query(Job).filter(
                Job.date_added >= cutoff_date
            ).all()
            
            if not all_jobs:
                return {'error': 'Insufficient job data for market analysis'}
            
            # Analyze job posting trends
            posting_trends = self._analyze_job_posting_trends(all_jobs)
            
            # Analyze salary trends
            salary_trends = self._analyze_salary_trends(all_jobs)
            
            # Analyze skill demand
            skill_demand = self._analyze_skill_demand(all_jobs)
            
            # Analyze location trends
            location_trends = self._analyze_location_trends(all_jobs)
            
            # Analyze company trends
            company_trends = self._analyze_company_trends(all_jobs)
            
            # Generate market insights
            market_insights = self._generate_market_insights(
                posting_trends, salary_trends, skill_demand, location_trends
            )
            
            market_data = {
                'analysis_date': datetime.utcnow().isoformat(),
                'period_days': days,
                'total_jobs_analyzed': len(all_jobs),
                'posting_trends': posting_trends,
                'salary_trends': salary_trends,
                'skill_demand': skill_demand,
                'location_trends': location_trends,
                'company_trends': company_trends,
                'market_insights': market_insights,
                'growth_metrics': self._calculate_market_growth_metrics(all_jobs, days)
            }
            
            # Save the analysis
            self._save_analytics_data(db, user_id, 'market_trends', market_data)
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Failed to analyze market trends: {e}")
            return {'error': f'Failed to analyze market trends: {str(e)}'}
    
    def _analyze_job_posting_trends(self, jobs: List[Job]) -> Dict:
        """Analyze job posting volume trends over time"""
        daily_counts = {}
        
        for job in jobs:
            if job.date_added:
                date_key = job.date_added.date().isoformat()
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        # Calculate weekly averages
        weekly_data = {}
        for date_str, count in daily_counts.items():
            date_obj = datetime.fromisoformat(date_str).date()
            week_start = date_obj - timedelta(days=date_obj.weekday())
            week_key = week_start.isoformat()
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {'total': 0, 'days': 0}
            
            weekly_data[week_key]['total'] += count
            weekly_data[week_key]['days'] += 1
        
        # Calculate weekly averages
        weekly_trends = []
        for week, data in sorted(weekly_data.items()):
            avg_daily = data['total'] / data['days'] if data['days'] > 0 else 0
            weekly_trends.append({
                'week_start': week,
                'total_jobs': data['total'],
                'avg_daily_jobs': round(avg_daily, 1)
            })
        
        return {
            'daily_posting_counts': daily_counts,
            'weekly_trends': weekly_trends,
            'peak_posting_day': max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None,
            'avg_daily_postings': round(sum(daily_counts.values()) / len(daily_counts), 1) if daily_counts else 0
        }
    
    def _analyze_salary_trends(self, jobs: List[Job]) -> Dict:
        """Analyze salary trends across job postings"""
        salary_data = []
        
        for job in jobs:
            if job.salary_min and job.salary_max:
                avg_salary = (job.salary_min + job.salary_max) / 2
                salary_data.append({
                    'salary': avg_salary,
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'date_posted': job.date_added.date().isoformat() if job.date_added else None
                })
        
        if not salary_data:
            return {'error': 'No salary data available'}
        
        # Calculate salary statistics
        salaries = [item['salary'] for item in salary_data]
        salaries.sort()
        
        n = len(salaries)
        median_salary = salaries[n // 2] if n % 2 == 1 else (salaries[n // 2 - 1] + salaries[n // 2]) / 2
        
        # Analyze by location
        location_salaries = {}
        for item in salary_data:
            location = item['location'] or 'Unknown'
            if location not in location_salaries:
                location_salaries[location] = []
            location_salaries[location].append(item['salary'])
        
        location_analysis = {}
        for location, salaries_list in location_salaries.items():
            if len(salaries_list) >= 3:  # Only include locations with sufficient data
                location_analysis[location] = {
                    'count': len(salaries_list),
                    'average': round(sum(salaries_list) / len(salaries_list), 0),
                    'median': round(sorted(salaries_list)[len(salaries_list) // 2], 0),
                    'min': min(salaries_list),
                    'max': max(salaries_list)
                }
        
        return {
            'total_jobs_with_salary': len(salary_data),
            'overall_statistics': {
                'average': round(sum(salaries) / len(salaries), 0),
                'median': round(median_salary, 0),
                'min': min(salaries),
                'max': max(salaries),
                'percentile_25': round(salaries[n // 4], 0),
                'percentile_75': round(salaries[3 * n // 4], 0)
            },
            'by_location': dict(sorted(location_analysis.items(), key=lambda x: x[1]['average'], reverse=True))
        }
    
    def _analyze_skill_demand(self, jobs: List[Job]) -> Dict:
        """Analyze skill demand from job requirements"""
        skill_counts = {}
        total_jobs_with_skills = 0
        
        for job in jobs:
            if job.requirements and isinstance(job.requirements, dict):
                skills = job.requirements.get('skills_required', [])
                if skills:
                    total_jobs_with_skills += 1
                    for skill in skills:
                        if isinstance(skill, str):
                            skill_lower = skill.lower().strip()
                            skill_counts[skill_lower] = skill_counts.get(skill_lower, 0) + 1
        
        if not skill_counts:
            return {'error': 'No skill data available in job requirements'}
        
        # Calculate skill demand percentages
        skill_demand = {}
        for skill, count in skill_counts.items():
            percentage = (count / total_jobs_with_skills) * 100
            skill_demand[skill] = {
                'count': count,
                'percentage': round(percentage, 1),
                'demand_level': self._categorize_skill_demand(percentage)
            }
        
        # Sort by demand
        top_skills = dict(sorted(skill_demand.items(), key=lambda x: x[1]['count'], reverse=True)[:20])
        
        return {
            'total_jobs_analyzed': total_jobs_with_skills,
            'unique_skills_found': len(skill_counts),
            'top_skills': top_skills,
            'skill_categories': self._categorize_skills(top_skills),
            'emerging_skills': self._identify_emerging_skills(skill_demand)
        }
    
    def _categorize_skill_demand(self, percentage: float) -> str:
        """Categorize skill demand level"""
        if percentage >= 50:
            return 'very_high'
        elif percentage >= 30:
            return 'high'
        elif percentage >= 15:
            return 'moderate'
        elif percentage >= 5:
            return 'low'
        else:
            return 'very_low'
    
    def _categorize_skills(self, skills: Dict) -> Dict:
        """Categorize skills by type"""
        categories = {
            'programming_languages': [],
            'frameworks': [],
            'databases': [],
            'cloud_platforms': [],
            'tools': [],
            'soft_skills': [],
            'other': []
        }
        
        # Define skill categories (simplified mapping)
        programming_languages = ['python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'typescript', 'php', 'ruby']
        frameworks = ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'fastapi', 'laravel']
        databases = ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite', 'oracle']
        cloud_platforms = ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform']
        tools = ['git', 'jenkins', 'jira', 'confluence', 'slack', 'figma', 'postman']
        soft_skills = ['communication', 'leadership', 'teamwork', 'problem-solving', 'analytical']
        
        for skill, data in skills.items():
            skill_lower = skill.lower()
            if any(lang in skill_lower for lang in programming_languages):
                categories['programming_languages'].append({skill: data})
            elif any(fw in skill_lower for fw in frameworks):
                categories['frameworks'].append({skill: data})
            elif any(db in skill_lower for db in databases):
                categories['databases'].append({skill: data})
            elif any(cloud in skill_lower for cloud in cloud_platforms):
                categories['cloud_platforms'].append({skill: data})
            elif any(tool in skill_lower for tool in tools):
                categories['tools'].append({skill: data})
            elif any(soft in skill_lower for soft in soft_skills):
                categories['soft_skills'].append({skill: data})
            else:
                categories['other'].append({skill: data})
        
        return categories
    
    def _identify_emerging_skills(self, skill_demand: Dict) -> List[Dict]:
        """Identify emerging skills (moderate demand but growing)"""
        # This is a simplified implementation - in practice, you'd compare with historical data
        emerging = []
        for skill, data in skill_demand.items():
            if data['demand_level'] in ['moderate', 'low'] and data['count'] >= 3:
                emerging.append({
                    'skill': skill,
                    'count': data['count'],
                    'percentage': data['percentage'],
                    'growth_potential': 'high' if data['percentage'] > 10 else 'moderate'
                })
        
        return sorted(emerging, key=lambda x: x['percentage'], reverse=True)[:10]
    
    def _analyze_location_trends(self, jobs: List[Job]) -> Dict:
        """Analyze job location trends"""
        location_counts = {}
        remote_count = 0
        
        for job in jobs:
            location = job.location or 'Unknown'
            
            # Check for remote work indicators
            if any(term in location.lower() for term in ['remote', 'anywhere', 'work from home']):
                remote_count += 1
                location = 'Remote'
            
            location_counts[location] = location_counts.get(location, 0) + 1
        
        # Calculate percentages
        total_jobs = len(jobs)
        location_analysis = {}
        for location, count in location_counts.items():
            percentage = (count / total_jobs) * 100
            location_analysis[location] = {
                'count': count,
                'percentage': round(percentage, 1)
            }
        
        # Sort by count
        top_locations = dict(sorted(location_analysis.items(), key=lambda x: x[1]['count'], reverse=True)[:15])
        
        return {
            'total_jobs': total_jobs,
            'remote_jobs': remote_count,
            'remote_percentage': round((remote_count / total_jobs) * 100, 1),
            'top_locations': top_locations,
            'location_diversity': len(location_counts)
        }
    
    def _analyze_company_trends(self, jobs: List[Job]) -> Dict:
        """Analyze company hiring trends"""
        company_counts = {}
        
        for job in jobs:
            company = job.company
            company_counts[company] = company_counts.get(company, 0) + 1
        
        # Calculate statistics
        job_counts = list(company_counts.values())
        avg_jobs_per_company = sum(job_counts) / len(job_counts) if job_counts else 0
        
        # Identify top hiring companies
        top_companies = dict(sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Categorize companies by hiring volume
        hiring_categories = {
            'high_volume': len([c for c in job_counts if c >= 5]),
            'medium_volume': len([c for c in job_counts if 2 <= c < 5]),
            'low_volume': len([c for c in job_counts if c == 1])
        }
        
        return {
            'total_companies': len(company_counts),
            'avg_jobs_per_company': round(avg_jobs_per_company, 1),
            'top_hiring_companies': top_companies,
            'hiring_volume_distribution': hiring_categories
        }
    
    def _generate_market_insights(self, posting_trends: Dict, salary_trends: Dict, 
                                skill_demand: Dict, location_trends: Dict) -> List[str]:
        """Generate market insights from trend analysis"""
        insights = []
        
        # Posting trends insights
        if 'weekly_trends' in posting_trends and posting_trends['weekly_trends']:
            recent_week = posting_trends['weekly_trends'][-1]
            insights.append(f"Recent week saw {recent_week['total_jobs']} new job postings")
        
        # Salary insights
        if 'overall_statistics' in salary_trends:
            avg_salary = salary_trends['overall_statistics']['average']
            insights.append(f"Average salary across all positions: ${avg_salary:,.0f}")
        
        # Skill demand insights
        if 'top_skills' in skill_demand:
            top_skill = list(skill_demand['top_skills'].keys())[0]
            top_skill_pct = skill_demand['top_skills'][top_skill]['percentage']
            insights.append(f"Most in-demand skill: {top_skill.title()} ({top_skill_pct}% of jobs)")
        
        # Location insights
        if 'remote_percentage' in location_trends:
            remote_pct = location_trends['remote_percentage']
            insights.append(f"Remote work opportunities: {remote_pct}% of all jobs")
        
        return insights
    
    def _calculate_market_growth_metrics(self, jobs: List[Job], days: int) -> Dict:
        """Calculate market growth metrics"""
        if days < 14:
            return {'error': 'Insufficient time period for growth calculation'}
        
        # Split period in half to compare growth
        mid_point = datetime.utcnow() - timedelta(days=days // 2)
        
        recent_jobs = [job for job in jobs if job.date_added and job.date_added >= mid_point]
        earlier_jobs = [job for job in jobs if job.date_added and job.date_added < mid_point]
        
        recent_count = len(recent_jobs)
        earlier_count = len(earlier_jobs)
        
        # Calculate growth rate
        if earlier_count > 0:
            growth_rate = ((recent_count - earlier_count) / earlier_count) * 100
        else:
            growth_rate = 0
        
        return {
            'recent_period_jobs': recent_count,
            'earlier_period_jobs': earlier_count,
            'growth_rate_percentage': round(growth_rate, 1),
            'growth_trend': 'increasing' if growth_rate > 5 else 'decreasing' if growth_rate < -5 else 'stable'
        }
    
    # Utility Methods
    
    def _save_analytics_data(self, db: Session, user_id: int, analytics_type: str, data: Dict) -> bool:
        """Save analytics data to database"""
        try:
            analytics = Analytics(
                user_id=user_id,
                type=analytics_type,
                data=data
            )
            db.add(analytics)
            db.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to save analytics data: {e}")
            db.rollback()
            return False
    
    def get_comprehensive_analytics_report(self, db: Session, user_id: int, days: int = 90) -> Dict:
        """Generate comprehensive analytics report combining all data collection methods"""
        try:
            # Collect all analytics data
            user_engagement = self.collect_user_engagement_metrics(db, user_id, days)
            application_success = self.monitor_application_success_rates(db, user_id, days)
            market_trends = self.analyze_market_trends(db, user_id, days)
            
            # Generate overall insights
            overall_insights = []
            
            if 'error' not in user_engagement:
                engagement_score = user_engagement.get('engagement_score', 0)
                overall_insights.append(f"User engagement score: {engagement_score}/100")
            
            if 'error' not in application_success:
                response_rate = application_success.get('success_metrics', {}).get('response_percentage', '0%')
                overall_insights.append(f"Application response rate: {response_rate}")
            
            if 'error' not in market_trends:
                total_jobs = market_trends.get('total_jobs_analyzed', 0)
                overall_insights.append(f"Market analysis based on {total_jobs} job postings")
            
            comprehensive_report = {
                'generated_at': datetime.utcnow().isoformat(),
                'analysis_period_days': days,
                'user_id': user_id,
                'user_engagement_metrics': user_engagement,
                'application_success_monitoring': application_success,
                'market_trend_analysis': market_trends,
                'overall_insights': overall_insights,
                'report_summary': {
                    'engagement_healthy': user_engagement.get('engagement_score', 0) > 50 if 'error' not in user_engagement else False,
                    'application_performance': 'good' if application_success.get('success_metrics', {}).get('response_rate', 0) > 0.2 else 'needs_improvement' if 'error' not in application_success else 'unknown',
                    'market_activity': 'active' if market_trends.get('total_jobs_analyzed', 0) > 100 else 'moderate' if 'error' not in market_trends else 'unknown'
                }
            }
            
            # Save comprehensive report
            self._save_analytics_data(db, user_id, 'comprehensive_analytics_report', comprehensive_report)
            
            return comprehensive_report
            
        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive analytics report: {e}")
            return {
                'error': f'Failed to generate comprehensive report: {str(e)}',
                'generated_at': datetime.utcnow().isoformat()
            }


# Global service instance
analytics_data_collection_service = AnalyticsDataCollectionService()