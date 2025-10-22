"""
Scheduled Analytics Reports Service
Generates and sends automated analytics reports via email
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import io
import base64

from app.models.user import User
from app.services.advanced_user_analytics_service import advanced_user_analytics_service
from app.services.market_analysis_service import market_analysis_service
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ScheduledAnalyticsReportsService:
    """Service for generating and sending scheduled analytics reports"""
    
    def __init__(self):
        self.smtp_settings = {
            'host': settings.smtp_host,
            'port': settings.smtp_port,
            'username': settings.smtp_user,
            'password': settings.smtp_password,
            'use_tls': settings.smtp_use_tls
        }
    
    def generate_weekly_report(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Generate comprehensive weekly analytics report"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'error': 'User not found'}
            
            # Get analytics data for the past week
            success_rates = advanced_user_analytics_service.calculate_detailed_success_rates(
                db, user_id, days=7
            )
            
            conversion_funnel = advanced_user_analytics_service.analyze_conversion_funnel(
                db, user_id, days=7
            )
            
            benchmarks = advanced_user_analytics_service.generate_performance_benchmarks(
                db, user_id, days=7
            )
            
            market_analysis = market_analysis_service.analyze_job_market_patterns(
                db, user_id, days=7
            )
            
            # Create report structure
            report = {
                'report_type': 'weekly',
                'generated_at': datetime.now().isoformat(),
                'user_id': user_id,
                'username': user.username,
                'period': 'Last 7 days',
                'summary': self._create_weekly_summary(success_rates, conversion_funnel, benchmarks),
                'detailed_analytics': {
                    'success_rates': success_rates,
                    'conversion_funnel': conversion_funnel,
                    'performance_benchmarks': benchmarks,
                    'market_analysis': market_analysis
                },
                'key_insights': self._generate_weekly_insights(success_rates, benchmarks, market_analysis),
                'recommendations': self._generate_weekly_recommendations(success_rates, benchmarks),
                'next_week_goals': self._suggest_next_week_goals(success_rates, benchmarks)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate weekly report for user {user_id}: {str(e)}")
            return {'error': f'Failed to generate report: {str(e)}'}
    
    def generate_monthly_report(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Generate comprehensive monthly analytics report"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'error': 'User not found'}
            
            # Get analytics data for the past month
            success_rates = advanced_user_analytics_service.calculate_detailed_success_rates(
                db, user_id, days=30
            )
            
            conversion_funnel = advanced_user_analytics_service.analyze_conversion_funnel(
                db, user_id, days=30
            )
            
            benchmarks = advanced_user_analytics_service.generate_performance_benchmarks(
                db, user_id, days=30
            )
            
            predictive = advanced_user_analytics_service.create_predictive_analytics(
                db, user_id, days=30
            )
            
            market_dashboard = market_analysis_service.create_market_dashboard_data(
                db, user_id
            )
            
            # Create comprehensive monthly report
            report = {
                'report_type': 'monthly',
                'generated_at': datetime.now().isoformat(),
                'user_id': user_id,
                'username': user.username,
                'period': 'Last 30 days',
                'executive_summary': self._create_monthly_executive_summary(
                    success_rates, benchmarks, predictive, market_dashboard
                ),
                'detailed_analytics': {
                    'success_rates': success_rates,
                    'conversion_funnel': conversion_funnel,
                    'performance_benchmarks': benchmarks,
                    'predictive_analytics': predictive,
                    'market_dashboard': market_dashboard
                },
                'trends_analysis': self._analyze_monthly_trends(success_rates),
                'competitive_position': self._analyze_competitive_position(benchmarks),
                'market_insights': market_dashboard.get('market_patterns', {}).get('market_insights', []),
                'strategic_recommendations': self._generate_strategic_recommendations(
                    benchmarks, predictive, market_dashboard
                ),
                'next_month_strategy': self._create_next_month_strategy(predictive, benchmarks)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate monthly report for user {user_id}: {str(e)}")
            return {'error': f'Failed to generate report: {str(e)}'}
    
    def send_report_email(self, report: Dict[str, Any], recipient_email: str) -> bool:
        """Send analytics report via email"""
        try:
            if not all([self.smtp_settings['host'], self.smtp_settings['username'], self.smtp_settings['password']]):
                logger.warning("SMTP settings not configured, skipping email send")
                return False
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Career Copilot {report['report_type'].title()} Analytics Report"
            msg['From'] = self.smtp_settings['username']
            msg['To'] = recipient_email
            
            # Create HTML email content
            html_content = self._create_html_email_content(report)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Create JSON attachment
            json_content = json.dumps(report, indent=2)
            json_attachment = MIMEBase('application', 'json')
            json_attachment.set_payload(json_content.encode())
            encoders.encode_base64(json_attachment)
            json_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="analytics_report_{report["report_type"]}_{datetime.now().strftime("%Y%m%d")}.json"'
            )
            msg.attach(json_attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_settings['host'], self.smtp_settings['port']) as server:
                if self.smtp_settings['use_tls']:
                    server.starttls()
                server.login(self.smtp_settings['username'], self.smtp_settings['password'])
                server.send_message(msg)
            
            logger.info(f"Successfully sent {report['report_type']} report to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send report email: {str(e)}")
            return False
    
    def schedule_weekly_reports(self, db: Session) -> Dict[str, Any]:
        """Generate and send weekly reports for all users"""
        results = {
            'total_users': 0,
            'reports_generated': 0,
            'emails_sent': 0,
            'errors': []
        }
        
        try:
            # Get all active users
            users = db.query(User).all()
            results['total_users'] = len(users)
            
            for user in users:
                try:
                    # Generate weekly report
                    report = self.generate_weekly_report(db, user.id)
                    
                    if 'error' not in report:
                        results['reports_generated'] += 1
                        
                        # Send email if user has email
                        if user.email:
                            if self.send_report_email(report, user.email):
                                results['emails_sent'] += 1
                            else:
                                results['errors'].append(f"Failed to send email to {user.username}")
                        else:
                            results['errors'].append(f"No email address for user {user.username}")
                    else:
                        results['errors'].append(f"Failed to generate report for {user.username}: {report['error']}")
                        
                except Exception as e:
                    results['errors'].append(f"Error processing user {user.username}: {str(e)}")
            
            logger.info(f"Weekly reports completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to schedule weekly reports: {str(e)}")
            results['errors'].append(f"Scheduling error: {str(e)}")
            return results
    
    def schedule_monthly_reports(self, db: Session) -> Dict[str, Any]:
        """Generate and send monthly reports for all users"""
        results = {
            'total_users': 0,
            'reports_generated': 0,
            'emails_sent': 0,
            'errors': []
        }
        
        try:
            # Get all active users
            users = db.query(User).all()
            results['total_users'] = len(users)
            
            for user in users:
                try:
                    # Generate monthly report
                    report = self.generate_monthly_report(db, user.id)
                    
                    if 'error' not in report:
                        results['reports_generated'] += 1
                        
                        # Send email if user has email
                        if user.email:
                            if self.send_report_email(report, user.email):
                                results['emails_sent'] += 1
                            else:
                                results['errors'].append(f"Failed to send email to {user.username}")
                        else:
                            results['errors'].append(f"No email address for user {user.username}")
                    else:
                        results['errors'].append(f"Failed to generate report for {user.username}: {report['error']}")
                        
                except Exception as e:
                    results['errors'].append(f"Error processing user {user.username}: {str(e)}")
            
            logger.info(f"Monthly reports completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to schedule monthly reports: {str(e)}")
            results['errors'].append(f"Scheduling error: {str(e)}")
            return results
    
    # Helper methods
    
    def _create_weekly_summary(self, success_rates: Dict, conversion_funnel: Dict, benchmarks: Dict) -> Dict[str, Any]:
        """Create weekly summary from analytics data"""
        if 'error' in success_rates:
            return {'error': 'Insufficient data for weekly summary'}
        
        return {
            'applications_submitted': success_rates.get('total_applications', 0),
            'interview_rate': success_rates.get('success_rates', {}).get('application_to_interview', 0),
            'success_rate': success_rates.get('success_rates', {}).get('overall_success', 0),
            'performance_score': benchmarks.get('overall_performance_score', 0),
            'market_position': benchmarks.get('market_position', 'average'),
            'trend_direction': success_rates.get('trends', {}).get('trend_direction', 'stable')
        }
    
    def _create_monthly_executive_summary(self, success_rates: Dict, benchmarks: Dict, 
                                        predictive: Dict, market_dashboard: Dict) -> Dict[str, Any]:
        """Create monthly executive summary"""
        if 'error' in success_rates:
            return {'error': 'Insufficient data for monthly summary'}
        
        return {
            'total_applications': success_rates.get('total_applications', 0),
            'overall_success_rate': success_rates.get('success_rates', {}).get('overall_success', 0),
            'interview_conversion_rate': success_rates.get('success_rates', {}).get('application_to_interview', 0),
            'offer_conversion_rate': success_rates.get('success_rates', {}).get('interview_to_offer', 0),
            'performance_score': benchmarks.get('overall_performance_score', 0),
            'market_position': benchmarks.get('market_position', 'average'),
            'success_probability': predictive.get('predictive_analytics', {}).get('success_probability', 0),
            'estimated_time_to_offer': predictive.get('predictive_analytics', {}).get('estimated_time_to_offer', 0),
            'market_growth': market_dashboard.get('summary', {}).get('market_growth', 0),
            'active_opportunities': market_dashboard.get('summary', {}).get('active_alerts', 0)
        }
    
    def _generate_weekly_insights(self, success_rates: Dict, benchmarks: Dict, market_analysis: Dict) -> List[str]:
        """Generate weekly insights"""
        insights = []
        
        if 'error' not in success_rates:
            trend = success_rates.get('trends', {}).get('trend_direction', 'stable')
            if trend == 'improving':
                insights.append("📈 Your performance is trending upward this week")
            elif trend == 'declining':
                insights.append("📉 Performance declined this week - consider strategy adjustment")
            else:
                insights.append("📊 Performance remained stable this week")
        
        if 'error' not in benchmarks:
            position = benchmarks.get('market_position', 'average')
            if position == 'top_performer':
                insights.append("🏆 You're performing in the top tier of job seekers")
            elif position == 'above_average':
                insights.append("👍 Your performance is above market average")
            else:
                insights.append("💪 Focus on improvement to reach above-average performance")
        
        return insights
    
    def _generate_weekly_recommendations(self, success_rates: Dict, benchmarks: Dict) -> List[str]:
        """Generate weekly recommendations"""
        recommendations = []
        
        if 'error' not in success_rates:
            apps = success_rates.get('total_applications', 0)
            if apps < 5:
                recommendations.append("Increase application volume - aim for 5-10 applications per week")
            elif apps > 20:
                recommendations.append("Consider focusing on quality over quantity in applications")
        
        if 'error' not in benchmarks:
            recs = benchmarks.get('recommendations', [])
            recommendations.extend(recs[:3])  # Top 3 recommendations
        
        return recommendations
    
    def _suggest_next_week_goals(self, success_rates: Dict, benchmarks: Dict) -> List[str]:
        """Suggest goals for next week"""
        goals = []
        
        if 'error' not in success_rates:
            current_apps = success_rates.get('total_applications', 0)
            target_apps = max(5, current_apps + 2)
            goals.append(f"Submit {target_apps} quality applications")
            
            interview_rate = success_rates.get('success_rates', {}).get('application_to_interview', 0)
            if interview_rate < 15:
                goals.append("Improve application quality to increase interview rate")
        
        goals.append("Monitor weekly performance trends")
        goals.append("Update job search strategy based on market insights")
        
        return goals
    
    def _analyze_monthly_trends(self, success_rates: Dict) -> Dict[str, Any]:
        """Analyze monthly trends"""
        if 'error' in success_rates:
            return {'error': 'Insufficient data for trend analysis'}
        
        weekly_performance = success_rates.get('weekly_performance', [])
        
        if len(weekly_performance) >= 4:
            recent_weeks = weekly_performance[-2:]
            early_weeks = weekly_performance[:2]
            
            recent_avg = sum(w['success_rate'] for w in recent_weeks) / len(recent_weeks)
            early_avg = sum(w['success_rate'] for w in early_weeks) / len(early_weeks)
            
            improvement = recent_avg - early_avg
            
            return {
                'improvement_rate': improvement,
                'trend_direction': 'improving' if improvement > 1 else 'declining' if improvement < -1 else 'stable',
                'consistency': 'high' if max(w['success_rate'] for w in weekly_performance) - min(w['success_rate'] for w in weekly_performance) < 10 else 'low'
            }
        
        return {'insufficient_data': True}
    
    def _analyze_competitive_position(self, benchmarks: Dict) -> Dict[str, Any]:
        """Analyze competitive position"""
        if 'error' in benchmarks:
            return {'error': 'Insufficient data for competitive analysis'}
        
        position = benchmarks.get('market_position', 'average')
        score = benchmarks.get('overall_performance_score', 0)
        
        return {
            'market_position': position,
            'performance_score': score,
            'percentile_estimate': 90 if position == 'top_performer' else 75 if position == 'above_average' else 50,
            'competitive_advantages': self._identify_competitive_advantages(benchmarks),
            'improvement_areas': self._identify_improvement_areas(benchmarks)
        }
    
    def _generate_strategic_recommendations(self, benchmarks: Dict, predictive: Dict, market_dashboard: Dict) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # From benchmarks
        if 'error' not in benchmarks:
            recommendations.extend(benchmarks.get('recommendations', [])[:2])
        
        # From predictive analytics
        if 'error' not in predictive:
            recommendations.extend(predictive.get('recommendations', [])[:2])
        
        # From market analysis
        if 'error' not in market_dashboard:
            market_insights = market_dashboard.get('market_patterns', {}).get('market_insights', [])
            recommendations.extend(market_insights[:1])
        
        return recommendations[:5]  # Top 5 strategic recommendations
    
    def _create_next_month_strategy(self, predictive: Dict, benchmarks: Dict) -> Dict[str, Any]:
        """Create next month strategy"""
        strategy = {
            'focus_areas': [],
            'targets': {},
            'action_items': []
        }
        
        if 'error' not in predictive:
            pred_analytics = predictive.get('predictive_analytics', {})
            strategy['targets']['recommended_applications_per_week'] = pred_analytics.get('recommended_application_rate', 10)
            strategy['targets']['success_probability_target'] = min(95, pred_analytics.get('success_probability', 0) + 10)
        
        if 'error' not in benchmarks:
            position = benchmarks.get('market_position', 'average')
            if position in ['needs_improvement', 'average']:
                strategy['focus_areas'].append('Improve application quality and targeting')
                strategy['focus_areas'].append('Enhance interview preparation')
            
            strategy['action_items'].extend(benchmarks.get('recommendations', [])[:3])
        
        return strategy
    
    def _identify_competitive_advantages(self, benchmarks: Dict) -> List[str]:
        """Identify competitive advantages"""
        advantages = []
        
        benchmark_list = benchmarks.get('benchmarks', [])
        for benchmark in benchmark_list:
            if benchmark.get('percentile_rank', 0) >= 75:
                advantages.append(f"Strong {benchmark['metric'].lower()}")
        
        return advantages
    
    def _identify_improvement_areas(self, benchmarks: Dict) -> List[str]:
        """Identify improvement areas"""
        areas = []
        
        benchmark_list = benchmarks.get('benchmarks', [])
        for benchmark in benchmark_list:
            if benchmark.get('percentile_rank', 0) < 50:
                areas.append(f"{benchmark['metric']} needs improvement")
        
        return areas
    
    def _create_html_email_content(self, report: Dict[str, Any]) -> str:
        """Create HTML email content for the report"""
        report_type = report.get('report_type', 'analytics').title()
        username = report.get('username', 'User')
        period = report.get('period', 'Recent period')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f8ff; padding: 20px; border-radius: 10px; }}
                .summary {{ background-color: #f9f9f9; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: white; border-radius: 5px; border-left: 4px solid #007acc; }}
                .insights {{ background-color: #e8f4fd; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .recommendations {{ background-color: #f0f8e8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                ul {{ padding-left: 20px; }}
                li {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Career Copilot {report_type} Report</h1>
                <p>Hello {username}! Here's your {report_type.lower()} analytics report for {period}.</p>
            </div>
        """
        
        # Add summary section
        if report_type == 'Weekly':
            summary = report.get('summary', {})
            if 'error' not in summary:
                html += f"""
                <div class="summary">
                    <h2>📊 Weekly Summary</h2>
                    <div class="metric">
                        <strong>Applications:</strong> {summary.get('applications_submitted', 0)}
                    </div>
                    <div class="metric">
                        <strong>Interview Rate:</strong> {summary.get('interview_rate', 0):.1f}%
                    </div>
                    <div class="metric">
                        <strong>Success Rate:</strong> {summary.get('success_rate', 0):.1f}%
                    </div>
                    <div class="metric">
                        <strong>Performance Score:</strong> {summary.get('performance_score', 0):.0f}/100
                    </div>
                </div>
                """
        else:  # Monthly
            exec_summary = report.get('executive_summary', {})
            if 'error' not in exec_summary:
                html += f"""
                <div class="summary">
                    <h2>📈 Executive Summary</h2>
                    <div class="metric">
                        <strong>Total Applications:</strong> {exec_summary.get('total_applications', 0)}
                    </div>
                    <div class="metric">
                        <strong>Success Rate:</strong> {exec_summary.get('overall_success_rate', 0):.1f}%
                    </div>
                    <div class="metric">
                        <strong>Performance Score:</strong> {exec_summary.get('performance_score', 0):.0f}/100
                    </div>
                    <div class="metric">
                        <strong>Success Probability:</strong> {exec_summary.get('success_probability', 0):.1f}%
                    </div>
                </div>
                """
        
        # Add insights
        insights = report.get('key_insights', [])
        if insights:
            html += """
            <div class="insights">
                <h2>💡 Key Insights</h2>
                <ul>
            """
            for insight in insights:
                html += f"<li>{insight}</li>"
            html += "</ul></div>"
        
        # Add recommendations
        recommendations = report.get('recommendations', [])
        if not recommendations:
            recommendations = report.get('strategic_recommendations', [])
        
        if recommendations:
            html += """
            <div class="recommendations">
                <h2>🎯 Recommendations</h2>
                <ul>
            """
            for rec in recommendations:
                html += f"<li>{rec}</li>"
            html += "</ul></div>"
        
        # Add footer
        html += f"""
            <div style="margin-top: 30px; padding: 20px; background-color: #f0f0f0; border-radius: 5px;">
                <p><strong>📊 Detailed Analytics:</strong> The complete analytics data is attached as a JSON file.</p>
                <p><strong>🔗 Dashboard:</strong> Log in to your Career Copilot dashboard for interactive charts and detailed analysis.</p>
                <p><em>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</em></p>
            </div>
        </body>
        </html>
        """
        
        return html


# Create service instance
scheduled_analytics_reports_service = ScheduledAnalyticsReportsService()