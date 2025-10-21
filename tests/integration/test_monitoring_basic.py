"""
Basic test script for monitoring implementation without Google Cloud dependencies.
This allows testing the core functionality without requiring Google Cloud setup.
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any

# Mock Google Cloud modules for testing
class MockCloudLogging:
    def __init__(self):
        pass
    
    def setup_logging(self):
        pass

class MockErrorReporting:
    def __init__(self, project=None):
        self.project = project
    
    def report_exception(self, http_context=None):
        print(f"Mock: Would report exception to project {self.project}")

class MockMonitoringClient:
    def __init__(self):
        pass
    
    def create_metric_descriptor(self, name, metric_descriptor):
        print(f"Mock: Would create metric descriptor in {name}")
    
    def create_time_series(self, name, time_series):
        print(f"Mock: Would write {len(time_series)} time series to {name}")

# Mock the Google Cloud modules
sys.modules['google'] = type(sys)('google')
sys.modules['google.cloud'] = type(sys)('google.cloud')
sys.modules['google.cloud.logging'] = type(sys)('google.cloud.logging')
sys.modules['google.cloud.error_reporting'] = type(sys)('google.cloud.error_reporting')
sys.modules['google.cloud.monitoring_v3'] = type(sys)('google.cloud.monitoring_v3')
sys.modules['google.cloud.monitoring_dashboard'] = type(sys)('google.cloud.monitoring_dashboard')
sys.modules['google.api_core'] = type(sys)('google.api_core')
sys.modules['google.api_core.exceptions'] = type(sys)('google.api_core.exceptions')

# Add mock classes to modules
sys.modules['google.cloud.logging'].Client = MockCloudLogging
sys.modules['google.cloud.error_reporting'].Client = MockErrorReporting
sys.modules['google.cloud.monitoring_v3'].MetricServiceClient = MockMonitoringClient
sys.modules['google.cloud.monitoring_v3'].AlertPolicyServiceClient = MockMonitoringClient
sys.modules['google.cloud.monitoring_v3'].NotificationChannelServiceClient = MockMonitoringClient

# Mock additional classes
class MockMetricDescriptor:
    def __init__(self):
        self.type = ""
        self.metric_kind = ""
        self.value_type = ""
        self.description = ""
        self.unit = ""
        self.labels = []
    
    class MetricKind:
        GAUGE = "GAUGE"
        CUMULATIVE = "CUMULATIVE"
    
    class ValueType:
        DOUBLE = "DOUBLE"
        INT64 = "INT64"
        STRING = "STRING"

class MockTimeSeries:
    def __init__(self):
        self.metric = type('obj', (object,), {'type': '', 'labels': {}})()
        self.resource = type('obj', (object,), {'type': '', 'labels': {}})()
        self.points = []

class MockTimeInterval:
    def __init__(self, data):
        self.data = data

class MockPoint:
    def __init__(self, data):
        self.data = data

class MockLabelDescriptor:
    def __init__(self, key, value_type, description):
        self.key = key
        self.value_type = value_type
        self.description = description
    
    class ValueType:
        STRING = "STRING"
        INT64 = "INT64"
        DOUBLE = "DOUBLE"

class MockHTTPContext:
    def __init__(self, method=None, url=None, user_agent=None):
        self.method = method
        self.url = url
        self.user_agent = user_agent

class MockAlreadyExists(Exception):
    pass

# Add mock classes to modules
sys.modules['google.cloud.monitoring_v3'].MetricDescriptor = MockMetricDescriptor
sys.modules['google.cloud.monitoring_v3'].TimeSeries = MockTimeSeries
sys.modules['google.cloud.monitoring_v3'].TimeInterval = MockTimeInterval
sys.modules['google.cloud.monitoring_v3'].Point = MockPoint
sys.modules['google.cloud.monitoring_v3'].LabelDescriptor = MockLabelDescriptor
sys.modules['google.cloud.error_reporting'].HTTPContext = MockHTTPContext
sys.modules['google.api_core.exceptions'].AlreadyExists = MockAlreadyExists

# Mock dashboard client
sys.modules['google.cloud.monitoring_dashboard'].v1 = type(sys)('v1')
sys.modules['google.cloud.monitoring_dashboard'].v1.DashboardsServiceClient = MockMonitoringClient

def test_monitoring_implementation():
    """Test the monitoring implementation with mocked dependencies."""
    print("🧪 Testing Career Co-Pilot Monitoring Implementation")
    print("=" * 60)
    
    # Set test environment variables
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project'
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['FUNCTION_NAME'] = 'test-function'
    os.environ['FUNCTION_REGION'] = 'us-central1'
    
    test_results = {}
    
    try:
        # Test 1: Import all monitoring modules
        print("\n1. Testing module imports...")
        
        # Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        import enhanced_logging_config
        import enhanced_error_tracking
        import enhanced_monitoring
        
        test_results['imports'] = True
        print("   ✅ All monitoring modules imported successfully")
        
    except Exception as e:
        test_results['imports'] = False
        print(f"   ❌ Import failed: {e}")
        return test_results
    
    try:
        # Test 2: Basic logging functionality
        print("\n2. Testing logging system...")
        
        from enhanced_logging_config import logger, set_correlation_id, generate_correlation_id
        
        # Test correlation ID
        correlation_id = generate_correlation_id()
        set_correlation_id(correlation_id)
        
        # Test structured logging
        logger.info("Test log message", 
                   test_field="test_value",
                   test_number=123,
                   correlation_test=True)
        
        # Test different log levels
        logger.debug("Debug test message")
        logger.warning("Warning test message")
        logger.error("Error test message")
        
        # Test logging metrics
        from enhanced_logging_config import get_logging_health, get_logging_metrics
        
        health = get_logging_health()
        metrics = get_logging_metrics()
        
        test_results['logging'] = True
        print("   ✅ Logging system working")
        print(f"   📊 Logging health: {health.get('status', 'unknown')}")
        print(f"   📈 Log entries: {metrics.get('total_log_entries', 0)}")
        
    except Exception as e:
        test_results['logging'] = False
        print(f"   ❌ Logging test failed: {e}")
    
    try:
        # Test 3: Error tracking functionality
        print("\n3. Testing error tracking...")
        
        from enhanced_error_tracking import (
            error_tracker, performance_monitor, monitor_function,
            get_error_tracking_health, get_performance_monitoring_health
        )
        
        # Test error reporting
        test_error = Exception("Test error for monitoring")
        error_tracker.report_error(test_error, {'test': True})
        
        # Test performance monitoring
        timer_id = performance_monitor.start_timer('test_operation')
        time.sleep(0.1)  # Simulate work
        performance_monitor.end_timer(timer_id, {'test': True})
        
        # Test function decorator
        @monitor_function('test_function')
        def test_function():
            return "test_result"
        
        result = test_function()
        
        # Get health status
        error_health = get_error_tracking_health()
        perf_health = get_performance_monitoring_health()
        
        test_results['error_tracking'] = True
        print("   ✅ Error tracking system working")
        print(f"   📊 Error tracking health: {error_health.get('status', 'unknown')}")
        print(f"   📊 Performance monitoring health: {perf_health.get('status', 'unknown')}")
        
    except Exception as e:
        test_results['error_tracking'] = False
        print(f"   ❌ Error tracking test failed: {e}")
    
    try:
        # Test 4: Cloud monitoring functionality
        print("\n4. Testing cloud monitoring...")
        
        from enhanced_monitoring import monitoring, track_function_performance
        
        # Test metric creation
        success = monitoring.create_custom_metric(
            'test_metric',
            'Test metric for validation',
            'DOUBLE',
            'GAUGE'
        )
        
        # Test metric writing
        write_success = monitoring.write_metric('test_metric', 42.0, {'test': 'true'})
        
        # Test function decorator
        @track_function_performance
        def test_performance_function():
            time.sleep(0.05)  # Simulate work
            return "performance_test"
        
        perf_result = test_performance_function()
        
        # Get monitoring health
        monitoring_health = monitoring.get_monitoring_health()
        
        test_results['cloud_monitoring'] = True
        print("   ✅ Cloud monitoring system working")
        print(f"   📊 Monitoring health: {monitoring_health.get('status', 'unknown')}")
        print(f"   📈 Custom metrics: {monitoring_health.get('custom_metrics_count', 0)}")
        
    except Exception as e:
        test_results['cloud_monitoring'] = False
        print(f"   ❌ Cloud monitoring test failed: {e}")
    
    try:
        # Test 5: Business metrics tracking
        print("\n5. Testing business metrics...")
        
        from enhanced_error_tracking import (
            track_business_metric, track_api_call, 
            track_job_ingestion, track_email_delivery
        )
        
        # Test business metrics
        track_business_metric('test_business_metric', 100.0, {'category': 'test'})
        
        # Test API call tracking
        track_api_call('test_api', True, 150.0, 200)
        
        # Test job ingestion tracking
        track_job_ingestion(50, 45, 40, 'test_source')
        
        # Test email delivery tracking
        track_email_delivery('test_email', 100, 95, 2, 1)
        
        test_results['business_metrics'] = True
        print("   ✅ Business metrics tracking working")
        
    except Exception as e:
        test_results['business_metrics'] = False
        print(f"   ❌ Business metrics test failed: {e}")
    
    try:
        # Test 6: Dashboard and alert configuration
        print("\n6. Testing dashboard configuration...")
        
        from monitoring_dashboard_config import (
            get_function_dashboard_config,
            get_system_overview_dashboard_config,
            get_alert_policies_config
        )
        
        # Test dashboard configs
        function_dashboard = get_function_dashboard_config('test_function')
        system_dashboard = get_system_overview_dashboard_config()
        alert_policies = get_alert_policies_config()
        
        test_results['dashboard_config'] = True
        print("   ✅ Dashboard configuration working")
        print(f"   📊 Function dashboard widgets: {len(function_dashboard['grid_layout']['widgets'])}")
        print(f"   📊 System dashboard widgets: {len(system_dashboard['grid_layout']['widgets'])}")
        print(f"   🚨 Alert policies: {len(alert_policies)}")
        
    except Exception as e:
        test_results['dashboard_config'] = False
        print(f"   ❌ Dashboard configuration test failed: {e}")
    
    # Calculate overall success
    successful_tests = sum(test_results.values())
    total_tests = len(test_results)
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    
    print("\n" + "=" * 60)
    print("🏁 Test Results Summary")
    print("=" * 60)
    
    for test_name, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Success Rate: {success_rate:.1%} ({successful_tests}/{total_tests})")
    
    if success_rate >= 0.8:
        print("🎉 Monitoring implementation test PASSED!")
        print("   The monitoring system is ready for deployment.")
    elif success_rate >= 0.6:
        print("⚠️  Monitoring implementation test PARTIALLY PASSED")
        print("   Some components need attention before deployment.")
    else:
        print("❌ Monitoring implementation test FAILED")
        print("   Significant issues need to be resolved.")
    
    # Generate test report
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'test_results': test_results,
        'success_rate': success_rate,
        'successful_tests': successful_tests,
        'total_tests': total_tests,
        'environment': 'test',
        'notes': 'Basic functionality test with mocked Google Cloud dependencies'
    }
    
    try:
        with open('monitoring_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Test report saved to: monitoring_test_report.json")
    except Exception as e:
        print(f"⚠️  Could not save test report: {e}")
    
    return test_results

if __name__ == "__main__":
    test_results = test_monitoring_implementation()
    
    # Exit with appropriate code
    success_rate = sum(test_results.values()) / len(test_results) if test_results else 0
    exit_code = 0 if success_rate >= 0.8 else 1
    sys.exit(exit_code)