#!/usr/bin/env python
"""
Command Line Interface for CareerCopilot Test Framework
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import click
import pytest


def load_config(config_path: str) -> dict:
    """Load configuration from JSON file."""
    with open(config_path) as f:
        return json.load(f)

def get_default_config() -> dict:
    """Get default test configuration."""
    return {
        'test_paths': ['tests'],
        'markers': [],
        'parallel': True,
        'max_workers': 4,
        'report_path': 'test-reports',
        'verbose': False,
        'fail_fast': False,
        'timeout': 300,
    }

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """CareerCopilot Test Framework CLI"""
    pass

@cli.command()
@click.option('--suite', '-s', multiple=True, help='Test suite to run (e.g., unit, integration, e2e)')
@click.option('--marker', '-m', multiple=True, help='Only run tests with specified markers')
@click.option('--parallel/--no-parallel', default=True, help='Run tests in parallel')
@click.option('--workers', '-w', default=4, help='Number of worker processes for parallel execution')
@click.option('--report', '-r', default='test-reports', help='Directory for test reports')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--fail-fast', '-f', is_flag=True, help='Stop on first failure')
@click.option('--config', '-c', help='Path to config file')
@click.option('--timeout', '-t', default=300, help='Test timeout in seconds')
def run(suite: tuple, marker: tuple, parallel: bool, workers: int, report: str,
        verbose: bool, fail_fast: bool, config: Optional[str], timeout: int):
    """Run test suites"""
    # Load configuration
    test_config = get_default_config()
    if config:
        test_config.update(load_config(config))

    # Override config with CLI options
    if suite:
        test_paths = []
        for s in suite:
            if s == 'unit':
                test_paths.append('tests/unit')
            elif s == 'integration':
                test_paths.append('tests/integration')
            elif s == 'e2e':
                test_paths.append('tests/e2e')
        test_config['test_paths'] = test_paths
    
    if marker:
        test_config['markers'] = list(marker)
    if not parallel:
        test_config['parallel'] = False
        test_config['max_workers'] = 1
    elif workers:
        test_config['max_workers'] = workers
    if report:
        test_config['report_path'] = report
    if verbose:
        test_config['verbose'] = True
    if fail_fast:
        test_config['fail_fast'] = True
    if timeout:
        test_config['timeout'] = timeout

    # Construct pytest arguments
    pytest_args = []
    
    # Add test paths
    pytest_args.extend(test_config['test_paths'])
    
    # Add markers
    if test_config['markers']:
        pytest_args.append('-m')
        pytest_args.append(' or '.join(test_config['markers']))
    
    # Configure parallelization
    if test_config['parallel']:
        pytest_args.extend(['-n', str(test_config['max_workers'])])
    
    # Add reporting options
    report_path = Path(test_config['report_path'])
    report_path.mkdir(parents=True, exist_ok=True)
    pytest_args.extend([
        f'--html={report_path}/report.html',
        f'--junitxml={report_path}/junit.xml'
    ])
    
    # Add other options
    if test_config['verbose']:
        pytest_args.append('-v')
    if test_config['fail_fast']:
        pytest_args.append('-x')
    
    # Set timeout
    os.environ['PYTEST_TIMEOUT'] = str(test_config['timeout'])
    
    # Run pytest
    sys.exit(pytest.main(pytest_args))

@cli.command()
@click.argument('report-dir', type=click.Path(exists=True))
def report(report_dir):
    """Generate consolidated test report"""
    click.echo(f"Generating consolidated report from {report_dir}")
    # Add report generation logic here

@cli.command()
@click.option('--check-only', is_flag=True, help='Only check if environment is properly configured')
def setup(check_only):
    """Setup test environment"""
    click.echo("Setting up test environment...")
    # Environment setup logic here

if __name__ == '__main__':
    cli()if __name__ == '__main__':
    cli()