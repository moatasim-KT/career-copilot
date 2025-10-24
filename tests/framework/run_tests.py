"""Main test runner script that orchestrates test execution and reporting."""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click
import yaml

from .test_orchestrator import TestOrchestrator, TestPhase
from .test_reporter import TestReporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_test_config(config_path: Path) -> dict:
    """Load test configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


async def run_test_suite(
    config_path: Path,
    output_dir: Path,
    phases: Optional[List[str]] = None,
    parallel: bool = True
) -> str:
    """Run the test suite with the specified configuration."""
    # Generate unique run ID
    run_id = f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # Load configuration
    config = load_test_config(config_path)
    
    # Initialize orchestrator and reporter
    orchestrator = TestOrchestrator()
    reporter = TestReporter(output_dir)
    
    # Register tests from configuration
    for test_config in config['tests']:
        orchestrator.add_test(
            test_id=test_config['id'],
            phase=TestPhase[test_config['phase'].upper()],
            dependencies=test_config.get('dependencies', [])
        )
    
    # Filter phases if specified
    if phases:
        valid_phases = [p.upper() for p in phases]
        config['tests'] = [
            t for t in config['tests']
            if t['phase'].upper() in valid_phases
        ]
    
    try:
        # Run tests
        logger.info(f"Starting test run {run_id}")
        results = await orchestrator.run_tests()
        
        # Generate reports
        logger.info("Generating test reports...")
        reporter.save_results(results, run_id)
        json_report = reporter.generate_json_report(results, run_id)
        html_report = reporter.generate_html_report(results, run_id)
        
        logger.info(f"Test reports generated: {json_report}, {html_report}")
        return run_id
        
    except Exception as e:
        logger.error(f"Error during test execution: {e!s}")
        raise


@click.command()
@click.option(
    '--config',
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help='Path to test configuration file'
)
@click.option(
    '--output-dir',
    type=click.Path(path_type=Path),
    default=Path('test_reports'),
    help='Directory for test reports'
)
@click.option(
    '--phases',
    multiple=True,
    help='Specific test phases to run (e.g., unit, integration)'
)
@click.option(
    '--parallel/--no-parallel',
    default=True,
    help='Enable/disable parallel test execution'
)
def main(config: Path, output_dir: Path, phases: List[str], parallel: bool):
    """Run the test suite with the specified configuration."""
    try:
        run_id = asyncio.run(run_test_suite(config, output_dir, phases, parallel))
        logger.info(f"Test run {run_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e!s}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    main()if __name__ == '__main__':
    main()