"""
Scheduled Analytics Collection Tasks for Career Co-Pilot System
Periodic tasks to collect and analyze user activity, application success, and market trends
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from celery import Celery

from app.core.database import get_db
from app.models.user import User
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

# Initialize Celery app (this would be configured in your main Celery setup)
celery_app = Celery('analytics_tasks')


@celery_app.task(name="collect_daily_analytics")
def collect_daily_analytics():
    """Daily task to collect analytics data for all active users"""
    logger.info("Starting daily analytics collection")
    
    db = next(get_db())
    try:
        # Get all active users
        active_users = db.query(User).filter(User.is_active == True).all()
        
        results = {
            'processed_users': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'errors': []
        }
        
        for user in active_users:
            try:
                # Create analytics service instance with database session
                analytics_service_instance = analytics_service.__class__(db=db)
                
                # Collect user engagement metrics
                engagement_result = analytics_service_instance.collect_user_engagement_metrics(
                    user.id, days=7  # Weekly engagement
                )
                
                # Monitor application success rates
                success_result = analytics_service_instance.monitor_application_success_rates(
                    user.id, days=30  # Monthly success monitoring
                )
                
                # Analyze market trends (only for users with recent activity)
                last_active = user.last_active or user.created_at
                if last_active >= datetime.utcnow() - timedelta(days=7):
                    market_result = analytics_service_instance.analyze_market_trends(
                        user.id, days=7  # Weekly market analysis
                    )
                
                results['successful_collections'] += 1
                logger.info(f"Successfully collected analytics for user {user.id}")
                
            except Exception as e:
                results['failed_collections'] += 1
                error_msg = f"Failed to collect analytics for user {user.id}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
            
            results['processed_users'] += 1
        
        logger.info(f"Daily analytics collection completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Daily analytics collection failed: {e}")
        return {'error': str(e)}
    finally:
        db.close()


@celery_app.task(name="generate_weekly_analytics_reports")
def generate_weekly_analytics_reports():
    """Weekly task to generate comprehensive analytics reports"""
    logger.info("Starting weekly analytics report generation")
    
    db = next(get_db())
    try:
        # Get users who have been active in the last week
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        active_users = db.query(User).filter(
            User.is_active == True,
            User.last_active >= cutoff_date
        ).all()
        
        results = {
            'processed_users': 0,
            'successful_reports': 0,
            'failed_reports': 0,
            'errors': []
        }
        
        for user in active_users:
            try:
                # Create analytics service instance with database session
                analytics_service_instance = analytics_service.__class__(db=db)
                
                # Generate comprehensive analytics report
                report = analytics_service_instance.get_comprehensive_analytics_report(
                    user.id, days=90  # 3-month comprehensive report
                )
                
                if 'error' not in report:
                    results['successful_reports'] += 1
                    logger.info(f"Successfully generated weekly report for user {user.id}")
                else:
                    results['failed_reports'] += 1
                    results['errors'].append(f"Report generation failed for user {user.id}: {report['error']}")
                
            except Exception as e:
                results['failed_reports'] += 1
                error_msg = f"Failed to generate report for user {user.id}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
            
            results['processed_users'] += 1
        
        logger.info(f"Weekly analytics report generation completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Weekly analytics report generation failed: {e}")
        return {'error': str(e)}
    finally:
        db.close()


@celery_app.task(name="analyze_market_trends_global")
def analyze_market_trends_global():
    """Daily task to analyze global market trends across all job data"""
    logger.info("Starting global market trends analysis")
    
    db = next(get_db())
    try:
        # Use a system user ID (0) for global market analysis
        system_user_id = 0
        
        # Create analytics service instance with database session
        analytics_service_instance = analytics_service.__class__(db=db)
        
        # Analyze market trends with extended period for better insights
        market_analysis = analytics_service_instance.analyze_market_trends(
            system_user_id, days=30
        )
        
        if 'error' not in market_analysis:
            logger.info("Successfully completed global market trends analysis")
            
            # Extract key insights for logging
            total_jobs = market_analysis.get('total_jobs_analyzed', 0)
            growth_rate = market_analysis.get('growth_metrics', {}).get('growth_rate_percentage', 0)
            top_skills = list(market_analysis.get('skill_demand', {}).get('top_skills', {}).keys())[:5]
            
            logger.info(f"Market analysis summary: {total_jobs} jobs analyzed, "
                       f"{growth_rate}% growth rate, top skills: {top_skills}")
            
            return {
                'success': True,
                'total_jobs_analyzed': total_jobs,
                'growth_rate': growth_rate,
                'top_skills': top_skills,
                'analysis_date': market_analysis.get('analysis_date')
            }
        else:
            logger.error(f"Global market trends analysis failed: {market_analysis['error']}")
            return {'error': market_analysis['error']}
        
    except Exception as e:
        logger.error(f"Global market trends analysis failed: {e}")
        return {'error': str(e)}
    finally:
        db.close()


@celery_app.task(name="cleanup_old_analytics_data")
def cleanup_old_analytics_data(retention_days: int = 365):
    """Task to cleanup old analytics data to manage database size"""
    logger.info(f"Starting analytics data cleanup (retention: {retention_days} days)")
    
    db = next(get_db())
    try:
        from app.models.analytics import Analytics
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Count records to be deleted
        old_records_count = db.query(Analytics).filter(
            Analytics.generated_at < cutoff_date
        ).count()
        
        if old_records_count > 0:
            # Delete old analytics records
            deleted_count = db.query(Analytics).filter(
                Analytics.generated_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old analytics records")
            return {
                'success': True,
                'deleted_records': deleted_count,
                'cutoff_date': cutoff_date.isoformat()
            }
        else:
            logger.info("No old analytics records found for cleanup")
            return {
                'success': True,
                'deleted_records': 0,
                'message': 'No records to cleanup'
            }
        
    except Exception as e:
        logger.error(f"Analytics data cleanup failed: {e}")
        db.rollback()
        return {'error': str(e)}
    finally:
        db.close()


@celery_app.task(name="generate_analytics_summary_report")
def generate_analytics_summary_report():
    """Generate system-wide analytics summary report"""
    logger.info("Starting analytics summary report generation")
    
    db = next(get_db())
    try:
        from app.models.analytics import Analytics
        
        # Get analytics data from the last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Count analytics records by type
        analytics_counts = db.query(
            Analytics.type,
            db.func.count(Analytics.id).label('count')
        ).filter(
            Analytics.generated_at >= cutoff_date
        ).group_by(Analytics.type).all()
        
        # Get total active users
        active_users_count = db.query(User).filter(
            User.is_active == True,
            User.last_active >= cutoff_date
        ).count()
        
        # Calculate analytics coverage
        users_with_analytics = db.query(Analytics.user_id).filter(
            Analytics.generated_at >= cutoff_date
        ).distinct().count()
        
        coverage_percentage = (users_with_analytics / active_users_count * 100) if active_users_count > 0 else 0
        
        summary_report = {
            'generated_at': datetime.utcnow().isoformat(),
            'period_days': 30,
            'active_users': active_users_count,
            'users_with_analytics': users_with_analytics,
            'analytics_coverage_percentage': round(coverage_percentage, 1),
            'analytics_by_type': {row.type: row.count for row in analytics_counts},
            'total_analytics_records': sum(row.count for row in analytics_counts)
        }
        
        logger.info(f"Analytics summary report generated: {summary_report}")
        return summary_report
        
    except Exception as e:
        logger.error(f"Analytics summary report generation failed: {e}")
        return {'error': str(e)}
    finally:
        db.close()


# Celery beat schedule configuration (add this to your main Celery config)
ANALYTICS_CELERY_BEAT_SCHEDULE = {
    'collect-daily-analytics': {
        'task': 'collect_daily_analytics',
        'schedule': 3600.0 * 24,  # Daily at midnight
    },
    'generate-weekly-analytics-reports': {
        'task': 'generate_weekly_analytics_reports',
        'schedule': 3600.0 * 24 * 7,  # Weekly on Sunday
    },
    'analyze-market-trends-global': {
        'task': 'analyze_market_trends_global',
        'schedule': 3600.0 * 24,  # Daily
    },
    'cleanup-old-analytics-data': {
        'task': 'cleanup_old_analytics_data',
        'schedule': 3600.0 * 24 * 7,  # Weekly cleanup
        'kwargs': {'retention_days': 365}
    },
    'generate-analytics-summary-report': {
        'task': 'generate_analytics_summary_report',
        'schedule': 3600.0 * 24,  # Daily summary
    }
}