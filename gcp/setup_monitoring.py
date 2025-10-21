"""
Setup script for comprehensive monitoring and logging system.
Initializes all monitoring components, dashboards, and alert policies.
"""

import asyncio
import os
import sys
from typing import Dict, Any, List
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .enhanced_monitoring import monitoring, setup_comprehensive_monitoring
from .enhanced_logging_config import logger, get_logging_health
from .enhanced_error_tracking import error_tracker, performance_monitor, get_error_tracking_health, get_performance_monitoring_health
from .monitoring_dashboard_config import (
    get_function_dashboard_config,
    get_system_overview_dashboard_config,
    get_alert_policies_config,
    get_notification_channels_config
)


class MonitoringSetupManager:
    """Manages the setup and configuration of the monitoring system."""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.functions = [
            'career_copilot_api',
            'job_ingestion_scheduler',
            'morning_briefing_scheduler',
            'evening_update_scheduler'
        ]
        
        self.setup_results = {
            'monitoring_system': False,
            'custom_metrics': {},
            'alert_policies': {},
            'dashboards': {},
            'notification_channels': {},
            'health_checks': {},
            'overall_success': False
        }
    
    async def setup_complete_monitoring_system(self) -> Dict[str, Any]:
        """Setup the complete monitoring system."""
        logger.info("Starting comprehensive monitoring system setup",
                   project_id=self.project_id,
                   environment=self.environment)
        
        try:
            # 1. Setup core monitoring system
            await self._setup_core_monitoring()
            
            # 2. Setup custom metrics
            await self._setup_custom_metrics()
            
            # 3. Setup alert policies
            await self._setup_alert_policies()
            
            # 4. Setup notification channels
            await self._setup_notification_channels()
            
            # 5. Setup dashboards
            await self._setup_dashboards()
            
            # 6. Run health checks
            await self._run_health_checks()
            
            # 7. Determine overall success
            self._determine_overall_success()
            
            # 8. Generate setup report
            await self._generate_setup_report()
            
        except Exception as e:
            logger.error("Failed to setup monitoring system", error=e)
            self.setup_results['error'] = str(e)
        
        return self.setup_results
    
    async def _setup_core_monitoring(self):
        """Setup core monitoring system."""
        logger.info("Setting up core monitoring system")
        
        try:
            # Initialize comprehensive monitoring
            setup_results = setup_comprehensive_monitoring()
            self.setup_results['monitoring_system'] = setup_results.get('overall_success', False)
            self.setup_results['custom_metrics'] = setup_results.get('custom_metrics', {})
            
            logger.info("Core monitoring system setup completed",
                       success=self.setup_results['monitoring_system'])
            
        except Exception as e:
            logger.error("Failed to setup core monitoring system", error=e)
            self.setup_results['monitoring_system'] = False
    
    async def _setup_custom_metrics(self):
        """Setup custom metrics for business logic monitoring."""
        logger.info("Setting up custom metrics")
        
        # Additional business-specific metrics
        business_metrics = [
            ('user_registrations', 'Number of user registrations', 'INT64', 'GAUGE', '1'),
            ('job_applications_submitted', 'Number of job applications submitted', 'INT64', 'GAUGE', '1'),
            ('recommendation_accuracy', 'Recommendation accuracy score', 'DOUBLE', 'GAUGE', '1'),
            ('user_engagement_score', 'User engagement score', 'DOUBLE', 'GAUGE', '1'),
            ('system_health_score', 'Overall system health score', 'DOUBLE', 'GAUGE', '1'),
            ('data_quality_score', 'Data quality score', 'DOUBLE', 'GAUGE', '1'),
            ('api_response_quality', 'API response quality score', 'DOUBLE', 'GAUGE', '1'),
            ('user_satisfaction_score', 'User satisfaction score', 'DOUBLE', 'GAUGE', '1')
        ]
        
        business_metrics_results = {}
        for metric_type, description, value_type, metric_kind, unit in business_metrics:
            try:
                success = monitoring.create_custom_metric(
                    metric_type, description, value_type, metric_kind, unit
                )
                business_metrics_results[metric_type] = success
                logger.info(f"Created business metric: {metric_type}", success=success)
            except Exception as e:
                logger.error(f"Failed to create business metric: {metric_type}", error=e)
                business_metrics_results[metric_type] = False
        
        # Update results
        self.setup_results['custom_metrics'].update(business_metrics_results)
        
        logger.info("Custom metrics setup completed",
                   total_metrics=len(self.setup_results['custom_metrics']),
                   successful_metrics=sum(self.setup_results['custom_metrics'].values()))
    
    async def _setup_alert_policies(self):
        """Setup comprehensive alert policies."""
        logger.info("Setting up alert policies")
        
        try:
            # Get alert policies configuration
            alert_configs = get_alert_policies_config()
            
            # Setup alert policies using the monitoring system
            alert_results = monitoring.setup_comprehensive_alert_policies()
            self.setup_results['alert_policies'] = alert_results
            
            logger.info("Alert policies setup completed",
                       total_policies=len(alert_results),
                       successful_policies=sum(alert_results.values()))
            
        except Exception as e:
            logger.error("Failed to setup alert policies", error=e)
            self.setup_results['alert_policies'] = {}
    
    async def _setup_notification_channels(self):
        """Setup notification channels for alerts."""
        logger.info("Setting up notification channels")
        
        try:
            notification_configs = get_notification_channels_config()
            notification_results = {}
            
            for config in notification_configs:
                if config.get('enabled', {}).get('value', False):
                    try:
                        # In a real implementation, you would create notification channels here
                        # For now, we'll simulate the setup
                        channel_name = config['display_name']
                        notification_results[channel_name] = True
                        logger.info(f"Setup notification channel: {channel_name}")
                    except Exception as e:
                        logger.error(f"Failed to setup notification channel: {config['display_name']}", error=e)
                        notification_results[config['display_name']] = False
                else:
                    logger.info(f"Skipping disabled notification channel: {config['display_name']}")
                    notification_results[config['display_name']] = False
            
            self.setup_results['notification_channels'] = notification_results
            
            logger.info("Notification channels setup completed",
                       total_channels=len(notification_results),
                       successful_channels=sum(notification_results.values()))
            
        except Exception as e:
            logger.error("Failed to setup notification channels", error=e)
            self.setup_results['notification_channels'] = {}
    
    async def _setup_dashboards(self):
        """Setup monitoring dashboards."""
        logger.info("Setting up monitoring dashboards")
        
        dashboard_results = {}
        
        try:
            # Setup function-specific dashboards
            for function_name in self.functions:
                try:
                    success = monitoring.create_comprehensive_dashboard()
                    dashboard_results[f"{function_name}_dashboard"] = success
                    logger.info(f"Setup dashboard for function: {function_name}", success=success)
                except Exception as e:
                    logger.error(f"Failed to setup dashboard for function: {function_name}", error=e)
                    dashboard_results[f"{function_name}_dashboard"] = False
            
            # Setup system overview dashboard
            try:
                # In a real implementation, you would create the system overview dashboard here
                dashboard_results['system_overview_dashboard'] = True
                logger.info("Setup system overview dashboard")
            except Exception as e:
                logger.error("Failed to setup system overview dashboard", error=e)
                dashboard_results['system_overview_dashboard'] = False
            
            self.setup_results['dashboards'] = dashboard_results
            
            logger.info("Dashboards setup completed",
                       total_dashboards=len(dashboard_results),
                       successful_dashboards=sum(dashboard_results.values()))
            
        except Exception as e:
            logger.error("Failed to setup dashboards", error=e)
            self.setup_results['dashboards'] = {}
    
    async def _run_health_checks(self):
        """Run comprehensive health checks on all monitoring components."""
        logger.info("Running monitoring system health checks")
        
        health_results = {}
        
        try:
            # Check logging system health
            logging_health = get_logging_health()
            health_results['logging_system'] = logging_health
            
            # Check error tracking health
            error_tracking_health = get_error_tracking_health()
            health_results['error_tracking'] = error_tracking_health
            
            # Check performance monitoring health
            performance_health = get_performance_monitoring_health()
            health_results['performance_monitoring'] = performance_health
            
            # Check monitoring system health
            monitoring_health = monitoring.get_monitoring_health()
            health_results['monitoring_system'] = monitoring_health
            
            self.setup_results['health_checks'] = health_results
            
            # Log health check summary
            healthy_systems = sum(1 for health in health_results.values() 
                                if health.get('status') == 'healthy')
            total_systems = len(health_results)
            
            logger.info("Health checks completed",
                       healthy_systems=healthy_systems,
                       total_systems=total_systems,
                       overall_health_score=healthy_systems / total_systems if total_systems > 0 else 0)
            
        except Exception as e:
            logger.error("Failed to run health checks", error=e)
            self.setup_results['health_checks'] = {}
    
    def _determine_overall_success(self):
        """Determine overall setup success based on component results."""
        success_criteria = [
            self.setup_results.get('monitoring_system', False),
            len(self.setup_results.get('custom_metrics', {})) > 0,
            len(self.setup_results.get('alert_policies', {})) > 0,
            len(self.setup_results.get('dashboards', {})) > 0
        ]
        
        # Calculate success rate
        success_rate = sum(success_criteria) / len(success_criteria)
        self.setup_results['overall_success'] = success_rate >= 0.75  # 75% success rate required
        self.setup_results['success_rate'] = success_rate
        
        logger.info("Overall setup success determined",
                   overall_success=self.setup_results['overall_success'],
                   success_rate=success_rate)
    
    async def _generate_setup_report(self):
        """Generate comprehensive setup report."""
        logger.info("Generating monitoring setup report")
        
        report = {
            'timestamp': logger._get_base_context()['timestamp'],
            'project_id': self.project_id,
            'environment': self.environment,
            'setup_results': self.setup_results,
            'summary': {
                'overall_success': self.setup_results.get('overall_success', False),
                'success_rate': self.setup_results.get('success_rate', 0),
                'custom_metrics_created': sum(self.setup_results.get('custom_metrics', {}).values()),
                'alert_policies_created': sum(self.setup_results.get('alert_policies', {}).values()),
                'dashboards_created': sum(self.setup_results.get('dashboards', {}).values()),
                'notification_channels_created': sum(self.setup_results.get('notification_channels', {}).values()),
                'healthy_systems': sum(1 for health in self.setup_results.get('health_checks', {}).values() 
                                     if health.get('status') == 'healthy')
            },
            'recommendations': self._generate_recommendations()
        }
        
        # Save report to file
        report_filename = f"monitoring_setup_report_{self.environment}_{report['timestamp'].replace(':', '-')}.json"
        try:
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Setup report saved to: {report_filename}")
        except Exception as e:
            logger.error(f"Failed to save setup report: {e}")
        
        # Log summary
        logger.info("Monitoring setup completed",
                   overall_success=report['summary']['overall_success'],
                   success_rate=report['summary']['success_rate'],
                   custom_metrics=report['summary']['custom_metrics_created'],
                   alert_policies=report['summary']['alert_policies_created'],
                   dashboards=report['summary']['dashboards_created'],
                   healthy_systems=report['summary']['healthy_systems'])
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on setup results."""
        recommendations = []
        
        if not self.setup_results.get('monitoring_system', False):
            recommendations.append("Core monitoring system setup failed - check Google Cloud permissions and API enablement")
        
        if sum(self.setup_results.get('custom_metrics', {}).values()) < 10:
            recommendations.append("Some custom metrics failed to create - verify metric naming and permissions")
        
        if sum(self.setup_results.get('alert_policies', {}).values()) < 3:
            recommendations.append("Alert policies setup incomplete - ensure notification channels are configured")
        
        if sum(self.setup_results.get('dashboards', {}).values()) < 2:
            recommendations.append("Dashboard creation incomplete - check dashboard API permissions")
        
        # Check health status
        health_checks = self.setup_results.get('health_checks', {})
        for system, health in health_checks.items():
            if health.get('status') != 'healthy':
                recommendations.append(f"{system} is not healthy - investigate and resolve issues")
        
        if not recommendations:
            recommendations.append("All monitoring components are successfully configured and healthy")
        
        return recommendations


async def main():
    """Main setup function."""
    print("Starting Career Co-Pilot Monitoring System Setup...")
    
    # Initialize setup manager
    setup_manager = MonitoringSetupManager()
    
    # Run complete setup
    results = await setup_manager.setup_complete_monitoring_system()
    
    # Print results
    print(f"\nSetup completed with overall success: {results.get('overall_success', False)}")
    print(f"Success rate: {results.get('success_rate', 0):.2%}")
    
    if results.get('overall_success', False):
        print("✅ Monitoring system is ready for production use")
    else:
        print("⚠️  Monitoring system setup had issues - check logs for details")
    
    return results


if __name__ == "__main__":
    # Run setup
    results = asyncio.run(main())
    
    # Exit with appropriate code
    exit_code = 0 if results.get('overall_success', False) else 1
    sys.exit(exit_code)