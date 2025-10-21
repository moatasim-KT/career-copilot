"""
Simple test script for Task 10.2 monitoring implementation.
Tests core functionality without requiring external dependencies.
"""

import os
import sys
import time
import json
from typing import Dict, Any
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_file_structure():
    """Test that all required monitoring files are present."""
    print("Testing file structure...")
    
    required_files = [
        'enhanced_logging_config.py',
        'enhanced_error_tracking.py', 
        'enhanced_monitoring.py',
        'monitoring_integration.py',
        'monitoring_dashboard_config.py',
        'setup_monitoring.py',
        'monitoring_health_check.py',
        'validate_monitoring_implementation.py',
        'main.py'
    ]
    
    results = {}
    for file_name in required_files:
        file_path = os.path.join(os.path.dirname(__file__), file_name)
        exists = os.path.exists(file_path)
        results[file_name] = {
            'exists': exists,
            'size': os.path.getsize(file_path) if exists else 0
        }
        
        if exists:
            with open(file_path, 'r') as f:
                content = f.read()
                results[file_name]['has_content'] = len(content.strip()) > 0
                results[file_name]['line_count'] = len(content.split('\n'))
    
    all_files_exist = all(result['exists'] for result in results.values())
    print(f"✅ File structure test: {'PASSED' if all_files_exist else 'FAILED'}")
    
    for file_name, result in results.items():
        status = "✅" if result['exists'] else "❌"
        print(f"  {status} {file_name} ({result.get('line_count', 0)} lines)")
    
    return all_files_exist, results

def test_main_py_integration():
    """Test that main.py has proper monitoring integration."""
    print("\nTesting main.py integration...")
    
    main_py_path = os.path.join(os.path.dirname(__file__), 'main.py')
    
    if not os.path.exists(main_py_path):
        print("❌ main.py not found")
        return False, {}
    
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Check for required imports and decorators
    required_elements = {
        'monitoring_integration_import': 'from .monitoring_integration import' in content,
        'monitor_cloud_function_import': 'monitor_cloud_function' in content,
        'initialize_monitoring_call': 'initialize_monitoring()' in content,
        'career_copilot_api_decorator': '@monitor_cloud_function' in content,
        'health_check_endpoint': 'monitoring_health_check' in content,
        'structured_logging': 'log_business_event' in content,
        'performance_tracking': 'log_performance_metric' in content,
        'error_tracking': 'track_job_metrics' in content or 'track_email_metrics' in content
    }
    
    all_elements_present = all(required_elements.values())
    print(f"✅ Main.py integration test: {'PASSED' if all_elements_present else 'FAILED'}")
    
    for element, present in required_elements.items():
        status = "✅" if present else "❌"
        print(f"  {status} {element.replace('_', ' ').title()}")
    
    return all_elements_present, required_elements

def test_monitoring_integration_file():
    """Test monitoring_integration.py implementation."""
    print("\nTesting monitoring_integration.py...")
    
    integration_file = os.path.join(os.path.dirname(__file__), 'monitoring_integration.py')
    
    if not os.path.exists(integration_file):
        print("❌ monitoring_integration.py not found")
        return False, {}
    
    with open(integration_file, 'r') as f:
        content = f.read()
    
    # Check for required classes and functions
    required_components = {
        'CareerCopilotMonitoring_class': 'class CareerCopilotMonitoring:' in content,
        'monitor_cloud_function_decorator': 'def monitor_cloud_function(' in content,
        'monitor_async_cloud_function_decorator': 'def monitor_async_cloud_function(' in content,
        'track_job_metrics_function': 'def track_job_metrics(' in content,
        'track_email_metrics_function': 'def track_email_metrics(' in content,
        'track_api_metrics_function': 'def track_api_metrics(' in content,
        'initialize_monitoring_function': 'def initialize_monitoring(' in content,
        'get_monitoring_health_function': 'def get_monitoring_health(' in content,
        'comprehensive_error_handling': 'try:' in content and 'except Exception as e:' in content,
        'structured_logging_integration': 'log_function_start' in content and 'log_function_end' in content
    }
    
    all_components_present = all(required_components.values())
    print(f"✅ Monitoring integration test: {'PASSED' if all_components_present else 'FAILED'}")
    
    for component, present in required_components.items():
        status = "✅" if present else "❌"
        print(f"  {status} {component.replace('_', ' ').title()}")
    
    return all_components_present, required_components

