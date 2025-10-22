"""
Advanced User Analytics Service
Provides detailed analytics for user performance tracking and benchmarking
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case
from collections import defaultdict, Counter
import statistics
import numpy as np

from app.models.user import User
from app.models.job import Job
from app.models.application import Application


class AdvancedUserAnalyticsService:
    """Service for advanced user analytics and performance tracking"""
    
    def __init__(self):
        # Market benchmarks (would be calculated from aggregate data in production)
        self.market_benchmarks = {
            'application_to_interview_rate': 15.0,  # 15% of applications lead to interviews
            'interview_to_offer_rate': 25.0,       # 25% of interviews lead to offers
            'overall_success_rate': 3.75,          # 3.75% of applications lead to offers
            'average_time_to_interview': 14,       # 14 days from application to interview
            'average_time_to_offer': 30,           # 30 days from application to offer
            'applications_per_week': 10,           # Average applications per week
            'job_search_duration': 90              # Average job search duration in days
        }
    
    def calculate_detailed_success_rates(self, db: Session, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Calculate detailed application success rates with temporal analysis"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all applications within the timeframe
        applications = db.query(Application).filter(
            Application.user_id == user_id,
            Application.created_at >= cutoff_date
        ).all()
        
        if not applications:
            return {'error': 'No applications found for analysis'}
        
        # Calculate basic success rates
        total_applications = len(applications)
        interviews = len([app for app in applications if app.status == 'interview'])
        offers = len([app for app in applications if app.status in ['offer', 'accepted']])
        rejections = len([app for app in applications if app.status == 'rejected'])
        pending = len([app for app in applications if app.status in ['interested', 'applied']])
        
        # Calculate rates
        application_to_interview_rate = (interviews / total_applications * 100) if total_applications > 0 else 0
        interview_to_offer_rate = (offers / interviews * 100) if interviews > 0 else 0
        overall_success_rate = (offers / total_applications * 100) if total_applications > 0 else 0
        rejection_rate = (rejections / total_applications * 100) if total_applications > 0 else 0
        
        # Temporal analysis - weekly breakdown
        weekly_performance = defaultdict(lambda: {
            'applications': 0, 'interviews': 0, 'offers': 0, 'rejections': 0
        })
        
        for app in applications:
            week_key = app.created_at.strftime('%Y-W%U')
            weekly_performance[week_key]['applications'] += 1
            
            if app.status == 'interview':
                weekly_performance[week_key]['interviews'] += 1
            elif app.status in ['offer', 'accepted']:
                weekly_performance[week_key]['offers'] += 1
            elif app.status == 'rejected':
                weekly_performance[week_key]['rejections'] += 1
        
        # Calculate weekly success rates
        weekly_success_rates = []
        for week, data in sorted(weekly_performance.items()):
            if data['applications'] > 0:
                week_interview_rate = (data['interviews'] / data['applications'] * 100)
                week_success_rate = (data['offers'] / data['applications'] * 100)
                weekly_success_rates.append({
                    'week': week,
                    'applications': data['applications'],
                    'interview_rate': round(week_interview_rate, 1),
                    'success_rate': round(week_success_rate, 1),
                    'offers': data['offers'],
                    'rejections': data['rejections']
                })
        
        # Calculate trends
        if len(weekly_success_rates) >= 4:
            recent_weeks = weekly_success_rates[-4:]
            early_weeks = weekly_success_rates[:4]
            
            recent_avg_interview_rate = sum(w['interview_rate'] for w in recent_weeks) / len(recent_weeks)
            early_avg_interview_rate = sum(w['interview_rate'] for w in early_weeks) / len(early_weeks)
            
            interview_rate_trend = recent_avg_interview_rate - early_avg_interview_rate
        else:
            interview_rate_trend = 0
        
        # Industry and company analysis
        industry_performance = self._analyze_performance_by_industry(db, applications)
        company_performance = self._analyze_performance_by_company(db, applications)
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'analysis_period_days': days,
            'total_applications': total_applications,
            'success_rates': {
                'application_to_interview': round(application_to_interview_rate, 2),
                'interview_to_offer': round(interview_to_offer_rate, 2),
                'overall_success': round(overall_success_rate, 2),
                'rejection_rate': round(rejection_rate, 2)
            },
            'status_breakdown': {
                'pending': pending,
                'interviews': interviews,
                'offers': offers,
                'rejections': rejections
            },
            'weekly_performance': weekly_success_rates,
            'trends': {
                'interview_rate_trend': round(interview_rate_trend, 2),
                'trend_direction': 'improving' if interview_rate_trend > 2 else 'declining' if interview_rate_trend < -2 else 'stable'
            },
            'industry_performance': industry_performance,
            'company_performance': company_performance
        }
    
    def analyze_conversion_funnel(self, db: Session, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Analyze the job application conversion funnel with detailed metrics"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        applications = db.query(Application).filter(
            Application.user_id == user_id,
            Application.created_at >= cutoff_date
        ).all()
        
        if not applications:
            return {'error': 'No applications found for funnel analysis'}
        
        # Define funnel stages
        funnel_stages = [
            {
                'stage': 'Applications Submitted',
                'count': len(applications),
                'conversion_rate': 100.0,
                'description': 'Total job applications submitted'
            },
            {
                'stage': 'Initial Screening',
                'count': len([app for app in applications if app.status not in ['interested']]),
                'description': 'Applications that progressed beyond initial interest'
            },
            {
                'stage': 'Interviews Scheduled',
                'count': len([app for app in applications if app.status == 'interview']),
                'description': 'Applications that resulted in interviews'
            },
            {
                'stage': 'Offers Received',
                'count': len([app for app in applications if app.status in ['offer', 'accepted']]),
                'description': 'Applications that resulted in job offers'
            },
            {
                'stage': 'Offers Accepted',
                'count': len([app for app in applications if app.status == 'accepted']),
                'description': 'Job offers that were accepted'
            }
        ]
        
        # Calculate conversion rates for each stage
        total_applications = len(applications)
        for i, stage in enumerate(funnel_stages):
            if i > 0:  # Skip first stage (already 100%)
                stage['conversion_rate'] = round((stage['count'] / total_applications * 100), 2)
            
            # Calculate stage-to-stage conversion
            if i > 0:
                previous_count = funnel_stages[i-1]['count']
                stage['stage_conversion_rate'] = round((stage['count'] / previous_count * 100), 2) if previous_count > 0 else 0
            else:
                stage['stage_conversion_rate'] = 100.0
        
        # Calculate average time in each stage
        stage_durations = self._calculate_stage_durations(applications)
        
        # Add duration data to funnel stages
        for stage in funnel_stages:
            stage_name = stage['stage'].lower().replace(' ', '_')
            stage['average_duration_days'] = stage_durations.get(stage_name, 0)
        
        # Identify bottlenecks
        bottlenecks = []
        for i in range(1, len(funnel_stages)):
            if funnel_stages[i]['stage_conversion_rate'] < 20:  # Less than 20% conversion
                bottlenecks.append({
                    'stage': funnel_stages[i]['stage'],
                    'conversion_rate': funnel_stages[i]['stage_conversion_rate'],
                    'improvement_potential': 'high'
                })
        
        # Success factors analysis
        success_factors = self._analyze_success_factors(db, applications)
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'analysis_period_days': days,
            'funnel_stages': funnel_stages,
            'bottlenecks': bottlenecks,
            'success_factors': success_factors,
            'overall_metrics': {
                'total_applications': total_applications,
                'funnel_efficiency': round(funnel_stages[-1]['conversion_rate'], 2),
                'average_time_to_offer': stage_durations.get('total_time_to_offer', 0)
            }
        }
    
    def generate_performance_benchmarks(self, db: Session, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Generate performance benchmarks comparing user to market averages"""
        success_rates = self.calculate_detailed_success_rates(db, user_id, days)
        
        if 'error' in success_rates:
            return success_rates
        
        user_metrics = success_rates['success_rates']
        
        # Calculate percentile rankings
        benchmarks = []
        
        for metric, user_value in user_metrics.items():
            if metric in ['application_to_interview', 'interview_to_offer', 'overall_success']:
                market_key = f"{metric.replace('_', '_to_')}_rate" if 'to' in metric else f"{metric}_rate"
                market_average = self.market_benchmarks.get(market_key, 0)
                
                # Calculate percentile rank (simplified)
                if user_value > market_average * 1.5:
                    percentile_rank = 90
                    category = 'excellent'
                elif user_value > market_average * 1.2:
                    percentile_rank = 75
                    category = 'above_average'
                elif user_value > market_average * 0.8:
                    percentile_rank = 50
                    category = 'average'
                else:
                    percentile_rank = 25
                    category = 'below_average'
                
                benchmarks.append({
                    'metric': metric.replace('_', ' ').title(),
                    'user_value': user_value,
                    'market_average': market_average,
                    'percentile_rank': percentile_rank,
                    'category': category,
                    'improvement_potential': market_average - user_value if user_value < market_average else 0
                })
        
        # Activity benchmarks
        total_applications = success_rates['total_applications']
        applications_per_week = total_applications / (days / 7)
        market_applications_per_week = self.market_benchmarks['applications_per_week']
        
        activity_category = 'high' if applications_per_week > market_applications_per_week * 1.2 else \
                           'average' if applications_per_week > market_applications_per_week * 0.8 else 'low'
        
        benchmarks.append({
            'metric': 'Application Activity',
            'user_value': round(applications_per_week, 1),
            'market_average': market_applications_per_week,
            'percentile_rank': 75 if activity_category == 'high' else 50 if activity_category == 'average' else 25,
            'category': activity_category,
            'improvement_potential': max(0, market_applications_per_week - applications_per_week)
        })
        
        # Generate insights and recommendations
        insights = self._generate_performance_insights(benchmarks, success_rates)
        recommendations = self._generate_performance_recommendations(benchmarks, success_rates)
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'user_id': user_id,
            'analysis_period_days': days,
            'benchmarks': benchmarks,
            'overall_performance_score': round(sum(b['percentile_rank'] for b in benchmarks) / len(benchmarks), 1),
            'insights': insights,
            'recommendations': recommendations,
            'market_position': self._calculate_market_position(benchmarks)
        }
    
    def create_predictive_analytics(self, db: Session, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Create predictive analytics for job search success"""
        success_rates = self.calculate_detailed_success_rates(db, user_id, days)
        
        if 'error' in success_rates:
            return success_rates
        
        # Get user data
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {'error': 'User not found'}
        
        # Calculate success probability based on current performance
        current_success_rate = success_rates['success_rates']['overall_success']
        application_rate = success_rates['success_rates']['application_to_interview']
        
        # Simple predictive model (would be more sophisticated in production)
        base_probability = min(95.0, max(5.0, current_success_rate * 2))
        
        # Adjust based on activity level
        total_applications = success_rates['total_applications']
        if total_applications > 50:
            base_probability += 10
        elif total_applications < 10:
            base_probability -= 15
        
        # Adjust based on trend
        trend_direction = success_rates['trends']['trend_direction']
        if trend_direction == 'improving':
            base_probability += 5
        elif trend_direction == 'declining':
            base_probability -= 5
        
        success_probability = max(5.0, min(95.0, base_probability))
        
        # Estimate time to offer
        if current_success_rate > 0:
            estimated_applications_needed = max(1, int(100 / current_success_rate))
            current_weekly_rate = total_applications / (days / 7)
            weeks_to_offer = estimated_applications_needed / max(1, current_weekly_rate)
            estimated_time_to_offer = int(weeks_to_offer * 7)
        else:
            estimated_time_to_offer = 120  # Default estimate
        
        # Recommended application rate
        target_success_rate = 5.0  # Target 5% success rate
        if current_success_rate > 0:
            recommended_weekly_applications = max(3, int(target_success_rate / current_success_rate * 10))
        else:
            recommended_weekly_applications = 15
        
        # Risk and success factors
        risk_factors = []
        success_factors = []
        
        if total_applications < 20:
            risk_factors.append("Low application volume may limit opportunities")
        if application_rate < 10:
            risk_factors.append("Low interview rate suggests need for application quality improvement")
        if success_rates['success_rates']['rejection_rate'] > 60:
            risk_factors.append("High rejection rate indicates potential skill or targeting issues")
        
        if application_rate > 20:
            success_factors.append("Strong interview conversion rate")
        if total_applications > 30:
            success_factors.append("High application activity increases opportunities")
        if trend_direction == 'improving':
            success_factors.append("Performance trending upward")
        
        # Optimal job types (based on user's successful applications)
        optimal_job_types = self._identify_optimal_job_types(db, user_id)
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'user_id': user_id,
            'analysis_period_days': days,
            'predictive_analytics': {
                'success_probability': round(success_probability, 1),
                'estimated_time_to_offer': estimated_time_to_offer,
                'recommended_application_rate': recommended_weekly_applications,
                'optimal_job_types': optimal_job_types,
                'risk_factors': risk_factors,
                'success_factors': success_factors
            },
            'confidence_level': 'medium',  # Would be calculated based on data quality
            'model_accuracy': 75.0,  # Would be based on historical validation
            'recommendations': [
                f"Apply to {recommended_weekly_applications} jobs per week to optimize success probability",
                f"Focus on {', '.join(optimal_job_types[:3])} roles for best results",
                "Monitor weekly performance trends to adjust strategy"
            ]
        }
    
    # Helper methods
    
    def _analyze_performance_by_industry(self, db: Session, applications: List[Application]) -> Dict[str, Any]:
        """Analyze performance by industry"""
        industry_performance = defaultdict(lambda: {'applications': 0, 'interviews': 0, 'offers': 0})
        
        for app in applications:
            job = db.query(Job).filter(Job.id == app.job_id).first()
            if job:
                # Simple industry classification (would use the market analysis service in production)
                industry = 'technology'  # Simplified for now
                industry_performance[industry]['applications'] += 1
                
                if app.status == 'interview':
                    industry_performance[industry]['interviews'] += 1
                elif app.status in ['offer', 'accepted']:
                    industry_performance[industry]['offers'] += 1
        
        # Calculate rates
        result = {}
        for industry, data in industry_performance.items():
            if data['applications'] > 0:
                result[industry] = {
                    'applications': data['applications'],
                    'interview_rate': round(data['interviews'] / data['applications'] * 100, 1),
                    'success_rate': round(data['offers'] / data['applications'] * 100, 1)
                }
        
        return result
    
    def _analyze_performance_by_company(self, db: Session, applications: List[Application]) -> Dict[str, Any]:
        """Analyze performance by company"""
        company_performance = defaultdict(lambda: {'applications': 0, 'interviews': 0, 'offers': 0})
        
        for app in applications:
            job = db.query(Job).filter(Job.id == app.job_id).first()
            if job:
                company = job.company
                company_performance[company]['applications'] += 1
                
                if app.status == 'interview':
                    company_performance[company]['interviews'] += 1
                elif app.status in ['offer', 'accepted']:
                    company_performance[company]['offers'] += 1
        
        # Return top performing companies
        result = {}
        for company, data in sorted(company_performance.items(), key=lambda x: x[1]['applications'], reverse=True)[:10]:
            if data['applications'] > 0:
                result[company] = {
                    'applications': data['applications'],
                    'interview_rate': round(data['interviews'] / data['applications'] * 100, 1),
                    'success_rate': round(data['offers'] / data['applications'] * 100, 1)
                }
        
        return result
    
    def _calculate_stage_durations(self, applications: List[Application]) -> Dict[str, float]:
        """Calculate average time spent in each stage"""
        durations = {
            'applications_submitted': 0,
            'initial_screening': 7,
            'interviews_scheduled': 14,
            'offers_received': 21,
            'total_time_to_offer': 30
        }
        
        # Would calculate actual durations from application timestamps in production
        return durations
    
    def _analyze_success_factors(self, db: Session, applications: List[Application]) -> List[str]:
        """Analyze factors that contribute to success"""
        success_factors = []
        
        successful_apps = [app for app in applications if app.status in ['offer', 'accepted']]
        
        if len(successful_apps) > 0:
            success_factors.append("Consistent application activity")
            success_factors.append("Targeted job selection")
            success_factors.append("Strong application materials")
        
        return success_factors
    
    def _generate_performance_insights(self, benchmarks: List[Dict], success_rates: Dict) -> List[str]:
        """Generate performance insights based on benchmarks"""
        insights = []
        
        # Find strongest and weakest areas
        best_metric = max(benchmarks, key=lambda x: x['percentile_rank'])
        worst_metric = min(benchmarks, key=lambda x: x['percentile_rank'])
        
        insights.append(f"Strongest performance area: {best_metric['metric']} (top {100-best_metric['percentile_rank']}%)")
        
        if worst_metric['percentile_rank'] < 50:
            insights.append(f"Area for improvement: {worst_metric['metric']} (bottom {worst_metric['percentile_rank']}%)")
        
        # Overall performance assessment
        avg_percentile = sum(b['percentile_rank'] for b in benchmarks) / len(benchmarks)
        if avg_percentile > 70:
            insights.append("Overall performance is above market average")
        elif avg_percentile < 40:
            insights.append("Performance is below market average - focus on improvement strategies")
        else:
            insights.append("Performance is around market average with room for optimization")
        
        return insights
    
    def _generate_performance_recommendations(self, benchmarks: List[Dict], success_rates: Dict) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Find areas with highest improvement potential
        improvement_opportunities = [b for b in benchmarks if b['improvement_potential'] > 0]
        improvement_opportunities.sort(key=lambda x: x['improvement_potential'], reverse=True)
        
        for opportunity in improvement_opportunities[:3]:
            if opportunity['metric'] == 'Application To Interview':
                recommendations.append("Improve application quality and targeting to increase interview rates")
            elif opportunity['metric'] == 'Interview To Offer':
                recommendations.append("Focus on interview preparation and presentation skills")
            elif opportunity['metric'] == 'Application Activity':
                recommendations.append("Increase application volume to create more opportunities")
        
        # General recommendations
        if success_rates['success_rates']['overall_success'] < 3:
            recommendations.append("Consider expanding job search criteria or improving skill set")
        
        return recommendations
    
    def _calculate_market_position(self, benchmarks: List[Dict]) -> str:
        """Calculate overall market position"""
        avg_percentile = sum(b['percentile_rank'] for b in benchmarks) / len(benchmarks)
        
        if avg_percentile >= 75:
            return 'top_performer'
        elif avg_percentile >= 50:
            return 'above_average'
        elif avg_percentile >= 25:
            return 'average'
        else:
            return 'needs_improvement'
    
    def _identify_optimal_job_types(self, db: Session, user_id: int) -> List[str]:
        """Identify optimal job types based on user's successful applications"""
        # Get successful applications
        successful_apps = db.query(Application).filter(
            Application.user_id == user_id,
            Application.status.in_(['offer', 'accepted'])
        ).all()
        
        job_types = []
        for app in successful_apps:
            job = db.query(Job).filter(Job.id == app.job_id).first()
            if job:
                job_types.append(job.title)
        
        # Return most common successful job types
        if job_types:
            job_type_counts = Counter(job_types)
            return [job_type for job_type, _ in job_type_counts.most_common(5)]
        else:
            # Default recommendations based on user skills
            return ['Software Engineer', 'Data Analyst', 'Product Manager']


# Create service instance
advanced_user_analytics_service = AdvancedUserAnalyticsService()