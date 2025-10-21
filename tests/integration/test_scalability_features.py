#!/usr/bin/env python3
"""
Test scalability features and configurations
"""

import yaml
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_production_resource_limits():
    """Test production resource limits configuration"""
    logger.info("Testing production resource limits...")
    
    try:
        prod_compose_path = 'deployment/docker/docker-compose.prod.yml'
        if not Path(prod_compose_path).exists():
            logger.error("Production compose file not found")
            return False
        
        with open(prod_compose_path, 'r') as f:
            prod_config = yaml.safe_load(f)
        
        services_with_resources = []
        for service_name, service_config in prod_config.get('services', {}).items():
            deploy_config = service_config.get('deploy', {})
            resources = deploy_config.get('resources', {})
            
            if 'limits' in resources and 'reservations' in resources:
                services_with_resources.append(service_name)
                limits = resources['limits']
                reservations = resources['reservations']
                
                logger.info(f"Service {service_name}:")
                logger.info(f"  Limits: {limits}")
                logger.info(f"  Reservations: {reservations}")
        
        logger.info(f"Services with resource limits: {services_with_resources}")
        return len(services_with_resources) >= 3
        
    except Exception as e:
        logger.error(f"Production resource limits test failed: {e}")
        return False

def test_horizontal_scaling_configuration():
    """Test horizontal scaling configuration"""
    logger.info("Testing horizontal scaling configuration...")
    
    try:
        prod_compose_path = 'deployment/docker/docker-compose.prod.yml'
        if not Path(prod_compose_path).exists():
            logger.error("Production compose file not found")
            return False
        
        with open(prod_compose_path, 'r') as f:
            prod_config = yaml.safe_load(f)
        
        services_with_scaling = []
        for service_name, service_config in prod_config.get('services', {}).items():
            deploy_config = service_config.get('deploy', {})
            
            # Check for scaling configuration
            replicas = deploy_config.get('replicas', 1)
            update_config = deploy_config.get('update_config', {})
            restart_policy = deploy_config.get('restart_policy', {})
            
            if replicas or update_config or restart_policy:
                services_with_scaling.append(service_name)
                logger.info(f"Service {service_name} scaling config:")
                logger.info(f"  Replicas: {replicas}")
                logger.info(f"  Update config: {update_config}")
                logger.info(f"  Restart policy: {restart_policy}")
        
        # Check for scaling script
        scale_script_path = 'scripts/scale-services.sh'
        has_scale_script = Path(scale_script_path).exists()
        
        logger.info(f"Services with scaling config: {services_with_scaling}")
        logger.info(f"Scale script exists: {has_scale_script}")
        
        return len(services_with_scaling) >= 3 and has_scale_script
        
    except Exception as e:
        logger.error(f"Horizontal scaling test failed: {e}")
        return False

def test_load_balancing_configuration():
    """Test load balancing configuration"""
    logger.info("Testing load balancing configuration...")
    
    try:
        nginx_config_path = 'nginx/nginx.conf'
        if not Path(nginx_config_path).exists():
            logger.error("Nginx configuration file not found")
            return False
        
        with open(nginx_config_path, 'r') as f:
            nginx_config = f.read()
        
        # Check for upstream configuration
        has_upstream = 'upstream' in nginx_config
        
        # Check for load balancing methods
        load_balancing_methods = ['least_conn', 'ip_hash', 'round_robin']
        has_load_balancing = any(method in nginx_config for method in load_balancing_methods)
        
        # Check for keepalive connections
        has_keepalive = 'keepalive' in nginx_config
        
        # Check for multiple server entries
        backend_servers = nginx_config.count('server backend:')
        frontend_servers = nginx_config.count('server frontend:')
        
        logger.info(f"Upstream configuration: {has_upstream}")
        logger.info(f"Load balancing methods: {has_load_balancing}")
        logger.info(f"Keepalive connections: {has_keepalive}")
        logger.info(f"Backend servers configured: {backend_servers}")
        logger.info(f"Frontend servers configured: {frontend_servers}")
        
        return has_upstream and (has_load_balancing or backend_servers > 0)
        
    except Exception as e:
        logger.error(f"Load balancing test failed: {e}")
        return False