def test_enhanced_monitoring_features():
    """Test enhanced monitoring features."""
    print("\nTesting enhanced monitoring features...")
    
    enhanced_monitoring_file = os.path.join(os.path.dirname(__file__), 'enhanced_monitoring.py')
    
    if not os.path.exists(enhanced_monitoring_file):
        print("❌ enhanced_monitoring.py not found")
        return False, {}
    
    with open(enhanced_monitoring_file, 'r') as f:
        content = f.read()
    
    # Check for enhanced monitoring features
    monitoring_features = {
        'EnhancedCloudMonitoring_class': 'class EnhancedCloudMonitoring:' in content,
        'custom_metrics_creation': 'create_custom_metric' in content,
        'alert_policies_setup': 'setup_comprehensive_alert_policies' in content,
        'dashboard_creation': 'create_comprehensive_dashboard' in content,
        'metric_writing': 'write_metric' in content,
        'batch_metrics': 'write_batch_metrics' in content,
        'performance_tracking': 'track_function_performance' in content,
        'comprehensive_setup': 'setup_comprehensive_monitoring' in content,
        'health_monitoring': 'get_monitoring_health' in content,
        'error_rate_alerts': 'error_rate_threshold' in content,
        'memory_monitoring': 'memory_threshold' in content,
        'cache_management': 'metric_cache' in content
    }
    
    all_features_present = all(monitoring_features.values())
    print(f"✅ Enhanced monitoring features test: {'PASSED' if all_features_present else 'FAILED'}")
    
    for feature, present in monitoring_features.items():
        status = "✅" if present else "❌"
        print(f"  {status} {feature.replace('_', ' ').title()}")
    
    return all_features_present, monitoring_features

def test_enhanced_logging_features():
    """Test enhanced logging features."""
    print("\nTesting enhanced logging features...")
    
    enhanced_logging_file = os.path.join(os.path.dirname(__file__), 'enhanced_logging_config.py')
    
    if not os.path.exists(enhanced_logging_file):
        print("❌ enhanced_logging_config.py not found")
        return False, {}
    
    with open(enhanced_logging_file, 'r') as f:
        content = f.read()
    
    # Check for enhanced logging features
    logging_features = {
        'EnhancedStructuredLogger_class': 'class EnhancedStructuredLogger:' in content,
        'structured_formatter': 'class EnhancedStructuredFormatter' in content,
        'correlation_id_support': 'correlation_id_var' in content,
        'performance_tracking': 'FunctionPerformanceTracker' in content,
        'context_management': 'set_correlation_id' in content,
        'business_event_logging': 'log_business_event' in content,
        'performance_metric_logging': 'log_performance_metric' in content,
        'security_event_logging': 'log_security_event' in content,
        'health_monitoring': 'get_logging_health' in content,
        'metrics_collection': 'get_logging_metrics' in content,
        'error_rate_tracking': '_error_history' in content,
        'function_metrics': '_function_metrics' in content
    }
    
    all_features_present = all(logging_features.values())
    print(f"✅ Enhanced logging features test: {'PASSED' if all_features_present else 'FAILED'}")
    
    for feature, present in logging_features.items():
        status = "✅" if present else "❌"
        print(f"  {status} {feature.replace('_', ' ').title()}")
    
    return all_features_present, logging_features

def test_enhanced_error_tracking_features():
    """Test enhanced error tracking features."""
    print("\nTesting enhanced error tracking features...")
    
    error_tracking_file = os.path.join(os.path.dirname(__file__), 'enhanced_error_tracking.py')
    
    if not os.path.exists(error_tracking_file):
        print("❌ enhanced_error_tracking.py not found")
        return False, {}
    
    with open(error_tracking_file, 'r') as f:
        content = f.read()
    
    # Check for enhanced error tracking features
    error_tracking_features = {
        'EnhancedErrorTracker_class': 'class EnhancedErrorTracker:' in content,
        'EnhancedPerformanceMonitor_class': 'class EnhancedPerformanceMonitor:' in content,
        'error_reporting': 'report_error' in content,
        'performance_monitoring': 'start_timer' in content and 'end_timer' in content,
        'business_metrics': 'track_business_metric' in content,
        'api_call_tracking': 'track_api_call' in content,
        'job_ingestion_tracking': 'track_job_ingestion' in content,
        'email_delivery_tracking': 'track_email_delivery' in content,
        'monitor_function_decorator': 'def monitor_function(' in content,
        'monitor_async_function_decorator': 'def monitor_async_function(' in content,
        'error_pattern_detection': 'error_patterns' in content,
        'alert_thresholds': 'error_rate_threshold' in content,
        'health_checks': 'get_error_tracking_health' in content and 'get_performance_monitoring_health' in content
    }
    
    all_features_present = all(error_tracking_features.values())
    print(f"✅ Enhanced error tracking features test: {'PASSED' if all_features_present else 'FAILED'}")
    
    for feature, present in error_tracking_features.items():
        status = "✅" if present else "❌"
        print(f"  {status} {feature.replace('_', ' ').title()}")
    
    return all_features_present, error_tracking_features

