#!/usr/bin/env python3
"""
Demo script showing how to use the E2E testing framework.

This script demonstrates the basic usage of the E2E testing framework
for the Career Copilot application.
"""

import asyncio
from tests.e2e.orchestrator import TestOrchestrator


async def main():
    """Run a demo of the E2E testing framework."""
    print("🚀 Career Copilot E2E Testing Framework Demo")
    print("=" * 50)
    
    # Initialize the test orchestrator
    orchestrator = TestOrchestrator()
    
    print(f"✅ Initialized orchestrator")
    print(f"   Backend URL: {orchestrator.environment.backend_url}")
    print(f"   Frontend URL: {orchestrator.environment.frontend_url}")
    print(f"   Database URL: {orchestrator.environment.database_url}")
    print()
    
    # Run selective tests (configuration only for demo)
    print("🔧 Running configuration tests...")
    results = await orchestrator.run_selective_tests(["configuration"])
    
    # Display results
    summary = results["summary"]
    print(f"📊 Test Results:")
    print(f"   Total tests: {summary['total_tests']}")
    print(f"   Passed: {summary['passed']}")
    print(f"   Failed: {summary['failed']}")
    print(f"   Success rate: {summary['success_rate']}%")
    print(f"   Duration: {summary['total_duration']}s")
    print()
    
    # Show test summary
    print(f"📋 {orchestrator.get_test_summary()}")
    
    # Save report
    report_path = orchestrator.save_report()
    print(f"💾 Report saved to: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())