def test_monitoring_and_observability():
    """Test monitoring and observability configuration"""
    logger.info("Testing monitoring and observability...")
    
    try:
        monitoring_compose_path = 'deployment/docker/docker-compose.monitoring.yml'
        if not Path(monitoring_compose_path).exists():
            logger.error("Monitoring compose file not found")
            return False
        
        with open(monitoring_compose_path, 'r') as f:
            monitoring_config = yaml.safe_load(f)
        
        monitoring_services = list(monitoring_config.get('services', {}).keys())
        
        # Check for essential monitoring services
        essential_services = ['prometheus', 'grafana', 'node-exporter', 'cadvisor']
        present_services = [service for service in essential_services 
                          if service in monitoring_services]
        
        logger.info(f"Monitoring services: {monitoring_services}")
        logger.info(f"Essential services present: {present_services}")
        
        # Check for Prometheus configuration
        prometheus_config_path = 'monitoring/prometheus/prometheus.yml'
        has_prometheus_config = Path(prometheus_config_path).exists()
        
        # Check for Grafana dashboards
        grafana_dashboards_path = 'monitoring/grafana/dashboards'
        has_grafana_dashboards = Path(grafana_dashboards_path).exists()
        
        logger.info(f"Prometheus config exists: {has_prometheus_config}")
        logger.info(f"Grafana dashboards exist: {has_grafana_dashboards}")
        
        return (len(present_services) >= 3 and 
                has_prometheus_config and 
                len(monitoring_services) >= 4)
        
    except Exception as e:
        logger.error(f"Monitoring and observability test failed: {e}")
        return False

def test_caching_mechanisms():
    """Test caching mechanisms"""
    logger.info("Testing caching mechanisms...")
    
    try:
        # Check Redis configuration in Docker Compose
        with open('docker-compose.yml', 'r') as f:
            compose_config = yaml.safe_load(f)
        
        redis_service = compose_config.get('services', {}).get('redis', {})
        redis_configured = bool(redis_service)
        
        if redis_configured:
            # Check Redis configuration details
            redis_command = redis_service.get('command', '')
            has_persistence = 'appendonly yes' in redis_command
            
            redis_volumes = redis_service.get('volumes', [])
            has_volume = any('redis_data' in str(vol) for vol in redis_volumes)
            
            has_healthcheck = 'healthcheck' in redis_service
            
            logger.info(f"Redis configured: {redis_configured}")
            logger.info(f"Redis persistence: {has_persistence}")
            logger.info(f"Redis volume: {has_volume}")
            logger.info(f"Redis healthcheck: {has_healthcheck}")
            
            return redis_configured and has_volume
        else:
            logger.warning("Redis not configured")
            return False
        
    except Exception as e:
        logger.error(f"Caching mechanisms test failed: {e}")
        return False

def test_performance_optimizations():
    """Test performance optimizations"""
    logger.info("Testing performance optimizations...")
    
    try:
        optimizations_found = []
        
        # Check Nginx performance settings
        nginx_config_path = 'nginx/nginx.conf'
        if Path(nginx_config_path).exists():
            with open(nginx_config_path, 'r') as f:
                nginx_config = f.read()
            
            nginx_optimizations = {
                'gzip_compression': 'gzip on' in nginx_config,
                'keepalive_timeout': 'keepalive_timeout' in nginx_config,
                'worker_processes': 'worker_processes' in nginx_config,
                'sendfile': 'sendfile on' in nginx_config,
                'tcp_nopush': 'tcp_nopush on' in nginx_config
            }
            
            for opt_name, opt_enabled in nginx_optimizations.items():
                if opt_enabled:
                    optimizations_found.append(f"nginx_{opt_name}")
            
            logger.info(f"Nginx optimizations: {nginx_optimizations}")
        
        # Check Docker performance settings
        with open('docker-compose.yml', 'r') as f:
            compose_config = yaml.safe_load(f)
        
        # Check for volumes (better than bind mounts for performance)
        volumes = compose_config.get('volumes', {})
        if volumes:
            optimizations_found.append('docker_volumes')
        
        # Check for networks (better than default bridge)
        networks = compose_config.get('networks', {})
        if networks:
            optimizations_found.append('docker_networks')
        
        logger.info(f"Performance optimizations found: {optimizations_found}")
        
        return len(optimizations_found) >= 4
        
    except Exception as e:
        logger.error(f"Performance optimizations test failed: {e}")
        return False

def main():
    """Run scalability tests"""
    logger.info("Starting scalability feature tests...")
    
    tests = [
        ("Production Resource Limits", test_production_resource_limits),
        ("Horizontal Scaling Configuration", test_horizontal_scaling_configuration),
        ("Load Balancing Configuration", test_load_balancing_configuration),
        ("Monitoring and Observability", test_monitoring_and_observability),
        ("Caching Mechanisms", test_caching_mechanisms),
        ("Performance Optimizations", test_performance_optimizations)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            logger.info(f"{test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"{test_name}: FAILED - {e}")
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    logger.info(f"\nScalability Test Summary:")
    logger.info(f"Passed: {passed_tests}/{total_tests}")
    logger.info(f"Pass Rate: {passed_tests/total_tests:.2%}")
    
    overall_passed = passed_tests >= (total_tests * 0.7)  # 70% pass rate for scalability
    logger.info(f"Overall Result: {'PASSED' if overall_passed else 'FAILED'}")
    
    return overall_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)