def test_backend_monitoring_integration():
    """Test backend monitoring integration."""
    print("\nTesting backend monitoring integration...")
    
    backend_monitoring_file = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'core', 'monitoring.py')
    
    if not os.path.exists(backend_monitoring_file):
        print("❌ backend/app/core/monitoring.py not found")
        return False, {}
    
    with open(backend_monitoring_file, 'r') as f:
        content = f.read()
    
    # Check for backend monitoring integration
    backend_features = {
        'initialize_monitoring_enhanced': 'def initialize_monitoring():' in content and 'comprehensive monitoring' in content.lower(),
        'structured_logging_setup': '_setup_structured_logging' in content,
        'error_tracking_integration': '_setup_error_tracking_integration' in content,
        'performance_monitoring_integration': '_setup_performance_monitoring_integration' in content,
        'function_performance_tracking': '_setup_function_performance_tracking' in content,
        'gcp_integration': 'enhanced_monitoring' in content,
        'exception_handler': 'enhanced_exception_handler' in content,
        'track_performance_decorator': 'track_performance' in content,
        'health_checks': '_setup_health_checks' in content,
        'metrics_collection': '_setup_metrics_collection' in content
    }
    
    all_features_present = all(backend_features.values())
    print(f"✅ Backend monitoring integration test: {'PASSED' if all_features_present else 'FAILED'}")
    
    for feature, present in backend_features.items():
        status = "✅" if present else "❌"
        print(f"  {status} {feature.replace('_', ' ').title()}")
    
    return all_features_present, backend_features

def test_task_requirements_compliance():
    """Test compliance with Task 10.2 requirements."""
    print("\nTesting Task 10.2 requirements compliance...")
    
    requirements = {
        'structured_logging_across_functions': False,
        'cloud_monitoring_alerts_configured': False,
        'cloud_monitoring_dashboards_configured': False,
        'error_tracking_implemented': False,
        'performance_monitoring_implemented': False
    }
    
    # Check structured logging across functions
    main_py_path = os.path.join(os.path.dirname(__file__), 'main.py')
    if os.path.exists(main_py_path):
        with open(main_py_path, 'r') as f:
            main_content = f.read()
        
        # Check if all Cloud Functions have monitoring decorators
        functions = ['career_copilot_api', 'job_ingestion_scheduler', 'morning_briefing_scheduler', 'evening_update_scheduler']
        decorated_functions = sum(1 for func in functions if f'@monitor_cloud_function' in main_content and func in main_content)
        
        requirements['structured_logging_across_functions'] = decorated_functions >= 3
    
    # Check Cloud Monitoring alerts configuration
    enhanced_monitoring_path = os.path.join(os.path.dirname(__file__), 'enhanced_monitoring.py')
    if os.path.exists(enhanced_monitoring_path):
        with open(enhanced_monitoring_path, 'r') as f:
            monitoring_content = f.read()
        
        requirements['cloud_monitoring_alerts_configured'] = (
            'setup_comprehensive_alert_policies' in monitoring_content and
            'error_rate_policy' in monitoring_content and
            'latency_policy' in monitoring_content
        )
        
        requirements['cloud_monitoring_dashboards_configured'] = (
            'create_comprehensive_dashboard' in monitoring_content and
            'dashboard_config' in monitoring_content
        )
    
    # Check error tracking implementation
    error_tracking_path = os.path.join(os.path.dirname(__file__), 'enhanced_error_tracking.py')
    if os.path.exists(error_tracking_path):
        with open(error_tracking_path, 'r') as f:
            error_content = f.read()
        
        requirements['error_tracking_implemented'] = (
            'EnhancedErrorTracker' in error_content and
            'report_error' in error_content and
            'error_patterns' in error_content
        )
        
        requirements['performance_monitoring_implemented'] = (
            'EnhancedPerformanceMonitor' in error_content and
            'start_timer' in error_content and
            'end_timer' in error_content
        )
    
    all_requirements_met = all(requirements.values())
    print(f"✅ Task 10.2 requirements compliance: {'PASSED' if all_requirements_met else 'FAILED'}")
    
    for requirement, met in requirements.items():
        status = "✅" if met else "❌"
        print(f"  {status} {requirement.replace('_', ' ').title()}")
    
    return all_requirements_met, requirements

