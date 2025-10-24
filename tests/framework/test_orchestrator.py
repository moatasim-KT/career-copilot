"""Test execution orchestrator for managing test phases and dependencies."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import networkx as nx

logger = logging.getLogger(__name__)


class TestPhase(Enum):
    """Test execution phases."""
    SETUP = "setup"
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    E2E = "e2e"
    CLEANUP = "cleanup"


class TestStatus(Enum):
    """Test execution status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Test execution result."""
    test_id: str
    phase: TestPhase
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = None


class TestOrchestrator:
    """Orchestrates test execution across different phases with dependency management."""

    def __init__(self):
        self.dependency_graph = nx.DiGraph()
        self.results: Dict[str, TestResult] = {}
        self.current_phase: Optional[TestPhase] = None
        self.start_time = datetime.now()

    def add_test(self, test_id: str, phase: TestPhase, dependencies: List[str] = None):
        """Add a test to the orchestrator with its dependencies."""
        if test_id in self.dependency_graph:
            raise ValueError(f"Test {test_id} already exists")

        self.dependency_graph.add_node(test_id, phase=phase)
        if dependencies:
            for dep in dependencies:
                if dep not in self.dependency_graph:
                    raise ValueError(f"Dependency {dep} not found")
                self.dependency_graph.add_edge(dep, test_id)

    async def run_tests(self) -> Dict[str, TestResult]:
        """Run all tests in the correct order based on dependencies."""
        try:
            for phase in TestPhase:
                await self._run_phase(phase)
            return self.results
        finally:
            await self._generate_execution_report()

    async def _run_phase(self, phase: TestPhase):
        """Run all tests in a specific phase."""
        logger.info(f"Starting test phase: {phase.value}")
        self.current_phase = phase
        
        # Get tests for this phase
        phase_tests = [
            node for node, attrs in self.dependency_graph.nodes(data=True)
            if attrs.get('phase') == phase
        ]
        
        if not phase_tests:
            logger.info(f"No tests found for phase {phase.value}")
            return

        # Group tests by their dependency levels
        levels = self._get_dependency_levels(phase_tests)
        
        for level_tests in levels:
            # Run tests in this level in parallel
            tasks = [self._execute_test(test_id) for test_id in level_tests]
            await asyncio.gather(*tasks)

    def _get_dependency_levels(self, tests: List[str]) -> List[Set[str]]:
        """Group tests by their dependency levels for parallel execution."""
        subgraph = self.dependency_graph.subgraph(tests)
        levels: List[Set[str]] = []
        remaining = set(tests)
        
        while remaining:
            # Find tests with no remaining dependencies
            level = {
                node for node in remaining
                if not any(pred in remaining for pred in subgraph.predecessors(node))
            }
            if not level:
                # Circular dependency detected
                raise ValueError("Circular dependency detected in tests")
            
            levels.append(level)
            remaining -= level

        return levels

    async def _execute_test(self, test_id: str):
        """Execute a single test and record its result."""
        start_time = datetime.now()
        self.results[test_id] = TestResult(
            test_id=test_id,
            phase=self.current_phase,
            status=TestStatus.IN_PROGRESS,
            start_time=start_time
        )

        try:
            # Import and run the test dynamically
            module_path = self._get_test_module_path(test_id)
            if not module_path.exists():
                raise FileNotFoundError(f"Test module not found: {module_path}")

            # Execute test (replace with actual test execution logic)
            await self._run_test_module(test_id, module_path)
            
            self.results[test_id].status = TestStatus.PASSED
            
        except Exception as e:
            logger.error(f"Error executing test {test_id}: {e!s}")
            self.results[test_id].status = TestStatus.ERROR
            self.results[test_id].error_message = str(e)
        
        finally:
            end_time = datetime.now()
            self.results[test_id].end_time = end_time
            self.results[test_id].execution_time = (
                end_time - start_time).total_seconds()

    def _get_test_module_path(self, test_id: str) -> Path:
        """Get the module path for a test."""
        # Convert test_id to path (e.g., "test_analytics.test_data_accuracy" -> "test_analytics/test_data_accuracy.py")
        parts = test_id.split('.')
        return Path('tests') / '/'.join(parts[:-1]) / f"{parts[-1]}.py"

    async def _run_test_module(self, test_id: str, module_path: Path):
        """Run a test module."""
        # This is a placeholder - replace with actual test execution logic
        import importlib.util
        spec = importlib.util.spec_from_file_location(test_id, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find and run test functions/classes
        # This is simplified - replace with proper test discovery and execution
        for attr_name in dir(module):
            if attr_name.startswith('test_'):
                test_func = getattr(module, attr_name)
                if callable(test_func):
                    await test_func()

    async def _generate_execution_report(self):
        """Generate execution report with test results."""
        total_time = (datetime.now() - self.start_time).total_seconds()
        
        summary = {
            'total_tests': len(self.results),
            'passed': sum(1 for r in self.results.values() if r.status == TestStatus.PASSED),
            'failed': sum(1 for r in self.results.values() if r.status == TestStatus.FAILED),
            'error': sum(1 for r in self.results.values() if r.status == TestStatus.ERROR),
            'skipped': sum(1 for r in self.results.values() if r.status == TestStatus.SKIPPED),
            'total_time': total_time
        }
        
        logger.info(f"Test Execution Summary: {summary}")
        return summary        return summary