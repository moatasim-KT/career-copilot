"""
Application success tracking and optimization service
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case

from app.models.user import User
from app.models.job import Job
from app.models.application import JobApplication, APPLICATION_STATUSES
from app.models.analytics import Analytics


class ApplicationAnalyticsService:
    """Service for tracking application success and optimization"""
    
    def calculate_conversion_rates(self, db: Session, user_id: int, days: int = 90) -> Dict:
        """Calculate application-to-interview conversion rates by category"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get applications in the period with job details
        applications = db.query(JobApplication, Job).join(Job).filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= cutoff_date
        ).all()
        
        if not applications:
            return {'error': 'No applications found in the specified period'}
        
        # Define status progression stages
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
        
        # Overall statistics
        total_applications = len(applications)
        responses = sum(1 for app, job in applications if app.status in response_statuses)
        interviews = sum(1 for app, job in applications if app.status in interview_statuses)
        offers = sum(1 for app, job in applications if app.status in offer_statuses)
        
        # Calculate overall rates
        response_rate = round(responses / total_applications, 3) if total_applications > 0 else 0
        interview_rate = round(interviews / total_applications, 3) if total_applications > 0 else 0
        offer_rate = round(offers / total_applications, 3) if total_applications > 0 else 0
        
        # Count by status
        status_counts = {}
        for app, job in applications:
            status = app.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Category analysis
        category_stats = self._analyze_by_category_internal(applications, response_statuses, interview_statuses, offer_statuses)
        
        return {
            'period_days': days,
            'analysis_date': datetime.utcnow().isoformat(),
            'total_applications': total_applications,
            'responses_received': responses,
            'interviews_scheduled': interviews,
            'offers_received': offers,
            'conversion_rates': {
                'response_rate': response_rate,
                'interview_rate': interview_rate,
                'offer_rate': offer_rate,
                'response_percentage': f"{response_rate:.1%}",
                'interview_percentage': f"{interview_rate:.1%}",
                'offer_percentage': f"{offer_rate:.1%}"
            },
            'status_breakdown': status_counts,
            'by_category': category_stats,
            'benchmarks': self._get_industry_benchmarks(),
            'recommendations': self._generate_conversion_recommendations(response_rate, interview_rate, offer_rate)
        }
    
    def _analyze_by_category_internal(self, applications: List[Tuple], response_statuses: List[str], 
                                    interview_statuses: List[str], offer_statuses: List[str]) -> Dict:
        """Internal method to analyze success rates by job category/industry"""
        category_stats = {}
        
        for app, job in applications:
            # Determine category from job data
            category = self._determine_job_category(job)
            
            if category not in category_stats:
                category_stats[category] = {
                    'applications': 0,
                    'responses': 0,
                    'interviews': 0,
                    'offers': 0,
                    'companies': set()
                }
            
            category_stats[category]['applications'] += 1
            category_stats[category]['companies'].add(job.company)
            
            if app.status in response_statuses:
                category_stats[category]['responses'] += 1
            
            if app.status in interview_statuses:
                category_stats[category]['interviews'] += 1
            
            if app.status in offer_statuses:
                category_stats[category]['offers'] += 1
        
        # Calculate rates and format results
        formatted_stats = {}
        for category, stats in category_stats.items():
            total = stats['applications']
            if total > 0:
                formatted_stats[category] = {
                    'applications': total,
                    'responses': stats['responses'],
                    'interviews': stats['interviews'],
                    'offers': stats['offers'],
                    'unique_companies': len(stats['companies']),
                    'response_rate': round(stats['responses'] / total, 3),
                    'interview_rate': round(stats['interviews'] / total, 3),
                    'offer_rate': round(stats['offers'] / total, 3),
                    'response_percentage': f"{stats['responses'] / total:.1%}",
                    'interview_percentage': f"{stats['interviews'] / total:.1%}",
                    'offer_percentage': f"{stats['offers'] / total:.1%}"
                }
        
        return formatted_stats
    
    def analyze_by_category(self, db: Session, user_id: int, days: int = 90) -> Dict:
        """Analyze success rates by job category/industry"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get applications with job details
        applications = db.query(JobApplication, Job).join(Job).filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= cutoff_date
        ).all()
        
        if not applications:
            return {'error': 'No applications found in the specified period'}
        
        # Define status categories
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
        
        category_stats = self._analyze_by_category_internal(applications, response_statuses, interview_statuses, offer_statuses)
        
        # Sort by success rate
        sorted_categories = sorted(category_stats.items(), key=lambda x: x[1]['response_rate'], reverse=True)
        
        return {
            'analysis_date': datetime.utcnow().isoformat(),
            'period_days': days,
            'categories': dict(sorted_categories),
            'top_performing_category': sorted_categories[0][0] if sorted_categories else None,
            'recommendations': self._generate_category_recommendations(sorted_categories)
        }
    
    def analyze_timing_patterns(self, db: Session, user_id: int, days: int = 180) -> Dict:
        """Analyze application timing patterns and success factors"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        applications = db.query(JobApplication, Job).join(Job).filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= cutoff_date
        ).all()
        
        if not applications:
            return {'error': 'No applications found'}
        
        # Define success statuses
        success_statuses = [
            'under_review', 'phone_screen_scheduled', 'phone_screen_completed',
            'interview_scheduled', 'interview_completed', 'final_round',
            'offer_received', 'offer_accepted'
        ]
        
        # Analyze by day of week
        day_stats = {i: {'applications': 0, 'responses': 0, 'avg_response_time': []} for i in range(7)}
        
        # Analyze by time since job posting
        timing_stats = {'quick': {'count': 0, 'responses': 0}, 
                       'medium': {'count': 0, 'responses': 0}, 
                       'slow': {'count': 0, 'responses': 0}}
        
        # Analyze by hour of day
        hour_stats = {i: {'applications': 0, 'responses': 0} for i in range(24)}
        
        # Monthly trend analysis
        monthly_stats = {}
        
        for app, job in applications:
            # Day of week analysis
            if app.applied_at:
                day_of_week = app.applied_at.weekday()
                hour_of_day = app.applied_at.hour
                month_key = app.applied_at.strftime('%Y-%m')
                
                day_stats[day_of_week]['applications'] += 1
                hour_stats[hour_of_day]['applications'] += 1
                
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {'applications': 0, 'responses': 0}
                monthly_stats[month_key]['applications'] += 1
                
                if app.status in success_statuses:
                    day_stats[day_of_week]['responses'] += 1
                    hour_stats[hour_of_day]['responses'] += 1
                    monthly_stats[month_key]['responses'] += 1
                    
                    # Calculate response time if available
                    if app.response_date:
                        response_time = (app.response_date - app.applied_at).days
                        day_stats[day_of_week]['avg_response_time'].append(response_time)
            
            # Timing analysis (days between job posting and application)
            if app.applied_at and job.date_posted:
                days_diff = (app.applied_at.date() - job.date_posted.date()).days
                has_response = app.status in success_statuses
                
                if days_diff <= 2:
                    timing_stats['quick']['count'] += 1
                    if has_response:
                        timing_stats['quick']['responses'] += 1
                elif days_diff <= 7:
                    timing_stats['medium']['count'] += 1
                    if has_response:
                        timing_stats['medium']['responses'] += 1
                else:
                    timing_stats['slow']['count'] += 1
                    if has_response:
                        timing_stats['slow']['responses'] += 1
        
        # Calculate success rates and format results
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_analysis = []
        
        for day, stats in day_stats.items():
            if stats['applications'] > 0:
                success_rate = round(stats['responses'] / stats['applications'], 3)
                avg_response_time = round(sum(stats['avg_response_time']) / len(stats['avg_response_time']), 1) if stats['avg_response_time'] else None
                day_analysis.append({
                    'day': day_names[day],
                    'day_number': day,
                    'applications': stats['applications'],
                    'responses': stats['responses'],
                    'success_rate': success_rate,
                    'success_percentage': f"{success_rate:.1%}",
                    'avg_response_time_days': avg_response_time
                })
        
        # Hour analysis
        hour_analysis = []
        for hour, stats in hour_stats.items():
            if stats['applications'] > 0:
                success_rate = round(stats['responses'] / stats['applications'], 3)
                hour_analysis.append({
                    'hour': hour,
                    'applications': stats['applications'],
                    'success_rate': success_rate
                })
        
        # Timing effectiveness analysis
        timing_effectiveness = {}
        for timing, stats in timing_stats.items():
            if stats['count'] > 0:
                timing_effectiveness[timing] = {
                    'applications': stats['count'],
                    'responses': stats['responses'],
                    'success_rate': round(stats['responses'] / stats['count'], 3),
                    'success_percentage': f"{stats['responses'] / stats['count']:.1%}"
                }
        
        # Monthly trends
        monthly_trends = []
        for month, stats in sorted(monthly_stats.items()):
            if stats['applications'] > 0:
                monthly_trends.append({
                    'month': month,
                    'applications': stats['applications'],
                    'responses': stats['responses'],
                    'success_rate': round(stats['responses'] / stats['applications'], 3)
                })
        
        return {
            'analysis_date': datetime.utcnow().isoformat(),
            'period_days': days,
            'day_of_week_analysis': sorted(day_analysis, key=lambda x: x['success_rate'], reverse=True),
            'hour_of_day_analysis': sorted(hour_analysis, key=lambda x: x['success_rate'], reverse=True)[:5],
            'timing_effectiveness': timing_effectiveness,
            'monthly_trends': monthly_trends,
            'best_application_day': max(day_analysis, key=lambda x: x['success_rate'])['day'] if day_analysis else None,
            'best_application_hour': max(hour_analysis, key=lambda x: x['success_rate'])['hour'] if hour_analysis else None,
            'recommendations': self._generate_timing_recommendations(day_analysis, timing_effectiveness, hour_analysis)
        }
    
    def track_company_response_times(self, db: Session, user_id: int, days: int = 365) -> Dict:
        """Track company response times and identify fast-responding organizations"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all applications with responses
        response_statuses = [
            'under_review', 'phone_screen_scheduled', 'phone_screen_completed',
            'interview_scheduled', 'interview_completed', 'final_round',
            'offer_received', 'offer_accepted', 'rejected'
        ]
        
        applications = db.query(JobApplication, Job).join(Job).filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= cutoff_date,
            JobApplication.status.in_(response_statuses)
        ).all()
        
        if not applications:
            return {'error': 'No responses found to analyze'}
        
        company_responses = {}
        all_response_times = []
        
        for app, job in applications:
            company = job.company
            if company not in company_responses:
                company_responses[company] = {
                    'total_applications': 0,
                    'responses': 0,
                    'response_times': [],
                    'positive_responses': 0,
                    'rejections': 0,
                    'latest_response': None
                }
            
            # Count all applications to this company (including non-responses)
            total_apps_to_company = db.query(JobApplication).join(Job).filter(
                JobApplication.user_id == user_id,
                Job.company == company,
                JobApplication.applied_at >= cutoff_date
            ).count()
            
            company_responses[company]['total_applications'] = total_apps_to_company
            company_responses[company]['responses'] += 1
            
            # Track response type
            if app.status == 'rejected':
                company_responses[company]['rejections'] += 1
            else:
                company_responses[company]['positive_responses'] += 1
            
            # Calculate response time
            response_date = app.response_date or app.updated_at
            if app.applied_at and response_date:
                response_days = (response_date - app.applied_at).days
                if response_days >= 0:  # Valid response time
                    company_responses[company]['response_times'].append(response_days)
                    all_response_times.append(response_days)
                    
                    # Track latest response date
                    if (company_responses[company]['latest_response'] is None or 
                        response_date > company_responses[company]['latest_response']):
                        company_responses[company]['latest_response'] = response_date
        
        # Calculate company statistics
        company_stats = []
        for company, data in company_responses.items():
            if data['response_times']:
                avg_response_time = round(sum(data['response_times']) / len(data['response_times']), 1)
                response_rate = round(data['responses'] / data['total_applications'], 3)
                
                company_stats.append({
                    'company': company,
                    'total_applications': data['total_applications'],
                    'responses': data['responses'],
                    'response_rate': response_rate,
                    'response_percentage': f"{response_rate:.1%}",
                    'avg_response_days': avg_response_time,
                    'positive_responses': data['positive_responses'],
                    'rejections': data['rejections'],
                    'latest_response': data['latest_response'].isoformat() if data['latest_response'] else None,
                    'response_speed_category': self._categorize_response_speed(avg_response_time)
                })
        
        # Sort companies by different metrics
        fast_companies = sorted([c for c in company_stats if c['avg_response_days'] <= 7], 
                               key=lambda x: x['avg_response_days'])[:10]
        
        responsive_companies = sorted([c for c in company_stats if c['response_rate'] >= 0.5], 
                                    key=lambda x: x['response_rate'], reverse=True)[:10]
        
        # Calculate overall statistics
        overall_avg_response_time = round(sum(all_response_times) / len(all_response_times), 1) if all_response_times else 0
        
        # Response time distribution
        response_time_distribution = {
            'same_day': len([t for t in all_response_times if t == 0]),
            '1-3_days': len([t for t in all_response_times if 1 <= t <= 3]),
            '4-7_days': len([t for t in all_response_times if 4 <= t <= 7]),
            '1-2_weeks': len([t for t in all_response_times if 8 <= t <= 14]),
            '2-4_weeks': len([t for t in all_response_times if 15 <= t <= 28]),
            'over_month': len([t for t in all_response_times if t > 28])
        }
        
        return {
            'analysis_date': datetime.utcnow().isoformat(),
            'period_days': days,
            'total_responding_companies': len(company_responses),
            'total_responses_analyzed': len(all_response_times),
            'overall_avg_response_time': overall_avg_response_time,
            'fast_responding_companies': fast_companies,
            'most_responsive_companies': responsive_companies,
            'all_company_stats': sorted(company_stats, key=lambda x: x['avg_response_days']),
            'response_time_distribution': response_time_distribution,
            'insights': self._generate_company_response_insights(company_stats, overall_avg_response_time),
            'recommendations': self._generate_company_recommendations(fast_companies, responsive_companies)
        }
    
    def _determine_job_category(self, job: Job) -> str:
        """Determine job category from job data"""
        # Check job requirements for industry
        if job.requirements and isinstance(job.requirements, dict):
            industry = job.requirements.get('industry')
            if industry:
                return industry.lower().replace(' ', '_')
        
        # Infer from job title
        title_lower = job.title.lower()
        
        if any(term in title_lower for term in ['frontend', 'front-end', 'react', 'vue', 'angular']):
            return 'frontend'
        elif any(term in title_lower for term in ['backend', 'back-end', 'api', 'server']):
            return 'backend'
        elif any(term in title_lower for term in ['fullstack', 'full-stack', 'full stack']):
            return 'fullstack'
        elif any(term in title_lower for term in ['data', 'analytics', 'scientist', 'ml', 'machine learning']):
            return 'data_science'
        elif any(term in title_lower for term in ['devops', 'sre', 'infrastructure', 'cloud']):
            return 'devops'
        elif any(term in title_lower for term in ['mobile', 'ios', 'android', 'react native']):
            return 'mobile'
        elif any(term in title_lower for term in ['qa', 'test', 'quality']):
            return 'qa'
        elif any(term in title_lower for term in ['product', 'manager', 'pm']):
            return 'product'
        elif any(term in title_lower for term in ['design', 'ux', 'ui']):
            return 'design'
        else:
            return 'other'
    
    def _categorize_response_speed(self, avg_days: float) -> str:
        """Categorize company response speed"""
        if avg_days <= 1:
            return 'very_fast'
        elif avg_days <= 3:
            return 'fast'
        elif avg_days <= 7:
            return 'moderate'
        elif avg_days <= 14:
            return 'slow'
        else:
            return 'very_slow'
    
    def _get_industry_benchmarks(self) -> Dict:
        """Get industry benchmark conversion rates"""
        return {
            'response_rate': {'low': 0.15, 'average': 0.25, 'high': 0.40},
            'interview_rate': {'low': 0.05, 'average': 0.10, 'high': 0.20},
            'offer_rate': {'low': 0.01, 'average': 0.03, 'high': 0.08}
        }
    
    def _generate_conversion_recommendations(self, response_rate: float, interview_rate: float, offer_rate: float) -> List[str]:
        """Generate recommendations based on conversion rates"""
        recommendations = []
        benchmarks = self._get_industry_benchmarks()
        
        if response_rate < benchmarks['response_rate']['low']:
            recommendations.append("Your response rate is below average. Consider improving your resume and cover letter.")
        elif response_rate > benchmarks['response_rate']['high']:
            recommendations.append("Excellent response rate! Your application materials are working well.")
        
        if interview_rate < benchmarks['interview_rate']['low']:
            recommendations.append("Focus on getting more interviews by tailoring applications to job requirements.")
        elif interview_rate > benchmarks['interview_rate']['high']:
            recommendations.append("Great interview rate! You're getting good traction with employers.")
        
        if offer_rate < benchmarks['offer_rate']['low']:
            recommendations.append("Consider practicing interview skills to improve your offer conversion rate.")
        elif offer_rate > benchmarks['offer_rate']['high']:
            recommendations.append("Outstanding offer rate! Your interview performance is excellent.")
        
        return recommendations
    
    def _generate_category_recommendations(self, sorted_categories: List[Tuple]) -> List[str]:
        """Generate recommendations based on category performance"""
        recommendations = []
        
        if not sorted_categories:
            return recommendations
        
        best_category = sorted_categories[0]
        if len(sorted_categories) > 1:
            worst_category = sorted_categories[-1]
            
            recommendations.append(f"Focus more on {best_category[0]} roles - your success rate is {best_category[1]['response_percentage']}")
            
            if worst_category[1]['response_rate'] < 0.1:
                recommendations.append(f"Consider avoiding {worst_category[0]} roles or improving your approach for this category")
        
        return recommendations
    
    def _generate_timing_recommendations(self, day_analysis: List[Dict], timing_effectiveness: Dict, hour_analysis: List[Dict]) -> List[str]:
        """Generate recommendations based on timing analysis"""
        recommendations = []
        
        # Best day recommendation
        if day_analysis:
            best_day = max(day_analysis, key=lambda x: x['success_rate'])
            recommendations.append(f"Best application day: {best_day['day']} (success rate: {best_day['success_percentage']})")
        
        # Best hour recommendation
        if hour_analysis:
            best_hour = max(hour_analysis, key=lambda x: x['success_rate'])
            recommendations.append(f"Best application time: {best_hour['hour']}:00 (success rate: {best_hour['success_rate']:.1%})")
        
        # Timing effectiveness
        if timing_effectiveness:
            quick_rate = timing_effectiveness.get('quick', {}).get('success_rate', 0)
            slow_rate = timing_effectiveness.get('slow', {}).get('success_rate', 0)
            
            if quick_rate > slow_rate * 1.5:
                recommendations.append("Apply within 2 days of job posting for significantly better results")
            elif quick_rate < slow_rate:
                recommendations.append("Taking time to craft quality applications may be more effective than speed")
        
        return recommendations
    
    def _generate_company_response_insights(self, company_stats: List[Dict], overall_avg: float) -> List[str]:
        """Generate insights about company response patterns"""
        insights = []
        
        if not company_stats:
            return insights
        
        # Fast responders insight
        fast_companies = [c for c in company_stats if c['avg_response_days'] <= 3]
        if fast_companies:
            insights.append(f"{len(fast_companies)} companies respond within 3 days on average")
        
        # Slow responders insight
        slow_companies = [c for c in company_stats if c['avg_response_days'] > 14]
        if slow_companies:
            insights.append(f"{len(slow_companies)} companies take over 2 weeks to respond")
        
        # Response rate insight
        high_response_companies = [c for c in company_stats if c['response_rate'] >= 0.5]
        if high_response_companies:
            insights.append(f"{len(high_response_companies)} companies have >50% response rates")
        
        return insights
    
    def _generate_company_recommendations(self, fast_companies: List[Dict], responsive_companies: List[Dict]) -> List[str]:
        """Generate recommendations based on company response analysis"""
        recommendations = []
        
        if fast_companies:
            top_fast = fast_companies[0]
            recommendations.append(f"Prioritize companies like {top_fast['company']} - they respond in {top_fast['avg_response_days']} days on average")
        
        if responsive_companies:
            top_responsive = responsive_companies[0]
            recommendations.append(f"Target companies like {top_responsive['company']} - they have a {top_responsive['response_percentage']} response rate")
        
        recommendations.append("Follow up with companies that haven't responded after 2 weeks")
        
        return recommendations
    
    def save_analysis(self, db: Session, user_id: int, analysis_type: str, data: Dict) -> bool:
        """Save application analysis to database"""
        try:
            analytics = Analytics(
                user_id=user_id,
                type=analysis_type,
                data=data
            )
            db.add(analytics)
            db.commit()
            return True
        except Exception as e:
            print(f"Failed to save application analysis: {e}")
            db.rollback()
            return False
    
    def get_historical_analysis(self, db: Session, user_id: int, analysis_type: str, limit: int = 10) -> List[Dict]:
        """Get historical analysis data for trend tracking"""
        analytics = db.query(Analytics).filter(
            Analytics.user_id == user_id,
            Analytics.type == analysis_type
        ).order_by(desc(Analytics.generated_at)).limit(limit).all()
        
        return [
            {
                'id': a.id,
                'generated_at': a.generated_at.isoformat(),
                'data': a.data
            }
            for a in analytics
        ]
    
    def get_success_trends(self, db: Session, user_id: int, months: int = 6) -> Dict:
        """Analyze success rate trends over time"""
        cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
        
        # Get monthly application data
        monthly_data = db.query(
            func.date_trunc('month', JobApplication.applied_at).label('month'),
            func.count(JobApplication.id).label('applications'),
            func.sum(case(
                (JobApplication.status.in_([
                    'under_review', 'phone_screen_scheduled', 'phone_screen_completed',
                    'interview_scheduled', 'interview_completed', 'final_round',
                    'offer_received', 'offer_accepted'
                ]), 1),
                else_=0
            )).label('responses')
        ).filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_at >= cutoff_date
        ).group_by(
            func.date_trunc('month', JobApplication.applied_at)
        ).order_by('month').all()
        
        trends = []
        for month, applications, responses in monthly_data:
            success_rate = round(responses / applications, 3) if applications > 0 else 0
            trends.append({
                'month': month.strftime('%Y-%m'),
                'applications': applications,
                'responses': responses,
                'success_rate': success_rate,
                'success_percentage': f"{success_rate:.1%}"
            })
        
        # Calculate trend direction
        trend_direction = 'stable'
        if len(trends) >= 2:
            recent_rate = trends[-1]['success_rate']
            previous_rate = trends[-2]['success_rate']
            
            if recent_rate > previous_rate * 1.1:
                trend_direction = 'improving'
            elif recent_rate < previous_rate * 0.9:
                trend_direction = 'declining'
        
        return {
            'analysis_date': datetime.utcnow().isoformat(),
            'period_months': months,
            'monthly_trends': trends,
            'trend_direction': trend_direction,
            'total_applications': sum(t['applications'] for t in trends),
            'total_responses': sum(t['responses'] for t in trends),
            'overall_success_rate': round(
                sum(t['responses'] for t in trends) / sum(t['applications'] for t in trends), 3
            ) if sum(t['applications'] for t in trends) > 0 else 0
        }
    
    def get_comprehensive_report(self, db: Session, user_id: int, days: int = 90) -> Dict:
        """Generate comprehensive application success report"""
        try:
            conversion_rates = self.calculate_conversion_rates(db, user_id, days)
            category_analysis = self.analyze_by_category(db, user_id, days)
            timing_patterns = self.analyze_timing_patterns(db, user_id, days * 2)  # Longer period for timing
            company_responses = self.track_company_response_times(db, user_id, days * 4)  # Even longer for companies
            success_trends = self.get_success_trends(db, user_id, 6)
            
            # Generate overall insights
            overall_insights = self._generate_overall_insights(
                conversion_rates, category_analysis, timing_patterns, company_responses
            )
            
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'report_period_days': days,
                'user_id': user_id,
                'conversion_rates': conversion_rates,
                'category_analysis': category_analysis,
                'timing_patterns': timing_patterns,
                'company_responses': company_responses,
                'success_trends': success_trends,
                'overall_insights': overall_insights,
                'summary': self._generate_report_summary(conversion_rates, success_trends)
            }
            
            # Save the comprehensive report
            self.save_analysis(db, user_id, 'comprehensive_application_report', report)
            
            return report
            
        except Exception as e:
            return {
                'error': f'Failed to generate comprehensive report: {str(e)}',
                'generated_at': datetime.utcnow().isoformat()
            }
    
    def _generate_overall_insights(self, conversion_rates: Dict, category_analysis: Dict, 
                                 timing_patterns: Dict, company_responses: Dict) -> List[str]:
        """Generate overall insights from all analyses"""
        insights = []
        
        # Conversion rate insights
        if 'conversion_rates' in conversion_rates:
            rates = conversion_rates['conversion_rates']
            if rates['response_rate'] > 0.3:
                insights.append("Your response rate is above average - your application materials are effective")
            elif rates['response_rate'] < 0.15:
                insights.append("Your response rate is below average - consider improving your resume and cover letters")
        
        # Category insights
        if 'categories' in category_analysis and category_analysis['categories']:
            best_category = max(category_analysis['categories'].items(), key=lambda x: x[1]['response_rate'])
            insights.append(f"You perform best in {best_category[0]} roles with {best_category[1]['response_percentage']} success rate")
        
        # Timing insights
        if 'best_application_day' in timing_patterns and timing_patterns['best_application_day']:
            insights.append(f"Your most successful application day is {timing_patterns['best_application_day']}")
        
        # Company insights
        if 'fast_responding_companies' in company_responses and company_responses['fast_responding_companies']:
            fast_count = len(company_responses['fast_responding_companies'])
            insights.append(f"You've identified {fast_count} fast-responding companies to prioritize")
        
        return insights
    
    def _generate_report_summary(self, conversion_rates: Dict, success_trends: Dict) -> Dict:
        """Generate executive summary of the report"""
        summary = {
            'status': 'healthy',
            'key_metrics': {},
            'primary_recommendation': 'Continue current strategy'
        }
        
        if 'conversion_rates' in conversion_rates:
            rates = conversion_rates['conversion_rates']
            summary['key_metrics'] = {
                'response_rate': rates['response_percentage'],
                'interview_rate': rates['interview_percentage'],
                'offer_rate': rates['offer_percentage']
            }
            
            # Determine overall status
            if rates['response_rate'] < 0.15:
                summary['status'] = 'needs_improvement'
                summary['primary_recommendation'] = 'Focus on improving application materials and targeting'
            elif rates['response_rate'] > 0.3:
                summary['status'] = 'excellent'
                summary['primary_recommendation'] = 'Maintain current approach and consider increasing application volume'
        
        # Add trend information
        if 'trend_direction' in success_trends:
            summary['trend'] = success_trends['trend_direction']
        
        return summary


application_analytics_service = ApplicationAnalyticsService()