"""
Test the enhanced E2E test orchestrator functionality.

This module tests the orchestrator's phase management, parallel execution,
and dependency management capabilities.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from tests.e2e.orchestrator import (
    TestOrchestrator as E2EOrchestrator, 
    TestStatus as E2ETestStatus, 
    TestPhase as E2ETestPhase, 
    TestSuiteConfig as E2ETestSuiteConfig,
    DependencyManager, 
    PhaseManager
)


class TestDependencyManager:
    """Test the dependency management functionality."""
    
    def test_dependency_manager_initialization(self):
        """Test dependency manager initializes correctly."""
        manager = DependencyManager()
        
        assert manager.dependencies == {}
        assert manager.completed_tests == set()
        assert manager.failed_tests == set()
    
    def test_add_dependency(self):
        """Test adding dependencies."""
        manager = DependencyManager()
        
        manager.add_dependency("test_a", ["test_b", "test_c"])
        
        assert "test_a" in manager.dependencies
        assert manager.dependencies["test_a"] == {"test_b", "test_c"}
    
    def test_can_execute_no_dependencies(self):
        """Test execution check for test with no dependencies."""
        manager = DependencyManager()
        
        assert manager.can_execute("test_a") is True
    
    def test_can_execute_with_completed_dependencies(self):
        """Test execution check with completed dependencies."""
        manager = DependencyManager()
        
        manager.add_dependency("test_a", ["test_b"])
        manager.mark_completed("test_b", True)
        
        assert manager.can_execute("test_a") is True
    
    def test_can_execute_with_failed_dependencies(self):
        """Test execution check with failed dependencies."""
        manager = DependencyManager()
        
        manager.add_dependency("test_a", ["test_b"])
        manager.mark_completed("test_b", False)
        
        assert manager.can_execute("test_a") is False
    
    def test_get_blocked_tests(self):
        """Test getting blocked tests."""
        manager = DependencyManager()
        
        manager.add_dependency("test_a", ["test_b"])
        manager.add_dependency("test_c", ["test_b"])
        manager.mark_completed("test_b", False)
        
        blocked = manager.get_blocked_tests()
        
        assert "test_a" in blocked
        assert "test_c" in blocked


class TestPhaseManager:
    """Test the phase management functionality."""
    
    def test_phase_manager_initialization(self):
        """Test phase manager initializes correctly."""
        manager = PhaseManager()
        
        assert manager.current_phase is None
        assert manager.phase_results == {}
        assert len(manager.phase_order) == 5
    
    def test_get_next_phase(self):
        """Test getting next phase."""
        manager = PhaseManager()
        
        # First phase
        next_phase = manager.get_next_phase()
        assert next_phase == E2ETestPhase.CONFIGURATION
        
        # Set current and get next
        manager.set_current_phase(E2ETestPhase.CONFIGURATION)
        next_phase = manager.get_next_phase()
        assert next_phase == E2ETestPhase.SERVICE_HEALTH
    
    def test_should_continue_to_next_phase(self):
        """Test phase continuation logic."""
        manager = PhaseManager()
        
        # No results - should continue
        assert manager.should_continue_to_next_phase(E2ETestPhase.CONFIGURATION) is True
        
        # Add successful result - should continue
        from tests.e2e.orchestrator import TestResult
        result = TestResult(
            test_name="test",
            status=E2ETestStatus.PASSED,
            phase=E2ETestPhase.CONFIGURATION
        )
        manager.add_phase_result(E2ETestPhase.CONFIGURATION, result)
        
        assert manager.should_continue_to_next_phase(E2ETestPhase.CONFIGURATION) is True


class TestEnhancedOrchestrator:
    """Test the enhanced orchestrator functionality."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator instance."""
        return E2EOrchestrator()
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes with enhanced features."""
        assert orchestrator.dependency_manager is not None
        assert orchestrator.phase_manager is not None
        assert len(orchestrator.test_suites) > 0
        assert orchestrator.max_workers > 0
    
    def test_register_test_suite(self, orchestrator):
        """Test registering a new test suite."""
        suite = E2ETestSuiteConfig(
            name="custom_test",
            phase=E2ETestPhase.FEATURE_VALIDATION,
            dependencies=["backend_health_check"]
        )
        
        orchestrator.register_test_suite(suite)
        
        assert "custom_test" in orchestrator.test_suites
        assert orchestrator.dependency_manager.can_execute("custom_test") is False
    
    def test_can_execute_test(self, orchestrator):
        """Test checking if a test can be executed."""
        # Configuration test should be executable (no dependencies)
        assert orchestrator.can_execute_test("configuration_validation") is True
        
        # Backend health check depends on configuration
        assert orchestrator.can_execute_test("backend_health_check") is False
    
    def test_get_executable_tests(self, orchestrator):
        """Test getting list of executable tests."""
        executable = orchestrator.get_executable_tests()
        
        # Only configuration validation should be executable initially
        assert "configuration_validation" in executable
        assert "backend_health_check" not in executable
    
    def test_reset_execution_state(self, orchestrator):
        """Test resetting orchestrator state."""
        # Add some test results
        orchestrator._add_test_result(
            "test", TestStatus.PASSED, 1.0, "Test message"
        )
        
        assert len(orchestrator.test_results) > 0
        
        # Reset state
        orchestrator.reset_execution_state()
        
        assert len(orchestrator.test_results) == 0
        assert orchestrator.start_time is None
        assert orchestrator.end_time is None
    
    @pytest.mark.asyncio
    async def test_run_single_test_not_found(self, orchestrator):
        """Test running a non-existent test."""
        result = await orchestrator.run_single_test("non_existent_test")
        
        assert "error" in result
        assert "not found" in result["error"]
        assert "available_tests" in result
    
    @pytest.mark.asyncio
    async def test_run_single_test_unmet_dependencies(self, orchestrator):
        """Test running a test with unmet dependencies."""
        result = await orchestrator.run_single_test("backend_health_check")
        
        assert "error" in result
        assert "unmet dependencies" in result["error"]
        assert "dependencies" in result
    
    @pytest.mark.asyncio
    async def test_execute_phase_tests(self, orchestrator):
        """Test executing tests for a specific phase."""
        # Get configuration phase suites
        config_suites = [
            suite for suite in orchestrator.test_suites.values()
            if suite.phase == TestPhase.CONFIGURATION
        ]
        
        assert len(config_suites) > 0
        
        # Execute phase tests
        await orchestrator._execute_phase_tests(TestPhase.CONFIGURATION, config_suites)
        
        # Check that results were recorded
        phase_results = orchestrator.phase_manager.phase_results.get(TestPhase.CONFIGURATION, [])
        assert len(phase_results) > 0
    
    @pytest.mark.asyncio
    async def test_run_selective_tests(self, orchestrator):
        """Test running selective test categories."""
        result = await orchestrator.run_selective_tests(["configuration"])
        
        assert "summary" in result
        assert "results" in result
        assert result["summary"]["total_tests"] > 0
    
    def test_get_phase_summary(self, orchestrator):
        """Test getting phase summary."""
        # Test for non-executed phase
        summary = orchestrator.get_phase_summary(TestPhase.CONFIGURATION)
        assert summary["status"] == "not_executed"
        
        # Add a result and test again
        from tests.e2e.orchestrator import TestResult
        result = TestResult(
            test_name="test",
            status=TestStatus.PASSED,
            phase=TestPhase.CONFIGURATION
        )
        orchestrator.phase_manager.add_phase_result(TestPhase.CONFIGURATION, result)
        
        summary = orchestrator.get_phase_summary(TestPhase.CONFIGURATION)
        assert summary["status"] == "completed"
        assert summary["total_tests"] == 1
        assert summary["passed"] == 1
    
    def test_generate_enhanced_report(self, orchestrator):
        """Test generating enhanced test report."""
        # Add some test results
        orchestrator._add_test_result(
            "test1", TestStatus.PASSED, 1.0, "Test 1", phase=TestPhase.CONFIGURATION
        )
        orchestrator._add_test_result(
            "test2", TestStatus.FAILED, 2.0, "Test 2", phase=TestPhase.SERVICE_HEALTH
        )
        
        report = orchestrator.generate_test_report()
        
        assert "summary" in report
        assert "phase_statistics" in report
        assert "dependency_info" in report
        assert "test_suites" in report
        
        # Check phase statistics
        assert TestPhase.CONFIGURATION.value in report["phase_statistics"]
        assert TestPhase.SERVICE_HEALTH.value in report["phase_statistics"]
        
        # Check summary includes parallel execution info
        assert "parallel_execution_enabled" in report["summary"]
        assert "max_workers" in report["summary"]


if __name__ == "__main__":
    pytest.main([__file__])