from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click
import yaml

from .orchestrator import TestOrchestrator, TestPhase
from .test_reporter import TestReporter

logger = logging.getLogger(__name__)


def load_test_config(config_path: Path) -> dict:
	"""Load test configuration from YAML file."""
	with open(config_path) as f:
		return yaml.safe_load(f)


async def run_test_suite(
	config_path: Path,
	output_dir: Path,
	phases: Optional[List[str]] = None,
	parallel: bool = True,
) -> str:
	"""Run the test suite with the specified configuration."""
	run_id = f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

	# Load configuration
	config = load_test_config(config_path)

	# Initialize orchestrator and reporter
	orchestrator = TestOrchestrator()
	reporter = TestReporter(output_dir)

	# Register tests from configuration, if present
	for test_config in config.get("tests", []):
		phase_name = str(test_config.get("phase", "feature_validation")).upper()
		try:
			phase = TestPhase[phase_name]
		except KeyError:
			phase = TestPhase.FEATURE_VALIDATION

		orchestrator.add_test(
			test_id=test_config.get("id", f"test_{uuid.uuid4().hex[:6]}"),
			phase=phase,
			dependencies=test_config.get("dependencies", []),
		)

	# Filter phases if specified (affects orchestrator scheduling, not raw config)
	if phases:
		valid_phases = {p.upper() for p in phases}
		orchestrator.filter_phases(valid_phases)

	try:
		logger.info(f"Starting test run {run_id}")
		results = await orchestrator.run_tests(parallel=parallel)

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
	"--config",
	type=click.Path(exists=True, path_type=Path),
	required=True,
	help="Path to test configuration file",
)
@click.option(
	"--output-dir",
	type=click.Path(path_type=Path),
	default=Path("test_reports"),
	help="Directory for test reports",
)
@click.option(
	"--phases",
	multiple=True,
	help="Specific test phases to run (e.g., unit, integration)",
)
@click.option(
	"--parallel/--no-parallel",
	default=True,
	help="Enable/disable parallel test execution",
)
def main(config: Path, output_dir: Path, phases: List[str], parallel: bool):
	"""Run the test suite with the specified configuration."""
	try:
		run_id = asyncio.run(run_test_suite(config, output_dir, list(phases) or None, parallel))
		logger.info(f"Test run {run_id} completed successfully")
	except Exception as e:
		logger.error(f"Test execution failed: {e!s}")
		raise click.ClickException(str(e))


if __name__ == "__main__":
	main()
