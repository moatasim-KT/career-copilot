#!/usr/bin/env python3
"""
Career Copilot Management CLI
Simple wrapper for system and development managers
"""

import sys
import subprocess
from pathlib import Path

def show_help():
    """Show help information"""
    print("""
Career Copilot Management CLI

SYSTEM MANAGEMENT:
  setup                 Complete system setup
  status                Show system status  
  backup [type]         Create backup (full/files/db/config)
  deploy [type]         Deploy system (dev/prod/build)
  validate [type]       Validate system (all/env/app/prod)
  config [action]       Manage config (generate/validate/template/sync)
  cleanup               Clean up system artifacts

DEVELOPMENT:
  dev setup             Setup development environment
  dev start             Start development services
  dev stop              Stop development services
  dev test [type]       Run tests (all/unit/integration/consolidated)
  dev quality           Run code quality checks
  dev docs              Generate documentation
  dev logs [service]    Show service logs

EXAMPLES:
  python manage.py setup
  python manage.py dev start
  python manage.py test unit
  python manage.py backup full
  python manage.py deploy dev
""")

def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    script_dir = Path(__file__).parent / "scripts"
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    # Development commands
    if command == "dev":
        if not args:
            show_help()
            sys.exit(1)
        
        dev_cmd = ["python", str(script_dir / "dev_manager.py")] + args
        sys.exit(subprocess.call(dev_cmd))
    
    # System commands
    elif command in ["setup", "status", "backup", "deploy", "validate", "config", "cleanup"]:
        sys_cmd = ["python", str(script_dir / "system_manager.py"), command]
        
        # Add type/action arguments
        if args:
            if command in ["backup", "deploy", "validate"]:
                sys_cmd.extend(["--type"] + args)
            elif command == "config":
                sys_cmd.extend(["--action"] + args)
            else:
                sys_cmd.extend(args)
        
        sys.exit(subprocess.call(sys_cmd))
    
    # Test shortcut
    elif command == "test":
        test_type = args[0] if args else "all"
        dev_cmd = ["python", str(script_dir / "dev_manager.py"), "test", "--type", test_type]
        sys.exit(subprocess.call(dev_cmd))
    
    # Help
    elif command in ["help", "-h", "--help"]:
        show_help()
        sys.exit(0)
    
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()