#!/usr/bin/env python3
"""
Deployment and Scalability Testing Script
Tests Docker configurations, backup mechanisms, SSL/TLS setup, and error handling
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_docker_configurations() -> Dict[str, Any]:
    """Test Docker and deployment configurations"""
    logger.info("Testing Docker configurations...")
    
    results = {}
    
    # Test docker-compose validation
    try:
        result = subprocess.run(
            ['docker-compose', 'config'],
            capture_output=True,
            text=True,
            cwd='.'
        )
        results['compose_validation'] = {
            'status': 'PASSED' if result.returncode == 0 else 'FAILED',
            'error': result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        results['compose_validation'] = {'status': 'FAILED', 'error': str(e)}
    
    # Test Dockerfile existence and basic validation
    dockerfiles = [
        'deployment/docker/Dockerfile.backend',
        'deployment/docker/Dockerfile.frontend'
    ]
    
    dockerfile_results = {}
    valid_dockerfiles = 0
    
    for dockerfile in dockerfiles:
        if Path(dockerfile).exists():
            with open(dockerfile, 'r') as f:
                content = f.read()
            
            has_from = 'FROM' in content
            has_user = 'USER' in content
            has_healthcheck = 'HEALTHCHECK' in content
            
            dockerfile_results[dockerfile] = {
                'exists': True,
                'has_from': has_from,
                'has_user': has_user,
                'has_healthcheck': has_healthcheck
            }
            
            # Count as valid if it has the essential elements
            if has_from and has_user and has_healthcheck:
                valid_dockerfiles += 1
        else:
            dockerfile_results[dockerfile] = {'exists': False}
    
    results['dockerfile_validation'] = {
        'status': 'PASSED' if valid_dockerfiles == len(dockerfiles) else 'FAILED',
        'dockerfiles': dockerfile_results,
        'valid_dockerfiles': valid_dockerfiles
    }
    
    return results

def test_backup_recovery() -> Dict[str, Any]:
    """Test backup and recovery mechanisms"""
    logger.info("Testing backup and recovery mechanisms...")
    
    results = {}
    
    # Test backup configuration
    backup_config_path = 'config/services/backup.yaml'
    if Path(backup_config_path).exists():
        try:
            with open(backup_config_path, 'r') as f:
                backup_config = yaml.safe_load(f)
            
            results['backup_configuration'] = {
                'status': 'PASSED',
                'has_targets': 'targets' in backup_config,
                'has_schedule': 'schedule' in backup_config,
                'has_storage': 'storage' in backup_config
            }
        except Exception as e:
            results['backup_configuration'] = {'status': 'FAILED', 'error': str(e)}
    else:
        results['backup_configuration'] = {'status': 'FAILED', 'error': 'Backup config not found'}
    
    # Test backup directories
    backup_dirs = ['data/backups', 'logs']
    existing_dirs = [d for d in backup_dirs if Path(d).exists()]
    
    results['backup_directories'] = {
        'status': 'PASSED' if len(existing_dirs) >= 1 else 'FAILED',
        'existing_dirs': existing_dirs,
        'total_dirs': len(backup_dirs)
    }
    
    return results

def test_ssl_tls_configurations() -> Dict[str, Any]:
    """Test SSL/TLS configurations"""
    logger.info("Testing SSL/TLS configurations...")
    
    results = {}
    
    # Test SSL certificate generation script
    ssl_script_path = 'scripts/generate_ssl_certs.sh'
    if Path(ssl_script_path).exists():
        results['ssl_script'] = {
            'status': 'PASSED',
            'exists': True,
            'executable': os.access(ssl_script_path, os.X_OK)
        }
    else:
        results['ssl_script'] = {'status': 'FAILED', 'exists': False}
    
    # Test Nginx SSL configuration
    nginx_config_path = 'nginx/nginx.conf'
    if Path(nginx_config_path).exists():
        with open(nginx_config_path, 'r') as f:
            nginx_config = f.read()
        
        results['nginx_ssl'] = {
            'status': 'PASSED' if 'ssl_certificate' in nginx_config else 'FAILED',
            'has_ssl_config': 'ssl_certificate' in nginx_config,
            'has_ssl_protocols': 'ssl_protocols' in nginx_config,
            'has_security_headers': 'Strict-Transport-Security' in nginx_config
        }
    else:
        results['nginx_ssl'] = {'status': 'FAILED', 'error': 'Nginx config not found'}
    
    # Test SSL certificate directories
    ssl_dirs = ['secrets/ssl/development', 'secrets/ssl/production']
    ssl_dir_results = {}
    valid_ssl_setups = 0
    
    for ssl_dir in ssl_dirs:
        ssl_dir_path = Path(ssl_dir)
        exists = ssl_dir_path.exists()
        has_cert = (ssl_dir_path / 'certificate.crt').exists() if exists else False
        has_key = (ssl_dir_path / 'private.key').exists() if exists else False
        
        ssl_dir_results[ssl_dir] = {
            'exists': exists,
            'has_cert': has_cert,
            'has_key': has_key
        }
        
        # For development, we expect certificates to exist
        # For production, it's acceptable if they don't exist (will be generated later)
        if ssl_dir == 'secrets/ssl/development':
            if exists and has_cert and has_key:
                valid_ssl_setups += 1
        else:  # production
            # Production passes if either certificates exist OR templates exist
            template_exists = (ssl_dir_path / 'cert.conf.template').exists()
            if (exists and has_cert and has_key) or template_exists:
                valid_ssl_setups += 1
    
    results['ssl_directories'] = {
        'status': 'PASSED' if valid_ssl_setups >= 1 else 'FAILED',
        'directories': ssl_dir_results,
        'valid_setups': valid_ssl_setups
    }
    
    return results

def test_error_handling_recovery() -> Dict[str, Any]:
    """Test error handling and recovery mechanisms"""
    logger.info("Testing error handling and recovery mechanisms...")
    
    results = {}
    
    # Test container restart policies
    try:
        with open('docker-compose.yml', 'r') as f:
            compose_config = yaml.safe_load(f)
        
        services_with_restart = []
        for service_name, service_config in compose_config.get('services', {}).items():
            restart_policy = service_config.get('restart')
            if restart_policy in ['unless-stopped', 'always', 'on-failure']:
                services_with_restart.append(service_name)
        
        results['restart_policies'] = {
            'status': 'PASSED' if len(services_with_restart) >= 3 else 'FAILED',
            'services_with_restart': services_with_restart,
            'total_services': len(compose_config.get('services', {}))
        }
    except Exception as e:
        results['restart_policies'] = {'status': 'FAILED', 'error': str(e)}
    
    # Test health checks
    try:
        health_check_services = []
        for service_name, service_config in compose_config.get('services', {}).items():
            if 'healthcheck' in service_config:
                health_check_services.append(service_name)
        
        results['health_checks'] = {
            'status': 'PASSED' if len(health_check_services) >= 2 else 'FAILED',
            'services_with_healthcheck': health_check_services
        }
    except Exception as e:
        results['health_checks'] = {'status': 'FAILED', 'error': str(e)}
    
    # Test logging configuration
    log_dirs = ['logs', 'backend/logs']
    existing_log_dirs = [d for d in log_dirs if Path(d).exists()]
    
    results['logging'] = {
        'status': 'PASSED' if len(existing_log_dirs) >= 1 else 'FAILED',
        'existing_log_dirs': existing_log_dirs
    }
    
    return results

def test_scalability() -> Dict[str, Any]:
    """Test scalability configurations"""
    logger.info("Testing scalability configurations...")
    
    results = {}
    
    # Test production scaling configuration
    prod_compose_path = 'deployment/docker/docker-compose.prod.yml'
    if Path(prod_compose_path).exists():
        try:
            with open(prod_compose_path, 'r') as f:
                prod_config = yaml.safe_load(f)
            
            services_with_resources = []
            for service_name, service_config in prod_config.get('services', {}).items():
                deploy_config = service_config.get('deploy', {})
                if 'resources' in deploy_config:
                    services_with_resources.append(service_name)
            
            results['resource_limits'] = {
                'status': 'PASSED' if len(services_with_resources) >= 2 else 'FAILED',
                'services_with_resources': services_with_resources
            }
        except Exception as e:
            results['resource_limits'] = {'status': 'FAILED', 'error': str(e)}
    else:
        results['resource_limits'] = {'status': 'FAILED', 'error': 'Production compose not found'}
    
    # Test monitoring configuration
    monitoring_compose_path = 'deployment/docker/docker-compose.monitoring.yml'
    if Path(monitoring_compose_path).exists():
        try:
            with open(monitoring_compose_path, 'r') as f:
                monitoring_config = yaml.safe_load(f)
            
            monitoring_services = list(monitoring_config.get('services', {}).keys())
            essential_services = ['prometheus', 'grafana']
            present_services = [s for s in essential_services if s in monitoring_services]
            
            results['monitoring'] = {
                'status': 'PASSED' if len(present_services) >= 2 else 'FAILED',
                'monitoring_services': monitoring_services,
                'essential_services_present': present_services
            }
        except Exception as e:
            results['monitoring'] = {'status': 'FAILED', 'error': str(e)}
    else:
        results['monitoring'] = {'status': 'FAILED', 'error': 'Monitoring compose not found'}
    
    # Test load balancing (Nginx)
    nginx_config_path = 'nginx/nginx.conf'
    if Path(nginx_config_path).exists():
        with open(nginx_config_path, 'r') as f:
            nginx_config = f.read()
        
        results['load_balancing'] = {
            'status': 'PASSED' if 'upstream' in nginx_config else 'FAILED',
            'has_upstream': 'upstream' in nginx_config,
            'has_load_balancing': any(method in nginx_config for method in ['least_conn', 'ip_hash'])
        }
    else:
        results['load_balancing'] = {'status': 'FAILED', 'error': 'Nginx config not found'}
    
    return results

def count_passed_tests(test_results: Dict[str, Any]) -> int:
    """Count number of passed tests"""
    passed = 0
    for category, tests in test_results.items():
        if isinstance(tests, dict):
            for test_name, test_result in tests.items():
                if isinstance(test_result, dict) and test_result.get('status') == 'PASSED':
                    passed += 1
    return passed

def count_total_tests(test_results: Dict[str, Any]) -> int:
    """Count total number of tests"""
    total = 0
    for category, tests in test_results.items():
        if isinstance(tests, dict):
            total += len(tests)
    return total

def main():
    """Main function to run deployment and scalability tests"""
    print("Starting Deployment and Scalability Testing...")
    print("=" * 60)
    
    # Run all test categories
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'docker_tests': test_docker_configurations(),
        'backup_tests': test_backup_recovery(),
        'ssl_tests': test_ssl_tls_configurations(),
        'error_handling_tests': test_error_handling_recovery(),
        'scalability_tests': test_scalability()
    }
    
    # Calculate overall results
    total_tests = count_total_tests(test_results)
    passed_tests = count_passed_tests(test_results)
    pass_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    # Determine overall status
    if pass_rate >= 0.8:
        overall_status = 'PASSED'
    elif pass_rate >= 0.6:
        overall_status = 'WARNING'
    else:
        overall_status = 'FAILED'
    
    test_results['overall_status'] = overall_status
    test_results['test_summary'] = {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'pass_rate': pass_rate
    }
    
    # Save results
    os.makedirs('logs', exist_ok=True)
    results_file = f"logs/deployment_scalability_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    # Print summary
    print(f"\nTest Results Summary:")
    print(f"Overall Status: {overall_status}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed Tests: {passed_tests}")
    print(f"Pass Rate: {pass_rate:.2%}")
    
    # Print category results
    print(f"\nCategory Results:")
    for category, tests in test_results.items():
        if category not in ['timestamp', 'overall_status', 'test_summary'] and isinstance(tests, dict):
            category_passed = sum(1 for test in tests.values() 
                                if isinstance(test, dict) and test.get('status') == 'PASSED')
            category_total = len(tests)
            print(f"  {category}: {category_passed}/{category_total} passed")
    
    print(f"\nDetailed results saved to: {results_file}")
    
    return overall_status == 'PASSED'

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)