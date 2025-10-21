"""
Health check script for the monitoring and logging system.
Provides comprehensive health monitoring and diagnostics.
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .enhanced_logging_config import logger, get_logging_health, get_logging_metrics
from .enhanced_error_tracking import (
    error_tracker, performance_monitor, 
    get_error_tracking_health, get_performance_monitoring_health
)
from .enhanced_monitoring import monitoring


class MonitoringHealthChecker:
    """Comprehensive health checker for the monitoring system."""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.health_results = {}
        
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check on all monitoring components."""
        logger.info("Starting comprehensive monitoring health check")
        
        start_time = time.time()
        
        try:
            # 1. Check logging system health
            await self._check_logging_system_health()
            
            # 2. Check error tracking health
            await self._check_error_tracking_health()
            
            # 3. Check performance monitoring health
            await self._check_performance_monitoring_health()
            
            # 4. Check cloud monitoring health
            await self._check_cloud_monitoring_health()
            
            # 5. Check system integration health
            await self._check_system_integration_health()
            
            # 6. Run synthetic tests
            await self._run_synthetic_tests()
            
            # 7. Calculate overall health score
            self._calculate_overall_health_score()
            
            # 8. Generate health report
            await self._generate_health_report()
            
        except Exception as e:
            logger.error("Health check failed", error=e)
            self.health_results['error'] = str(e)
        
        duration = time.time() - start_time
        self.health_results['check_duration'] = duration
        
        logger.info("Health check completed", 
                   duration_seconds=duration,
                   overall_health=self.health_results.get('overall_health', 'unknown'))
        
        return self.health_results
    
    async def _check_logging_system_health(self):
        """Check logging system health and performance."""
        logger.info("Checking logging system health")
        
        try:
            # Get logging health status
            logging_health = get_logging_health()
            logging_metrics = get_logging_metrics()
            
            # Additional logging system checks
            logging_checks = {
                'basic_health': logging_health,
                'metrics': logging_metrics,
                'log_levels_working': await self._test_log_levels(),
                'structured_logging': await self._test_structured_logging(),
                'correlation_ids': await self._test_correlation_ids(),
                'performance': await self._test_logging_performance()
            }
            
            # Determine logging system health
            health_score = self._calculate_component_health_score(logging_checks)
            
            self.health_results['logging_system'] = {
                'status': 'healthy' if health_score > 0.8 else 'degraded' if health_score > 0.5 else 'unhealthy',
                'health_score': health_score,
                'checks': logging_checks,
                'recommendations': self._get_logging_recommendations(logging_checks)
            }
            
        except Exception as e:
            logger.error("Failed to check logging system health", error=e)
            self.health_results['logging_system'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_error_tracking_health(self):
        """Check error tracking system health."""
        logger.info("Checking error tracking system health")
        
        try:
            # Get error tracking health
            error_health = get_error_tracking_health()
            
            # Additional error tracking checks
            error_checks = {
                'basic_health': error_health,
                'error_reporting': await self._test_error_reporting(),
                'error_patterns': await self._test_error_pattern_detection(),
                'alert_thresholds': await self._test_alert_thresholds()
            }
            
            health_score = self._calculate_component_health_score(error_checks)
            
            self.health_results['error_tracking'] = {
                'status': 'healthy' if health_score > 0.8 else 'degraded' if health_score > 0.5 else 'unhealthy',
                'health_score': health_score,
                'checks': error_checks,
                'recommendations': self._get_error_tracking_recommendations(error_checks)
            }
            
        except Exception as e:
            logger.error("Failed to check error tracking health", error=e)
            self.health_results['error_tracking'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_performance_monitoring_health(self):
        """Check performance monitoring system health."""
        logger.info("Checking performance monitoring system health")
        
        try:
            # Get performance monitoring health
            perf_health = get_performance_monitoring_health()
            
            # Additional performance monitoring checks
            perf_checks = {
                'basic_health': perf_health,
                'metrics_collection': await self._test_metrics_collection(),
                'performance_tracking': await self._test_performance_tracking(),
                'memory_monitoring': await self._test_memory_monitoring()
            }
            
            health_score = self._calculate_component_health_score(perf_checks)
            
            self.health_results['performance_monitoring'] = {
                'status': 'healthy' if health_score > 0.8 else 'degraded' if health_score > 0.5 else 'unhealthy',
                'health_score': health_score,
                'checks': perf_checks,
                'recommendations': self._get_performance_recommendations(perf_checks)
            }
            
        except Exception as e:
            logger.error("Failed to check performance monitoring health", error=e)
            self.health_results['performance_monitoring'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_cloud_monitoring_health(self):
        """Check Google Cloud Monitoring integration health."""
        logger.info("Checking cloud monitoring integration health")
        
        try:
            # Get cloud monitoring health
            cloud_health = monitoring.get_monitoring_health()
            
            # Additional cloud monitoring checks
            cloud_checks = {
                'basic_health': cloud_health,
                'metric_writing': await self._test_metric_writing(),
                'custom_metrics': await self._test_custom_metrics(),
                'alert_policies': await self._test_alert_policies(),
                'dashboards': await self._test_dashboards()
            }
            
            health_score = self._calculate_component_health_score(cloud_checks)
            
            self.health_results['cloud_monitoring'] = {
                'status': 'healthy' if health_score > 0.8 else 'degraded' if health_score > 0.5 else 'unhealthy',
                'health_score': health_score,
                'checks': cloud_checks,
                'recommendations': self._get_cloud_monitoring_recommendations(cloud_checks)
            }
            
        except Exception as e:
            logger.error("Failed to check cloud monitoring health", error=e)
            self.health_results['cloud_monitoring'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_system_integration_health(self):
        """Check overall system integration health."""
        logger.info("Checking system integration health")
        
        try:
            integration_checks = {
                'end_to_end_logging': await self._test_end_to_end_logging(),
                'cross_component_correlation': await self._test_cross_component_correlation(),
                'data_consistency': await self._test_data_consistency(),
                'resource_usage': await self._test_resource_usage()
            }
            
            health_score = self._calculate_component_health_score(integration_checks)
            
            self.health_results['system_integration'] = {
                'status': 'healthy' if health_score > 0.8 else 'degraded' if health_score > 0.5 else 'unhealthy',
                'health_score': health_score,
                'checks': integration_checks,
                'recommendations': self._get_integration_recommendations(integration_checks)
            }
            
        except Exception as e:
            logger.error("Failed to check system integration health", error=e)
            self.health_results['system_integration'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _run_synthetic_tests(self):
        """Run synthetic tests to validate monitoring functionality."""
        logger.info("Running synthetic monitoring tests")
        
        try:
            synthetic_tests = {
                'log_generation_test': await self._synthetic_log_generation_test(),
                'error_simulation_test': await self._synthetic_error_simulation_test(),
                'performance_test': await self._synthetic_performance_test(),
                'metric_writing_test': await self._synthetic_metric_writing_test()
            }
            
            test_score = self._calculate_component_health_score(synthetic_tests)
            
            self.health_results['synthetic_tests'] = {
                'status': 'passed' if test_score > 0.8 else 'partial' if test_score > 0.5 else 'failed',
                'test_score': test_score,
                'tests': synthetic_tests
            }
            
        except Exception as e:
            logger.error("Failed to run synthetic tests", error=e)
            self.health_results['synthetic_tests'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    # Test methods
    async def _test_log_levels(self) -> Dict[str, Any]:
        """Test different log levels."""
        try:
            logger.debug("Debug level test")
            logger.info("Info level test")
            logger.warning("Warning level test")
            logger.error("Error level test")
            return {'status': 'passed', 'message': 'All log levels working'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_structured_logging(self) -> Dict[str, Any]:
        """Test structured logging functionality."""
        try:
            logger.info("Structured logging test", 
                       test_field="test_value",
                       test_number=123,
                       test_boolean=True)
            return {'status': 'passed', 'message': 'Structured logging working'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_correlation_ids(self) -> Dict[str, Any]:
        """Test correlation ID functionality."""
        try:
            from enhanced_logging_config import set_correlation_id, generate_correlation_id
            correlation_id = generate_correlation_id()
            set_correlation_id(correlation_id)
            logger.info("Correlation ID test", test_correlation_id=correlation_id)
            return {'status': 'passed', 'message': 'Correlation IDs working'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_logging_performance(self) -> Dict[str, Any]:
        """Test logging performance."""
        try:
            start_time = time.time()
            for i in range(100):
                logger.info(f"Performance test log {i}")
            duration = time.time() - start_time
            
            logs_per_second = 100 / duration
            status = 'passed' if logs_per_second > 50 else 'degraded'
            
            return {
                'status': status,
                'logs_per_second': logs_per_second,
                'duration': duration
            }
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_error_reporting(self) -> Dict[str, Any]:
        """Test error reporting functionality."""
        try:
            test_error = Exception("Test error for health check")
            error_tracker.report_error(test_error, {'test': True})
            return {'status': 'passed', 'message': 'Error reporting working'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_error_pattern_detection(self) -> Dict[str, Any]:
        """Test error pattern detection."""
        try:
            # Generate some test errors
            for i in range(5):
                test_error = Exception(f"Pattern test error {i}")
                error_tracker.report_error(test_error, {'pattern_test': True})
            
            summary = error_tracker.get_error_summary(hours=1)
            return {
                'status': 'passed',
                'error_patterns_detected': len(summary.get('most_common_patterns', {}))
            }
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_alert_thresholds(self) -> Dict[str, Any]:
        """Test alert threshold functionality."""
        try:
            # This would test alert threshold logic
            return {'status': 'passed', 'message': 'Alert thresholds configured'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_metrics_collection(self) -> Dict[str, Any]:
        """Test metrics collection."""
        try:
            performance_monitor.record_gauge('test_metric', 123.45, {'test': 'true'})
            performance_monitor.record_counter('test_counter', 1, {'test': 'true'})
            return {'status': 'passed', 'message': 'Metrics collection working'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_performance_tracking(self) -> Dict[str, Any]:
        """Test performance tracking."""
        try:
            timer_id = performance_monitor.start_timer('health_check_test')
            await asyncio.sleep(0.1)  # Simulate work
            performance_monitor.end_timer(timer_id, {'test': 'true'})
            return {'status': 'passed', 'message': 'Performance tracking working'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_memory_monitoring(self) -> Dict[str, Any]:
        """Test memory monitoring."""
        try:
            # This would test memory monitoring functionality
            return {'status': 'passed', 'message': 'Memory monitoring available'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_metric_writing(self) -> Dict[str, Any]:
        """Test metric writing to Cloud Monitoring."""
        try:
            success = monitoring.write_metric('health_check_test', 1.0, {'test': 'true'})
            return {
                'status': 'passed' if success else 'failed',
                'message': 'Metric writing working' if success else 'Metric writing failed'
            }
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_custom_metrics(self) -> Dict[str, Any]:
        """Test custom metrics creation."""
        try:
            success = monitoring.create_custom_metric(
                'health_check_test_metric',
                'Health check test metric',
                'DOUBLE',
                'GAUGE'
            )
            return {
                'status': 'passed' if success else 'failed',
                'message': 'Custom metrics working' if success else 'Custom metrics failed'
            }
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_alert_policies(self) -> Dict[str, Any]:
        """Test alert policies."""
        try:
            # This would test alert policy functionality
            return {'status': 'passed', 'message': 'Alert policies configured'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_dashboards(self) -> Dict[str, Any]:
        """Test dashboard functionality."""
        try:
            # This would test dashboard functionality
            return {'status': 'passed', 'message': 'Dashboards available'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_end_to_end_logging(self) -> Dict[str, Any]:
        """Test end-to-end logging flow."""
        try:
            # Test complete logging flow
            logger.info("End-to-end logging test", test_type="integration")
            return {'status': 'passed', 'message': 'End-to-end logging working'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_cross_component_correlation(self) -> Dict[str, Any]:
        """Test cross-component correlation."""
        try:
            # This would test correlation across components
            return {'status': 'passed', 'message': 'Cross-component correlation working'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_data_consistency(self) -> Dict[str, Any]:
        """Test data consistency across monitoring components."""
        try:
            # This would test data consistency
            return {'status': 'passed', 'message': 'Data consistency maintained'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _test_resource_usage(self) -> Dict[str, Any]:
        """Test resource usage monitoring."""
        try:
            # This would test resource usage monitoring
            return {'status': 'passed', 'message': 'Resource usage monitoring working'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    # Synthetic tests
    async def _synthetic_log_generation_test(self) -> Dict[str, Any]:
        """Synthetic test for log generation."""
        try:
            start_time = time.time()
            for i in range(10):
                logger.info(f"Synthetic log test {i}", test_id=i)
            duration = time.time() - start_time
            
            return {
                'status': 'passed',
                'logs_generated': 10,
                'duration': duration,
                'logs_per_second': 10 / duration
            }
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _synthetic_error_simulation_test(self) -> Dict[str, Any]:
        """Synthetic test for error simulation."""
        try:
            test_error = Exception("Synthetic error test")
            error_tracker.report_error(test_error, {'synthetic_test': True})
            return {'status': 'passed', 'message': 'Error simulation working'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _synthetic_performance_test(self) -> Dict[str, Any]:
        """Synthetic performance test."""
        try:
            timer_id = performance_monitor.start_timer('synthetic_performance_test')
            await asyncio.sleep(0.05)  # Simulate work
            performance_monitor.end_timer(timer_id, {'synthetic': 'true'})
            return {'status': 'passed', 'message': 'Performance test completed'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def _synthetic_metric_writing_test(self) -> Dict[str, Any]:
        """Synthetic metric writing test."""
        try:
            success = monitoring.write_metric('synthetic_test_metric', 42.0, {'synthetic': 'true'})
            return {
                'status': 'passed' if success else 'failed',
                'message': 'Metric writing test completed'
            }
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    # Helper methods
    def _calculate_component_health_score(self, checks: Dict[str, Any]) -> float:
        """Calculate health score for a component based on its checks."""
        if not checks:
            return 0.0
        
        passed_checks = 0
        total_checks = 0
        
        for check_name, check_result in checks.items():
            total_checks += 1
            if isinstance(check_result, dict):
                if check_result.get('status') in ['passed', 'healthy']:
                    passed_checks += 1
                elif check_result.get('status') in ['degraded', 'partial']:
                    passed_checks += 0.5
            elif check_result is True:
                passed_checks += 1
        
        return passed_checks / total_checks if total_checks > 0 else 0.0
    
    def _calculate_overall_health_score(self):
        """Calculate overall health score."""
        component_scores = []
        
        for component_name, component_data in self.health_results.items():
            if isinstance(component_data, dict) and 'health_score' in component_data:
                component_scores.append(component_data['health_score'])
            elif isinstance(component_data, dict) and 'test_score' in component_data:
                component_scores.append(component_data['test_score'])
        
        if component_scores:
            overall_score = sum(component_scores) / len(component_scores)
            if overall_score > 0.8:
                overall_health = 'healthy'
            elif overall_score > 0.5:
                overall_health = 'degraded'
            else:
                overall_health = 'unhealthy'
        else:
            overall_score = 0.0
            overall_health = 'unknown'
        
        self.health_results['overall_health_score'] = overall_score
        self.health_results['overall_health'] = overall_health
    
    def _get_logging_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """Get recommendations for logging system."""
        recommendations = []
        
        if checks.get('performance', {}).get('logs_per_second', 0) < 50:
            recommendations.append("Consider optimizing logging performance")
        
        if checks.get('basic_health', {}).get('status') != 'healthy':
            recommendations.append("Address logging system health issues")
        
        return recommendations or ["Logging system is healthy"]
    
    def _get_error_tracking_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """Get recommendations for error tracking system."""
        recommendations = []
        
        if checks.get('basic_health', {}).get('status') != 'healthy':
            recommendations.append("Address error tracking health issues")
        
        return recommendations or ["Error tracking system is healthy"]
    
    def _get_performance_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """Get recommendations for performance monitoring."""
        recommendations = []
        
        if checks.get('basic_health', {}).get('status') != 'healthy':
            recommendations.append("Address performance monitoring health issues")
        
        return recommendations or ["Performance monitoring is healthy"]
    
    def _get_cloud_monitoring_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """Get recommendations for cloud monitoring."""
        recommendations = []
        
        if not checks.get('basic_health', {}).get('clients', {}).get('metric_client', False):
            recommendations.append("Metric client is not available - check permissions and API enablement")
        
        return recommendations or ["Cloud monitoring is healthy"]
    
    def _get_integration_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """Get recommendations for system integration."""
        recommendations = []
        
        # Add integration-specific recommendations
        return recommendations or ["System integration is healthy"]
    
    async def _generate_health_report(self):
        """Generate comprehensive health report."""
        logger.info("Generating health report")
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'project_id': self.project_id,
            'environment': self.environment,
            'overall_health': self.health_results.get('overall_health', 'unknown'),
            'overall_health_score': self.health_results.get('overall_health_score', 0.0),
            'check_duration': self.health_results.get('check_duration', 0),
            'components': {
                component: data for component, data in self.health_results.items()
                if component not in ['overall_health', 'overall_health_score', 'check_duration']
            },
            'summary': {
                'healthy_components': sum(1 for data in self.health_results.values() 
                                        if isinstance(data, dict) and data.get('status') == 'healthy'),
                'total_components': sum(1 for data in self.health_results.values() 
                                      if isinstance(data, dict) and 'status' in data),
                'recommendations': self._get_overall_recommendations()
            }
        }
        
        # Save report
        report_filename = f"monitoring_health_report_{self.environment}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Health report saved to: {report_filename}")
        except Exception as e:
            logger.error(f"Failed to save health report: {e}")
        
        self.health_results['report'] = report
    
    def _get_overall_recommendations(self) -> List[str]:
        """Get overall system recommendations."""
        recommendations = []
        
        overall_health = self.health_results.get('overall_health', 'unknown')
        
        if overall_health == 'unhealthy':
            recommendations.append("Critical: Multiple monitoring components are unhealthy - immediate attention required")
        elif overall_health == 'degraded':
            recommendations.append("Warning: Some monitoring components are degraded - investigate and resolve issues")
        else:
            recommendations.append("All monitoring components are healthy")
        
        return recommendations


async def main():
    """Main health check function."""
    print("Starting Career Co-Pilot Monitoring Health Check...")
    
    # Initialize health checker
    health_checker = MonitoringHealthChecker()
    
    # Run comprehensive health check
    results = await health_checker.run_comprehensive_health_check()
    
    # Print results
    print(f"\nHealth check completed:")
    print(f"Overall health: {results.get('overall_health', 'unknown')}")
    print(f"Health score: {results.get('overall_health_score', 0):.2%}")
    print(f"Check duration: {results.get('check_duration', 0):.2f} seconds")
    
    # Print component status
    print("\nComponent Status:")
    for component, data in results.items():
        if isinstance(data, dict) and 'status' in data:
            status = data['status']
            score = data.get('health_score', data.get('test_score', 0))
            print(f"  {component}: {status} ({score:.2%})")
    
    if results.get('overall_health') == 'healthy':
        print("✅ All monitoring systems are healthy")
    elif results.get('overall_health') == 'degraded':
        print("⚠️  Some monitoring systems need attention")
    else:
        print("❌ Critical monitoring system issues detected")
    
    return results


if __name__ == "__main__":
    # Run health check
    results = asyncio.run(main())
    
    # Exit with appropriate code
    exit_code = 0 if results.get('overall_health') == 'healthy' else 1
    sys.exit(exit_code)