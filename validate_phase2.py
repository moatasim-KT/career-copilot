#!/usr/bin/env python3
"""
Phase 2 Validation Script
Validates that all Phase 2 components can be imported and initialized.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def validate_imports():
    """Validate all Phase 2 imports."""
    print("Validating Phase 2 imports...\n")
    
    errors = []
    
    # Test optimizer imports
    try:
        from backend.app.services.groq_optimizer import (
            GROQOptimizer,
            GROQOptimizationConfig,
            OptimizationStrategy,
            get_groq_optimizer
        )
        print("✅ GROQ Optimizer imports successful")
    except Exception as e:
        errors.append(f"❌ GROQ Optimizer import failed: {e}")
        print(errors[-1])
    
    # Test router imports
    try:
        from backend.app.services.groq_router import (
            GROQModelRouter,
            RoutingStrategy,
            RoutingDecision,
            get_groq_router
        )
        print("✅ GROQ Router imports successful")
    except Exception as e:
        errors.append(f"❌ GROQ Router import failed: {e}")
        print(errors[-1])
    
    # Test monitor imports
    try:
        from backend.app.services.groq_monitor import (
            GROQMonitor,
            MonitoringConfig,
            AlertLevel,
            get_groq_monitor
        )
        print("✅ GROQ Monitor imports successful")
    except Exception as e:
        errors.append(f"❌ GROQ Monitor import failed: {e}")
        print(errors[-1])
    
    # Test base service
    try:
        from backend.app.services.groq_service import (
            GROQService,
            GROQModel,
            GROQTaskType,
            get_groq_service
        )
        print("✅ GROQ Service imports successful")
    except Exception as e:
        errors.append(f"❌ GROQ Service import failed: {e}")
        print(errors[-1])
    
    return errors


def validate_initialization():
    """Validate component initialization."""
    print("\n\nValidating Phase 2 initialization...\n")
    
    errors = []
    
    # Test optimizer initialization
    try:
        from backend.app.services.groq_optimizer import GROQOptimizationConfig, GROQOptimizer
        config = GROQOptimizationConfig()
        optimizer = GROQOptimizer(config)
        print("✅ GROQ Optimizer initialization successful")
    except Exception as e:
        errors.append(f"❌ GROQ Optimizer initialization failed: {e}")
        print(errors[-1])
    
    # Test router initialization
    try:
        from backend.app.services.groq_service import GROQService
        from backend.app.services.groq_router import GROQModelRouter
        service = GROQService()
        router = GROQModelRouter(service)
        print("✅ GROQ Router initialization successful")
    except Exception as e:
        errors.append(f"❌ GROQ Router initialization failed: {e}")
        print(errors[-1])
    
    # Test monitor initialization
    try:
        from backend.app.services.groq_service import GROQService
        from backend.app.services.groq_monitor import GROQMonitor, MonitoringConfig
        service = GROQService()
        config = MonitoringConfig()
        monitor = GROQMonitor(service, config)
        print("✅ GROQ Monitor initialization successful")
    except Exception as e:
        errors.append(f"❌ GROQ Monitor initialization failed: {e}")
        print(errors[-1])
    
    return errors


def main():
    """Run validation."""
    print("=" * 60)
    print("Phase 2 Validation")
    print("=" * 60)
    
    import_errors = validate_imports()
    init_errors = validate_initialization()
    
    all_errors = import_errors + init_errors
    
    print("\n" + "=" * 60)
    if not all_errors:
        print("✅ All Phase 2 validations passed!")
        print("=" * 60)
        return 0
    else:
        print(f"❌ {len(all_errors)} validation error(s) found:")
        for error in all_errors:
            print(f"  - {error}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
