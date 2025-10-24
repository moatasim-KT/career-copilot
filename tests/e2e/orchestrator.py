"""
E2E Test Orchestrator for Career Copilot Application

This module provides the main test orchestrator class that manages
the execution of end-to-end tests with configuration management,
parallel execution support, and comprehensive reporting.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import yaml
from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    """Test execution status enumeration."""
    
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestPhase(str, Enum):
    """Test execution phases."""
    
    CONFIGURATION = "configuration"
    SERVICE_HEALTH = "service_health"
    FEATURE_VALIDATION = "feature_validation"
    INTEGRATION = "integration"
    CLEANUP = "cleanup"


class TestResult(BaseModel):
    """Test result data model."""
    
    test_name: str
    status: TestStatus
    duration: float = 0.0
    message: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    error_traceback: Optional[str] = None
    phase: Optional[TestPhase] = None


class TestSuiteConfig(BaseModel):
    """Configuration for individual test suites."""
    
    name: str
    enabled: bool = True
    timeout: int = 300  # 5 minutes default
    retry_count: int = 0
    parallel: bool = False
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    phase: TestPhase = TestPhase.FEATURE_VALIDATION


class TestEnvironment(BaseModel):
    """Test environment configuration."""
    
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    database_url: str = "sqlite:///./test.db"
    test_user_credentials: Dict[str, str] = Field(default_factory=dict)
    external_service_configs: Dict[str, Any] = Field(default_factory=dict)
    timeout_settings: Dict[str, int] = Field(default_factory=lambda: {
        "individual_test_timeout": 120,
        "test_class_timeout": 600,
        "total_suite_timeout": 1800
    })


class DependencyManager:
    """Manages test dependencies and execution order."""
    
    def __init__(self):
        self.dependencies: Dict[str, Set[str]] = {}
        self.completed_tests: Set[str] = set()
        self.failed_tests: Set[str] = set()
    
    def add_dependency(self, test_name: str, depends_on: List[str]):
        """Add dependencies for a test."""
        self.dependencies[test_name] = set(depends_on)
    
    def can_execute(self, test_name: str) -> bool:
        """Check if a test can be executed based on its dependencies."""
        if test_name not in self.dependencies:
            return True
        
        required_deps = self.dependencies[test_name]
        
        # Check if any required dependency has failed
        if required_deps.intersection(self.failed_tests):
            return False
        
        # Check if all dependencies are completed
        return required_deps.issubset(self.completed_tests)
    
    def mark_completed(self, test_name: str, success: bool):
        """Mark a test as completed."""
        if success:
            self.completed_tests.add(test_name)
        else:
            self.failed_tests.add(test_name)
    
    def get_blocked_tests(self) -> List[str]:
        """Get tests that are blocked by failed dependencies."""
        blocked = []
        for test_name, deps in self.dependencies.items():
            if test_name not in self.completed_tests and test_name not in self.failed_tests:
                if deps.intersection(self.failed_tests):
                    blocked.append(test_name)
        return blocked


class PhaseManager:
    """Manages test execution phases and their order."""
    
    def __init__(self):
        self.phase_order = [
            TestPhase.CONFIGURATION,
            TestPhase.SERVICE_HEALTH,
            TestPhase.FEATURE_VALIDATION,
            TestPhase.INTEGRATION,
            TestPhase.CLEANUP
        ]
        self.phase_results: Dict[TestPhase, List[TestResult]] = {}
        self.current_phase: Optional[TestPhase] = None
    
    def get_next_phase(self) -> Optional[TestPhase]:
        """Get the next phase to execute."""
        if self.current_phase is None:
            return self.phase_order[0]
        
        try:
            current_index = self.phase_order.index(self.current_phase)
            if current_index + 1 < len(self.phase_order):
                return self.phase_order[current_index + 1]
        except ValueError:
            pass
        
        return None
    
    def set_current_phase(self, phase: TestPhase):
        """Set the current execution phase."""
        self.current_phase = phase
        if phase not in self.phase_results:
            self.phase_results[phase] = []
    
    def add_phase_result(self, phase: TestPhase, result: TestResult):
        """Add a test result to a specific phase."""
        if phase not in self.phase_results:
            self.phase_results[phase] = []
        self.phase_results[phase].append(result)
    
    def should_continue_to_next_phase(self, phase: TestPhase) -> bool:
        """Determine if execution should continue to the next phase."""
        if phase not in self.phase_results:
            return True
        
        results = self.phase_results[phase]
        if not results:
            return True
        
        # For critical phases, stop if there are failures
        if phase in [TestPhase.CONFIGURATION, TestPhase.SERVICE_HEALTH]:
            failed_results = [r for r in results if r.status in [TestStatus.FAILED, TestStatus.ERROR]]
            return len(failed_results) == 0
        
        return True
class TestOrchestrator:
    """
    Main test orchestrator for managing E2E test execution.
    
    This class coordinates the execution of different test suites,
    manages configuration, handles parallel execution, and generates
    comprehensive test reports.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize the test orchestrator.
        
        Args:
            config_path: Path to configuration file. If None, uses default config.
        """
        self.config_path = Path(config_path) if config_path else Path("tests/e2e/test_config.json")
        self.logger = self._setup_logging()
        self.test_results: List[TestResult] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Load configuration
        self.config = self._load_configuration()
        self.environment = self._load_environment_config()
        
        # Initialize managers
        self.dependency_manager = DependencyManager()
        self.phase_manager = PhaseManager()
        
        # Test suite registry
        self.test_suites: Dict[str, TestSuiteConfig] = {}
        self._register_default_test_suites()
        
        # Parallel execution settings
        self.max_workers = self.config.get("parallel_execution", {}).get("max_workers", 4)
        self.parallel_enabled = self.config.get("parallel_execution", {}).get("enabled", False)
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the orchestrator."""
        logger = logging.getLogger("e2e_orchestrator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load test configuration from file."""
        try:
            # Try JSON config first
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            
            # Try YAML config as fallback
            yaml_config_path = self.config_path.with_suffix('.yaml')
            if yaml_config_path.exists():
                with open(yaml_config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            
            # Fall back to environment variables
            return self._load_config_from_env()
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _load_config_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            "base_url": os.environ.get("E2E_BASE_URL", "http://localhost:8000"),
            "frontend_url": os.environ.get("E2E_FRONTEND_URL", "http://localhost:3000"),
            "default_timeout_seconds": int(os.environ.get("E2E_TIMEOUT", "10")),
            "parallel_execution": {
                "enabled": os.environ.get("E2E_PARALLEL", "false").lower() == "true",
                "max_workers": int(os.environ.get("E2E_MAX_WORKERS", "4"))
            }
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when config file is not available."""
        return {
            "test_execution_settings": {
                "timeout_settings": {
                    "individual_test_timeout": 120,
                    "test_class_timeout": 600,
                    "total_suite_timeout": 1800
                },
                "retry_settings": {
                    "max_retries": 2,
                    "retry_delay": 5
                },
                "parallel_execution": {
                    "enabled": False,
                    "max_workers": 4
                }
            }
        }
    
    def _load_environment_config(self) -> TestEnvironment:
        """Load environment configuration."""
        env_config = self.config.get("environment", {})
        return TestEnvironment(**env_config)
    
    def _register_default_test_suites(self):
        """Register default test suites with their configurations."""
        default_suites = [
            TestSuiteConfig(
                name="configuration_validation",
                phase=TestPhase.CONFIGURATION,
                timeout=60,
                parallel=False,
                dependencies=[]
            ),
            TestSuiteConfig(
                name="backend_health_check",
                phase=TestPhase.SERVICE_HEALTH,
                timeout=120,
                parallel=True,
                dependencies=["configuration_validation"]
            ),
            TestSuiteConfig(
                name="frontend_health_check",
                phase=TestPhase.SERVICE_HEALTH,
                timeout=120,
                parallel=True,
                dependencies=["configuration_validation"]
            ),
            TestSuiteConfig(
                name="database_health_check",
                phase=TestPhase.SERVICE_HEALTH,
                timeout=120,
                parallel=True,
                dependencies=["configuration_validation"]
            ),
            TestSuiteConfig(
                name="job_scraping_test",
                phase=TestPhase.FEATURE_VALIDATION,
                timeout=300,
                parallel=True,
                dependencies=["backend_health_check", "database_health_check"]
            ),
            TestSuiteConfig(
                name="job_recommendation_test",
                phase=TestPhase.FEATURE_VALIDATION,
                timeout=300,
                parallel=True,
                dependencies=["backend_health_check", "database_health_check"]
            ),
            TestSuiteConfig(
                name="skill_gap_analysis_test",
                phase=TestPhase.FEATURE_VALIDATION,
                timeout=300,
                parallel=True,
                dependencies=["backend_health_check"]
            ),
            TestSuiteConfig(
                name="course_recommendation_test",
                phase=TestPhase.FEATURE_VALIDATION,
                timeout=300,
                parallel=True,
                dependencies=["backend_health_check"]
            ),
            TestSuiteConfig(
                name="notification_system_test",
                phase=TestPhase.FEATURE_VALIDATION,
                timeout=300,
                parallel=True,
                dependencies=["backend_health_check"]
            ),
            TestSuiteConfig(
                name="analytics_performance_test",
                phase=TestPhase.FEATURE_VALIDATION,
                timeout=300,
                parallel=True,
                dependencies=["backend_health_check", "database_health_check"]
            ),
            TestSuiteConfig(
                name="integration_workflow_test",
                phase=TestPhase.INTEGRATION,
                timeout=600,
                parallel=False,
                dependencies=["job_scraping_test", "job_recommendation_test"]
            )
        ]
        
        for suite in default_suites:
            self.test_suites[suite.name] = suite
            self.dependency_manager.add_dependency(suite.name, suite.dependencies)
    
    def register_test_suite(self, suite_config: TestSuiteConfig):
        """Register a new test suite."""
        self.test_suites[suite_config.name] = suite_config
        self.dependency_manager.add_dependency(suite_config.name, suite_config.dependencies)
        self.logger.info(f"Registered test suite: {suite_config.name}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value (for backward compatibility)."""
        return self.config.get(key, default)
    
    def run_phase(self, name: str) -> None:
        """Run a specific phase (for backward compatibility)."""
        self.logger.info(f"[e2e.orchestrator] run_phase: {name}")
    
    async def run_full_test_suite(self) -> Dict[str, Any]:
        """
        Execute the complete E2E test suite with phase management.
        
        Returns:
            Dictionary containing test execution summary and results.
        """
        self.logger.info("Starting full E2E test suite execution")
        self.start_time = datetime.now()
        
        try:
            # Execute phases in order
            for phase in self.phase_manager.phase_order:
                self.logger.info(f"Starting phase: {phase.value}")
                self.phase_manager.set_current_phase(phase)
                
                # Get test suites for this phase
                phase_suites = [
                    suite for suite in self.test_suites.values()
                    if suite.phase == phase and suite.enabled
                ]
                
                if not phase_suites:
                    self.logger.info(f"No test suites found for phase: {phase.value}")
                    continue
                
                # Execute phase tests
                await self._execute_phase_tests(phase, phase_suites)
                
                # Check if we should continue to next phase
                if not self.phase_manager.should_continue_to_next_phase(phase):
                    self.logger.warning(f"Stopping execution due to failures in phase: {phase.value}")
                    break
            
        except Exception as e:
            self.logger.error(f"Test suite execution failed: {e}")
            self._add_test_result(
                "test_suite_execution",
                TestStatus.ERROR,
                0.0,
                f"Suite execution error: {str(e)}",
                phase=self.phase_manager.current_phase
            )
        finally:
            self.end_time = datetime.now()
        
        return self.generate_test_report()
    
    async def run_selective_tests(self, categories: List[str]) -> Dict[str, Any]:
        """
        Run specific test categories or phases.
        
        Args:
            categories: List of test categories/phases to run.
            
        Returns:
            Dictionary containing test execution summary and results.
        """
        self.logger.info(f"Running selective tests: {categories}")
        self.start_time = datetime.now()
        
        try:
            # Map categories to phases
            phase_mapping = {
                "configuration": TestPhase.CONFIGURATION,
                "health": TestPhase.SERVICE_HEALTH,
                "features": TestPhase.FEATURE_VALIDATION,
                "integration": TestPhase.INTEGRATION,
                "cleanup": TestPhase.CLEANUP
            }
            
            selected_phases = []
            selected_suites = []
            
            for category in categories:
                if category in phase_mapping:
                    selected_phases.append(phase_mapping[category])
                elif category in self.test_suites:
                    selected_suites.append(self.test_suites[category])
                else:
                    self.logger.warning(f"Unknown test category: {category}")
            
            # Execute selected phases
            for phase in selected_phases:
                self.logger.info(f"Starting selective phase: {phase.value}")
                self.phase_manager.set_current_phase(phase)
                
                phase_suites = [
                    suite for suite in self.test_suites.values()
                    if suite.phase == phase and suite.enabled
                ]
                
                await self._execute_phase_tests(phase, phase_suites)
            
            # Execute individual selected suites
            if selected_suites:
                await self._execute_selected_suites(selected_suites)
                    
        except Exception as e:
            self.logger.error(f"Selective test execution failed: {e}")
            self._add_test_result(
                f"selective_tests_{'-'.join(categories)}",
                TestStatus.ERROR,
                0.0,
                f"Selective test error: {str(e)}",
                phase=self.phase_manager.current_phase
            )
        finally:
            self.end_time = datetime.now()
        
        return self.generate_test_report()
    
    async def _execute_phase_tests(self, phase: TestPhase, suites: List[TestSuiteConfig]):
        """Execute all test suites for a specific phase."""
        self.logger.info(f"Executing {len(suites)} test suites for phase: {phase.value}")
        
        # Separate parallel and sequential tests
        parallel_suites = [suite for suite in suites if suite.parallel and self.parallel_enabled]
        sequential_suites = [suite for suite in suites if not suite.parallel or not self.parallel_enabled]
        
        # Execute parallel tests
        if parallel_suites:
            await self._execute_parallel_tests(parallel_suites)
        
        # Execute sequential tests
        for suite in sequential_suites:
            await self._execute_single_test_suite(suite)
    
    async def _execute_parallel_tests(self, suites: List[TestSuiteConfig]):
        """Execute test suites in parallel."""
        self.logger.info(f"Executing {len(suites)} test suites in parallel")
        
        # Create semaphore to limit concurrent executions
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def execute_with_semaphore(suite: TestSuiteConfig):
            async with semaphore:
                return await self._execute_single_test_suite(suite)
        
        # Filter suites that can be executed (dependencies met)
        executable_suites = [
            suite for suite in suites
            if self.dependency_manager.can_execute(suite.name)
        ]
        
        if executable_suites:
            tasks = [execute_with_semaphore(suite) for suite in executable_suites]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_selected_suites(self, suites: List[TestSuiteConfig]):
        """Execute a specific list of test suites."""
        for suite in suites:
            if self.dependency_manager.can_execute(suite.name):
                await self._execute_single_test_suite(suite)
            else:
                self.logger.warning(f"Skipping {suite.name} due to unmet dependencies")
                self._add_test_result(
                    suite.name,
                    TestStatus.SKIPPED,
                    0.0,
                    "Skipped due to unmet dependencies",
                    phase=suite.phase
                )
    
    async def _execute_single_test_suite(self, suite: TestSuiteConfig) -> TestResult:
        """Execute a single test suite with timeout and retry logic."""
        self.logger.info(f"Executing test suite: {suite.name}")
        start_time = datetime.now()
        
        for attempt in range(suite.retry_count + 1):
            try:
                # Execute the test suite with timeout
                result = await asyncio.wait_for(
                    self._run_test_suite_implementation(suite),
                    timeout=suite.timeout
                )
                
                duration = (datetime.now() - start_time).total_seconds()
                
                # Mark dependency completion
                success = result.get("status") == "passed"
                self.dependency_manager.mark_completed(suite.name, success)
                
                test_result = TestResult(
                    test_name=suite.name,
                    status=TestStatus.PASSED if success else TestStatus.FAILED,
                    duration=duration,
                    message=result.get("message", "Test completed"),
                    details=result.get("details", {}),
                    phase=suite.phase
                )
                
                self.test_results.append(test_result)
                self.phase_manager.add_phase_result(suite.phase, test_result)
                
                if success:
                    self.logger.info(f"Test suite {suite.name} completed successfully")
                    return test_result
                else:
                    self.logger.warning(f"Test suite {suite.name} failed: {result.get('message')}")
                    if attempt < suite.retry_count:
                        self.logger.info(f"Retrying {suite.name} (attempt {attempt + 2}/{suite.retry_count + 1})")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return test_result
                
            except asyncio.TimeoutError:
                duration = (datetime.now() - start_time).total_seconds()
                self.logger.error(f"Test suite {suite.name} timed out after {suite.timeout}s")
                
                self.dependency_manager.mark_completed(suite.name, False)
                
                test_result = TestResult(
                    test_name=suite.name,
                    status=TestStatus.ERROR,
                    duration=duration,
                    message=f"Test timed out after {suite.timeout} seconds",
                    phase=suite.phase
                )
                
                self.test_results.append(test_result)
                self.phase_manager.add_phase_result(suite.phase, test_result)
                return test_result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                self.logger.error(f"Test suite {suite.name} failed with error: {e}")
                
                if attempt < suite.retry_count:
                    self.logger.info(f"Retrying {suite.name} (attempt {attempt + 2}/{suite.retry_count + 1})")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
                self.dependency_manager.mark_completed(suite.name, False)
                
                test_result = TestResult(
                    test_name=suite.name,
                    status=TestStatus.ERROR,
                    duration=duration,
                    message=f"Test error: {str(e)}",
                    error_traceback=str(e),
                    phase=suite.phase
                )
                
                self.test_results.append(test_result)
                self.phase_manager.add_phase_result(suite.phase, test_result)
                return test_result
    
    async def _run_test_suite_implementation(self, suite: TestSuiteConfig) -> Dict[str, Any]:
        """Run the actual test suite implementation."""
        # This is a placeholder that will be replaced by actual test implementations
        # For now, simulate test execution
        await asyncio.sleep(0.1)
        
        return {
            "status": "passed",
            "message": f"Test suite {suite.name} completed successfully",
            "details": {
                "suite_name": suite.name,
                "phase": suite.phase.value,
                "simulated": True
            }
        }
    

    
    def _add_test_result(self, test_name: str, status: TestStatus, 
                        duration: float, message: str, details: Optional[Dict[str, Any]] = None,
                        phase: Optional[TestPhase] = None):
        """Add a test result to the results list."""
        result = TestResult(
            test_name=test_name,
            status=status,
            duration=duration,
            message=message,
            details=details or {},
            phase=phase
        )
        self.test_results.append(result)
        
        if phase:
            self.phase_manager.add_phase_result(phase, result)
        
        self.logger.info(f"Test {test_name}: {status.value} ({duration:.2f}s) - {message}")
    
    def generate_test_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive test execution report.
        
        Returns:
            Dictionary containing test summary, results, and metrics.
        """
        total_duration = 0.0
        if self.start_time and self.end_time:
            total_duration = (self.end_time - self.start_time).total_seconds()
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in self.test_results if r.status == TestStatus.FAILED])
        error_tests = len([r for r in self.test_results if r.status == TestStatus.ERROR])
        skipped_tests = len([r for r in self.test_results if r.status == TestStatus.SKIPPED])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Generate phase-specific statistics
        phase_stats = {}
        for phase in TestPhase:
            phase_results = self.phase_manager.phase_results.get(phase, [])
            if phase_results:
                phase_passed = len([r for r in phase_results if r.status == TestStatus.PASSED])
                phase_total = len(phase_results)
                phase_stats[phase.value] = {
                    "total": phase_total,
                    "passed": phase_passed,
                    "failed": len([r for r in phase_results if r.status == TestStatus.FAILED]),
                    "errors": len([r for r in phase_results if r.status == TestStatus.ERROR]),
                    "skipped": len([r for r in phase_results if r.status == TestStatus.SKIPPED]),
                    "success_rate": round((phase_passed / phase_total * 100) if phase_total > 0 else 0, 2)
                }
        
        # Get dependency information
        blocked_tests = self.dependency_manager.get_blocked_tests()
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "skipped": skipped_tests,
                "success_rate": round(success_rate, 2),
                "total_duration": round(total_duration, 2),
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "parallel_execution_enabled": self.parallel_enabled,
                "max_workers": self.max_workers
            },
            "phase_statistics": phase_stats,
            "dependency_info": {
                "completed_tests": list(self.dependency_manager.completed_tests),
                "failed_tests": list(self.dependency_manager.failed_tests),
                "blocked_tests": blocked_tests
            },
            "results": [result.dict() for result in self.test_results],
            "environment": self.environment.dict(),
            "configuration": self.config,
            "test_suites": {name: suite.dict() for name, suite in self.test_suites.items()}
        }
        
        return report
    
    def save_report(self, output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Save test report to file.
        
        Args:
            output_path: Path to save the report. If None, uses default path.
            
        Returns:
            Path where the report was saved.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"tests/e2e/reports/test_report_{timestamp}.json")
        else:
            output_path = Path(output_path)
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_test_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Test report saved to: {output_path}")
        return output_path
    
    def get_failed_tests(self) -> List[TestResult]:
        """Get list of failed test results."""
        return [r for r in self.test_results if r.status in [TestStatus.FAILED, TestStatus.ERROR]]
    
    def get_test_summary(self) -> str:
        """Get a brief text summary of test results."""
        report = self.generate_test_report()
        summary = report["summary"]
        
        parallel_info = f" (parallel: {self.parallel_enabled})" if self.parallel_enabled else ""
        
        return (
            f"E2E Test Summary: "
            f"{summary['passed']}/{summary['total_tests']} passed "
            f"({summary['success_rate']}% success rate) "
            f"in {summary['total_duration']}s{parallel_info}"
        )
    
    def get_phase_summary(self, phase: TestPhase) -> Dict[str, Any]:
        """Get summary for a specific phase."""
        phase_results = self.phase_manager.phase_results.get(phase, [])
        
        if not phase_results:
            return {"phase": phase.value, "status": "not_executed", "tests": 0}
        
        passed = len([r for r in phase_results if r.status == TestStatus.PASSED])
        total = len(phase_results)
        
        return {
            "phase": phase.value,
            "status": "completed",
            "total_tests": total,
            "passed": passed,
            "failed": len([r for r in phase_results if r.status == TestStatus.FAILED]),
            "errors": len([r for r in phase_results if r.status == TestStatus.ERROR]),
            "success_rate": round((passed / total * 100) if total > 0 else 0, 2)
        }
    
    def can_execute_test(self, test_name: str) -> bool:
        """Check if a specific test can be executed."""
        return self.dependency_manager.can_execute(test_name)
    
    def get_executable_tests(self) -> List[str]:
        """Get list of tests that can currently be executed."""
        return [
            name for name in self.test_suites.keys()
            if self.dependency_manager.can_execute(name)
        ]
    
    def reset_execution_state(self):
        """Reset the orchestrator state for a new execution."""
        self.test_results.clear()
        self.start_time = None
        self.end_time = None
        self.dependency_manager = DependencyManager()
        self.phase_manager = PhaseManager()
        
        # Re-register dependencies
        for suite in self.test_suites.values():
            self.dependency_manager.add_dependency(suite.name, suite.dependencies)
        
        self.logger.info("Orchestrator state reset for new execution")
    
    async def run_single_test(self, test_name: str) -> Dict[str, Any]:
        """
        Run a single test suite by name.
        
        Args:
            test_name: Name of the test suite to run.
            
        Returns:
            Dictionary containing test result.
        """
        if test_name not in self.test_suites:
            return {
                "error": f"Test suite '{test_name}' not found",
                "available_tests": list(self.test_suites.keys())
            }
        
        if not self.dependency_manager.can_execute(test_name):
            return {
                "error": f"Test suite '{test_name}' cannot be executed due to unmet dependencies",
                "dependencies": self.test_suites[test_name].dependencies,
                "completed_tests": list(self.dependency_manager.completed_tests),
                "failed_tests": list(self.dependency_manager.failed_tests)
            }
        
        self.logger.info(f"Running single test: {test_name}")
        self.start_time = datetime.now()
        
        try:
            suite = self.test_suites[test_name]
            result = await self._execute_single_test_suite(suite)
            
            return {
                "test_name": test_name,
                "result": result.dict(),
                "status": "completed"
            }
        except Exception as e:
            self.logger.error(f"Single test execution failed: {e}")
            return {
                "test_name": test_name,
                "error": str(e),
                "status": "failed"
            }
        finally:
            self.end_time = datetime.now()