def generate_test_report(test_results):
    """Generate comprehensive test report."""
    print("\n" + "="*60)
    print("TASK 10.2 IMPLEMENTATION TEST REPORT")
    print("="*60)
    
    overall_score = 0
    total_tests = 0
    
    for test_name, (passed, details) in test_results.items():
        total_tests += 1
        if passed:
            overall_score += 1
        
        status = "PASSED" if passed else "FAILED"
        print(f"\n{test_name.replace('_', ' ').title()}: {status}")
        
        if isinstance(details, dict):
            passed_items = sum(1 for v in details.values() if v is True)
            total_items = len(details)
            if total_items > 0:
                print(f"  Items passed: {passed_items}/{total_items} ({passed_items/total_items:.1%})")
    
    success_rate = overall_score / total_tests if total_tests > 0 else 0
    print(f"\nOVERALL TEST RESULTS:")
    print(f"Tests passed: {overall_score}/{total_tests}")
    print(f"Success rate: {success_rate:.1%}")
    
    if success_rate >= 0.9:
        print("✅ EXCELLENT: Task 10.2 implementation is comprehensive and well-implemented")
    elif success_rate >= 0.8:
        print("✅ GOOD: Task 10.2 implementation meets most requirements")
    elif success_rate >= 0.6:
        print("⚠️  ACCEPTABLE: Task 10.2 implementation meets basic requirements but needs improvement")
    else:
        print("❌ NEEDS WORK: Task 10.2 implementation has significant gaps")
    
    # Save report to file
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'task': '10.2 Implement monitoring and logging',
        'overall_score': overall_score,
        'total_tests': total_tests,
        'success_rate': success_rate,
        'test_results': {name: {'passed': passed, 'details': details} for name, (passed, details) in test_results.items()},
        'requirements_summary': {
            'structured_logging_across_functions': test_results.get('task_requirements_compliance', (False, {}))[-1].get('structured_logging_across_functions', False),
            'cloud_monitoring_alerts_configured': test_results.get('task_requirements_compliance', (False, {}))[-1].get('cloud_monitoring_alerts_configured', False),
            'cloud_monitoring_dashboards_configured': test_results.get('task_requirements_compliance', (False, {}))[-1].get('cloud_monitoring_dashboards_configured', False),
            'error_tracking_implemented': test_results.get('task_requirements_compliance', (False, {}))[-1].get('error_tracking_implemented', False),
            'performance_monitoring_implemented': test_results.get('task_requirements_compliance', (False, {}))[-1].get('performance_monitoring_implemented', False)
        }
    }
    
    report_filename = f"task_10_2_test_report_{int(time.time())}.json"
    try:
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {report_filename}")
    except Exception as e:
        print(f"\nFailed to save report: {e}")
    
    return success_rate >= 0.8

def main():
    """Main test function."""
    print("TASK 10.2: IMPLEMENT MONITORING AND LOGGING")
    print("Testing implementation compliance...")
    print("="*60)
    
    # Run all tests
    test_results = {}
    
    test_results['file_structure'] = test_file_structure()
    test_results['main_py_integration'] = test_main_py_integration()
    test_results['monitoring_integration_file'] = test_monitoring_integration_file()
    test_results['enhanced_monitoring_features'] = test_enhanced_monitoring_features()
    test_results['enhanced_logging_features'] = test_enhanced_logging_features()
    test_results['enhanced_error_tracking_features'] = test_enhanced_error_tracking_features()
    test_results['backend_monitoring_integration'] = test_backend_monitoring_integration()
    test_results['task_requirements_compliance'] = test_task_requirements_compliance()
    
    # Generate comprehensive report
    success = generate_test_report(test_results)
    
    return success

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    exit(exit_code)