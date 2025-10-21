"""
Reporting and Insights Generation Service for Career Co-Pilot System
Implements weekly/monthly progress reports, salary trend analysis, career insights, and recommendation effectiveness tracking
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case, text
from collections import defaultdict, Counter

from app.models.user import User
from app.models.job import Job
from app.models.application import JobApplication, APPLICATION_STATUSES
from app.models.analytics import Analytics, ANALYTICS_TYPES
from app.core.database import get_db

logger = logging.getLogger(__name__)


class ReportingInsightsService:
    """Service for generating comprehensive reports and career insights"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # Weekly and Monthly Progress Reports
    
    def generate_weekly_progress_report(self, db: Session, user_id: int, week_offset: int = 0) -> Dict:
        """Generate comprehensive weekly progress report"""
        try:
            # Calculate week boundaries
            today = datetime.utcnow().date()
            week_start = today - timedelta(days=today.weekday() + (week_offset * 7))
            week_end = week_start + timedelta(days=6)
            
            # Get week data
            week_applications = self._get_applications_in_period(db, user_id, week_start, week_end)
            week_jobs_added = self._get_jobs_added_in_period(db, user_id, week_start, week_end)
            week_activities = self._get_user_activities_in_period(db, user_id, week_start, week_end)
            
            # Calculate metrics
            applications_count = len(week_applications)
            jobs_added_count = len(week_jobs_added)
            
            # Get status updates
            status_changes = self._analyze_status_changes(week_applications)
            
            # Calculate engagement metrics
            engagement_metrics = self._calculate_weekly_engagement(week_activities)
            
            # Get previous week for comparison
            prev_week_start = week_start - timedelta(days=7)
            prev_week_end = week_start - timedelta(days=1)
            prev_applications = self._get_applications_in_period(db, user_id, prev_week_start, prev_week_end)
            
            # Calculate trends
            application_trend = self._calculate_trend(applications_count, len(prev_applications))
            
            # Generate insights
            weekly_insights = self._generate_weekly_insights(
                applications_count, jobs_added_count, status_changes, engagement_metrics, application_trend
            )
            
            # Get goals and achievements
            weekly_goals = self._get_weekly_goals(db, user_id, week_start)
            achievements = self._identify_weekly_achievements(
                applications_count, status_changes, engagement_metrics
            )
            
            report = {
                'report_type': 'weekly_progress',
                'generated_at': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'period': {
                    'week_start': week_start.isoformat(),
                    'week_end': week_end.isoformat(),
                    'week_number': week_start.isocalendar()[1],
                    'year': week_start.year
                },
                'metrics': {
                    'applications_submitted': applications_count,
                    'jobs_added_to_tracker': jobs_added_count,
                    'status_updates': len(status_changes),
                    'active_days': engagement_metrics.get('active_days', 0),
                    'total_activities': engagement_metrics.get('total_activities', 0)
                },
                'application_breakdown': {
                    'by_status': self._group_applications_by_status(week_applications),
                    'by_source': self._group_applications_by_source(week_applications),
                    'by_day': self._group_applications_by_day(week_applications)
                },
                'status_progression': status_changes,
                'engagement_analysis': engagement_metrics,
                'trends': {
                    'applications_vs_previous_week': application_trend,
                    'momentum': 'increasing' if application_trend > 0 else 'decreasing' if application_trend < 0 else 'stable'
                },
                'goals_and_achievements': {
                    'weekly_goals': weekly_goals,
                    'achievements': achievements,
                    'goal_completion_rate': self._calculate_goal_completion_rate(weekly_goals, achievements)
                },
                'insights': weekly_insights,
                'recommendations': self._generate_weekly_recommendations(
                    applications_count, engagement_metrics, status_changes
                )
            }
            
            # Save the report
            self._save_report(db, user_id, 'weekly_progress_report', report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate weekly progress report: {e}")
            return {'error': f'Failed to generate weekly report: {str(e)}'}
    
    def generate_monthly_progress_report(self, db: Session, user_id: int, month_offset: int = 0) -> Dict:
        """Generate comprehensive monthly progress report"""
        try:
            # Calculate month boundaries
            today = datetime.utcnow().date()
            if month_offset == 0:
                month_start = today.replace(day=1)
                if today.month == 12:
                    month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            else:
                # Handle previous months
                if today.month + month_offset <= 0:
                    year = today.year - 1
                    month = 12 + (today.month + month_offset)
                else:
                    year = today.year
                    month = today.month + month_offset
                
                month_start = datetime(year, month, 1).date()
                if month == 12:
                    month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
                else:
                    month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
            # Get month data
            month_applications = self._get_applications_in_period(db, user_id, month_start, month_end)
            month_jobs_added = self._get_jobs_added_in_period(db, user_id, month_start, month_end)
            month_activities = self._get_user_activities_in_period(db, user_id, month_start, month_end)
            
            # Calculate comprehensive metrics
            applications_count = len(month_applications)
            jobs_added_count = len(month_jobs_added)
            
            # Analyze application success rates
            success_metrics = self._calculate_monthly_success_metrics(month_applications)
            
            # Weekly breakdown
            weekly_breakdown = self._generate_weekly_breakdown(db, user_id, month_start, month_end)
            
            # Get previous month for comparison
            prev_month_start = month_start - timedelta(days=32)
            prev_month_start = prev_month_start.replace(day=1)
            prev_month_end = month_start - timedelta(days=1)
            prev_applications = self._get_applications_in_period(db, user_id, prev_month_start, prev_month_end)
            
            # Calculate trends
            monthly_trends = self._calculate_monthly_trends(
                applications_count, len(prev_applications), success_metrics
            )
            
            # Career progression analysis
            career_progression = self._analyze_career_progression(db, user_id, month_start, month_end)
            
            # Generate comprehensive insights
            monthly_insights = self._generate_monthly_insights(
                applications_count, success_metrics, career_progression, monthly_trends
            )
            
            # Calculate monthly achievements
            monthly_achievements = self._identify_monthly_achievements(
                applications_count, success_metrics, career_progression
            )
            
            report = {
                'report_type': 'monthly_progress',
                'generated_at': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'period': {
                    'month_start': month_start.isoformat(),
                    'month_end': month_end.isoformat(),
                    'month_name': month_start.strftime('%B'),
                    'year': month_start.year
                },
                'summary_metrics': {
                    'total_applications': applications_count,
                    'jobs_added': jobs_added_count,
                    'response_rate': success_metrics.get('response_rate', 0),
                    'interview_rate': success_metrics.get('interview_rate', 0),
                    'active_days': len(set(activity.get('date') for activity in month_activities if activity.get('date'))),
                    'avg_applications_per_week': round(applications_count / 4.33, 1)
                },
                'success_analysis': success_metrics,
                'weekly_breakdown': weekly_breakdown,
                'application_patterns': {
                    'by_status': self._group_applications_by_status(month_applications),
                    'by_source': self._group_applications_by_source(month_applications),
                    'by_company_type': self._analyze_company_types(month_applications),
                    'timing_patterns': self._analyze_application_timing(month_applications)
                },
                'career_progression': career_progression,
                'trends_analysis': monthly_trends,
                'achievements': monthly_achievements,
                'insights': monthly_insights,
                'goals_assessment': self._assess_monthly_goals(db, user_id, month_start, month_end),
                'recommendations': self._generate_monthly_recommendations(
                    applications_count, success_metrics, career_progression, monthly_trends
                )
            }
            
            # Save the report
            self._save_report(db, user_id, 'monthly_progress_report', report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate monthly progress report: {e}")
            return {'error': f'Failed to generate monthly report: {str(e)}'}    

    # Salary Trend Analysis and Career Insights
    
    def analyze_salary_trends_comprehensive(self, db: Session, user_id: int, days: int = 180) -> Dict:
        """Comprehensive salary trend analysis with career insights"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get user's applications and jobs
            user_applications = db.query(JobApplication, Job).join(Job).filter(
                JobApplication.user_id == user_id,
                JobApplication.applied_at >= cutoff_date
            ).all()
            
            # Get all jobs for market comparison
            market_jobs = db.query(Job).filter(
                Job.date_added >= cutoff_date,
                Job.salary_min.isnot(None),
                Job.salary_max.isnot(None)
            ).all()
            
            if not market_jobs:
                return {'error': 'Insufficient salary data for analysis'}
            
            # Analyze user's target salary range
            user_salary_analysis = self._analyze_user_salary_targets(user_applications)
            
            # Market salary trends
            market_salary_trends = self._analyze_market_salary_trends(market_jobs, days)
            
            # Career level progression insights
            career_insights = self._generate_career_salary_insights(
                user_salary_analysis, market_salary_trends, user_id
            )
            
            # Salary negotiation insights
            negotiation_insights = self._generate_salary_negotiation_insights(
                user_salary_analysis, market_salary_trends
            )
            
            # Geographic salary analysis
            geographic_analysis = self._analyze_geographic_salary_trends(market_jobs)
            
            # Industry salary comparison
            industry_analysis = self._analyze_industry_salary_trends(market_jobs)
            
            # Generate salary growth projections
            growth_projections = self._generate_salary_growth_projections(
                user_salary_analysis, market_salary_trends
            )
            
            report = {
                'analysis_type': 'comprehensive_salary_trends',
                'generated_at': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'analysis_period_days': days,
                'user_salary_profile': user_salary_analysis,
                'market_trends': market_salary_trends,
                'career_insights': career_insights,
                'negotiation_strategy': negotiation_insights,
                'geographic_analysis': geographic_analysis,
                'industry_comparison': industry_analysis,
                'growth_projections': growth_projections,
                'recommendations': self._generate_salary_recommendations(
                    user_salary_analysis, market_salary_trends, career_insights
                )
            }
            
            # Save the analysis
            self._save_report(db, user_id, 'salary_trends_analysis', report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to analyze salary trends: {e}")
            return {'error': f'Failed to analyze salary trends: {str(e)}'}
    
    def generate_career_insights_report(self, db: Session, user_id: int) -> Dict:
        """Generate comprehensive career insights and progression analysis"""
        try:
            # Get user's complete job search history
            all_applications = db.query(JobApplication, Job).join(Job).filter(
                JobApplication.user_id == user_id
            ).order_by(JobApplication.applied_at.desc()).all()
            
            if not all_applications:
                return {'error': 'No application history available for career insights'}
            
            # Analyze career trajectory
            career_trajectory = self._analyze_career_trajectory(all_applications)
            
            # Skill evolution analysis
            skill_evolution = self._analyze_skill_evolution(all_applications)
            
            # Industry focus analysis
            industry_focus = self._analyze_industry_focus(all_applications)
            
            # Company size preferences
            company_preferences = self._analyze_company_size_preferences(all_applications)
            
            # Career velocity metrics
            career_velocity = self._calculate_career_velocity(all_applications)
            
            # Market positioning analysis
            market_positioning = self._analyze_market_positioning(db, user_id, all_applications)
            
            # Career gap analysis
            career_gaps = self._identify_career_gaps(all_applications, skill_evolution)
            
            # Future career path recommendations
            career_path_recommendations = self._generate_career_path_recommendations(
                career_trajectory, skill_evolution, market_positioning
            )
            
            report = {
                'analysis_type': 'career_insights',
                'generated_at': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'career_trajectory': career_trajectory,
                'skill_evolution': skill_evolution,
                'industry_analysis': industry_focus,
                'company_preferences': company_preferences,
                'career_velocity': career_velocity,
                'market_positioning': market_positioning,
                'identified_gaps': career_gaps,
                'career_recommendations': career_path_recommendations,
                'next_steps': self._generate_career_next_steps(
                    career_trajectory, career_gaps, career_path_recommendations
                )
            }
            
            # Save the insights
            self._save_report(db, user_id, 'career_insights_report', report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate career insights: {e}")
            return {'error': f'Failed to generate career insights: {str(e)}'}
    
    # Recommendation Effectiveness Tracking
    
    def track_recommendation_effectiveness(self, db: Session, user_id: int, days: int = 90) -> Dict:
        """Track and analyze recommendation system effectiveness"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get recommendation analytics data
            recommendation_analytics = db.query(Analytics).filter(
                Analytics.user_id == user_id,
                Analytics.type == 'recommendation_performance',
                Analytics.generated_at >= cutoff_date
            ).all()
            
            # Get user applications to correlate with recommendations
            user_applications = db.query(JobApplication, Job).join(Job).filter(
                JobApplication.user_id == user_id,
                JobApplication.applied_at >= cutoff_date
            ).all()
            
            # Calculate recommendation metrics
            recommendation_metrics = self._calculate_recommendation_metrics(
                recommendation_analytics, user_applications
            )
            
            # Analyze recommendation quality over time
            quality_trends = self._analyze_recommendation_quality_trends(recommendation_analytics)
            
            # Calculate conversion rates
            conversion_analysis = self._analyze_recommendation_conversions(
                recommendation_analytics, user_applications
            )
            
            # Analyze recommendation categories performance
            category_performance = self._analyze_recommendation_category_performance(
                recommendation_analytics, user_applications
            )
            
            # User feedback analysis (if available)
            feedback_analysis = self._analyze_recommendation_feedback(db, user_id, days)
            
            # Generate improvement suggestions
            improvement_suggestions = self._generate_recommendation_improvements(
                recommendation_metrics, quality_trends, conversion_analysis
            )
            
            report = {
                'analysis_type': 'recommendation_effectiveness',
                'generated_at': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'analysis_period_days': days,
                'overall_metrics': recommendation_metrics,
                'quality_trends': quality_trends,
                'conversion_analysis': conversion_analysis,
                'category_performance': category_performance,
                'user_feedback': feedback_analysis,
                'effectiveness_score': self._calculate_overall_effectiveness_score(
                    recommendation_metrics, conversion_analysis
                ),
                'improvement_areas': improvement_suggestions,
                'recommendations': self._generate_recommendation_system_recommendations(
                    recommendation_metrics, quality_trends, conversion_analysis
                )
            }
            
            # Save the analysis
            self._save_report(db, user_id, 'recommendation_effectiveness', report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to track recommendation effectiveness: {e}")
            return {'error': f'Failed to track recommendation effectiveness: {str(e)}'}
    
    # Helper Methods for Data Retrieval
    
    def _get_applications_in_period(self, db: Session, user_id: int, start_date, end_date) -> List[Tuple]:
        """Get applications within a specific period"""
        return db.query(JobApplication, Job).join(Job).filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= datetime.combine(start_date, datetime.min.time()),
            JobApplication.applied_at <= datetime.combine(end_date, datetime.max.time())
        ).all()
    
    def _get_jobs_added_in_period(self, db: Session, user_id: int, start_date, end_date) -> List[Job]:
        """Get jobs added to tracker within a specific period"""
        return db.query(Job).filter(
            Job.user_id == user_id,
            Job.date_added >= datetime.combine(start_date, datetime.min.time()),
            Job.date_added <= datetime.combine(end_date, datetime.max.time())
        ).all()
    
    def _get_user_activities_in_period(self, db: Session, user_id: int, start_date, end_date) -> List[Dict]:
        """Get user activities within a specific period"""
        activities = db.query(Analytics).filter(
            Analytics.user_id == user_id,
            Analytics.type == 'user_activity',
            Analytics.generated_at >= datetime.combine(start_date, datetime.min.time()),
            Analytics.generated_at <= datetime.combine(end_date, datetime.max.time())
        ).all()
        
        all_activities = []
        for record in activities:
            activities_data = record.data.get('activities', [])
            all_activities.extend(activities_data)
        
        return all_activities
    
    # Helper Methods for Analysis
    
    def _analyze_status_changes(self, applications: List[Tuple]) -> List[Dict]:
        """Analyze status changes in applications"""
        status_changes = []
        for app, job in applications:
            if app.status != 'applied':
                status_changes.append({
                    'job_title': job.title,
                    'company': job.company,
                    'old_status': 'applied',
                    'new_status': app.status,
                    'change_date': app.updated_at.isoformat() if app.updated_at else None
                })
        return status_changes
    
    def _calculate_weekly_engagement(self, activities: List[Dict]) -> Dict:
        """Calculate weekly engagement metrics"""
        if not activities:
            return {'active_days': 0, 'total_activities': 0, 'avg_daily_activities': 0}
        
        daily_activities = defaultdict(int)
        activity_types = Counter()
        
        for activity in activities:
            date = activity.get('timestamp', '')[:10]  # Get date part
            daily_activities[date] += 1
            activity_types[activity.get('activity_type', 'unknown')] += 1
        
        active_days = len(daily_activities)
        total_activities = len(activities)
        avg_daily = total_activities / max(active_days, 1)
        
        return {
            'active_days': active_days,
            'total_activities': total_activities,
            'avg_daily_activities': round(avg_daily, 1),
            'activity_breakdown': dict(activity_types),
            'engagement_level': 'high' if avg_daily >= 5 else 'medium' if avg_daily >= 2 else 'low'
        }
    
    def _calculate_trend(self, current_value: int, previous_value: int) -> float:
        """Calculate trend percentage change"""
        if previous_value == 0:
            return 100.0 if current_value > 0 else 0.0
        return round(((current_value - previous_value) / previous_value) * 100, 1)
    
    def _generate_weekly_insights(self, applications: int, jobs_added: int, 
                                status_changes: List, engagement: Dict, trend: float) -> List[str]:
        """Generate insights for weekly report"""
        insights = []
        
        if applications == 0:
            insights.append("No applications submitted this week - consider increasing application velocity")
        elif applications >= 5:
            insights.append(f"Strong application activity with {applications} submissions")
        else:
            insights.append(f"Moderate application activity with {applications} submissions")
        
        if trend > 20:
            insights.append(f"Application rate increased by {trend}% compared to last week")
        elif trend < -20:
            insights.append(f"Application rate decreased by {abs(trend)}% compared to last week")
        
        if len(status_changes) > 0:
            insights.append(f"Received {len(status_changes)} status updates - good engagement from employers")
        
        engagement_level = engagement.get('engagement_level', 'low')
        if engagement_level == 'high':
            insights.append("High engagement level - maintaining consistent job search activity")
        elif engagement_level == 'low':
            insights.append("Low engagement level - consider increasing daily job search activities")
        
        return insights
    
    def _get_weekly_goals(self, db: Session, user_id: int, week_start) -> Dict:
        """Get or generate weekly goals"""
        # This would typically come from user preferences or goal-setting system
        # For now, return default goals
        return {
            'applications_target': 5,
            'jobs_to_add': 10,
            'networking_activities': 3,
            'skill_development_hours': 5
        }
    
    def _identify_weekly_achievements(self, applications: int, status_changes: List, 
                                   engagement: Dict) -> List[str]:
        """Identify weekly achievements"""
        achievements = []
        
        if applications >= 5:
            achievements.append("Met weekly application target")
        
        if len(status_changes) > 0:
            achievements.append("Received employer responses")
        
        if engagement.get('active_days', 0) >= 5:
            achievements.append("Maintained daily job search consistency")
        
        if engagement.get('engagement_level') == 'high':
            achievements.append("High engagement in job search activities")
        
        return achievements
    
    def _calculate_goal_completion_rate(self, goals: Dict, achievements: List) -> float:
        """Calculate goal completion rate"""
        if not goals:
            return 0.0
        
        # Simple calculation based on achievements
        completion_score = len(achievements) / max(len(goals), 1)
        return min(completion_score * 100, 100.0)
    
    def _generate_weekly_recommendations(self, applications: int, engagement: Dict, 
                                       status_changes: List) -> List[str]:
        """Generate weekly recommendations"""
        recommendations = []
        
        if applications < 3:
            recommendations.append("Increase application velocity - aim for 5+ applications per week")
        
        if engagement.get('active_days', 0) < 4:
            recommendations.append("Maintain daily job search activities for better momentum")
        
        if len(status_changes) == 0 and applications > 0:
            recommendations.append("Follow up on recent applications after 1-2 weeks")
        
        if engagement.get('engagement_level') == 'low':
            recommendations.append("Set daily job search goals to improve consistency")
        
        return recommendations
    
    def _group_applications_by_status(self, applications: List[Tuple]) -> Dict:
        """Group applications by status"""
        status_groups = defaultdict(int)
        for app, job in applications:
            status_groups[app.status] += 1
        return dict(status_groups)
    
    def _group_applications_by_source(self, applications: List[Tuple]) -> Dict:
        """Group applications by job source"""
        source_groups = defaultdict(int)
        for app, job in applications:
            source_groups[job.source] += 1
        return dict(source_groups)
    
    def _group_applications_by_day(self, applications: List[Tuple]) -> Dict:
        """Group applications by day of week"""
        day_groups = defaultdict(int)
        for app, job in applications:
            if app.applied_at:
                day_name = app.applied_at.strftime('%A')
                day_groups[day_name] += 1
        return dict(day_groups)
    
    def _calculate_monthly_success_metrics(self, applications: List[Tuple]) -> Dict:
        """Calculate monthly success metrics"""
        if not applications:
            return {'error': 'No applications to analyze'}
        
        total_apps = len(applications)
        response_statuses = ['under_review', 'phone_screen_scheduled', 'phone_screen_completed',
                           'interview_scheduled', 'interview_completed', 'final_round',
                           'offer_received', 'offer_accepted']
        interview_statuses = ['phone_screen_scheduled', 'phone_screen_completed',
                            'interview_scheduled', 'interview_completed', 'final_round',
                            'offer_received', 'offer_accepted']
        offer_statuses = ['offer_received', 'offer_accepted']
        
        responses = sum(1 for app, job in applications if app.status in response_statuses)
        interviews = sum(1 for app, job in applications if app.status in interview_statuses)
        offers = sum(1 for app, job in applications if app.status in offer_statuses)
        
        return {
            'total_applications': total_apps,
            'responses_received': responses,
            'interviews_scheduled': interviews,
            'offers_received': offers,
            'response_rate': round(responses / total_apps, 3) if total_apps > 0 else 0,
            'interview_rate': round(interviews / total_apps, 3) if total_apps > 0 else 0,
            'offer_rate': round(offers / total_apps, 3) if total_apps > 0 else 0,
            'conversion_funnel': {
                'application_to_response': f"{(responses/total_apps)*100:.1f}%" if total_apps > 0 else "0%",
                'response_to_interview': f"{(interviews/responses)*100:.1f}%" if responses > 0 else "0%",
                'interview_to_offer': f"{(offers/interviews)*100:.1f}%" if interviews > 0 else "0%"
            }
        }
    
    def _generate_weekly_breakdown(self, db: Session, user_id: int, month_start, month_end) -> List[Dict]:
        """Generate weekly breakdown for monthly report"""
        weekly_data = []
        current_week_start = month_start
        
        while current_week_start <= month_end:
            week_end = min(current_week_start + timedelta(days=6), month_end)
            week_applications = self._get_applications_in_period(db, user_id, current_week_start, week_end)
            
            weekly_data.append({
                'week_start': current_week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'applications': len(week_applications),
                'status_updates': len(self._analyze_status_changes(week_applications))
            })
            
            current_week_start += timedelta(days=7)
        
        return weekly_data
    
    def _calculate_monthly_trends(self, current_apps: int, previous_apps: int, success_metrics: Dict) -> Dict:
        """Calculate monthly trends"""
        app_trend = self._calculate_trend(current_apps, previous_apps)
        
        return {
            'application_trend': {
                'change_percentage': app_trend,
                'direction': 'increasing' if app_trend > 0 else 'decreasing' if app_trend < 0 else 'stable',
                'interpretation': f"Applications {'increased' if app_trend > 0 else 'decreased' if app_trend < 0 else 'remained stable'} by {abs(app_trend):.1f}%"
            },
            'success_rate_trend': {
                'response_rate': success_metrics.get('response_rate', 0),
                'benchmark_comparison': self._compare_to_benchmarks(success_metrics.get('response_rate', 0))
            }
        }
    
    def _analyze_career_progression(self, db: Session, user_id: int, month_start, month_end) -> Dict:
        """Analyze career progression indicators"""
        # Get applications in period
        applications = self._get_applications_in_period(db, user_id, month_start, month_end)
        
        if not applications:
            return {'error': 'No applications to analyze for career progression'}
        
        # Analyze job levels applied to
        job_levels = []
        salary_ranges = []
        companies = []
        
        for app, job in applications:
            # Extract job level from title (simplified)
            title_lower = job.title.lower()
            if any(term in title_lower for term in ['senior', 'sr.', 'lead']):
                job_levels.append('senior')
            elif any(term in title_lower for term in ['junior', 'jr.', 'entry']):
                job_levels.append('junior')
            else:
                job_levels.append('mid')
            
            # Collect salary data
            if job.salary_min and job.salary_max:
                avg_salary = (job.salary_min + job.salary_max) / 2
                salary_ranges.append(avg_salary)
            
            companies.append(job.company)
        
        level_distribution = Counter(job_levels)
        avg_salary = sum(salary_ranges) / len(salary_ranges) if salary_ranges else 0
        
        return {
            'job_level_distribution': dict(level_distribution),
            'average_target_salary': round(avg_salary, 0) if avg_salary > 0 else None,
            'salary_range': {
                'min': min(salary_ranges) if salary_ranges else None,
                'max': max(salary_ranges) if salary_ranges else None
            },
            'company_diversity': len(set(companies)),
            'career_direction': self._determine_career_direction(level_distribution)
        }
    
    def _determine_career_direction(self, level_distribution: Counter) -> str:
        """Determine career direction based on job levels"""
        senior_count = level_distribution.get('senior', 0)
        mid_count = level_distribution.get('mid', 0)
        junior_count = level_distribution.get('junior', 0)
        
        total = senior_count + mid_count + junior_count
        if total == 0:
            return 'unclear'
        
        senior_pct = senior_count / total
        if senior_pct > 0.6:
            return 'advancing_to_senior'
        elif senior_pct > 0.3:
            return 'mixed_levels'
        else:
            return 'current_level_focus'
    
    def _generate_monthly_insights(self, applications: int, success_metrics: Dict, 
                                 career_progression: Dict, trends: Dict) -> List[str]:
        """Generate monthly insights"""
        insights = []
        
        # Application volume insights
        if applications >= 20:
            insights.append(f"High application volume with {applications} submissions")
        elif applications >= 10:
            insights.append(f"Moderate application volume with {applications} submissions")
        else:
            insights.append(f"Low application volume with {applications} submissions - consider increasing activity")
        
        # Success rate insights
        response_rate = success_metrics.get('response_rate', 0)
        if response_rate > 0.25:
            insights.append(f"Strong response rate of {response_rate:.1%} - above industry average")
        elif response_rate > 0.15:
            insights.append(f"Good response rate of {response_rate:.1%} - meeting industry standards")
        else:
            insights.append(f"Response rate of {response_rate:.1%} - room for improvement")
        
        # Career progression insights
        career_direction = career_progression.get('career_direction', 'unclear')
        if career_direction == 'advancing_to_senior':
            insights.append("Focusing on senior-level positions - good career advancement strategy")
        elif career_direction == 'mixed_levels':
            insights.append("Applying to mixed job levels - consider focusing on target level")
        
        # Trend insights
        app_trend = trends.get('application_trend', {}).get('direction', 'stable')
        if app_trend == 'increasing':
            insights.append("Application activity is increasing - maintaining good momentum")
        elif app_trend == 'decreasing':
            insights.append("Application activity is decreasing - consider re-energizing job search")
        
        return insights
    
    def _identify_monthly_achievements(self, applications: int, success_metrics: Dict, 
                                     career_progression: Dict) -> List[str]:
        """Identify monthly achievements"""
        achievements = []
        
        if applications >= 15:
            achievements.append("Maintained high application volume")
        
        response_rate = success_metrics.get('response_rate', 0)
        if response_rate > 0.2:
            achievements.append("Achieved strong employer response rate")
        
        interview_rate = success_metrics.get('interview_rate', 0)
        if interview_rate > 0.1:
            achievements.append("Successfully converted applications to interviews")
        
        offers = success_metrics.get('offers_received', 0)
        if offers > 0:
            achievements.append(f"Received {offers} job offer{'s' if offers > 1 else ''}")
        
        company_diversity = career_progression.get('company_diversity', 0)
        if company_diversity >= 10:
            achievements.append("Applied to diverse range of companies")
        
        return achievements
    
    def _assess_monthly_goals(self, db: Session, user_id: int, month_start, month_end) -> Dict:
        """Assess monthly goal achievement"""
        # This would typically integrate with a goal-setting system
        # For now, return default assessment
        return {
            'goals_set': {
                'applications_target': 20,
                'response_rate_target': 0.2,
                'interviews_target': 3
            },
            'achievement_status': 'partial',  # This would be calculated based on actual vs target
            'completion_percentage': 75.0
        }
    
    def _generate_monthly_recommendations(self, applications: int, success_metrics: Dict, 
                                        career_progression: Dict, trends: Dict) -> List[str]:
        """Generate monthly recommendations"""
        recommendations = []
        
        if applications < 15:
            recommendations.append("Increase monthly application target to 15-20 applications")
        
        response_rate = success_metrics.get('response_rate', 0)
        if response_rate < 0.15:
            recommendations.append("Focus on improving resume and application quality")
        
        interview_rate = success_metrics.get('interview_rate', 0)
        if interview_rate < 0.05:
            recommendations.append("Review job targeting strategy and application materials")
        
        career_direction = career_progression.get('career_direction', 'unclear')
        if career_direction == 'unclear':
            recommendations.append("Define clear career level targets for more focused applications")
        
        app_trend = trends.get('application_trend', {}).get('direction', 'stable')
        if app_trend == 'decreasing':
            recommendations.append("Re-energize job search with daily application goals")
        
        return recommendations
    
    def _analyze_company_types(self, applications: List[Tuple]) -> Dict:
        """Analyze types of companies applied to"""
        company_sizes = defaultdict(int)
        industries = defaultdict(int)
        
        for app, job in applications:
            # This would ideally use company data from a database
            # For now, make simple classifications based on company name
            company = job.company.lower()
            
            # Simple heuristics for company size (would be better with actual data)
            if any(term in company for term in ['google', 'microsoft', 'amazon', 'apple', 'meta']):
                company_sizes['large_tech'] += 1
            elif any(term in company for term in ['startup', 'inc.', 'llc']):
                company_sizes['startup'] += 1
            else:
                company_sizes['mid_size'] += 1
            
            # Simple industry classification
            if any(term in company for term in ['tech', 'software', 'data', 'ai']):
                industries['technology'] += 1
            elif any(term in company for term in ['finance', 'bank', 'capital']):
                industries['finance'] += 1
            else:
                industries['other'] += 1
        
        return {
            'company_size_distribution': dict(company_sizes),
            'industry_distribution': dict(industries)
        }
    
    def _analyze_application_timing(self, applications: List[Tuple]) -> Dict:
        """Analyze application timing patterns"""
        day_of_week = defaultdict(int)
        hour_of_day = defaultdict(int)
        
        for app, job in applications:
            if app.applied_at:
                day_name = app.applied_at.strftime('%A')
                hour = app.applied_at.hour
                
                day_of_week[day_name] += 1
                hour_of_day[hour] += 1
        
        # Find peak times
        peak_day = max(day_of_week.items(), key=lambda x: x[1]) if day_of_week else None
        peak_hour = max(hour_of_day.items(), key=lambda x: x[1]) if hour_of_day else None
        
        return {
            'by_day_of_week': dict(day_of_week),
            'by_hour_of_day': dict(hour_of_day),
            'peak_application_day': peak_day[0] if peak_day else None,
            'peak_application_hour': peak_hour[0] if peak_hour else None,
            'timing_insights': self._generate_timing_insights(day_of_week, hour_of_day)
        }
    
    def _generate_timing_insights(self, day_data: Dict, hour_data: Dict) -> List[str]:
        """Generate insights about application timing"""
        insights = []
        
        if day_data:
            weekday_apps = sum(count for day, count in day_data.items() 
                             if day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
            weekend_apps = sum(count for day, count in day_data.items() 
                             if day in ['Saturday', 'Sunday'])
            
            if weekend_apps > weekday_apps * 0.3:
                insights.append("High weekend application activity - good dedication")
            
            peak_day = max(day_data.items(), key=lambda x: x[1])[0]
            insights.append(f"Most active application day: {peak_day}")
        
        if hour_data:
            business_hours = sum(count for hour, count in hour_data.items() if 9 <= hour <= 17)
            total_apps = sum(hour_data.values())
            
            if business_hours / total_apps > 0.7:
                insights.append("Primarily applying during business hours")
            else:
                insights.append("Flexible application timing throughout the day")
        
        return insights
    
    def _compare_to_benchmarks(self, response_rate: float) -> str:
        """Compare response rate to industry benchmarks"""
        if response_rate >= 0.25:
            return "above_average"
        elif response_rate >= 0.15:
            return "average"
        else:
            return "below_average" 
   
    # Salary Analysis Helper Methods
    
    def _analyze_user_salary_targets(self, user_applications: List[Tuple]) -> Dict:
        """Analyze user's salary targets from applications"""
        salary_data = []
        
        for app, job in user_applications:
            if job.salary_min and job.salary_max:
                avg_salary = (job.salary_min + job.salary_max) / 2
                salary_data.append({
                    'salary': avg_salary,
                    'min': job.salary_min,
                    'max': job.salary_max,
                    'job_title': job.title,
                    'company': job.company,
                    'applied_date': app.applied_at.isoformat() if app.applied_at else None
                })
        
        if not salary_data:
            return {'error': 'No salary data available from user applications'}
        
        salaries = [item['salary'] for item in salary_data]
        salaries.sort()
        
        n = len(salaries)
        median_salary = salaries[n // 2] if n % 2 == 1 else (salaries[n // 2 - 1] + salaries[n // 2]) / 2
        
        return {
            'total_applications_with_salary': len(salary_data),
            'salary_statistics': {
                'average': round(sum(salaries) / len(salaries), 0),
                'median': round(median_salary, 0),
                'min': min(salaries),
                'max': max(salaries),
                'range': max(salaries) - min(salaries)
            },
            'salary_progression': self._analyze_salary_progression(salary_data),
            'target_range': {
                'lower_bound': round(median_salary * 0.9, 0),
                'upper_bound': round(median_salary * 1.1, 0)
            }
        }
    
    def _analyze_market_salary_trends(self, market_jobs: List[Job], days: int) -> Dict:
        """Analyze market salary trends"""
        salary_data = []
        
        for job in market_jobs:
            if job.salary_min and job.salary_max:
                avg_salary = (job.salary_min + job.salary_max) / 2
                salary_data.append({
                    'salary': avg_salary,
                    'date_posted': job.date_added,
                    'title': job.title,
                    'location': job.location,
                    'company': job.company
                })
        
        # Calculate overall market statistics
        salaries = [item['salary'] for item in salary_data]
        salaries.sort()
        
        n = len(salaries)
        median_salary = salaries[n // 2] if n % 2 == 1 else (salaries[n // 2 - 1] + salaries[n // 2]) / 2
        
        # Analyze trends over time
        time_trends = self._analyze_salary_time_trends(salary_data, days)
        
        # Analyze by job title patterns
        title_analysis = self._analyze_salary_by_title_patterns(salary_data)
        
        return {
            'market_statistics': {
                'total_jobs_analyzed': len(salary_data),
                'average_salary': round(sum(salaries) / len(salaries), 0),
                'median_salary': round(median_salary, 0),
                'percentile_25': round(salaries[n // 4], 0),
                'percentile_75': round(salaries[3 * n // 4], 0),
                'salary_range': max(salaries) - min(salaries)
            },
            'time_trends': time_trends,
            'title_analysis': title_analysis,
            'growth_indicators': self._calculate_salary_growth_indicators(time_trends)
        }
    
    def _analyze_salary_progression(self, salary_data: List[Dict]) -> Dict:
        """Analyze salary progression over time"""
        if len(salary_data) < 2:
            return {'insufficient_data': True}
        
        # Sort by application date
        sorted_data = sorted(salary_data, key=lambda x: x.get('applied_date', ''))
        
        first_half = sorted_data[:len(sorted_data)//2]
        second_half = sorted_data[len(sorted_data)//2:]
        
        first_avg = sum(item['salary'] for item in first_half) / len(first_half)
        second_avg = sum(item['salary'] for item in second_half) / len(second_half)
        
        progression_rate = ((second_avg - first_avg) / first_avg) * 100 if first_avg > 0 else 0
        
        return {
            'early_period_avg': round(first_avg, 0),
            'recent_period_avg': round(second_avg, 0),
            'progression_rate': round(progression_rate, 1),
            'trend': 'increasing' if progression_rate > 5 else 'decreasing' if progression_rate < -5 else 'stable'
        }
    
    def _analyze_salary_time_trends(self, salary_data: List[Dict], days: int) -> Dict:
        """Analyze salary trends over time"""
        # Group by time periods
        cutoff_date = datetime.utcnow() - timedelta(days=days//2)
        
        recent_salaries = [item['salary'] for item in salary_data 
                          if item['date_posted'] and item['date_posted'] >= cutoff_date]
        earlier_salaries = [item['salary'] for item in salary_data 
                           if item['date_posted'] and item['date_posted'] < cutoff_date]
        
        if not recent_salaries or not earlier_salaries:
            return {'insufficient_data': True}
        
        recent_avg = sum(recent_salaries) / len(recent_salaries)
        earlier_avg = sum(earlier_salaries) / len(earlier_salaries)
        
        growth_rate = ((recent_avg - earlier_avg) / earlier_avg) * 100 if earlier_avg > 0 else 0
        
        return {
            'recent_period_avg': round(recent_avg, 0),
            'earlier_period_avg': round(earlier_avg, 0),
            'growth_rate': round(growth_rate, 1),
            'trend_direction': 'increasing' if growth_rate > 2 else 'decreasing' if growth_rate < -2 else 'stable'
        }
    
    def _analyze_salary_by_title_patterns(self, salary_data: List[Dict]) -> Dict:
        """Analyze salary by job title patterns"""
        title_salaries = defaultdict(list)
        
        for item in salary_data:
            title_lower = item['title'].lower()
            
            # Categorize by seniority level
            if any(term in title_lower for term in ['senior', 'sr.', 'lead', 'principal']):
                title_salaries['senior_level'].append(item['salary'])
            elif any(term in title_lower for term in ['junior', 'jr.', 'entry', 'associate']):
                title_salaries['junior_level'].append(item['salary'])
            else:
                title_salaries['mid_level'].append(item['salary'])
            
            # Categorize by role type
            if any(term in title_lower for term in ['engineer', 'developer', 'programmer']):
                title_salaries['engineering'].append(item['salary'])
            elif any(term in title_lower for term in ['manager', 'director', 'lead']):
                title_salaries['management'].append(item['salary'])
            elif any(term in title_lower for term in ['data', 'analyst', 'scientist']):
                title_salaries['data_roles'].append(item['salary'])
        
        # Calculate averages for each category
        title_analysis = {}
        for category, salaries in title_salaries.items():
            if len(salaries) >= 3:  # Only include categories with sufficient data
                title_analysis[category] = {
                    'count': len(salaries),
                    'average': round(sum(salaries) / len(salaries), 0),
                    'median': round(sorted(salaries)[len(salaries) // 2], 0),
                    'range': {
                        'min': min(salaries),
                        'max': max(salaries)
                    }
                }
        
        return title_analysis
    
    def _calculate_salary_growth_indicators(self, time_trends: Dict) -> Dict:
        """Calculate salary growth indicators"""
        if 'insufficient_data' in time_trends:
            return {'insufficient_data': True}
        
        growth_rate = time_trends.get('growth_rate', 0)
        
        return {
            'annual_growth_projection': round(growth_rate * 2, 1),  # Extrapolate to annual
            'market_health': 'strong' if growth_rate > 5 else 'moderate' if growth_rate > 0 else 'declining',
            'salary_momentum': 'positive' if growth_rate > 2 else 'negative' if growth_rate < -2 else 'stable'
        }
    
    def _generate_career_salary_insights(self, user_analysis: Dict, market_analysis: Dict, user_id: int) -> List[str]:
        """Generate career salary insights"""
        insights = []
        
        if 'error' in user_analysis or 'error' in market_analysis:
            return ['Insufficient data for salary insights']
        
        user_avg = user_analysis.get('salary_statistics', {}).get('average', 0)
        market_avg = market_analysis.get('market_statistics', {}).get('average', 0)
        
        if user_avg and market_avg:
            if user_avg > market_avg * 1.1:
                insights.append(f"Your target salary (${user_avg:,.0f}) is above market average (${market_avg:,.0f})")
            elif user_avg < market_avg * 0.9:
                insights.append(f"Your target salary (${user_avg:,.0f}) is below market average (${market_avg:,.0f})")
            else:
                insights.append(f"Your target salary (${user_avg:,.0f}) aligns well with market average (${market_avg:,.0f})")
        
        # Market growth insights
        growth_indicators = market_analysis.get('growth_indicators', {})
        market_health = growth_indicators.get('market_health', 'unknown')
        
        if market_health == 'strong':
            insights.append("Strong salary growth in the market - good time for negotiations")
        elif market_health == 'declining':
            insights.append("Market showing salary decline - consider focusing on other benefits")
        
        # User progression insights
        user_progression = user_analysis.get('salary_progression', {})
        if not user_progression.get('insufficient_data'):
            trend = user_progression.get('trend', 'stable')
            if trend == 'increasing':
                insights.append("Your salary targets are increasing over time - showing career growth ambition")
            elif trend == 'decreasing':
                insights.append("Your salary targets are decreasing - consider if this aligns with your career goals")
        
        return insights
    
    def _generate_salary_negotiation_insights(self, user_analysis: Dict, market_analysis: Dict) -> Dict:
        """Generate salary negotiation insights"""
        if 'error' in user_analysis or 'error' in market_analysis:
            return {'error': 'Insufficient data for negotiation insights'}
        
        user_stats = user_analysis.get('salary_statistics', {})
        market_stats = market_analysis.get('market_statistics', {})
        
        negotiation_range = {
            'conservative': round(market_stats.get('percentile_25', 0), 0),
            'target': round(market_stats.get('median_salary', 0), 0),
            'aggressive': round(market_stats.get('percentile_75', 0), 0)
        }
        
        user_target = user_stats.get('median', 0)
        market_median = market_stats.get('median_salary', 0)
        
        negotiation_position = 'strong' if user_target <= market_median else 'moderate'
        
        return {
            'negotiation_range': negotiation_range,
            'your_position': negotiation_position,
            'market_leverage': self._assess_market_leverage(market_analysis),
            'negotiation_tips': self._generate_negotiation_tips(negotiation_position, market_analysis)
        }
    
    def _assess_market_leverage(self, market_analysis: Dict) -> str:
        """Assess market leverage for negotiations"""
        growth_indicators = market_analysis.get('growth_indicators', {})
        market_health = growth_indicators.get('market_health', 'moderate')
        
        if market_health == 'strong':
            return 'high'
        elif market_health == 'declining':
            return 'low'
        else:
            return 'moderate'
    
    def _generate_negotiation_tips(self, position: str, market_analysis: Dict) -> List[str]:
        """Generate salary negotiation tips"""
        tips = []
        
        if position == 'strong':
            tips.append("Your salary expectations are reasonable - negotiate confidently")
            tips.append("Use market data to support your salary requests")
        else:
            tips.append("Consider negotiating total compensation package, not just base salary")
            tips.append("Focus on demonstrating unique value you bring to the role")
        
        growth_indicators = market_analysis.get('growth_indicators', {})
        if growth_indicators.get('market_health') == 'strong':
            tips.append("Strong market conditions favor salary negotiations")
        
        tips.append("Research company-specific salary ranges before negotiations")
        tips.append("Consider timing - negotiate after demonstrating value")
        
        return tips
    
    def _analyze_geographic_salary_trends(self, market_jobs: List[Job]) -> Dict:
        """Analyze salary trends by geographic location"""
        location_salaries = defaultdict(list)
        
        for job in market_jobs:
            if job.salary_min and job.salary_max and job.location:
                avg_salary = (job.salary_min + job.salary_max) / 2
                
                # Normalize location (simplified)
                location = job.location.split(',')[0].strip()  # Get city part
                if 'remote' in location.lower():
                    location = 'Remote'
                
                location_salaries[location].append(avg_salary)
        
        # Calculate statistics for each location
        location_analysis = {}
        for location, salaries in location_salaries.items():
            if len(salaries) >= 3:  # Only include locations with sufficient data
                location_analysis[location] = {
                    'count': len(salaries),
                    'average': round(sum(salaries) / len(salaries), 0),
                    'median': round(sorted(salaries)[len(salaries) // 2], 0),
                    'range': {
                        'min': min(salaries),
                        'max': max(salaries)
                    }
                }
        
        # Sort by average salary
        sorted_locations = dict(sorted(location_analysis.items(), 
                                     key=lambda x: x[1]['average'], reverse=True))
        
        return {
            'by_location': sorted_locations,
            'top_paying_locations': list(sorted_locations.keys())[:5],
            'location_insights': self._generate_location_salary_insights(sorted_locations)
        }
    
    def _generate_location_salary_insights(self, location_data: Dict) -> List[str]:
        """Generate insights about location-based salary differences"""
        insights = []
        
        if not location_data:
            return ['Insufficient location data for analysis']
        
        locations = list(location_data.items())
        if len(locations) >= 2:
            highest = locations[0]
            lowest = locations[-1]
            
            salary_diff = highest[1]['average'] - lowest[1]['average']
            diff_percentage = (salary_diff / lowest[1]['average']) * 100
            
            insights.append(f"Highest paying location: {highest[0]} (${highest[1]['average']:,.0f})")
            insights.append(f"Salary difference between top and bottom locations: {diff_percentage:.1f}%")
        
        # Check for remote work salary data
        if 'Remote' in location_data:
            remote_avg = location_data['Remote']['average']
            all_averages = [data['average'] for data in location_data.values() if data != location_data['Remote']]
            
            if all_averages:
                market_avg = sum(all_averages) / len(all_averages)
                if remote_avg > market_avg:
                    insights.append("Remote positions offer competitive salaries")
                else:
                    insights.append("Remote positions may have lower salary ranges")
        
        return insights
    
    def _analyze_industry_salary_trends(self, market_jobs: List[Job]) -> Dict:
        """Analyze salary trends by industry"""
        # This is a simplified implementation - would be better with actual industry data
        industry_salaries = defaultdict(list)
        
        for job in market_jobs:
            if job.salary_min and job.salary_max:
                avg_salary = (job.salary_min + job.salary_max) / 2
                
                # Simple industry classification based on company name/title
                company_lower = job.company.lower()
                title_lower = job.title.lower()
                
                if any(term in company_lower or term in title_lower for term in ['tech', 'software', 'ai', 'data']):
                    industry_salaries['technology'].append(avg_salary)
                elif any(term in company_lower or term in title_lower for term in ['finance', 'bank', 'capital']):
                    industry_salaries['finance'].append(avg_salary)
                elif any(term in company_lower or term in title_lower for term in ['health', 'medical', 'pharma']):
                    industry_salaries['healthcare'].append(avg_salary)
                else:
                    industry_salaries['other'].append(avg_salary)
        
        # Calculate statistics for each industry
        industry_analysis = {}
        for industry, salaries in industry_salaries.items():
            if len(salaries) >= 3:
                industry_analysis[industry] = {
                    'count': len(salaries),
                    'average': round(sum(salaries) / len(salaries), 0),
                    'median': round(sorted(salaries)[len(salaries) // 2], 0),
                    'growth_potential': self._assess_industry_growth_potential(industry)
                }
        
        return {
            'by_industry': dict(sorted(industry_analysis.items(), 
                                     key=lambda x: x[1]['average'], reverse=True)),
            'industry_insights': self._generate_industry_salary_insights(industry_analysis)
        }
    
    def _assess_industry_growth_potential(self, industry: str) -> str:
        """Assess growth potential for industry (simplified)"""
        high_growth = ['technology', 'healthcare', 'ai', 'data']
        moderate_growth = ['finance', 'consulting']
        
        if industry in high_growth:
            return 'high'
        elif industry in moderate_growth:
            return 'moderate'
        else:
            return 'stable'
    
    def _generate_industry_salary_insights(self, industry_data: Dict) -> List[str]:
        """Generate insights about industry salary differences"""
        insights = []
        
        if not industry_data:
            return ['Insufficient industry data for analysis']
        
        industries = list(industry_data.items())
        if len(industries) >= 2:
            highest = industries[0]
            insights.append(f"Highest paying industry: {highest[0].title()} (${highest[1]['average']:,.0f})")
        
        # Growth potential insights
        high_growth_industries = [name for name, data in industry_data.items() 
                                if data.get('growth_potential') == 'high']
        
        if high_growth_industries:
            insights.append(f"High growth potential industries: {', '.join(high_growth_industries)}")
        
        return insights
    
    def _generate_salary_growth_projections(self, user_analysis: Dict, market_analysis: Dict) -> Dict:
        """Generate salary growth projections"""
        if 'error' in user_analysis or 'error' in market_analysis:
            return {'error': 'Insufficient data for projections'}
        
        current_target = user_analysis.get('salary_statistics', {}).get('median', 0)
        market_growth = market_analysis.get('growth_indicators', {}).get('annual_growth_projection', 0)
        
        if not current_target or not market_growth:
            return {'error': 'Insufficient data for projections'}
        
        projections = {}
        for years in [1, 3, 5]:
            projected_salary = current_target * ((1 + market_growth / 100) ** years)
            projections[f'{years}_year'] = round(projected_salary, 0)
        
        return {
            'current_target': round(current_target, 0),
            'market_growth_rate': market_growth,
            'projections': projections,
            'assumptions': [
                f"Based on {market_growth:.1f}% annual market growth rate",
                "Assumes consistent career progression",
                "Market conditions may vary"
            ]
        }
    
    def _generate_salary_recommendations(self, user_analysis: Dict, market_analysis: Dict, 
                                       career_insights: List[str]) -> List[str]:
        """Generate salary-related recommendations"""
        recommendations = []
        
        if 'error' in user_analysis or 'error' in market_analysis:
            return ['Gather more salary data from job applications for better analysis']
        
        user_avg = user_analysis.get('salary_statistics', {}).get('average', 0)
        market_avg = market_analysis.get('market_statistics', {}).get('average', 0)
        
        if user_avg and market_avg:
            if user_avg < market_avg * 0.9:
                recommendations.append("Consider increasing salary expectations to match market rates")
            elif user_avg > market_avg * 1.2:
                recommendations.append("Your salary expectations may be above market - ensure you can justify the premium")
        
        growth_indicators = market_analysis.get('growth_indicators', {})
        if growth_indicators.get('market_health') == 'strong':
            recommendations.append("Strong market conditions - good time for salary negotiations")
        
        recommendations.append("Research company-specific salary ranges before applying")
        recommendations.append("Consider total compensation package, not just base salary")
        recommendations.append("Track salary trends in your target roles and locations")
        
        return recommendations    

    # Career Insights Helper Methods
    
    def _analyze_career_trajectory(self, applications: List[Tuple]) -> Dict:
        """Analyze career trajectory from application history"""
        if not applications:
            return {'error': 'No application history available'}
        
        # Sort applications by date
        sorted_apps = sorted(applications, key=lambda x: x[0].applied_at or datetime.min)
        
        # Analyze job level progression
        job_levels = []
        salary_progression = []
        
        for app, job in sorted_apps:
            # Extract job level
            title_lower = job.title.lower()
            if any(term in title_lower for term in ['senior', 'sr.', 'lead', 'principal']):
                job_levels.append('senior')
            elif any(term in title_lower for term in ['junior', 'jr.', 'entry', 'associate']):
                job_levels.append('junior')
            else:
                job_levels.append('mid')
            
            # Track salary if available
            if job.salary_min and job.salary_max:
                avg_salary = (job.salary_min + job.salary_max) / 2
                salary_progression.append({
                    'date': app.applied_at.isoformat() if app.applied_at else None,
                    'salary': avg_salary
                })
        
        # Analyze progression patterns
        level_progression = self._analyze_level_progression(job_levels)
        salary_trend = self._analyze_salary_trend_progression(salary_progression)
        
        return {
            'total_applications': len(applications),
            'time_span': self._calculate_application_timespan(sorted_apps),
            'level_progression': level_progression,
            'salary_progression': salary_trend,
            'career_direction': self._determine_overall_career_direction(level_progression, salary_trend),
            'progression_insights': self._generate_progression_insights(level_progression, salary_trend)
        }
    
    def _analyze_skill_evolution(self, applications: List[Tuple]) -> Dict:
        """Analyze skill evolution from job requirements"""
        skill_timeline = []
        all_skills = set()
        
        for app, job in applications:
            if job.requirements and isinstance(job.requirements, dict):
                skills = job.requirements.get('skills_required', [])
                if skills and app.applied_at:
                    skill_timeline.append({
                        'date': app.applied_at.isoformat(),
                        'skills': skills,
                        'job_title': job.title
                    })
                    all_skills.update(skills)
        
        if not skill_timeline:
            return {'error': 'No skill data available from job requirements'}
        
        # Sort by date
        skill_timeline.sort(key=lambda x: x['date'])
        
        # Analyze skill frequency over time
        skill_evolution = self._track_skill_frequency_evolution(skill_timeline)
        
        # Identify emerging and declining skills
        emerging_skills = self._identify_emerging_skills_in_timeline(skill_timeline)
        declining_skills = self._identify_declining_skills_in_timeline(skill_timeline)
        
        return {
            'total_unique_skills': len(all_skills),
            'skill_timeline': skill_timeline[-10:],  # Last 10 for brevity
            'skill_evolution': skill_evolution,
            'emerging_skills': emerging_skills,
            'declining_skills': declining_skills,
            'skill_diversity_trend': self._calculate_skill_diversity_trend(skill_timeline)
        }
    
    def _analyze_industry_focus(self, applications: List[Tuple]) -> Dict:
        """Analyze industry focus from applications"""
        industry_timeline = []
        
        for app, job in applications:
            # Simple industry classification
            company_lower = job.company.lower()
            title_lower = job.title.lower()
            
            industry = 'other'
            if any(term in company_lower or term in title_lower for term in ['tech', 'software', 'ai']):
                industry = 'technology'
            elif any(term in company_lower or term in title_lower for term in ['finance', 'bank']):
                industry = 'finance'
            elif any(term in company_lower or term in title_lower for term in ['health', 'medical']):
                industry = 'healthcare'
            elif any(term in company_lower or term in title_lower for term in ['retail', 'ecommerce']):
                industry = 'retail'
            
            if app.applied_at:
                industry_timeline.append({
                    'date': app.applied_at.isoformat(),
                    'industry': industry,
                    'company': job.company
                })
        
        # Analyze industry distribution
        industry_counts = Counter(item['industry'] for item in industry_timeline)
        
        # Analyze industry focus over time
        industry_focus_trend = self._analyze_industry_focus_trend(industry_timeline)
        
        return {
            'industry_distribution': dict(industry_counts),
            'primary_industry': industry_counts.most_common(1)[0][0] if industry_counts else 'unknown',
            'industry_diversity': len(industry_counts),
            'focus_trend': industry_focus_trend,
            'industry_insights': self._generate_industry_focus_insights(industry_counts, industry_focus_trend)
        }
    
    def _analyze_company_size_preferences(self, applications: List[Tuple]) -> Dict:
        """Analyze company size preferences"""
        company_sizes = []
        
        for app, job in applications:
            # Simple heuristics for company size (would be better with actual data)
            company_lower = job.company.lower()
            
            if any(term in company_lower for term in ['google', 'microsoft', 'amazon', 'apple', 'meta', 'netflix']):
                size = 'large_tech'
            elif any(term in company_lower for term in ['startup', 'inc.', 'llc']) or len(job.company.split()) <= 2:
                size = 'startup'
            else:
                size = 'mid_size'
            
            company_sizes.append(size)
        
        size_distribution = Counter(company_sizes)
        
        return {
            'size_distribution': dict(size_distribution),
            'preferred_size': size_distribution.most_common(1)[0][0] if size_distribution else 'unknown',
            'size_diversity': len(size_distribution),
            'size_insights': self._generate_company_size_insights(size_distribution)
        }
    
    def _calculate_career_velocity(self, applications: List[Tuple]) -> Dict:
        """Calculate career velocity metrics"""
        if not applications:
            return {'error': 'No applications to analyze'}
        
        # Sort by date
        sorted_apps = sorted(applications, key=lambda x: x[0].applied_at or datetime.min)
        
        if len(sorted_apps) < 2:
            return {'insufficient_data': True}
        
        # Calculate time span
        first_app = sorted_apps[0][0].applied_at
        last_app = sorted_apps[-1][0].applied_at
        
        if not first_app or not last_app:
            return {'insufficient_data': True}
        
        time_span_days = (last_app - first_app).days
        
        # Calculate application velocity
        total_apps = len(applications)
        apps_per_week = (total_apps / max(time_span_days, 1)) * 7
        
        # Calculate response velocity (simplified)
        responses = sum(1 for app, job in applications if app.status != 'applied')
        response_rate = responses / total_apps if total_apps > 0 else 0
        
        return {
            'time_span_days': time_span_days,
            'total_applications': total_apps,
            'applications_per_week': round(apps_per_week, 1),
            'response_rate': round(response_rate, 3),
            'velocity_assessment': self._assess_career_velocity(apps_per_week, response_rate)
        }
    
    def _analyze_market_positioning(self, db: Session, user_id: int, applications: List[Tuple]) -> Dict:
        """Analyze user's market positioning"""
        if not applications:
            return {'error': 'No applications to analyze'}
        
        # Get user's skill profile (simplified - would integrate with user profile)
        user_skills = set()
        user_salary_targets = []
        
        for app, job in applications:
            if job.requirements and isinstance(job.requirements, dict):
                skills = job.requirements.get('skills_required', [])
                user_skills.update(skills)
            
            if job.salary_min and job.salary_max:
                avg_salary = (job.salary_min + job.salary_max) / 2
                user_salary_targets.append(avg_salary)
        
        # Compare with market (simplified analysis)
        market_positioning = {
            'skill_breadth': len(user_skills),
            'salary_positioning': self._analyze_salary_positioning(user_salary_targets),
            'application_diversity': self._analyze_application_diversity(applications),
            'market_competitiveness': self._assess_market_competitiveness(user_skills, user_salary_targets)
        }
        
        return market_positioning
    
    def _identify_career_gaps(self, applications: List[Tuple], skill_evolution: Dict) -> Dict:
        """Identify career gaps and improvement areas"""
        gaps = {
            'skill_gaps': [],
            'experience_gaps': [],
            'industry_gaps': [],
            'recommendations': []
        }
        
        # Analyze skill gaps
        if 'error' not in skill_evolution:
            declining_skills = skill_evolution.get('declining_skills', [])
            if declining_skills:
                gaps['skill_gaps'] = declining_skills[:5]  # Top 5 declining skills
        
        # Analyze experience level gaps
        job_levels = []
        for app, job in applications:
            title_lower = job.title.lower()
            if any(term in title_lower for term in ['senior', 'sr.', 'lead']):
                job_levels.append('senior')
            elif any(term in title_lower for term in ['junior', 'jr.', 'entry']):
                job_levels.append('junior')
            else:
                job_levels.append('mid')
        
        level_distribution = Counter(job_levels)
        if level_distribution.get('senior', 0) > level_distribution.get('mid', 0) * 2:
            gaps['experience_gaps'].append('May be targeting roles above current experience level')
        
        # Generate recommendations based on gaps
        if gaps['skill_gaps']:
            gaps['recommendations'].append('Focus on developing declining skills or pivot to emerging technologies')
        
        if gaps['experience_gaps']:
            gaps['recommendations'].append('Consider building experience in current level before advancing')
        
        return gaps
    
    def _generate_career_path_recommendations(self, trajectory: Dict, skill_evolution: Dict, 
                                            market_positioning: Dict) -> List[str]:
        """Generate career path recommendations"""
        recommendations = []
        
        # Based on trajectory
        if 'error' not in trajectory:
            career_direction = trajectory.get('career_direction', 'unclear')
            if career_direction == 'advancing':
                recommendations.append('Continue focusing on senior-level positions for career advancement')
            elif career_direction == 'lateral':
                recommendations.append('Consider targeting higher-level roles for career progression')
        
        # Based on skill evolution
        if 'error' not in skill_evolution:
            emerging_skills = skill_evolution.get('emerging_skills', [])
            if emerging_skills:
                top_emerging = emerging_skills[0] if emerging_skills else None
                if top_emerging:
                    recommendations.append(f'Develop expertise in {top_emerging} - showing strong market demand')
        
        # Based on market positioning
        competitiveness = market_positioning.get('market_competitiveness', 'unknown')
        if competitiveness == 'low':
            recommendations.append('Focus on skill development and experience building to improve market position')
        elif competitiveness == 'high':
            recommendations.append('Leverage your strong market position for better opportunities')
        
        # General recommendations
        recommendations.append('Maintain consistent application activity for better market visibility')
        recommendations.append('Network within your target industry and role level')
        
        return recommendations
    
    def _generate_career_next_steps(self, trajectory: Dict, gaps: Dict, 
                                  recommendations: List[str]) -> List[str]:
        """Generate specific next steps for career development"""
        next_steps = []
        
        # Based on identified gaps
        skill_gaps = gaps.get('skill_gaps', [])
        if skill_gaps:
            next_steps.append(f'Prioritize learning: {", ".join(skill_gaps[:3])}')
        
        experience_gaps = gaps.get('experience_gaps', [])
        if experience_gaps:
            next_steps.append('Seek projects or roles that build missing experience')
        
        # Based on trajectory
        if 'error' not in trajectory:
            career_direction = trajectory.get('career_direction', 'unclear')
            if career_direction == 'unclear':
                next_steps.append('Define clear career level and role targets')
        
        # Actionable steps
        next_steps.extend([
            'Update resume to highlight relevant skills and achievements',
            'Set weekly application and networking goals',
            'Research target companies and roles thoroughly',
            'Prepare for technical interviews in your target skills'
        ])
        
        return next_steps[:6]  # Limit to top 6 actionable steps    

    # Recommendation Effectiveness Tracking Helper Methods
    
    def _calculate_recommendation_metrics(self, recommendation_analytics: List[Analytics], 
                                        user_applications: List[Tuple]) -> Dict:
        """Calculate recommendation system metrics"""
        if not recommendation_analytics:
            return {'error': 'No recommendation analytics data available'}
        
        total_recommendations_shown = 0
        total_clicks = 0
        total_applications_from_recommendations = 0
        
        for analytics in recommendation_analytics:
            data = analytics.data
            total_recommendations_shown += data.get('recommendations_shown', 0)
            total_clicks += data.get('recommendations_clicked', 0)
            total_applications_from_recommendations += data.get('recommendations_applied', 0)
        
        # Calculate rates
        click_through_rate = total_clicks / total_recommendations_shown if total_recommendations_shown > 0 else 0
        application_rate = total_applications_from_recommendations / total_recommendations_shown if total_recommendations_shown > 0 else 0
        conversion_rate = total_applications_from_recommendations / total_clicks if total_clicks > 0 else 0
        
        return {
            'total_recommendations_shown': total_recommendations_shown,
            'total_clicks': total_clicks,
            'total_applications': total_applications_from_recommendations,
            'click_through_rate': round(click_through_rate, 3),
            'application_rate': round(application_rate, 3),
            'conversion_rate': round(conversion_rate, 3),
            'engagement_level': self._assess_recommendation_engagement(click_through_rate, application_rate)
        }
    
    def _analyze_recommendation_quality_trends(self, recommendation_analytics: List[Analytics]) -> Dict:
        """Analyze recommendation quality trends over time"""
        if not recommendation_analytics:
            return {'error': 'No analytics data for trend analysis'}
        
        # Sort by date
        sorted_analytics = sorted(recommendation_analytics, key=lambda x: x.generated_at)
        
        quality_timeline = []
        for analytics in sorted_analytics:
            data = analytics.data
            avg_score = data.get('avg_recommendation_score', 0)
            quality_timeline.append({
                'date': analytics.generated_at.isoformat(),
                'avg_score': avg_score,
                'recommendations_count': data.get('recommendations_shown', 0)
            })
        
        # Calculate trend
        if len(quality_timeline) >= 2:
            recent_scores = [item['avg_score'] for item in quality_timeline[-5:]]  # Last 5 data points
            earlier_scores = [item['avg_score'] for item in quality_timeline[:5]]   # First 5 data points
            
            recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
            earlier_avg = sum(earlier_scores) / len(earlier_scores) if earlier_scores else 0
            
            trend_direction = 'improving' if recent_avg > earlier_avg else 'declining' if recent_avg < earlier_avg else 'stable'
        else:
            trend_direction = 'insufficient_data'
        
        return {
            'quality_timeline': quality_timeline,
            'trend_direction': trend_direction,
            'current_avg_quality': quality_timeline[-1]['avg_score'] if quality_timeline else 0,
            'quality_insights': self._generate_quality_insights(quality_timeline, trend_direction)
        }
    
    def _analyze_recommendation_conversions(self, recommendation_analytics: List[Analytics], 
                                          user_applications: List[Tuple]) -> Dict:
        """Analyze recommendation to application conversions"""
        conversion_data = []
        
        for analytics in recommendation_analytics:
            data = analytics.data
            date = analytics.generated_at.date()
            
            # Find applications on the same day (simplified correlation)
            same_day_applications = [
                app for app, job in user_applications 
                if app.applied_at and app.applied_at.date() == date
            ]
            
            conversion_data.append({
                'date': date.isoformat(),
                'recommendations_shown': data.get('recommendations_shown', 0),
                'applications_same_day': len(same_day_applications),
                'estimated_conversion': min(len(same_day_applications), data.get('recommendations_shown', 0))
            })
        
        # Calculate overall conversion metrics
        total_recommendations = sum(item['recommendations_shown'] for item in conversion_data)
        total_conversions = sum(item['estimated_conversion'] for item in conversion_data)
        
        overall_conversion_rate = total_conversions / total_recommendations if total_recommendations > 0 else 0
        
        return {
            'conversion_timeline': conversion_data,
            'overall_conversion_rate': round(overall_conversion_rate, 3),
            'total_estimated_conversions': total_conversions,
            'conversion_insights': self._generate_conversion_insights(conversion_data, overall_conversion_rate)
        }
    
    def _analyze_recommendation_category_performance(self, recommendation_analytics: List[Analytics], 
                                                   user_applications: List[Tuple]) -> Dict:
        """Analyze performance by recommendation category"""
        category_performance = defaultdict(lambda: {
            'shown': 0, 'clicked': 0, 'applied': 0
        })
        
        for analytics in recommendation_analytics:
            data = analytics.data
            categories = data.get('recommendation_categories', {})
            
            for category, metrics in categories.items():
                category_performance[category]['shown'] += metrics.get('shown', 0)
                category_performance[category]['clicked'] += metrics.get('clicked', 0)
                category_performance[category]['applied'] += metrics.get('applied', 0)
        
        # Calculate rates for each category
        category_analysis = {}
        for category, metrics in category_performance.items():
            shown = metrics['shown']
            clicked = metrics['clicked']
            applied = metrics['applied']
            
            category_analysis[category] = {
                'total_shown': shown,
                'total_clicked': clicked,
                'total_applied': applied,
                'click_rate': round(clicked / shown, 3) if shown > 0 else 0,
                'application_rate': round(applied / shown, 3) if shown > 0 else 0,
                'performance_score': self._calculate_category_performance_score(shown, clicked, applied)
            }
        
        # Sort by performance score
        sorted_categories = dict(sorted(category_analysis.items(), 
                                      key=lambda x: x[1]['performance_score'], reverse=True))
        
        return {
            'by_category': sorted_categories,
            'best_performing_category': list(sorted_categories.keys())[0] if sorted_categories else None,
            'category_insights': self._generate_category_insights(sorted_categories)
        }
    
    def _analyze_recommendation_feedback(self, db: Session, user_id: int, days: int) -> Dict:
        """Analyze user feedback on recommendations"""
        # This would integrate with a feedback system
        # For now, return placeholder structure
        return {
            'feedback_available': False,
            'total_feedback_items': 0,
            'average_rating': 0,
            'feedback_insights': ['No feedback system implemented yet']
        }
    
    def _generate_recommendation_improvements(self, metrics: Dict, quality_trends: Dict, 
                                           conversion_analysis: Dict) -> List[str]:
        """Generate improvement suggestions for recommendation system"""
        improvements = []
        
        # Based on metrics
        if 'error' not in metrics:
            ctr = metrics.get('click_through_rate', 0)
            if ctr < 0.3:
                improvements.append('Improve recommendation relevance to increase click-through rate')
            
            app_rate = metrics.get('application_rate', 0)
            if app_rate < 0.1:
                improvements.append('Enhance job matching algorithm to increase application rate')
        
        # Based on quality trends
        if 'error' not in quality_trends:
            trend = quality_trends.get('trend_direction', 'stable')
            if trend == 'declining':
                improvements.append('Review recommendation algorithm - quality scores are declining')
        
        # Based on conversion analysis
        if 'error' not in conversion_analysis:
            conversion_rate = conversion_analysis.get('overall_conversion_rate', 0)
            if conversion_rate < 0.15:
                improvements.append('Optimize recommendation timing and presentation')
        
        # General improvements
        improvements.extend([
            'Implement user feedback collection for recommendations',
            'A/B test different recommendation presentation formats',
            'Personalize recommendations based on user behavior patterns'
        ])
        
        return improvements
    
    def _calculate_overall_effectiveness_score(self, metrics: Dict, conversion_analysis: Dict) -> float:
        """Calculate overall recommendation effectiveness score"""
        if 'error' in metrics or 'error' in conversion_analysis:
            return 0.0
        
        # Weight different factors
        ctr_score = min(metrics.get('click_through_rate', 0) * 100, 100) * 0.3
        app_rate_score = min(metrics.get('application_rate', 0) * 100, 100) * 0.4
        conversion_score = min(conversion_analysis.get('overall_conversion_rate', 0) * 100, 100) * 0.3
        
        overall_score = ctr_score + app_rate_score + conversion_score
        return round(overall_score, 1)
    
    def _generate_recommendation_system_recommendations(self, metrics: Dict, quality_trends: Dict, 
                                                      conversion_analysis: Dict) -> List[str]:
        """Generate recommendations for improving the recommendation system"""
        recommendations = []
        
        effectiveness_score = self._calculate_overall_effectiveness_score(metrics, conversion_analysis)
        
        if effectiveness_score < 30:
            recommendations.append('Recommendation system needs significant improvement')
            recommendations.append('Review core matching algorithms and user profiling')
        elif effectiveness_score < 60:
            recommendations.append('Recommendation system shows moderate effectiveness')
            recommendations.append('Focus on improving user engagement and conversion rates')
        else:
            recommendations.append('Recommendation system performing well')
            recommendations.append('Continue optimizing and consider advanced personalization')
        
        # Specific recommendations based on metrics
        if 'error' not in metrics:
            if metrics.get('click_through_rate', 0) < 0.2:
                recommendations.append('Improve recommendation titles and descriptions')
            
            if metrics.get('application_rate', 0) < 0.05:
                recommendations.append('Better match user skills and preferences')
        
        return recommendations
    
    # Additional Helper Methods
    
    def _assess_recommendation_engagement(self, ctr: float, app_rate: float) -> str:
        """Assess recommendation engagement level"""
        if ctr > 0.4 and app_rate > 0.15:
            return 'high'
        elif ctr > 0.2 and app_rate > 0.08:
            return 'moderate'
        else:
            return 'low'
    
    def _generate_quality_insights(self, timeline: List[Dict], trend: str) -> List[str]:
        """Generate insights about recommendation quality"""
        insights = []
        
        if not timeline:
            return ['No quality data available']
        
        current_quality = timeline[-1]['avg_score'] if timeline else 0
        
        if current_quality > 0.8:
            insights.append('High quality recommendations - users receiving well-matched jobs')
        elif current_quality > 0.6:
            insights.append('Moderate quality recommendations - room for improvement')
        else:
            insights.append('Low quality recommendations - algorithm needs optimization')
        
        if trend == 'improving':
            insights.append('Recommendation quality is improving over time')
        elif trend == 'declining':
            insights.append('Recommendation quality is declining - needs attention')
        
        return insights
    
    def _generate_conversion_insights(self, conversion_data: List[Dict], overall_rate: float) -> List[str]:
        """Generate insights about recommendation conversions"""
        insights = []
        
        if overall_rate > 0.2:
            insights.append('Strong conversion rate from recommendations to applications')
        elif overall_rate > 0.1:
            insights.append('Moderate conversion rate - opportunities for improvement')
        else:
            insights.append('Low conversion rate - recommendations may not be compelling enough')
        
        if conversion_data:
            # Analyze conversion patterns
            recent_conversions = conversion_data[-5:] if len(conversion_data) >= 5 else conversion_data
            avg_recent_conversion = sum(item['estimated_conversion'] for item in recent_conversions) / len(recent_conversions)
            
            if avg_recent_conversion > 2:
                insights.append('Recent recommendation performance is strong')
            else:
                insights.append('Recent recommendation performance could be improved')
        
        return insights
    
    def _calculate_category_performance_score(self, shown: int, clicked: int, applied: int) -> float:
        """Calculate performance score for recommendation category"""
        if shown == 0:
            return 0.0
        
        click_rate = clicked / shown
        app_rate = applied / shown
        
        # Weight application rate higher than click rate
        score = (click_rate * 0.3) + (app_rate * 0.7)
        return round(score, 3)
    
    def _generate_category_insights(self, category_analysis: Dict) -> List[str]:
        """Generate insights about category performance"""
        insights = []
        
        if not category_analysis:
            return ['No category data available']
        
        categories = list(category_analysis.items())
        if categories:
            best_category = categories[0]
            insights.append(f'Best performing category: {best_category[0]} (score: {best_category[1]["performance_score"]:.3f})')
            
            if len(categories) > 1:
                worst_category = categories[-1]
                insights.append(f'Lowest performing category: {worst_category[0]} (score: {worst_category[1]["performance_score"]:.3f})')
        
        # Analyze click vs application rates
        high_click_low_app = [
            name for name, data in category_analysis.items()
            if data['click_rate'] > 0.3 and data['application_rate'] < 0.1
        ]
        
        if high_click_low_app:
            insights.append(f'Categories with high interest but low applications: {", ".join(high_click_low_app)}')
        
        return insights
    
    # Utility method for saving reports
    
    def _save_report(self, db: Session, user_id: int, report_type: str, report_data: Dict) -> bool:
        """Save report to analytics table"""
        try:
            analytics = Analytics(
                user_id=user_id,
                type=report_type,
                data=report_data
            )
            db.add(analytics)
            db.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
            db.rollback()
            return False


    # Additional Helper Methods for Career Analysis
    
    def _analyze_level_progression(self, job_levels: List[str]) -> Dict:
        """Analyze job level progression patterns"""
        if not job_levels:
            return {'error': 'No job level data'}
        
        level_counts = Counter(job_levels)
        
        # Analyze progression trend
        if len(job_levels) >= 3:
            recent_levels = job_levels[-len(job_levels)//2:]  # Recent half
            earlier_levels = job_levels[:len(job_levels)//2]  # Earlier half
            
            recent_senior = recent_levels.count('senior')
            earlier_senior = earlier_levels.count('senior')
            
            if recent_senior > earlier_senior:
                progression_trend = 'advancing'
            elif recent_senior < earlier_senior:
                progression_trend = 'declining'
            else:
                progression_trend = 'stable'
        else:
            progression_trend = 'insufficient_data'
        
        return {
            'level_distribution': dict(level_counts),
            'primary_level': level_counts.most_common(1)[0][0] if level_counts else 'unknown',
            'progression_trend': progression_trend,
            'level_diversity': len(level_counts)
        }
    
    def _analyze_salary_trend_progression(self, salary_progression: List[Dict]) -> Dict:
        """Analyze salary trend in progression"""
        if len(salary_progression) < 2:
            return {'insufficient_data': True}
        
        # Sort by date
        sorted_salaries = sorted(salary_progression, key=lambda x: x['date'] or '')
        
        salaries = [item['salary'] for item in sorted_salaries]
        
        # Calculate trend
        first_half_avg = sum(salaries[:len(salaries)//2]) / (len(salaries)//2)
        second_half_avg = sum(salaries[len(salaries)//2:]) / (len(salaries) - len(salaries)//2)
        
        trend_percentage = ((second_half_avg - first_half_avg) / first_half_avg) * 100 if first_half_avg > 0 else 0
        
        return {
            'salary_range': {'min': min(salaries), 'max': max(salaries)},
            'average_salary': round(sum(salaries) / len(salaries), 0),
            'trend_percentage': round(trend_percentage, 1),
            'trend_direction': 'increasing' if trend_percentage > 5 else 'decreasing' if trend_percentage < -5 else 'stable'
        }
    
    def _determine_overall_career_direction(self, level_progression: Dict, salary_trend: Dict) -> str:
        """Determine overall career direction"""
        level_trend = level_progression.get('progression_trend', 'stable')
        salary_direction = salary_trend.get('trend_direction', 'stable') if 'insufficient_data' not in salary_trend else 'unknown'
        
        if level_trend == 'advancing' and salary_direction == 'increasing':
            return 'strong_advancement'
        elif level_trend == 'advancing' or salary_direction == 'increasing':
            return 'moderate_advancement'
        elif level_trend == 'declining' or salary_direction == 'decreasing':
            return 'concerning_trend'
        else:
            return 'stable_career'
    
    def _generate_progression_insights(self, level_progression: Dict, salary_trend: Dict) -> List[str]:
        """Generate career progression insights"""
        insights = []
        
        # Level progression insights
        level_trend = level_progression.get('progression_trend', 'stable')
        if level_trend == 'advancing':
            insights.append('Targeting increasingly senior positions - good career advancement')
        elif level_trend == 'declining':
            insights.append('Recent applications target lower-level positions - consider career strategy')
        
        primary_level = level_progression.get('primary_level', 'unknown')
        if primary_level != 'unknown':
            insights.append(f'Primarily targeting {primary_level}-level positions')
        
        # Salary progression insights
        if 'insufficient_data' not in salary_trend:
            salary_direction = salary_trend.get('trend_direction', 'stable')
            trend_pct = salary_trend.get('trend_percentage', 0)
            
            if salary_direction == 'increasing':
                insights.append(f'Salary expectations increasing by {trend_pct}% - showing growth ambition')
            elif salary_direction == 'decreasing':
                insights.append(f'Salary expectations decreasing by {abs(trend_pct)}% - may indicate market adjustment')
        
        return insights
    
    def _calculate_application_timespan(self, sorted_applications: List[Tuple]) -> Dict:
        """Calculate timespan of application history"""
        if not sorted_applications:
            return {'error': 'No applications'}
        
        first_app = sorted_applications[0][0].applied_at
        last_app = sorted_applications[-1][0].applied_at
        
        if not first_app or not last_app:
            return {'error': 'Missing application dates'}
        
        timespan_days = (last_app - first_app).days
        
        return {
            'start_date': first_app.isoformat(),
            'end_date': last_app.isoformat(),
            'total_days': timespan_days,
            'total_weeks': round(timespan_days / 7, 1),
            'total_months': round(timespan_days / 30, 1)
        }
    
    def _track_skill_frequency_evolution(self, skill_timeline: List[Dict]) -> Dict:
        """Track how skill frequency evolves over time"""
        if len(skill_timeline) < 2:
            return {'insufficient_data': True}
        
        # Split timeline into periods
        mid_point = len(skill_timeline) // 2
        early_period = skill_timeline[:mid_point]
        recent_period = skill_timeline[mid_point:]
        
        # Count skill frequencies in each period
        early_skills = Counter()
        recent_skills = Counter()
        
        for entry in early_period:
            early_skills.update(entry['skills'])
        
        for entry in recent_period:
            recent_skills.update(entry['skills'])
        
        # Analyze changes
        skill_changes = {}
        all_skills = set(early_skills.keys()) | set(recent_skills.keys())
        
        for skill in all_skills:
            early_count = early_skills.get(skill, 0)
            recent_count = recent_skills.get(skill, 0)
            
            if early_count == 0:
                change_type = 'new'
            elif recent_count == 0:
                change_type = 'dropped'
            elif recent_count > early_count:
                change_type = 'increasing'
            elif recent_count < early_count:
                change_type = 'decreasing'
            else:
                change_type = 'stable'
            
            skill_changes[skill] = {
                'early_frequency': early_count,
                'recent_frequency': recent_count,
                'change_type': change_type
            }
        
        return {
            'skill_changes': skill_changes,
            'evolution_summary': self._summarize_skill_evolution(skill_changes)
        }
    
    def _identify_emerging_skills_in_timeline(self, skill_timeline: List[Dict]) -> List[str]:
        """Identify skills that are emerging in recent applications"""
        if len(skill_timeline) < 3:
            return []
        
        # Look at recent third of timeline
        recent_cutoff = len(skill_timeline) * 2 // 3
        recent_entries = skill_timeline[recent_cutoff:]
        earlier_entries = skill_timeline[:recent_cutoff]
        
        recent_skills = Counter()
        earlier_skills = Counter()
        
        for entry in recent_entries:
            recent_skills.update(entry['skills'])
        
        for entry in earlier_entries:
            earlier_skills.update(entry['skills'])
        
        # Find skills that appear more frequently in recent period
        emerging = []
        for skill, recent_count in recent_skills.items():
            earlier_count = earlier_skills.get(skill, 0)
            if recent_count > earlier_count and recent_count >= 2:
                emerging.append(skill)
        
        return emerging[:5]  # Top 5 emerging skills
    
    def _identify_declining_skills_in_timeline(self, skill_timeline: List[Dict]) -> List[str]:
        """Identify skills that are declining in recent applications"""
        if len(skill_timeline) < 3:
            return []
        
        # Look at recent third of timeline
        recent_cutoff = len(skill_timeline) * 2 // 3
        recent_entries = skill_timeline[recent_cutoff:]
        earlier_entries = skill_timeline[:recent_cutoff]
        
        recent_skills = Counter()
        earlier_skills = Counter()
        
        for entry in recent_entries:
            recent_skills.update(entry['skills'])
        
        for entry in earlier_entries:
            earlier_skills.update(entry['skills'])
        
        # Find skills that appear less frequently in recent period
        declining = []
        for skill, earlier_count in earlier_skills.items():
            recent_count = recent_skills.get(skill, 0)
            if earlier_count > recent_count and earlier_count >= 2:
                declining.append(skill)
        
        return declining[:5]  # Top 5 declining skills
    
    def _calculate_skill_diversity_trend(self, skill_timeline: List[Dict]) -> Dict:
        """Calculate skill diversity trend over time"""
        if len(skill_timeline) < 2:
            return {'insufficient_data': True}
        
        # Calculate diversity for each time period
        diversity_over_time = []
        
        for entry in skill_timeline:
            unique_skills = len(set(entry['skills']))
            diversity_over_time.append({
                'date': entry['date'],
                'skill_count': unique_skills
            })
        
        # Calculate trend
        if len(diversity_over_time) >= 2:
            early_avg = sum(item['skill_count'] for item in diversity_over_time[:len(diversity_over_time)//2]) / (len(diversity_over_time)//2)
            recent_avg = sum(item['skill_count'] for item in diversity_over_time[len(diversity_over_time)//2:]) / (len(diversity_over_time) - len(diversity_over_time)//2)
            
            trend = 'increasing' if recent_avg > early_avg else 'decreasing' if recent_avg < early_avg else 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'diversity_timeline': diversity_over_time,
            'trend': trend,
            'current_diversity': diversity_over_time[-1]['skill_count'] if diversity_over_time else 0
        }
    
    def _analyze_industry_focus_trend(self, industry_timeline: List[Dict]) -> Dict:
        """Analyze industry focus trend over time"""
        if len(industry_timeline) < 2:
            return {'insufficient_data': True}
        
        # Split into periods
        mid_point = len(industry_timeline) // 2
        early_period = industry_timeline[:mid_point]
        recent_period = industry_timeline[mid_point:]
        
        early_industries = Counter(entry['industry'] for entry in early_period)
        recent_industries = Counter(entry['industry'] for entry in recent_period)
        
        # Calculate focus change
        early_primary = early_industries.most_common(1)[0][0] if early_industries else 'unknown'
        recent_primary = recent_industries.most_common(1)[0][0] if recent_industries else 'unknown'
        
        focus_change = 'shifted' if early_primary != recent_primary else 'consistent'
        
        return {
            'early_primary_industry': early_primary,
            'recent_primary_industry': recent_primary,
            'focus_change': focus_change,
            'industry_diversity_early': len(early_industries),
            'industry_diversity_recent': len(recent_industries)
        }
    
    def _generate_industry_focus_insights(self, industry_counts: Counter, focus_trend: Dict) -> List[str]:
        """Generate insights about industry focus"""
        insights = []
        
        if not industry_counts:
            return ['No industry data available']
        
        primary_industry = industry_counts.most_common(1)[0][0]
        primary_count = industry_counts.most_common(1)[0][1]
        total_apps = sum(industry_counts.values())
        
        focus_percentage = (primary_count / total_apps) * 100
        
        if focus_percentage > 70:
            insights.append(f'Highly focused on {primary_industry} industry ({focus_percentage:.1f}% of applications)')
        elif focus_percentage > 50:
            insights.append(f'Primarily targeting {primary_industry} industry ({focus_percentage:.1f}% of applications)')
        else:
            insights.append(f'Diversified industry targeting with {primary_industry} as primary focus')
        
        if 'insufficient_data' not in focus_trend:
            focus_change = focus_trend.get('focus_change', 'unknown')
            if focus_change == 'shifted':
                early_industry = focus_trend.get('early_primary_industry', 'unknown')
                recent_industry = focus_trend.get('recent_primary_industry', 'unknown')
                insights.append(f'Industry focus shifted from {early_industry} to {recent_industry}')
            elif focus_change == 'consistent':
                insights.append('Maintaining consistent industry focus over time')
        
        return insights
    
    def _generate_company_size_insights(self, size_distribution: Counter) -> List[str]:
        """Generate insights about company size preferences"""
        insights = []
        
        if not size_distribution:
            return ['No company size data available']
        
        preferred_size = size_distribution.most_common(1)[0][0]
        preferred_count = size_distribution.most_common(1)[0][1]
        total_apps = sum(size_distribution.values())
        
        preference_percentage = (preferred_count / total_apps) * 100
        
        size_names = {
            'large_tech': 'large technology companies',
            'startup': 'startups and small companies',
            'mid_size': 'mid-size companies'
        }
        
        size_name = size_names.get(preferred_size, preferred_size)
        insights.append(f'Primarily targeting {size_name} ({preference_percentage:.1f}% of applications)')
        
        if len(size_distribution) > 1:
            insights.append(f'Applying to {len(size_distribution)} different company size categories')
        else:
            insights.append('Focused on single company size category - consider diversifying')
        
        return insights
    
    def _assess_career_velocity(self, apps_per_week: float, response_rate: float) -> str:
        """Assess career search velocity"""
        if apps_per_week >= 5 and response_rate >= 0.2:
            return 'high_velocity'
        elif apps_per_week >= 3 and response_rate >= 0.15:
            return 'moderate_velocity'
        elif apps_per_week >= 1:
            return 'low_velocity'
        else:
            return 'very_low_velocity'
    
    def _analyze_salary_positioning(self, salary_targets: List[float]) -> Dict:
        """Analyze salary positioning"""
        if not salary_targets:
            return {'error': 'No salary data'}
        
        avg_target = sum(salary_targets) / len(salary_targets)
        salary_range = max(salary_targets) - min(salary_targets)
        
        return {
            'average_target': round(avg_target, 0),
            'salary_range': round(salary_range, 0),
            'consistency': 'high' if salary_range < avg_target * 0.2 else 'moderate' if salary_range < avg_target * 0.5 else 'low'
        }
    
    def _analyze_application_diversity(self, applications: List[Tuple]) -> Dict:
        """Analyze diversity of applications"""
        companies = set()
        industries = set()
        locations = set()
        
        for app, job in applications:
            companies.add(job.company)
            locations.add(job.location)
            
            # Simple industry classification
            company_lower = job.company.lower()
            if any(term in company_lower for term in ['tech', 'software']):
                industries.add('technology')
            elif any(term in company_lower for term in ['finance', 'bank']):
                industries.add('finance')
            else:
                industries.add('other')
        
        return {
            'company_diversity': len(companies),
            'industry_diversity': len(industries),
            'location_diversity': len(locations),
            'overall_diversity_score': (len(companies) + len(industries) + len(locations)) / 3
        }
    
    def _assess_market_competitiveness(self, skills: set, salary_targets: List[float]) -> str:
        """Assess market competitiveness"""
        skill_breadth = len(skills)
        avg_salary = sum(salary_targets) / len(salary_targets) if salary_targets else 0
        
        # Simple heuristic assessment
        if skill_breadth >= 10 and avg_salary >= 100000:
            return 'high'
        elif skill_breadth >= 5 and avg_salary >= 70000:
            return 'moderate'
        else:
            return 'low'
    
    def _summarize_skill_evolution(self, skill_changes: Dict) -> Dict:
        """Summarize skill evolution patterns"""
        change_types = Counter()
        
        for skill, data in skill_changes.items():
            change_types[data['change_type']] += 1
        
        return {
            'total_skills_tracked': len(skill_changes),
            'new_skills': change_types.get('new', 0),
            'dropped_skills': change_types.get('dropped', 0),
            'increasing_skills': change_types.get('increasing', 0),
            'decreasing_skills': change_types.get('decreasing', 0),
            'stable_skills': change_types.get('stable', 0)
        }


# Global service instance
reporting_insights_service = ReportingInsightsService()