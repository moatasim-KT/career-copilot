"""
Market trend analysis and reporting service
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case
from collections import Counter, defaultdict
import statistics
import re

from app.models.user import User
from app.models.job import Job
from app.models.analytics import Analytics


class MarketAnalysisService:
    """Service for analyzing job market trends and opportunities"""
    
    def __init__(self):
        # Industry classification patterns
        self.industry_patterns = {
            'technology': ['tech', 'software', 'saas', 'startup', 'ai', 'ml', 'data', 'google', 'microsoft', 'apple'],
            'finance': ['bank', 'finance', 'fintech', 'trading', 'investment', 'insurance', 'goldman', 'morgan', 'jpmorgan'],
            'healthcare': ['health', 'medical', 'pharma', 'biotech', 'hospital', 'kaiser', 'permanente', 'pfizer', 'johnson'],
            'consulting': ['consulting', 'advisory', 'strategy', 'management', 'mckinsey', 'bain', 'bcg', 'deloitte'],
            'retail': ['retail', 'ecommerce', 'e-commerce', 'consumer', 'marketplace', 'amazon', 'walmart', 'target'],
            'education': ['education', 'university', 'school', 'learning', 'training'],
            'government': ['government', 'public', 'federal', 'state', 'municipal'],
            'media': ['media', 'entertainment', 'gaming', 'content', 'publishing'],
            'manufacturing': ['manufacturing', 'automotive', 'industrial', 'production', 'tesla', 'ford', 'gm'],
            'energy': ['energy', 'oil', 'renewable', 'utilities', 'solar', 'wind']
        }
        
        # Company size patterns
        self.company_size_patterns = {
            'startup': ['startup', 'early stage', 'seed', 'series a', 'series b'],
            'small': ['small', '1-50', '10-50', 'boutique'],
            'medium': ['medium', '50-200', '100-500', 'mid-size'],
            'large': ['large', '500+', '1000+', 'enterprise', 'fortune'],
            'enterprise': ['enterprise', 'fortune 500', 'multinational', 'global', 'google', 'microsoft', 'apple', 'amazon']
        }
    
    def analyze_salary_trends(self, db: Session, user_id: int, role_filter: Optional[str] = None, days: int = 180) -> Dict:
        """Enhanced salary trend analysis with temporal and comparative insights"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get jobs with salary data from multiple time periods
        query = db.query(Job).filter(
            Job.user_id == user_id,
            Job.salary_min.isnot(None),
            Job.salary_max.isnot(None),
            Job.created_at >= cutoff_date
        )
        
        if role_filter:
            query = query.filter(Job.title.ilike(f'%{role_filter}%'))
        
        jobs = query.all()
        
        if not jobs:
            return {'error': 'No salary data available for analysis'}
        
        # Calculate comprehensive salary statistics
        min_salaries = [job.salary_min for job in jobs if job.salary_min]
        max_salaries = [job.salary_max for job in jobs if job.salary_max]
        avg_salaries = [(job.salary_min + job.salary_max) / 2 for job in jobs if job.salary_min and job.salary_max]
        
        # Temporal analysis - group by month
        monthly_salary_trends = defaultdict(list)
        for job in jobs:
            if job.salary_min and job.salary_max:
                month_key = job.created_at.strftime('%Y-%m')
                avg_salary = (job.salary_min + job.salary_max) / 2
                monthly_salary_trends[month_key].append(avg_salary)
        
        # Calculate monthly averages and trends
        monthly_averages = []
        for month, salaries in sorted(monthly_salary_trends.items()):
            monthly_averages.append({
                'month': month,
                'average_salary': int(sum(salaries) / len(salaries)),
                'job_count': len(salaries),
                'min_salary': int(min(salaries)),
                'max_salary': int(max(salaries)),
                'median_salary': int(statistics.median(salaries))
            })
        
        # Calculate salary growth rate
        salary_growth_rate = 0
        if len(monthly_averages) >= 2:
            recent_avg = sum([m['average_salary'] for m in monthly_averages[-3:]]) / min(3, len(monthly_averages))
            early_avg = sum([m['average_salary'] for m in monthly_averages[:3]]) / min(3, len(monthly_averages))
            if early_avg > 0:
                salary_growth_rate = round((recent_avg - early_avg) / early_avg, 3)
        
        # Enhanced location analysis with market insights
        location_salaries = defaultdict(list)
        location_job_counts = defaultdict(int)
        
        for job in jobs:
            location = self._normalize_location(job.location)
            location_job_counts[location] += 1
            
            if job.salary_min and job.salary_max:
                location_salaries[location].append((job.salary_min + job.salary_max) / 2)
        
        # Calculate comprehensive location analysis
        location_analysis = {}
        for location, salaries in location_salaries.items():
            if len(salaries) >= 2:  # Lowered threshold for better coverage
                sorted_salaries = sorted(salaries)
                location_analysis[location] = {
                    'count': len(salaries),
                    'total_jobs': location_job_counts[location],
                    'salary_data_coverage': round(len(salaries) / location_job_counts[location], 2),
                    'min': int(min(salaries)),
                    'max': int(max(salaries)),
                    'median': int(statistics.median(salaries)),
                    'average': int(sum(salaries) / len(salaries)),
                    'percentile_25': int(sorted_salaries[len(sorted_salaries)//4]),
                    'percentile_75': int(sorted_salaries[3*len(sorted_salaries)//4]),
                    'market_competitiveness': self._calculate_market_competitiveness(salaries, avg_salaries)
                }
        
        # Industry-based salary analysis
        industry_salaries = self._analyze_salary_by_industry(jobs)
        
        # Experience level analysis (if available in job requirements)
        experience_salary_analysis = self._analyze_salary_by_experience(jobs)
        
        # Company size analysis
        company_size_analysis = self._analyze_salary_by_company_size(jobs)
        
        # Generate salary insights and recommendations
        salary_insights = self._generate_salary_insights(
            monthly_averages, location_analysis, industry_salaries, salary_growth_rate
        )
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'analysis_period_days': days,
            'total_jobs_analyzed': len(jobs),
            'jobs_with_salary_data': len(avg_salaries),
            'salary_data_coverage': round(len(avg_salaries) / len(jobs), 2),
            'role_filter': role_filter,
            'overall_salary_range': {
                'min': int(min(min_salaries)) if min_salaries else 0,
                'max': int(max(max_salaries)) if max_salaries else 0,
                'median': int(statistics.median(avg_salaries)) if avg_salaries else 0,
                'average': int(sum(avg_salaries) / len(avg_salaries)) if avg_salaries else 0,
                'percentile_25': int(sorted(avg_salaries)[len(avg_salaries)//4]) if avg_salaries else 0,
                'percentile_75': int(sorted(avg_salaries)[3*len(avg_salaries)//4]) if avg_salaries else 0,
                'standard_deviation': int(statistics.stdev(avg_salaries)) if len(avg_salaries) > 1 else 0
            },
            'monthly_trends': monthly_averages,
            'salary_growth_rate': salary_growth_rate,
            'growth_percentage': f"{salary_growth_rate:.1%}" if salary_growth_rate else "0.0%",
            'by_location': dict(sorted(location_analysis.items(), key=lambda x: x[1]['average'], reverse=True)),
            'by_industry': industry_salaries,
            'by_experience_level': experience_salary_analysis,
            'by_company_size': company_size_analysis,
            'market_insights': salary_insights,
            'chart_data': {
                'monthly_trend': [{'month': m['month'], 'salary': m['average_salary']} for m in monthly_averages],
                'location_comparison': [{'location': loc, 'salary': data['average']} for loc, data in location_analysis.items()],
                'industry_comparison': [{'industry': ind, 'salary': data['average']} for ind, data in industry_salaries.items()]
            }
        }
    
    def analyze_job_market_patterns(self, db: Session, user_id: int, days: int = 90) -> Dict:
        """Enhanced job market pattern analysis with comprehensive insights"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        jobs = db.query(Job).filter(
            Job.user_id == user_id,
            Job.created_at >= cutoff_date
        ).all()
        
        if not jobs:
            return {'error': 'No recent jobs found for analysis'}
        
        # Enhanced temporal analysis
        daily_counts = defaultdict(int)
        weekly_counts = defaultdict(int)
        monthly_counts = defaultdict(int)
        
        for job in jobs:
            # Daily analysis
            day_key = job.created_at.strftime('%Y-%m-%d')
            daily_counts[day_key] += 1
            
            # Weekly analysis
            week_start = job.created_at.date() - timedelta(days=job.created_at.weekday())
            week_key = week_start.strftime('%Y-W%U')
            weekly_counts[week_key] += 1
            
            # Monthly analysis
            month_key = job.created_at.strftime('%Y-%m')
            monthly_counts[month_key] += 1
        
        # Calculate multiple growth rates
        growth_metrics = self._calculate_growth_metrics(daily_counts, weekly_counts, monthly_counts)
        
        # Enhanced source analysis
        source_analysis = self._analyze_job_sources(jobs)
        
        # Company analysis with market insights
        company_analysis = self._analyze_company_patterns(jobs)
        
        # Industry distribution analysis
        industry_distribution = self._analyze_industry_distribution(jobs)
        
        # Location and remote work analysis
        location_analysis = self._analyze_location_patterns(jobs)
        
        # Job title and role analysis
        role_analysis = self._analyze_role_patterns(jobs)
        
        # Seasonal and cyclical patterns
        seasonal_patterns = self._analyze_seasonal_patterns(jobs)
        
        # Market velocity and competition analysis
        market_velocity = self._calculate_market_velocity(jobs)
        
        # Generate comprehensive market insights
        market_insights = self._generate_market_pattern_insights(
            growth_metrics, industry_distribution, location_analysis, seasonal_patterns
        )
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'analysis_period_days': days,
            'total_jobs': len(jobs),
            'daily_average': round(len(jobs) / days, 1),
            'weekly_average': round(len(jobs) / (days / 7), 1),
            'temporal_distribution': {
                'daily_counts': dict(sorted(daily_counts.items())[-30:]),  # Last 30 days
                'weekly_counts': dict(sorted(weekly_counts.items())[-12:]),  # Last 12 weeks
                'monthly_counts': dict(sorted(monthly_counts.items()))
            },
            'growth_metrics': growth_metrics,
            'job_sources': source_analysis,
            'company_analysis': company_analysis,
            'industry_distribution': industry_distribution,
            'location_analysis': location_analysis,
            'role_analysis': role_analysis,
            'seasonal_patterns': seasonal_patterns,
            'market_velocity': market_velocity,
            'market_insights': market_insights,
            'chart_data': {
                'jobs_over_time': [{'date': date, 'count': count} for date, count in sorted(daily_counts.items())[-30:]],
                'weekly_trend': [{'week': week, 'count': count} for week, count in sorted(weekly_counts.items())[-12:]],
                'industry_pie': [{'industry': ind, 'count': data['count']} for ind, data in industry_distribution.items()],
                'location_distribution': [{'location': loc, 'count': data['count']} for loc, data in location_analysis.items()],
                'source_breakdown': [{'source': source, 'count': data['count']} for source, data in source_analysis.items()]
            }
        }
    
    def generate_opportunity_alerts(self, db: Session, user_id: int) -> List[Dict]:
        """Generate market opportunity alerts for user's target roles"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        alerts = []
        
        # Get user preferences
        profile = user.profile or {}
        target_roles = profile.get('career_goals', [])
        preferred_locations = profile.get('locations', [])
        
        # Recent job market analysis
        market_data = self.analyze_job_market_patterns(db, user_id, days=30)
        
        # High growth alert
        if market_data.get('growth_rate', 0) > 0.2:
            alerts.append({
                'type': 'high_growth',
                'title': 'Job Market Surge Detected',
                'message': f"Job postings increased by {market_data['growth_rate']:.1%} in the last month",
                'priority': 'high',
                'action': 'Consider increasing your application rate'
            })
        
        # New company alert
        if market_data.get('top_companies'):
            new_companies = [comp for comp in market_data['top_companies'][:3] if comp['count'] >= 3]
            if new_companies:
                alerts.append({
                    'type': 'new_companies',
                    'title': 'Active Hiring Companies',
                    'message': f"Companies actively hiring: {', '.join([c['company'] for c in new_companies])}",
                    'priority': 'medium',
                    'action': 'Research these companies for opportunities'
                })
        
        # Remote work trend alert
        remote_data = market_data.get('remote_options', {})
        remote_pct = (remote_data.get('remote', 0) + remote_data.get('hybrid', 0)) / sum(remote_data.values()) if remote_data else 0
        
        if remote_pct > 0.6:
            alerts.append({
                'type': 'remote_trend',
                'title': 'High Remote Work Availability',
                'message': f"{remote_pct:.1%} of jobs offer remote/hybrid options",
                'priority': 'medium',
                'action': 'Expand your search to include remote positions'
            })
        
        return alerts
    
    def create_market_dashboard_data(self, db: Session, user_id: int) -> Dict:
        """Create comprehensive market dashboard data"""
        salary_trends = self.analyze_salary_trends(db, user_id)
        market_patterns = self.analyze_job_market_patterns(db, user_id)
        opportunity_alerts = self.generate_opportunity_alerts(db, user_id)
        
        # Generate chart data for visualization
        chart_data = {
            'salary_by_location': [],
            'jobs_over_time': [],
            'company_distribution': [],
            'employment_type_pie': []
        }
        
        # Salary by location chart
        if 'by_location' in salary_trends:
            for location, data in salary_trends['by_location'].items():
                chart_data['salary_by_location'].append({
                    'location': location,
                    'median_salary': data['median'],
                    'job_count': data['count']
                })
        
        # Jobs over time chart
        if 'weekly_distribution' in market_patterns:
            for week, count in market_patterns['weekly_distribution'].items():
                chart_data['jobs_over_time'].append({
                    'week': week,
                    'count': count
                })
        
        # Company distribution chart
        if 'top_companies' in market_patterns:
            chart_data['company_distribution'] = market_patterns['top_companies'][:8]
        
        # Employment type pie chart
        if 'employment_types' in market_patterns:
            for emp_type, count in market_patterns['employment_types'].items():
                chart_data['employment_type_pie'].append({
                    'type': emp_type,
                    'count': count
                })
        
        return {
            'generated_at': datetime.now().isoformat(),
            'salary_trends': salary_trends,
            'market_patterns': market_patterns,
            'opportunity_alerts': opportunity_alerts,
            'chart_data': chart_data,
            'summary': {
                'total_jobs_analyzed': market_patterns.get('total_jobs', 0),
                'market_growth': market_patterns.get('growth_rate', 0),
                'avg_salary': salary_trends.get('overall_salary_range', {}).get('average', 0),
                'active_alerts': len(opportunity_alerts)
            }
        }
    
    def save_analysis(self, db: Session, user_id: int, analysis_data: Dict) -> bool:
        """Save market analysis to database"""
        try:
            analytics = Analytics(
                user_id=user_id,
                type="market_trends",
                data=analysis_data
            )
            db.add(analytics)
            db.commit()
            return True
        except Exception as e:
            print(f"Failed to save market analysis: {e}")
            return False
    
    # Helper methods for enhanced analysis
    
    def _normalize_location(self, location: Optional[str]) -> str:
        """Normalize location strings for better grouping"""
        if not location:
            return 'Remote'
        
        location = location.lower().strip()
        
        # Common location normalizations
        if 'remote' in location or 'anywhere' in location:
            return 'Remote'
        elif 'san francisco' in location or 'sf' in location:
            return 'San Francisco, CA'
        elif 'new york' in location or 'nyc' in location:
            return 'New York, NY'
        elif 'los angeles' in location or 'la' in location:
            return 'Los Angeles, CA'
        elif 'seattle' in location:
            return 'Seattle, WA'
        elif 'austin' in location:
            return 'Austin, TX'
        elif 'boston' in location:
            return 'Boston, MA'
        elif 'chicago' in location:
            return 'Chicago, IL'
        else:
            return location.title()
    
    def _calculate_market_competitiveness(self, location_salaries: List[float], all_salaries: List[float]) -> str:
        """Calculate market competitiveness for a location"""
        if not location_salaries or not all_salaries:
            return 'unknown'
        
        location_avg = sum(location_salaries) / len(location_salaries)
        overall_avg = sum(all_salaries) / len(all_salaries)
        
        ratio = location_avg / overall_avg
        
        if ratio >= 1.15:  # Adjusted threshold
            return 'highly_competitive'
        elif ratio >= 1.05:  # Adjusted threshold
            return 'competitive'
        elif ratio >= 0.95:  # Adjusted threshold
            return 'average'
        else:
            return 'below_average'
    
    def _analyze_salary_by_industry(self, jobs: List[Job]) -> Dict:
        """Analyze salary trends by industry"""
        industry_salaries = defaultdict(list)
        
        for job in jobs:
            if job.salary_min and job.salary_max:
                industry = self._classify_industry(job)
                avg_salary = (job.salary_min + job.salary_max) / 2
                industry_salaries[industry].append(avg_salary)
        
        industry_analysis = {}
        for industry, salaries in industry_salaries.items():
            if len(salaries) >= 2:
                industry_analysis[industry] = {
                    'count': len(salaries),
                    'average': int(sum(salaries) / len(salaries)),
                    'median': int(statistics.median(salaries)),
                    'min': int(min(salaries)),
                    'max': int(max(salaries))
                }
        
        return industry_analysis
    
    def _analyze_salary_by_experience(self, jobs: List[Job]) -> Dict:
        """Analyze salary by experience level"""
        experience_salaries = defaultdict(list)
        
        for job in jobs:
            if job.salary_min and job.salary_max and job.requirements:
                exp_level = self._extract_experience_level(job)
                if exp_level:
                    avg_salary = (job.salary_min + job.salary_max) / 2
                    experience_salaries[exp_level].append(avg_salary)
        
        experience_analysis = {}
        for level, salaries in experience_salaries.items():
            if len(salaries) >= 2:
                experience_analysis[level] = {
                    'count': len(salaries),
                    'average': int(sum(salaries) / len(salaries)),
                    'median': int(statistics.median(salaries))
                }
        
        return experience_analysis
    
    def _analyze_salary_by_company_size(self, jobs: List[Job]) -> Dict:
        """Analyze salary by company size"""
        size_salaries = defaultdict(list)
        
        for job in jobs:
            if job.salary_min and job.salary_max:
                company_size = self._classify_company_size(job)
                avg_salary = (job.salary_min + job.salary_max) / 2
                size_salaries[company_size].append(avg_salary)
        
        size_analysis = {}
        for size, salaries in size_salaries.items():
            if len(salaries) >= 2:
                size_analysis[size] = {
                    'count': len(salaries),
                    'average': int(sum(salaries) / len(salaries)),
                    'median': int(statistics.median(salaries))
                }
        
        return size_analysis
    
    def _classify_industry(self, job: Job) -> str:
        """Classify job into industry category"""
        text_to_analyze = f"{getattr(job, 'company', '')} {getattr(job, 'description', '') or ''} {getattr(job, 'title', '')}".lower()
        
        for industry, patterns in self.industry_patterns.items():
            if any(pattern in text_to_analyze for pattern in patterns):
                return industry
        
        return 'other'
    
    def _classify_company_size(self, job: Job) -> str:
        """Classify company size based on job information"""
        text_to_analyze = f"{getattr(job, 'company', '')} {getattr(job, 'description', '') or ''}".lower()
        
        for size, patterns in self.company_size_patterns.items():
            if any(pattern in text_to_analyze for pattern in patterns):
                return size
        
        return 'unknown'
    
    def _extract_experience_level(self, job: Job) -> Optional[str]:
        """Extract experience level from job requirements"""
        # Check explicit experience level in requirements
        if hasattr(job, 'requirements') and job.requirements and isinstance(job.requirements, dict):
            exp_level = job.requirements.get('experience_level')
            if exp_level:
                return exp_level.lower()
        
        # Extract from title and description
        text = f"{getattr(job, 'title', '')} {getattr(job, 'description', '') or ''}".lower()
        
        if any(term in text for term in ['senior', 'sr.', 'lead', 'principal', '5+ years', '7+ years']):
            return 'senior'
        elif any(term in text for term in ['junior', 'jr.', 'entry', 'graduate', '0-2 years', '1-3 years']):
            return 'junior'
        elif any(term in text for term in ['mid', 'intermediate', '3-5 years', '2-4 years']):
            return 'mid'
        
        return None
    
    def _calculate_growth_metrics(self, daily_counts: Dict, weekly_counts: Dict, monthly_counts: Dict) -> Dict:
        """Calculate comprehensive growth metrics"""
        metrics = {}
        
        # Daily growth rate (last 7 days vs previous 7 days)
        daily_values = list(daily_counts.values())
        if len(daily_values) >= 14:
            recent_week = sum(daily_values[-7:])
            previous_week = sum(daily_values[-14:-7])
            metrics['daily_growth_rate'] = round((recent_week - previous_week) / previous_week, 3) if previous_week > 0 else 0
        else:
            metrics['daily_growth_rate'] = 0
        
        # Weekly growth rate
        weekly_values = list(weekly_counts.values())
        if len(weekly_values) >= 4:
            recent_weeks = sum(weekly_values[-2:])
            previous_weeks = sum(weekly_values[-4:-2])
            metrics['weekly_growth_rate'] = round((recent_weeks - previous_weeks) / previous_weeks, 3) if previous_weeks > 0 else 0
        else:
            metrics['weekly_growth_rate'] = 0
        
        # Monthly growth rate
        monthly_values = list(monthly_counts.values())
        if len(monthly_values) >= 2:
            current_month = monthly_values[-1]
            previous_month = monthly_values[-2]
            metrics['monthly_growth_rate'] = round((current_month - previous_month) / previous_month, 3) if previous_month > 0 else 0
        else:
            metrics['monthly_growth_rate'] = 0
        
        return metrics
    
    def _analyze_job_sources(self, jobs: List[Job]) -> Dict:
        """Analyze job sources with performance metrics"""
        source_data = defaultdict(lambda: {'count': 0, 'recent_count': 0})
        recent_cutoff = datetime.now() - timedelta(days=7)
        
        for job in jobs:
            source = job.source or 'manual'
            source_data[source]['count'] += 1
            
            if job.created_at >= recent_cutoff:
                source_data[source]['recent_count'] += 1
        
        # Calculate source performance
        for source, data in source_data.items():
            data['percentage'] = round(data['count'] / len(jobs) * 100, 1)
            data['recent_percentage'] = round(data['recent_count'] / sum(d['recent_count'] for d in source_data.values()) * 100, 1) if sum(d['recent_count'] for d in source_data.values()) > 0 else 0
            data['trend'] = 'increasing' if data['recent_percentage'] > data['percentage'] else 'decreasing' if data['recent_percentage'] < data['percentage'] else 'stable'
        
        return dict(source_data)
    
    def _analyze_company_patterns(self, jobs: List[Job]) -> Dict:
        """Analyze company hiring patterns"""
        company_data = defaultdict(lambda: {'count': 0, 'recent_activity': 0, 'first_seen': None, 'last_seen': None})
        recent_cutoff = datetime.now() - timedelta(days=14)
        
        for job in jobs:
            company = job.company
            company_data[company]['count'] += 1
            
            if job.created_at >= recent_cutoff:
                company_data[company]['recent_activity'] += 1
            
            if not company_data[company]['first_seen'] or job.created_at < company_data[company]['first_seen']:
                company_data[company]['first_seen'] = job.created_at
            
            if not company_data[company]['last_seen'] or job.created_at > company_data[company]['last_seen']:
                company_data[company]['last_seen'] = job.created_at
        
        # Identify top companies and hiring patterns
        top_companies = sorted(company_data.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
        active_companies = [comp for comp, data in company_data.items() if data['recent_activity'] >= 2]
        
        return {
            'total_companies': len(company_data),
            'active_companies_count': len(active_companies),
            'top_companies': [{'company': comp, **data} for comp, data in top_companies],
            'most_active_recently': sorted(active_companies, key=lambda x: company_data[x]['recent_activity'], reverse=True)[:5]
        }
    
    def _analyze_industry_distribution(self, jobs: List[Job]) -> Dict:
        """Analyze industry distribution and trends"""
        industry_data = defaultdict(lambda: {'count': 0, 'recent_count': 0, 'companies': set()})
        recent_cutoff = datetime.now() - timedelta(days=14)
        
        for job in jobs:
            industry = self._classify_industry(job)
            industry_data[industry]['count'] += 1
            industry_data[industry]['companies'].add(job.company)
            
            if job.created_at >= recent_cutoff:
                industry_data[industry]['recent_count'] += 1
        
        # Calculate industry metrics
        for industry, data in industry_data.items():
            data['percentage'] = round(data['count'] / len(jobs) * 100, 1)
            data['company_count'] = len(data['companies'])
            data['companies'] = list(data['companies'])  # Convert set to list for JSON serialization
            data['avg_jobs_per_company'] = round(data['count'] / len(data['companies']), 1)
        
        return dict(industry_data)
    
    def _analyze_location_patterns(self, jobs: List[Job]) -> Dict:
        """Analyze location and remote work patterns"""
        location_data = defaultdict(lambda: {'count': 0, 'remote_count': 0, 'hybrid_count': 0, 'onsite_count': 0})
        
        for job in jobs:
            location = self._normalize_location(job.location)
            location_data[location]['count'] += 1
            
            # Analyze remote work options
            if job.requirements and isinstance(job.requirements, dict):
                remote_option = job.requirements.get('remote_options', '').lower()
                if 'remote' in remote_option:
                    location_data[location]['remote_count'] += 1
                elif 'hybrid' in remote_option:
                    location_data[location]['hybrid_count'] += 1
                else:
                    location_data[location]['onsite_count'] += 1
        
        # Calculate location metrics
        for location, data in location_data.items():
            data['percentage'] = round(data['count'] / len(jobs) * 100, 1)
            data['remote_percentage'] = round(data['remote_count'] / data['count'] * 100, 1) if data['count'] > 0 else 0
        
        return dict(location_data)
    
    def _analyze_role_patterns(self, jobs: List[Job]) -> Dict:
        """Analyze job role and title patterns"""
        role_keywords = defaultdict(int)
        seniority_levels = defaultdict(int)
        
        for job in jobs:
            title_lower = job.title.lower()
            
            # Extract role keywords
            common_roles = ['engineer', 'developer', 'manager', 'analyst', 'designer', 'scientist', 'architect', 'consultant']
            for role in common_roles:
                if role in title_lower:
                    role_keywords[role] += 1
            
            # Extract seniority levels
            if any(term in title_lower for term in ['senior', 'sr.', 'lead', 'principal']):
                seniority_levels['senior'] += 1
            elif any(term in title_lower for term in ['junior', 'jr.', 'entry', 'associate']):
                seniority_levels['junior'] += 1
            else:
                seniority_levels['mid'] += 1
        
        return {
            'role_keywords': dict(role_keywords),
            'seniority_distribution': dict(seniority_levels)
        }
    
    def _analyze_seasonal_patterns(self, jobs: List[Job]) -> Dict:
        """Analyze seasonal hiring patterns"""
        monthly_patterns = defaultdict(int)
        weekly_patterns = defaultdict(int)
        
        for job in jobs:
            month = job.created_at.month
            weekday = job.created_at.weekday()  # 0 = Monday
            
            monthly_patterns[month] += 1
            weekly_patterns[weekday] += 1
        
        # Convert to readable format
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            'monthly_distribution': {month_names[month-1]: count for month, count in monthly_patterns.items()},
            'weekly_distribution': {weekday_names[day]: count for day, count in weekly_patterns.items()},
            'peak_hiring_month': month_names[max(monthly_patterns, key=monthly_patterns.get) - 1] if monthly_patterns else None,
            'peak_hiring_day': weekday_names[max(weekly_patterns, key=weekly_patterns.get)] if weekly_patterns else None
        }
    
    def _calculate_market_velocity(self, jobs: List[Job]) -> Dict:
        """Calculate market velocity and competition metrics"""
        recent_jobs = [job for job in jobs if job.created_at >= datetime.now() - timedelta(days=7)]
        
        return {
            'jobs_per_day_recent': round(len(recent_jobs) / 7, 1),
            'jobs_per_day_overall': round(len(jobs) / 90, 1),  # Assuming 90-day analysis
            'market_acceleration': len(recent_jobs) > len(jobs) / 90 * 7,
            'competition_level': 'high' if len(recent_jobs) > 20 else 'medium' if len(recent_jobs) > 10 else 'low'
        }
    
    def _generate_salary_insights(self, monthly_averages: List[Dict], location_analysis: Dict, 
                                industry_salaries: Dict, growth_rate: float) -> List[str]:
        """Generate actionable salary insights"""
        insights = []
        
        # Growth trend insight
        if growth_rate > 0.1:
            insights.append(f"📈 Salary growth trending upward with {growth_rate:.1%} increase over the analysis period")
        elif growth_rate < -0.1:
            insights.append(f"📉 Salary growth slowing with {abs(growth_rate):.1%} decrease - consider expanding search criteria")
        else:
            insights.append("📊 Salary levels remain stable across the market")
        
        # Location insights
        if location_analysis:
            top_location = max(location_analysis.items(), key=lambda x: x[1]['average'])
            insights.append(f"💰 Highest paying location: {top_location[0]} (${top_location[1]['average']:,} average)")
        
        # Industry insights
        if industry_salaries:
            top_industry = max(industry_salaries.items(), key=lambda x: x[1]['average'])
            insights.append(f"🏢 Highest paying industry: {top_industry[0].title()} (${top_industry[1]['average']:,} average)")
        
        return insights
    
    def _generate_market_pattern_insights(self, growth_metrics: Dict, industry_distribution: Dict, 
                                        location_analysis: Dict, seasonal_patterns: Dict) -> List[str]:
        """Generate comprehensive market pattern insights"""
        insights = []
        
        # Growth insights
        weekly_growth = growth_metrics.get('weekly_growth_rate', 0)
        if weekly_growth > 0.2:
            insights.append("🚀 Job market is rapidly expanding - excellent time to be active in your search")
        elif weekly_growth < -0.2:
            insights.append("⚠️ Job market showing signs of contraction - focus on quality applications")
        
        # Industry insights
        if industry_distribution:
            top_industry = max(industry_distribution.items(), key=lambda x: x[1]['count'])
            insights.append(f"🏭 Most active industry: {top_industry[0].title()} ({top_industry[1]['percentage']}% of jobs)")
        
        # Location insights
        remote_jobs = sum(1 for data in location_analysis.values() if data.get('remote_percentage', 0) > 50)
        if remote_jobs > len(location_analysis) * 0.3:
            insights.append("🏠 Strong remote work opportunities available across multiple locations")
        
        # Seasonal insights
        if seasonal_patterns.get('peak_hiring_month'):
            insights.append(f"📅 Peak hiring typically occurs in {seasonal_patterns['peak_hiring_month']}")
        
        return insights


market_analysis_service = MarketAnalysisService()