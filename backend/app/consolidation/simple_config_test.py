#!/usr/bin/env python3
"""
Simple test to verify configuration consolidation works.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def test_config():
    """Test basic configuration functionality."""
    print("Testing configuration consolidation...")
    
    try:
        # Test new imports
        from app.core.config import get_config_manager, get_config_value, get_settings
        
        # Test configuration manager
        config_manager = get_config_manager()
        print(f"✅ Config manager: {type(config_manager).__name__}")
        
        # Test settings
        settings = get_settings()
        print(f"✅ Settings: {settings.api_host}:{settings.api_port}")
        
        # Test config value
        debug = get_config_value("DEBUG", True)
        print(f"✅ Config value DEBUG: {debug}")
        
        print("✅ Configuration consolidation working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_config()